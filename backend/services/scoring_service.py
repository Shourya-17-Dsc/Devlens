"""
================================================================================
ML Scoring Service
================================================================================
Loads the trained RandomForest model and runs skill score inference.
Also handles the rule-based fallback when no trained model exists,
and generates human-readable strength/weakness analysis.

Architecture Note:
  This service acts as the "brain" of the system. It receives features,
  runs the model (or heuristic fallback), and returns structured analysis.
================================================================================
"""

import os
import math
import logging
from pathlib import Path
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model path — relative to the project root
# ---------------------------------------------------------------------------
MODEL_DIR  = Path(__file__).parent.parent.parent / "ml_training" / "saved_models"
MODEL_PATH = MODEL_DIR / "skill_model.joblib"
SCALER_PATH = MODEL_DIR / "feature_scaler.joblib"


# ---------------------------------------------------------------------------
# Model Loading (lazy singleton)
# ---------------------------------------------------------------------------
_model  = None
_scaler = None

def _load_model():
    """
    Lazy-loads the trained model from disk.
    Falls back gracefully if joblib/model not available.
    """
    global _model, _scaler
    if _model is not None:
        return _model, _scaler

    try:
        import joblib
        if MODEL_PATH.exists():
            _model  = joblib.load(MODEL_PATH)
            _scaler = joblib.load(SCALER_PATH) if SCALER_PATH.exists() else None
            logger.info(f"✅ ML model loaded from {MODEL_PATH}")
        else:
            logger.warning(f"⚠️  Model not found at {MODEL_PATH}. Using heuristic scoring.")
    except ImportError:
        logger.warning("joblib not installed. Using heuristic scoring.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")

    return _model, _scaler


# ---------------------------------------------------------------------------
# Heuristic Scorer (no ML model needed)
# ---------------------------------------------------------------------------

def heuristic_score(features: dict) -> float:
    """
    Rule-based skill score when no trained model is available.
    Weighted sum of key feature groups, each contributing to the 0–10 score.

    This is intentionally transparent so students can understand the scoring logic.
    """
    weights = {
        # Productivity & activity (30%)
        "productivity_score":    2.0,
        "commit_freq_norm":      0.5,
        "recent_activity_ratio": 0.5,

        # Code quality & project scope (25%)
        "avg_repo_size_norm":    0.8,
        "has_large_projects":    0.5,
        "licensed_ratio":        0.5,
        "repos_with_desc":       0.3,
        "topics_diversity":      0.4,

        # Popularity & community impact (25%)
        "popularity_score":      1.5,
        "has_viral_repo":        0.5,
        "follower_score":        0.5,
        "issue_engagement":      0.3,
        "contributes_oss":       0.2,

        # Language breadth (15%)
        "language_diversity":    0.8,
        "uses_typed_language":   0.4,
        "uses_systems_lang":     0.3,
        "language_count_norm":   0.3,

        # Profile completeness (5%)
        "account_age_norm":      0.3,
        "has_blog":              0.1,
        "has_bio":               0.1,
    }

    # Maximum achievable score from weights
    max_score = sum(weights.values())   # ~11.1
    raw_score = sum(
        features.get(feat, 0.0) * weight
        for feat, weight in weights.items()
    )

    # Normalise to 0–10
    return round(min((raw_score / max_score) * 10, 10.0), 2)


# ---------------------------------------------------------------------------
# ML Model Scorer
# ---------------------------------------------------------------------------

def ml_score(features: dict, feature_names: list[str]) -> float:
    """
    Runs inference through the trained RandomForest model.
    Returns a score in [0, 10].
    """
    model, scaler = _load_model()
    if model is None:
        return heuristic_score(features)

    # Build feature array in the correct column order
    X = np.array([[features.get(name, 0.0) for name in feature_names]])

    # Apply the same scaler used during training
    if scaler is not None:
        X = scaler.transform(X)

    prediction = model.predict(X)[0]
    return round(float(np.clip(prediction, 0.0, 10.0)), 2)


# ---------------------------------------------------------------------------
# Strength & Weakness Analysis
# ---------------------------------------------------------------------------

STRENGTH_RULES = [
    # (label, condition_fn)
    ("Backend Development",   lambda f: f.get("uses_typed_language", 0) > 0.5 and f.get("repo_count_norm", 0) > 0.3),
    ("Open Source Impact",    lambda f: f.get("has_viral_repo", 0) > 0.5 or f.get("total_stars_norm", 0) > 0.4),
    ("Polyglot Developer",    lambda f: f.get("language_count_norm", 0) > 0.4 and f.get("language_diversity", 0) > 0.6),
    ("Consistent Contributor",lambda f: f.get("productivity_score", 0) > 0.6),
    ("Systems Programming",   lambda f: f.get("uses_systems_lang", 0) > 0.5),
    ("Documentation Culture", lambda f: f.get("repos_with_desc", 0) > 0.7 and f.get("licensed_ratio", 0) > 0.5),
    ("Community Builder",     lambda f: f.get("follower_score", 0) > 0.3 or f.get("contributes_oss", 0) > 0.5),
    ("Project Architecture",  lambda f: f.get("has_large_projects", 0) > 0.5 and f.get("topics_diversity", 0) > 0.4),
    ("Active Maintainer",     lambda f: f.get("recent_activity_ratio", 0) > 0.5 and f.get("issue_engagement", 0) > 0.3),
]

