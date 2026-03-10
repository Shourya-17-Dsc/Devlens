"""
collect_real_data.py
=====================
Fetches real GitHub developer profiles and builds a labeled
training dataset using proxy scoring.

Run:
    python collect_real_data.py --output dataset.csv --count 500
"""

import asyncio
import argparse
import logging
import math
import time
import json
import httpx
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
# Load GitHub token from environment variable for security
import os
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN environment variable is required. Please set it before running this script.")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
BASE_URL = "https://api.github.com"
SLEEP_BETWEEN_USERS = 1.2   # seconds — stays well within rate limits

# ── Seed usernames (manually curated across all skill levels) ─────────────────
# Add as many as you want. The script will also discover more via GitHub Search.
SEED_USERS = {
    # Expert tier (score ~8.5–10)
    "torvalds": 9.8, "gvanrossum": 9.7, "yyx990803": 9.5,
    "sindresorhus": 9.3, "tj": 9.0, "antirez": 9.2,
    "dhh": 8.8, "kennethreitz": 8.7, "jashkenas": 8.6,
    "nicowillis": 8.5,

    # Advanced tier (score ~6.5–8.4)
    "mxstbr": 8.0, "wesbos": 7.8, "paulirish": 7.9,
    "getify": 7.7, "addyosmani": 7.8, "bmizerany": 7.5,

    # Intermediate tier (score ~3.5–6.4)
    # (These will mostly come from GitHub Search discovery)

    # Beginner tier (score ~0–3.4)
    # (These will mostly come from GitHub Search discovery)
}


# ── GitHub API helpers ────────────────────────────────────────────────────────

async def safe_get(client: httpx.AsyncClient, url: str, params=None) -> dict | list | None:
    """GET with retry on rate limit."""
    for attempt in range(3):
        try:
            resp = await client.get(url, params=params, headers=HEADERS, timeout=15)
            if resp.status_code == 403:
                reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
                wait = max(reset - time.time(), 1)
                logger.warning(f"Rate limited. Waiting {wait:.0f}s...")
                await asyncio.sleep(wait)
                continue
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"Request failed ({attempt+1}/3): {e}")
            await asyncio.sleep(2 ** attempt)
    return None


async def fetch_user_profile(client, username: str) -> dict | None:
    return await safe_get(client, f"{BASE_URL}/users/{username}")


async def fetch_user_repos(client, username: str) -> list:
    data = await safe_get(
        client, f"{BASE_URL}/users/{username}/repos",
        params={"per_page": 100, "sort": "updated", "type": "public"}
    )
    return data or []


async def fetch_languages(client, username: str, repo_name: str) -> dict:
    data = await safe_get(client, f"{BASE_URL}/repos/{username}/{repo_name}/languages")
    return data or {}


async def fetch_commit_activity(client, username: str, repo_name: str) -> list:
    data = await safe_get(
        client, f"{BASE_URL}/repos/{username}/{repo_name}/stats/commit_activity"
    )
    return data if isinstance(data, list) else []


# ── Feature extraction ────────────────────────────────────────────────────────

def _days_since(iso_str: str | None) -> float:
    if not iso_str:
        return 9999.0
    dt = datetime.fromisoformat(iso_str.rstrip("Z")).replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - dt).days


