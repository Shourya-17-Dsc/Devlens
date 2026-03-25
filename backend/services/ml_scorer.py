"""
ml_scorer.py
============
Loads the trained skill model and runs inference for a given feature dict.


"""

import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"


class MLScorer:
    """
    Loads the serialised pipeline and scores a developer's feature vector.

    Usage:
        scorer = MLScorer()
        scorer.load()
        score = scorer.predict(feature_dict)
    """

    def __init__(self):
        self._pipeline = None
        self._feature_cols: Optional[list[str]] = None

    def load(self):
        """Load model and feature column list from disk."""
        try:
            import joblib
            model_path   = MODEL_DIR / "skill_model.joblib"
            columns_path = MODEL_DIR / "feature_columns.json"

            if not model_path.exists():
                logger.warning("Model not found — falling back to heuristic scorer.")
                return

            self._pipeline     = joblib.load(model_path)
            self._feature_cols = json.loads(columns_path.read_text())
            logger.info(f"Model loaded from {model_path}")

        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            self._pipeline = None

    def predict(self, features: dict) -> float:
        """
        Predict skill score (0–10) for a feature dict.

        Falls back to heuristic scoring when no model is loaded.

        Args:
            features: dict produced by FeatureEngineer.extract()

        Returns:
            Float skill score in [0.0, 10.0]
        """
        if self._pipeline is not None:
            return self._ml_predict(features)
        return self._heuristic_score(features)

    def _ml_predict(self, features: dict) -> float:
        """Run the trained scikit-learn pipeline."""
        # Build DataFrame with exact column order expected by model
        row = {col: features.get(col, 0.0) for col in self._feature_cols}
        df  = pd.DataFrame([row])
        score = float(self._pipeline.predict(df)[0])
        return round(float(np.clip(score, 0.0, 10.0)), 2)

    def _heuristic_score(self, features: dict) -> float:
        """
        Rule-based fallback scoring.
        Weighted sum of normalised signals → 0–10.

        Used when the model hasn't been trained yet.
        """
        def clamp(v, lo=0.0, hi=1.0):
            return max(lo, min(hi, v))

        weights = {
            "repo_count":         (clamp(features.get("repo_count", 0)      / 50),  0.10),
            "total_stars":        (clamp(features.get("total_stars", 0)      / 500), 0.20),
            "language_diversity": (clamp(features.get("language_diversity",0)/ 8),   0.10),
            "weekly_commit_avg":  (clamp(features.get("weekly_commit_avg",0) / 15),  0.15),
            "commit_consistency": (clamp(features.get("commit_consistency",0)),       0.15),
            "has_readme_ratio":   (clamp(features.get("has_readme_ratio",0)),         0.10),
            "has_license_ratio":  (clamp(features.get("has_license_ratio",0)),        0.05),
            "non_fork_ratio":     (clamp(features.get("non_fork_ratio",0)),            0.05),
            "account_age_years":  (clamp(features.get("account_age_years",0)/ 10),   0.10),
        }

        score = sum(norm_val * weight for norm_val, weight in weights.values())
        return round(score * 10, 2)


# Singleton instance — import and share across modules
scorer = MLScorer()