WEAKNESS_RULES = [
    ("Testing & Quality",     lambda f: f.get("licensed_ratio", 0) < 0.2 and f.get("repos_with_desc", 0) < 0.3),
    ("Documentation",         lambda f: f.get("repos_with_desc", 0) < 0.3),
    ("Low Activity",          lambda f: f.get("productivity_score", 0) < 0.3),
    ("Limited Language Range",lambda f: f.get("language_count_norm", 0) < 0.15),
    ("No Open Source",        lambda f: f.get("popularity_score", 0) < 0.1 and f.get("contributes_oss", 0) < 0.5),
    ("Stale Projects",        lambda f: f.get("recent_activity_ratio", 0) < 0.2),
    ("Small Project Scope",   lambda f: f.get("avg_repo_size_norm", 0) < 0.1 and f.get("repo_count_norm", 0) > 0.2),
    ("No Community Presence", lambda f: f.get("follower_score", 0) < 0.05 and f.get("has_blog", 0) == 0),
]


def identify_strengths(features: dict, max_strengths: int = 4) -> list[str]:
    """Returns up to max_strengths strength areas based on feature thresholds."""
    return [
        label for label, condition in STRENGTH_RULES
        if condition(features)
    ][:max_strengths]


def identify_weaknesses(features: dict, max_weaknesses: int = 3) -> list[str]:
    """Returns up to max_weaknesses weakness areas based on feature thresholds."""
    return [
        label for label, condition in WEAKNESS_RULES
        if condition(features)
    ][:max_weaknesses]


# ---------------------------------------------------------------------------
# Activity Level Classification
# ---------------------------------------------------------------------------

def classify_activity_level(features: dict) -> str:
    """
    Returns a human-readable activity level based on productivity score.
    """
    score = features.get("productivity_score", 0)
    if score >= 0.7:
        return "Very High"
    elif score >= 0.5:
        return "High"
    elif score >= 0.3:
        return "Moderate"
    elif score >= 0.1:
        return "Low"
    else:
        return "Inactive"


# ---------------------------------------------------------------------------
# Full Analysis Builder
# ---------------------------------------------------------------------------

def build_analysis(username: str, github_data: dict, features: dict) -> dict:
    """
    ============================================================
    MAIN ENTRY POINT: Runs the full scoring pipeline and returns
    the structured analysis JSON.
    ============================================================

    Args:
        username    : GitHub username
        github_data : Raw data from github_client
        features    : Feature vector from feature_engineering

    Returns:
        The complete analysis dict as specified in the project spec.
    """
    from backend.services.feature_engineering import get_feature_names

    # ── Score ──────────────────────────────────────────────────────────────
    feature_names = get_feature_names()
    skill_score   = ml_score(features, feature_names)

    # ── Raw stats for display ───────────────────────────────────────────────
    profile     = github_data["profile"]
    repos       = github_data["repositories"]
    lang_totals = github_data["language_totals"]
    own_repos   = [r for r in repos if not r.get("is_fork", False)]

    total_stars      = sum(r.get("stars", 0) for r in own_repos)
    total_forks      = sum(r.get("forks", 0) for r in own_repos)
    top_languages    = list(lang_totals.keys())[:5]
    language_diversity = len(lang_totals)

    # ── Qualitative signals ─────────────────────────────────────────────────
    strengths       = identify_strengths(features)
    weaknesses      = identify_weaknesses(features)
    activity_level  = classify_activity_level(features)

    # ── Repo breakdown ──────────────────────────────────────────────────────
    top_repos = sorted(own_repos, key=lambda r: r.get("stars", 0), reverse=True)[:5]
    top_repos_summary = [
        {
            "name":     r["name"],
            "stars":    r.get("stars", 0),
            "forks":    r.get("forks", 0),
            "language": r.get("language"),
            "topics":   r.get("topics", [])[:3],
        }
        for r in top_repos
    ]

    # ── Language distribution (for charts) ─────────────────────────────────
    lang_total_bytes = sum(lang_totals.values()) or 1
    language_breakdown = {
        lang: round(bytes_count / lang_total_bytes * 100, 1)
        for lang, bytes_count in list(lang_totals.items())[:8]
    }

    return {
        # Core identity
        "username":          username,
        "avatar_url":        profile.get("avatar_url"),
        "name":              profile.get("name") or username,
        "bio":               profile.get("bio"),

        # 🏆 The headline metric
        "skill_score":       skill_score,

        # Repository statistics
        "repo_count":        len(own_repos),
        "total_stars":       total_stars,
        "total_forks":       total_forks,
        "top_repos":         top_repos_summary,

        # Language analysis
        "language_diversity":    language_diversity,
        "top_languages":         top_languages,
        "language_breakdown":    language_breakdown,    # {lang: percent}

        # Activity metrics
        "activity_level":        activity_level,
        "account_age_days":      profile.get("account_age_days"),
        "followers":             profile.get("followers", 0),
        "total_commits_sampled": github_data.get("total_commits_sampled", 0),

        # ML-derived insights
        "strengths":         strengths,
        "weaknesses":        weaknesses,

        # Raw feature vector (for debugging / model retraining)
        "feature_vector":    features,

        # Metadata
        "analyzed_at":       github_data.get("collected_at"),
        "scoring_method":    "ml_model" if _model is not None else "heuristic",
    }