def extract_features(profile: dict, repos: list, languages: dict, commits: list) -> dict:
    """Extract the same 21 features used in the ML model."""
    if not repos:
        repos = []

    n = len(repos)
    stars  = [r.get("stargazers_count", 0) for r in repos]
    forks  = [r.get("forks_count", 0) for r in repos]
    sizes  = [r.get("size", 0) for r in repos]
    orig   = [r for r in repos if not r.get("fork", False)]
    recent = [r for r in repos if _days_since(r.get("pushed_at")) <= 180]

    def sdiv(a, b): return a / b if b > 0 else 0.0

    # Repo features
    total_stars = sum(stars)
    total_forks = sum(forks)
    avg_stars   = sdiv(total_stars, n)

    # Language features
    total_bytes = sum(languages.values()) or 1
    shares = [v / total_bytes for v in languages.values()]
    entropy = -sum(p * math.log2(p) for p in shares if p > 0)
    HIGH_DEMAND = {"Python","TypeScript","Rust","Go","Kotlin","Swift","Dart","Elixir"}

    # Commit features
    weekly_totals = [w.get("total", 0) for w in commits] if commits else []
    commit_freq   = sdiv(sum(weekly_totals), len(weekly_totals)) if weekly_totals else 0
    active_weeks  = sum(1 for t in weekly_totals if t > 0)
    active_ratio  = sdiv(active_weeks, len(weekly_totals)) if weekly_totals else 0

    # Popularity score
    followers = profile.get("followers", 0)
    pop = (math.log1p(total_stars) * 3 +
           math.log1p(total_forks) * 2 +
           math.log1p(followers)   * 1.5)
    popularity_score = min(pop / 0.35, 100.0)

    return {
        "repo_count":              float(n),
        "total_stars":             float(total_stars),
        "total_forks":             float(total_forks),
        "avg_stars_per_repo":      avg_stars,
        "max_stars_single_repo":   float(max(stars, default=0)),
        "fork_ratio":              sdiv(total_forks, n),
        "has_description_ratio":   sdiv(sum(1 for r in repos if r.get("description")), n),
        "avg_repo_size_kb":        sdiv(sum(sizes), n),
        "recent_repo_count":       float(len(recent)),
        "open_source_ratio":       sdiv(len(orig), n),
        "language_diversity":      float(len(languages)),
        "top_language_dominance":  max(shares, default=0.0),
        "high_demand_lang_count":  float(sum(1 for l in languages if l in HIGH_DEMAND)),
        "language_entropy":        entropy,
        "account_age_days":        float(_days_since(profile.get("created_at"))),
        "commit_frequency":        commit_freq,
        "active_weeks_ratio":      active_ratio,
        "follower_count":          float(followers),
        "following_count":         float(profile.get("following", 0)),
        "public_gists_count":      float(profile.get("public_gists", 0)),
        "popularity_score":        popularity_score,
    }


def compute_proxy_label(features: dict, manual_score: float | None = None) -> float:
    """
    Compute a proxy skill score from features.
    If a manual score is provided (for seed users), use it directly.
    """
    if manual_score is not None:
        return manual_score

    f = features
    score = 0.0

    # Stars signal (log-scaled to handle viral repos)
    score += min(math.log1p(f["avg_stars_per_repo"]) * 0.8, 2.5)

    # Commit consistency
    score += min(f["commit_frequency"] * 0.15, 1.5)
    score += f["active_weeks_ratio"] * 1.0

    # Language breadth
    score += min(f["language_diversity"] * 0.12, 1.2)

    # Community recognition
    score += min(math.log1p(f["follower_count"]) * 0.12, 1.0)

    # Documentation habit
    score += f["has_description_ratio"] * 0.6

    # Account maturity
    score += min(f["account_age_days"] / 365 * 0.08, 0.6)

    # Original work
    score += f["open_source_ratio"] * 0.5

    # Popularity composite
    score += min(f["popularity_score"] / 100 * 0.8, 0.8)

    return round(max(0.0, min(score, 10.0)), 2)


# ── GitHub Search: discover more users ───────────────────────────────────────

async def discover_users_via_search(client, count: int = 400) -> list[str]:
    """
    Use GitHub Search API to discover real developers at various skill levels.
    Searches by different follower ranges to get diverse skill distribution.
    """
    queries = [
        # Expert: high followers
        ("followers:>5000", 50),
        ("followers:1000..5000", 80),
        # Advanced: moderate followers
        ("followers:200..1000", 100),
        # Intermediate: some following
        ("followers:50..200 repos:>10", 100),
        # Beginner: low activity
        ("followers:5..50 repos:>3", 100),
        ("repos:1..5 followers:<10", 70),
    ]

    discovered = []
    for query, target in queries:
        if len(discovered) >= count:
            break
        params = {"q": query, "sort": "followers", "per_page": min(target, 100), "page": 1}
        data = await safe_get(client, f"{BASE_URL}/search/users", params=params)
        if data and "items" in data:
            usernames = [item["login"] for item in data["items"]]
            discovered.extend(usernames)
            logger.info(f"Search '{query}' → {len(usernames)} users found")
        await asyncio.sleep(2)  # Search API is stricter: 30 req/min

    return list(dict.fromkeys(discovered))  # deduplicate, preserve order


