

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import logging

from backend.services.github_client      import collect_all_data
from backend.services.feature_engineering import build_feature_vector
from backend.services.skill_scorer        import (
    predict_skill_score, analyse_strengths_weaknesses, classify_activity_level
)
from backend.services.radar_scorer        import extract_skill_radar
from backend.database.db                 import save_analysis, get_cached_analysis

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check():
    """Simple liveness probe — used by Docker healthchecks and load balancers."""
    return {"status": "ok", "service": "github-skill-platform"}


@router.get("/analyze/{username}")
async def analyze_developer(username: str, background_tasks: BackgroundTasks):
    """
    Full developer analysis pipeline:
      1. Check cache (return immediately if fresh enough)
      2. Fetch raw data from GitHub API
      3. Run feature engineering
      4. Score with ML model
      5. Persist to Supabase (async, doesn't block response)
      6. Return structured JSON

    Args:
        username: GitHub login handle (case-insensitive)

    Returns:
        JSON matching the AnalysisResult schema
    """
    username = username.strip().lower()

    # ── 1. Cache check ────────────────────────────────────────────────────
    cached = await get_cached_analysis(username)
    if cached:
        logger.info("Cache hit for '%s'", username)
        return JSONResponse(content={**cached, "source": "cache"})

    # ── 2. GitHub data collection ─────────────────────────────────────────
    try:
        raw_data = await collect_all_data(username)
        logger.info(
            "[%s] Raw data: %d repos, %d languages, %d commit-weeks",
            username,
            len(raw_data.get("repos", [])),
            len(raw_data.get("languages", {})),
            len(raw_data.get("commits", [])),
        )
    except Exception as exc:
        status = getattr(getattr(exc, "response", None), "status_code", 500)
        if status == 404:
            raise HTTPException(status_code=404,
                                detail=f"GitHub user '{username}' not found.")
        raise HTTPException(status_code=502,
                            detail=f"GitHub API error: {exc}")

    # ── 3. Feature engineering ────────────────────────────────────────────
    try:
        eng = build_feature_vector(raw_data)
    except Exception as exc:
        logger.error("Feature engineering failed: %s", exc)
        raise HTTPException(status_code=500,
                            detail="Feature extraction failed.")

    features      = eng["features"]
    top_languages = eng["top_languages"]
    all_languages = eng["all_languages"]
    repos         = eng["repos"]
    profile       = raw_data.get("profile") or {}

    # ── 4. ML scoring ─────────────────────────────────────────────────────
    skill_score    = predict_skill_score(features)
    sw             = analyse_strengths_weaknesses(features, top_languages, repos)
    activity_level = classify_activity_level(features)

    # ── 4b. Skill Radar scoring ───────────────────────────────────────────
    radar_scores = extract_skill_radar(raw_data)

    # ── 5. Build response payload ─────────────────────────────────────────
    # Create language breakdown dict from top languages
    language_breakdown = {lang: all_languages.get(lang, 0) for lang in top_languages}
    
    # Format repos with essential data
    formatted_repos = [
        {
            "name": r.get("name", ""),
            "url": r.get("html_url", ""),
            "description": r.get("description", ""),
            "stars": r.get("stargazers_count", 0),
            "forks": r.get("forks_count", 0),
            "language": r.get("language", "Unknown"),
            "updated_at": r.get("updated_at", ""),
        }
        for r in repos
    ]
    
    result = {
        "username":          username,
        "name":              profile.get("name") or username,
        "avatar_url":        profile.get("avatar_url", ""),
        "bio":               profile.get("bio", ""),
        "skill_score":       skill_score,
        "language_breakdown": language_breakdown,
        "strengths_weaknesses": {
            "strengths": sw["strengths"],
            "weaknesses": sw["weaknesses"],
        },
        "code_metrics": {
            "repo_count":        int(features.get("repo_count", 0)),
            "total_stars":       int(features.get("total_stars", 0)),
            "total_forks":       int(features.get("total_forks", 0)),
            "language_diversity":int(features.get("language_diversity", 0)),
            "activity_level":    activity_level,
            "follower_count":    int(features.get("follower_count", 0)),
            "following_count":   int(features.get("following_count", 0)),
            "avg_stars_per_repo":round(features.get("avg_stars_per_repo", 0), 2),
            "commit_frequency":  round(features.get("commit_frequency", 0), 2),
            "popularity_score":  round(features.get("popularity_score", 0), 2),
            "account_age_days":  int(features.get("account_age_days", 0)),
        },
        "radar_scores":      radar_scores,
        "repositories":      formatted_repos,
        "features":          {k: round(v, 4) for k, v in features.items()},
        "fetched_at":        raw_data["fetched_at"],
        "source":            "live",
    }

    # ── 6. Async DB persist ───────────────────────────────────────────────
    background_tasks.add_task(save_analysis, result)

    return JSONResponse(content=result)


@router.get("/cache/{username}")
async def get_cached(username: str):
    """Return the most recent cached analysis for a user (if any)."""
    cached = await get_cached_analysis(username.lower())
    if not cached:
        raise HTTPException(status_code=404, detail="No cached analysis found.")
    return cached
