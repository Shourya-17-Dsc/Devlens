"""
ML Model Training Script
=========================
Trains a RandomForestRegressor (or XGBoost) to predict
developer skill score (0-10) from the engineered feature vector.

Usage:
  python -m ml_training.train_model.train

The "ground truth" dataset is a manually labelled CSV where each row
is a developer and the target column is `skill_score` (0-10).

For bootstrapping the MVP, we use SYNTHETIC data generation
that encodes reasonable domain assumptions. Replace with real
labelled data as the platform grows.
"""

import os, json, logging, joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "saved_model"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Feature order must match skill_scorer.py ──────────────────────────────
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
# Synthetic data generation (domain-knowledge bootstrapping)
# ---------------------------------------------------------------------------

def generate_synthetic_dataset(n: int = 2000) -> pd.DataFrame:
    """
    Generate plausible developer profiles and corresponding skill scores.

    Skill scoring logic:
      - Beginners:      few repos, low stars, 1-2 languages
      - Intermediate:   10-30 repos, growing stars, diverse languages
      - Advanced:       30+ repos, many stars, high commit frequency
      - Expert:         strong community presence, multiple high-star projects
    """
    rng = np.random.default_rng(42)

    rows = []
    for _ in range(n):
        # Sample a "true" skill tier first, then generate correlated features
        tier = rng.choice([0, 1, 2, 3],
                          p=[0.25, 0.35, 0.25, 0.15])   # beginner→expert

        # Base ranges per tier
        repo_base    = [2,  10,  30,  60 ][tier]
        star_base    = [0,   5,  50, 300 ][tier]
        follow_base  = [0,  20, 150, 800 ][tier]
        freq_base    = [0.1, 1,  3,   8  ][tier]

        repo_count         = max(1, int(rng.normal(repo_base, repo_base * 0.4)))
        total_stars        = max(0, int(rng.exponential(max(1, star_base))))
        total_forks        = max(0, int(total_stars * rng.uniform(0.1, 0.5)))
        avg_stars          = total_stars / repo_count
        max_stars          = int(total_stars * rng.uniform(0.3, 0.8))
        fork_ratio         = total_forks / max(1, repo_count)
        desc_ratio         = rng.uniform(0.2 + tier * 0.15, 0.5 + tier * 0.15)
        repo_size_kb       = rng.uniform(100, 5000)
        recent_repos       = min(repo_count, int(rng.poisson(1 + tier * 2)))
        open_src_ratio     = rng.uniform(0.5, 1.0)

        lang_div           = max(1, int(rng.normal(1 + tier * 2, 1)))
        top_dom            = max(0.3, 1.0 - lang_div * 0.08)
        hd_langs           = min(lang_div, int(rng.poisson(tier)))
        lang_entropy       = rng.uniform(0, lang_div * 0.4)

        account_age        = int(rng.uniform(180 + tier * 365, 365 + tier * 1000))
        commit_freq        = max(0, rng.normal(freq_base, freq_base * 0.5))
        active_ratio       = min(1.0, rng.uniform(0.1 + tier * 0.2, 0.4 + tier * 0.2))
        followers          = max(0, int(rng.exponential(max(1, follow_base))))
        following          = max(0, int(followers * rng.uniform(0.3, 2.0)))
        gists              = int(rng.poisson(tier * 3))

        pop_raw = (np.log1p(total_stars) * 3 +
                   np.log1p(total_forks) * 2 +
                   np.log1p(followers)   * 1.5)
        popularity_score = min(pop_raw / 0.35, 100.0)

        # ── Compute a ground-truth skill score (IMPROVED) ────────────────────────────
        # Adjusted to better match real GitHub patterns
        score = 0.0
        
        # Base from tier (0-3 maps to 0-10)
        score += tier * 2.5
        
        # Penalize accounts with very few repos (beginners rarely achieve much)
        if repo_count < 5:
            score -= 2.0
        elif repo_count < 10:
            score -= 0.5
        
        # Stars/impact (logarithmic)
        score += min(np.log1p(total_stars) * 0.5, 2.0)
        
        # Language diversity (real devs know multiple languages)
        score += min(lang_div * 0.3, 1.5)
        
        # Commit consistency (more important than frequency)
        score += min(active_ratio * 1.2, 1.5)
        
        # Community contribution (followers/engagement)
        score += min(np.log1p(followers) * 0.2, 1.0)
        
        # Code quality indicators (documentation)
        score += desc_ratio * 0.8
        
        # Trending (recent activity)
        score += min(recent_repos / max(1, repo_count) * 1.0, 1.0)
        
        # Open source contribution (not just forks)
        score += open_src_ratio * 0.5
        
        # Account maturity (older accounts, more experience)
        score += min(account_age / 1000.0, 1.0)
        
        # Add realistic noise
        noise = rng.normal(0, 0.3)
        score += noise
        
        # Normalize to 0-10 with realistic distribution
        score = round(max(0.5, min(score, 10.0)), 2)

        rows.append([
            repo_count, total_stars, total_forks, avg_stars, max_stars,
            fork_ratio, desc_ratio, repo_size_kb, recent_repos, open_src_ratio,
            lang_div, top_dom, hd_langs, lang_entropy,
            account_age, commit_freq, active_ratio, followers, following,
            gists, popularity_score, score
        ])

    cols = FEATURES + ["skill_score"]
    return pd.DataFrame(rows, columns=cols)


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train(use_xgb: bool = False) -> None:
    logger.info("Generating synthetic training dataset …")
    df = generate_synthetic_dataset(2000)
    logger.info("Dataset: %d rows × %d features", len(df), len(FEATURES))

    X = df[FEATURES].values
    y = df["skill_score"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    # ── Scaler ────────────────────────────────────────────────────────────
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    # ── Model selection ───────────────────────────────────────────────────
    if use_xgb and HAS_XGB:
        logger.info("Training XGBoostRegressor …")
        model = xgb.XGBRegressor(
            n_estimators=200, max_depth=5, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, random_state=42)
    else:
        logger.info("Training RandomForestRegressor …")
        model = RandomForestRegressor(
            n_estimators=200, max_depth=None, min_samples_leaf=3,
            max_features="sqrt", random_state=42, n_jobs=-1)

    model.fit(X_train_s, y_train)

    # ── Evaluation ────────────────────────────────────────────────────────
    y_pred = model.predict(X_test_s)
    mae    = mean_absolute_error(y_test, y_pred)
    r2     = r2_score(y_test, y_pred)
    cv     = cross_val_score(model, X_train_s, y_train, cv=5,
                             scoring="neg_mean_absolute_error")
    logger.info("Test MAE: %.3f | R²: %.3f | CV MAE: %.3f ± %.3f",
                mae, r2, -cv.mean(), cv.std())

    # ── Feature importances ───────────────────────────────────────────────
    if hasattr(model, "feature_importances_"):
        imp = sorted(zip(FEATURES, model.feature_importances_),
                     key=lambda x: -x[1])
        logger.info("Top features: %s", imp[:5])

    # ── Serialise ─────────────────────────────────────────────────────────
    joblib.dump(model,  OUTPUT_DIR / "skill_model.joblib")
    joblib.dump(scaler, OUTPUT_DIR / "scaler.joblib")

    meta = {"mae": mae, "r2": r2, "cv_mae": float(-cv.mean()),
            "n_features": len(FEATURES), "n_train": len(X_train),
            "model_type": type(model).__name__}
    (OUTPUT_DIR / "model_meta.json").write_text(json.dumps(meta, indent=2))

    logger.info("Model saved to %s", OUTPUT_DIR)


if __name__ == "__main__":
    train(use_xgb=HAS_XGB)