# ── Per-user data collection ──────────────────────────────────────────────────

async def collect_user_data(client, username: str, manual_score=None) -> dict | None:
    """Collect all data for one user and return a labeled feature row."""
    profile = await fetch_user_profile(client, username)
    if not profile or profile.get("type") != "User":
        return None

    repos = await fetch_user_repos(client, username)
    await asyncio.sleep(0.3)

    # Aggregate languages from top 5 repos by stars
    top_repos = sorted(
        [r for r in repos if not r.get("fork")],
        key=lambda r: r.get("stargazers_count", 0), reverse=True
    )[:5]

    languages: dict[str, int] = {}
    for repo in top_repos:
        lang_data = await fetch_languages(client, username, repo["name"])
        for lang, cnt in lang_data.items():
            languages[lang] = languages.get(lang, 0) + cnt
        await asyncio.sleep(0.2)

    # Commit activity from top 2 repos
    commits = []
    for repo in top_repos[:2]:
        weekly = await fetch_commit_activity(client, username, repo["name"])
        commits.extend(weekly)
        await asyncio.sleep(0.5)  # stats endpoint needs extra breathing room

    features = extract_features(profile, repos, languages, commits)
    label    = compute_proxy_label(features, manual_score)

    return {
        "username":    username,
        "skill_score": label,
        **features,
        "top_languages": ",".join(sorted(languages, key=languages.get, reverse=True)[:3]),
    }


# ── Main orchestrator ─────────────────────────────────────────────────────────

async def build_dataset(output_path: str, target_count: int):
    rows = []

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=20) as client:
        # Phase 1: Seed users (with manual labels)
        logger.info(f"Phase 1: Collecting {len(SEED_USERS)} seed users...")
        for username, manual_score in tqdm(SEED_USERS.items(), desc="Seed users"):
            row = await collect_user_data(client, username, manual_score)
            if row:
                rows.append(row)
            await asyncio.sleep(SLEEP_BETWEEN_USERS)

        # Phase 2: Discover more users via GitHub Search
        remaining = target_count - len(rows)
        if remaining > 0:
            logger.info(f"Phase 2: Discovering {remaining} more users via GitHub Search...")
            discovered = await discover_users_via_search(client, count=remaining + 50)

            already_collected = {r["username"] for r in rows}
            new_users = [u for u in discovered if u not in already_collected]

            for username in tqdm(new_users[:remaining], desc="Discovered users"):
                row = await collect_user_data(client, username)
                if row:
                    rows.append(row)
                await asyncio.sleep(SLEEP_BETWEEN_USERS)
                if len(rows) >= target_count:
                    break

    # Save
    df = pd.DataFrame(rows)
    df = df.dropna()
    df.to_csv(output_path, index=False)

    logger.info(f"\n✅ Dataset saved: {output_path}")
    logger.info(f"   Total rows:     {len(df)}")
    logger.info(f"   Score range:    {df['skill_score'].min():.1f} – {df['skill_score'].max():.1f}")
    logger.info(f"   Score mean:     {df['skill_score'].mean():.2f}")
    logger.info(f"   Score std:      {df['skill_score'].std():.2f}")
    print("\nScore distribution:")
    print(pd.cut(df["skill_score"], bins=[0,2.5,4,6,8,10]).value_counts().sort_index())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output",  default="real_dataset.csv")
    parser.add_argument("--count",   type=int, default=500)
    args = parser.parse_args()
    asyncio.run(build_dataset(args.output, args.count))
