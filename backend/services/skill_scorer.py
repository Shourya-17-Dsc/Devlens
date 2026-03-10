"""
Skill Scorer Service
====================
Loads the serialised ML model and runs inference.
Also contains the heuristic strength/weakness analyser.

The ML model outputs a raw 0-10 skill score.
Post-processing adds human-readable insights.
"""

import os
import logging
import numpy as np
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent.parent.parent / "ml_training" / "saved_model" / "skill_model.joblib"
SCALER_PATH = Path(__file__).parent.parent.parent / "ml_training" / "saved_model" / "scaler.joblib"

# Feature order MUST match what was used during training
FEATURE_ORDER = [
    "repo_count", "total_stars", "total_forks", "avg_stars_per_repo",
    "max_stars_single_repo", "fork_ratio", "has_description_ratio",
    "avg_repo_size_kb", "recent_repo_count", "open_source_ratio",
    "language_diversity", "top_language_dominance", "high_demand_lang_count",
    "language_entropy", "account_age_days", "commit_frequency",
    "active_weeks_ratio", "follower_count", "following_count",
    "public_gists_count", "popularity_score",
]

# ---------------------------------------------------------------------------
# Model loader (cached at module level)
# ---------------------------------------------------------------------------
_model  = None
_scaler = None

def _load_model():
    global _model, _scaler
    if _model is None:
        if MODEL_PATH.exists():
            _model  = joblib.load(MODEL_PATH)
            _scaler = joblib.load(SCALER_PATH)
            logger.info("ML model loaded from %s", MODEL_PATH)
        else:
            logger.warning("Model not found — using heuristic fallback scorer")
    return _model, _scaler


# ---------------------------------------------------------------------------
# Heuristic fallback (used before model is trained)
# ---------------------------------------------------------------------------

def _heuristic_score(features: dict) -> float:
    """
    Rule-based score (0-10) when the ML model isn't available.
    Weighted sum of normalised features.
    """
    w = {
        "repo_count":          0.10,
        "avg_stars_per_repo":  0.15,
        "language_diversity":  0.10,
        "commit_frequency":    0.15,
        "active_weeks_ratio":  0.15,
        "follower_count":      0.10,
        "popularity_score":    0.15,
        "has_description_ratio": 0.10,
    }
    # Rough normalisation constants
    norms = {
        "repo_count": 100, "avg_stars_per_repo": 50, "language_diversity": 10,
        "commit_frequency": 5, "active_weeks_ratio": 1, "follower_count": 500,
        "popularity_score": 100, "has_description_ratio": 1,
    }
    score = 0.0
    for feat, weight in w.items():
        val = features.get(feat, 0)
        norm = norms.get(feat, 1)
        score += weight * min(val / norm, 1.0) * 10
    return round(min(score, 10.0), 2)


# ---------------------------------------------------------------------------
# ML inference
# ---------------------------------------------------------------------------

def predict_skill_score(features: dict) -> float:
    """Run the ML model (or heuristic fallback) and return a 0-10 float."""
    model, scaler = _load_model()

    if model is None:
        return _heuristic_score(features)

    # Build feature array in the correct column order
    x = np.array([[features.get(f, 0.0) for f in FEATURE_ORDER]])
    x_scaled = scaler.transform(x)
    raw = float(model.predict(x_scaled)[0])
    return round(max(0.0, min(raw, 10.0)), 2)


# ---------------------------------------------------------------------------
# Strength / Weakness analyser
# ---------------------------------------------------------------------------

def analyse_strengths_weaknesses(features: dict,
                                  top_languages: list[str],
                                  repos: list[dict]) -> dict:
    """
    Apply threshold-based rules to tag a developer's strengths
    and areas for improvement.  Returns two lists of strings.
    """
    strengths:   list[str] = []
    weaknesses:  list[str] = []

    # ── Activity ──────────────────────────────────────────────────────────
    if features.get("commit_frequency", 0) >= 3:
        strengths.append("Consistent Contributor")
    elif features.get("commit_frequency", 0) < 0.5:
        weaknesses.append("Low Commit Frequency")

    if features.get("active_weeks_ratio", 0) >= 0.6:
        strengths.append("High Activity Level")

    # ── Repository quality ────────────────────────────────────────────────
    if features.get("has_description_ratio", 0) >= 0.7:
        strengths.append("Good Documentation Habits")
    else:
        weaknesses.append("Needs Better Documentation")

    if features.get("avg_stars_per_repo", 0) >= 5:
        strengths.append("Impactful Projects")

    if features.get("open_source_ratio", 0) >= 0.8:
        strengths.append("Original Work Focused")

    # ── Language diversity ────────────────────────────────────────────────
    if features.get("language_diversity", 0) >= 5:
        strengths.append("Polyglot Developer")
    elif features.get("language_diversity", 0) <= 1:
        weaknesses.append("Limited Language Range")

    # ── Community engagement ──────────────────────────────────────────────
    if features.get("follower_count", 0) >= 100:
        strengths.append("Community Recognized")

    if features.get("public_gists_count", 0) >= 5:
        strengths.append("Knowledge Sharer")

    # ── Testing heuristic (look for test repos / test language) ───────────
    has_tests = any(
        "test" in r.get("name", "").lower() or
        "test" in (r.get("description") or "").lower()
        for r in repos
    )
    if not has_tests:
        weaknesses.append("No Dedicated Test Repositories")

    # ── Language-based domain strengths ───────────────────────────────────
    lang_set = set(top_languages)
    if lang_set & {"Python", "R", "Julia", "Jupyter Notebook"}:
        strengths.append("Data Science / ML")
    if lang_set & {"JavaScript", "TypeScript", "HTML", "CSS", "Vue", "Svelte"}:
        strengths.append("Frontend Development")
    if lang_set & {"Go", "Rust", "C", "C++", "Zig"}:
        strengths.append("Systems Programming")
    if lang_set & {"Java", "Kotlin", "Scala", "C#"}:
        strengths.append("Enterprise / JVM Ecosystem")
    if lang_set & {"Solidity", "Vyper"}:
        strengths.append("Blockchain / Web3")

    # ── Recency check ─────────────────────────────────────────────────────
    if features.get("recent_repo_count", 0) == 0:
        weaknesses.append("No Recent Activity (180 days)")

    return {"strengths": strengths[:6], "weaknesses": weaknesses[:4]}


# ---------------------------------------------------------------------------
# Activity level label
# ---------------------------------------------------------------------------

def classify_activity_level(features: dict) -> str:
    freq  = features.get("commit_frequency", 0)
    ratio = features.get("active_weeks_ratio", 0)
    score = freq * 0.6 + ratio * 10 * 0.4
    if score >= 6:  return "Very High"
    if score >= 3:  return "High"
    if score >= 1:  return "Medium"
    return "Low"
