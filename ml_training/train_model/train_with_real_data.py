
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

import argparse

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

def load_real_dataset(csv_path: str) -> pd.DataFrame:
    """Load real developer data from CSV."""
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} real developers from {csv_path}")
    
    # Ensure all required features are present
    for feat in FEATURES:
        if feat not in df.columns:
            logger.warning(f"Feature '{feat}' not in CSV, filling with 0")
            df[feat] = 0.0
    
    # Handle missing values
    df[FEATURES] = df[FEATURES].fillna(0.0)
    
    return df

def train_model(X, y):
    """Train an XGBoost or RandomForest regressor."""
    logger.info(f"Training with {len(X)} samples, {len(X.columns)} features")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)
    
    # Create pipeline with scaling
    scaler = StandardScaler()
    
    if HAS_XGB:
        # Use XGBoost (better performance)
        model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
            objective='reg:squarederror'
        )
        logger.info("Training XGBoostRegressor …")
    else:
        # Fallback to RandomForest
        model = RandomForestRegressor(
            n_estimators=200,
            max_depth=12,
            random_state=42,
            n_jobs=-1
        )
        logger.info("Training RandomForestRegressor …")
    
    # Scale and train
    X_train_scaled = scaler.fit_transform(X_train)
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    X_test_scaled = scaler.transform(X_test)
    y_pred = model.predict(X_test_scaled)
    
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    # Cross-validation
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5,
                                scoring='neg_mean_absolute_error')
    cv_mae = -cv_scores.mean()
    cv_std = cv_scores.std()
    
    logger.info(f"Test MAE: {mae:.3f} | R²: {r2:.3f} | CV MAE: {cv_mae:.3f} ± {cv_std:.3f}")
    
    # Feature importance
    importances = model.feature_importances_
    top_features = sorted(zip(X.columns, importances), key=lambda x: x[1], reverse=True)[:5]
    logger.info(f"Top features: {top_features}")
    
    return model, scaler

def save_model(model, scaler, features):
    """Save the trained model and metadata."""
    model_path = OUTPUT_DIR / "skill_model.joblib"
    scaler_path = OUTPUT_DIR / "scaler.joblib"
    columns_path = OUTPUT_DIR / "feature_columns.json"
    
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    
    with open(columns_path, 'w') as f:
        json.dump(features, f)
    
    logger.info(f"Model saved to {OUTPUT_DIR}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to CSV with real developer data")
    args = parser.parse_args()
    
    # Load data
    df = load_real_dataset(args.input)
    
    # Extract features and target
    X = df[FEATURES]
    y = df["skill_score"]
    
    logger.info(f"Dataset: {len(X)} rows × {len(X.columns)} features")
    logger.info(f"Skill score range: {y.min():.2f} – {y.max():.2f}")
    
    # Train
    model, scaler = train_model(X, y)
    
    # Save
    save_model(model, scaler, FEATURES)
    
    logger.info("✅ Training complete!")

if __name__ == "__main__":
    main()
