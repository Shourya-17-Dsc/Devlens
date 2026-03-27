"""
Hybrid ML Model Training Script
================================
Trains on REAL GitHub developer data (primary) augmented with
calibrated synthetic data to prevent overfitting on the small
real dataset (79 rows).

Strategy:
  1. Load real data (real_developers_expanded.csv) → weighted 3x
  2. Generate synthetic data calibrated to real distribution → 500 rows
  3. Combine, train XGBoost/RandomForest, save model

Usage:
  python ml_training/train_model/train_hybrid.py
"""

import os, json, logging, joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR    = Path(__file__).resolve().parent.parent.parent  # Devlens/
OUTPUT_DIR  = Path(__file__).parent.parent / "saved_model"
OUTPUT_DIR.mkdir(exist_ok=True)

REAL_CSV    = ROOT_DIR / "real_developers_expanded.csv"

FEATURES = [
    "repo_count", "total_stars", "total_forks", "avg_stars_per_repo",
    "max_stars_single_repo", "fork_ratio", "has_description_ratio",
    "avg_repo_size_kb", "recent_repo_count", "open_source_ratio",
    "language_diversity", "top_language_dominance", "high_demand_lang_count",
    "language_entropy", "account_age_days", "commit_frequency",
    "active_weeks_ratio", "follower_count", "following_count",
    "public_gists_count", "popularity_score",
]


# ---------------------------------------------------------------------------
# Load real data
# ---------------------------------------------------------------------------

def load_real_data(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    logger.info("Loaded %d real developers from %s", len(df), csv_path)

    # Fill any missing feature columns with 0
    for feat in FEATURES:
        if feat not in df.columns:
            logger.warning("Feature '%s' not found in CSV — filling with 0", feat)
            df[feat] = 0.0

    df[FEATURES] = df[FEATURES].fillna(0.0)
    df["skill_score"] = df["skill_score"].fillna(df["skill_score"].median())
    return df[FEATURES + ["skill_score"]]


# ---------------------------------------------------------------------------
# Generate synthetic data calibrated to real distribution
# ---------------------------------------------------------------------------

def generate_calibrated_synthetic(real_df: pd.DataFrame, n: int = 500) -> pd.DataFrame:
    """
    Generate synthetic samples that respect the real data's statistical
    distribution (mean/std per feature) rather than hard-coded tiers.
    Skill scores are derived from the same formula as the original train.py
    but re-calibrated to the real score distribution.
    """
    rng = np.random.default_rng(999)
    real_mean = real_df[FEATURES].mean()
    real_std  = real_df[FEATURES].std().clip(lower=0.1)

    rows = []
    for _ in range(n):
        # Sample features from a distribution centred on real data statistics
        sample = {}
        for feat in FEATURES:
            val = rng.normal(real_mean[feat], real_std[feat] * 0.8)
            # Clip to non-negative for count/ratio features
            sample[feat] = max(0.0, val)

        # Derive a skill score anchored to real data patterns
        score = 0.0
        rc  = sample["repo_count"]
        ts  = sample["total_stars"]
        ld  = sample["language_diversity"]
        ar  = sample["active_weeks_ratio"]
        fl  = sample["follower_count"]
        dr  = sample["has_description_ratio"]
        rr  = sample["recent_repo_count"]
        osr = sample["open_source_ratio"]
        age = sample["account_age_days"]

        score  = 3.5                                     # base
        score += min(np.log1p(rc)  * 0.6, 2.0)
        score += min(np.log1p(ts)  * 0.5, 2.5)
        score += min(ld            * 0.3, 1.5)
        score += min(ar            * 1.2, 1.5)
        score += min(np.log1p(fl)  * 0.2, 1.0)
        score += dr                * 0.5
        score += min(rr / max(1, rc) * 0.8, 0.8)
        score += osr               * 0.4
        score += min(age / 1500.0, 0.8)
        score += rng.normal(0, 0.25)   # noise

        # Clip to real score range
        real_min = real_df["skill_score"].min()
        real_max = real_df["skill_score"].max()
        score = round(float(np.clip(score, real_min, real_max)), 2)

        rows.append({**sample, "skill_score": score})

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main training routine
# ---------------------------------------------------------------------------

def train():
    # ── 1. Load real data ──────────────────────────────────────────────────
    real_df = load_real_data(REAL_CSV)

    # ── 2. Generate calibrated synthetic augmentation ──────────────────────
    logger.info("Generating 500 calibrated synthetic samples for augmentation …")
    synth_df = generate_calibrated_synthetic(real_df, n=500)

    # ── 3. Combine with real data weighted 3x ─────────────────────────────
    # Repeat real rows 3× so the model prioritises their patterns
    combined = pd.concat([real_df] * 3 + [synth_df], ignore_index=True)
    combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)
    logger.info("Combined dataset: %d rows (real×3 + synthetic)", len(combined))

    X = combined[FEATURES].values
    y = combined["skill_score"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    # ── 4. Scale ───────────────────────────────────────────────────────────
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    # ── 5. Train ───────────────────────────────────────────────────────────
    if HAS_XGB:
        logger.info("Training XGBoostRegressor on hybrid dataset …")
        model = xgb.XGBRegressor(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            objective="reg:squarederror",
        )
    else:
        logger.info("Training RandomForestRegressor on hybrid dataset …")
        model = RandomForestRegressor(
            n_estimators=300,
            max_depth=8,
            min_samples_leaf=4,
            max_features="sqrt",
            random_state=42,
            n_jobs=-1,
        )

    model.fit(X_train_s, y_train)

    # ── 6. Evaluate ────────────────────────────────────────────────────────
    y_pred = model.predict(X_test_s)
    mae = mean_absolute_error(y_test, y_pred)
    r2  = r2_score(y_test, y_pred)
    cv  = cross_val_score(model, X_train_s, y_train, cv=5,
                          scoring="neg_mean_absolute_error")
    logger.info("Test MAE : %.3f | R² : %.3f", mae, r2)
    logger.info("CV  MAE  : %.3f ± %.3f", -cv.mean(), cv.std())

    if hasattr(model, "feature_importances_"):
        imp = sorted(zip(FEATURES, model.feature_importances_), key=lambda x: -x[1])
        logger.info("Top 5 features: %s", imp[:5])

    # ── 7. Save ────────────────────────────────────────────────────────────
    joblib.dump(model,  OUTPUT_DIR / "skill_model.joblib")
    joblib.dump(scaler, OUTPUT_DIR / "scaler.joblib")

    meta = {
        "mae": mae, "r2": r2, "cv_mae": float(-cv.mean()), "cv_std": float(cv.std()),
        "n_features": len(FEATURES), "n_train": len(X_train),
        "model_type": type(model).__name__,
        "data_source": "real_github_hybrid",
        "real_samples": int(len(real_df)),
        "synthetic_samples": 500,
    }
    (OUTPUT_DIR / "model_meta.json").write_text(json.dumps(meta, indent=2))
    logger.info("✅ Model saved to %s", OUTPUT_DIR)


if __name__ == "__main__":
    train()
