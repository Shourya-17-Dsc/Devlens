"""
Feature Engineering Pipeline
==============================
Converts raw GitHub API data into a numerical feature vector
that the ML model can consume.

Each feature is documented with its purpose and expected range.
"""

import math
import logging
from datetime import datetime, timezone
from collections import Counter

logger = logging.getLogger(__name__)

# Languages we consider "modern / in-demand" for a mild bonus
HIGH_DEMAND_LANGUAGES = {
    "Python", "TypeScript", "Rust", "Go", "Kotlin",
    "Swift", "Solidity", "Julia", "Dart", "Elixir",
}

def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    return a / b if b > 0 else default

def _days_since(iso_str: str | None) -> float:
    """Return days elapsed since an ISO-8601 timestamp (or 9999 if missing)."""
    if not iso_str:
        return 9999.0
    dt = datetime.fromisoformat(iso_str.rstrip("Z")).replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - dt).days

# ---------------------------------------------------------------------------
# Individual feature extractors
# ---------------------------------------------------------------------------

def extract_repo_features(repos: list[dict]) -> dict:
    """
    repo_count            – total public repos
    total_stars           – sum of all stargazers
    total_forks           – sum of all forks
    avg_stars_per_repo    – mean stars (signals impact)
    max_stars_single_repo – viral/breakout project indicator
    fork_ratio            – forks / repos (shows code reuse by community)
    has_description_ratio – % repos with a description (documentation habit)
    avg_repo_size_kb      – proxy for code volume
    recent_repo_count     – repos pushed in last 180 days (recency)
    open_source_ratio     – repos without fork origin (original work)
    """
    if not repos:
        return {k: 0.0 for k in [
            "repo_count","total_stars","total_forks","avg_stars_per_repo",
            "max_stars_single_repo","fork_ratio","has_description_ratio",
            "avg_repo_size_kb","recent_repo_count","open_source_ratio"]}

    n = len(repos)
    stars  = [r.get("stargazers_count", 0) for r in repos]
    forks  = [r.get("forks_count", 0)      for r in repos]
    sizes  = [r.get("size", 0)             for r in repos]

    recent = sum(1 for r in repos if _days_since(r.get("pushed_at")) <= 180)
    orig   = sum(1 for r in repos if not r.get("fork", False))
    has_desc = sum(1 for r in repos if r.get("description"))

    return {
        "repo_count":            float(n),
        "total_stars":           float(sum(stars)),
        "total_forks":           float(sum(forks)),
        "avg_stars_per_repo":    _safe_div(sum(stars), n),
        "max_stars_single_repo": float(max(stars, default=0)),
        "fork_ratio":            _safe_div(sum(forks), n),
        "has_description_ratio": _safe_div(has_desc, n),
        "avg_repo_size_kb":      _safe_div(sum(sizes), n),
        "recent_repo_count":     float(recent),
        "open_source_ratio":     _safe_div(orig, n),
    }


def extract_language_features(languages: dict[str, int]) -> dict:
    """
    language_diversity       – unique language count
    top_language_dominance   – byte share of the #1 language (0→1)
    high_demand_lang_count   – count of in-demand languages used
    entropy                  – Shannon entropy of language distribution
    """
    if not languages:
        return {"language_diversity": 0, "top_language_dominance": 0.0,
                "high_demand_lang_count": 0, "language_entropy": 0.0}

    total = sum(languages.values())
    shares = [v / total for v in languages.values()]
    entropy = -sum(p * math.log2(p) for p in shares if p > 0)

    return {
        "language_diversity":     float(len(languages)),
        "top_language_dominance": max(shares, default=0.0),
        "high_demand_lang_count": float(sum(
            1 for l in languages if l in HIGH_DEMAND_LANGUAGES)),
        "language_entropy":       entropy,
    }


def extract_activity_features(commits: list[dict], profile: dict) -> dict:
    """
    account_age_days      – days since account creation
    commit_frequency      – avg weekly commits across sampled repos
    active_weeks_ratio    – fraction of weeks with ≥1 commit
    follower_count        – social proof / community recognition
    following_count       – engagement with community
    public_gists_count    – code snippet sharing habit
    """
    account_age = _days_since(profile.get("created_at"))

    if commits:
        totals = [w.get("total", 0) for w in commits]
        commit_freq    = _safe_div(sum(totals), len(totals))
        active_weeks   = sum(1 for t in totals if t > 0)
        active_ratio   = _safe_div(active_weeks, len(totals))
    else:
        commit_freq  = 0.0
        active_ratio = 0.0

    return {
        "account_age_days":    float(account_age),
        "commit_frequency":    commit_freq,
        "active_weeks_ratio":  active_ratio,
        "follower_count":      float(profile.get("followers", 0)),
        "following_count":     float(profile.get("following", 0)),
        "public_gists_count":  float(profile.get("public_gists", 0)),
    }


def extract_popularity_score(features: dict) -> dict:
    """
    Composite popularity_score (0–100) derived from stars + forks + followers.
    Uses log-scaling to prevent mega-repos from dominating.
    """
    stars     = features.get("total_stars", 0)
    forks     = features.get("total_forks", 0)
    followers = features.get("follower_count", 0)

    score = (math.log1p(stars)     * 3.0 +
             math.log1p(forks)     * 2.0 +
             math.log1p(followers) * 1.5)
    # normalise roughly to 0-100
    normalized = min(score / 0.35, 100.0)

    return {"popularity_score": normalized}


# ---------------------------------------------------------------------------
# Master pipeline
# ---------------------------------------------------------------------------

def build_feature_vector(raw_data: dict) -> dict:
    """
    Entry point for the feature engineering layer.
    Takes raw_data from github_client.collect_all_data()
    and returns a flat dict of floats ready for the ML model.
    """
    profile   = raw_data.get("profile", {})
    repos     = raw_data.get("repos",   [])
    languages = raw_data.get("languages", {})
    commits   = raw_data.get("commits", [])

    repo_feats  = extract_repo_features(repos)
    lang_feats  = extract_language_features(languages)
    act_feats   = extract_activity_features(commits, profile)
    pop_feats   = extract_popularity_score({**repo_feats, **act_feats})

    features = {**repo_feats, **lang_feats, **act_feats, **pop_feats}

    # Derive top languages list (sorted by byte count)
    top_languages = sorted(languages, key=languages.get, reverse=True)[:5]

    logger.info("Feature vector built: %d features", len(features))
    return {"features": features, "top_languages": top_languages,
            "all_languages": languages, "repos": repos}
