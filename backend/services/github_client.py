"""
GitHub API Client Service
=========================
Handles all communication with the GitHub REST API.
"""

import os, time, logging
from typing import Any
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN    = os.getenv("GITHUB_TOKEN", "")
REQUEST_TIMEOUT = 15
MAX_REPOS       = 100

def _headers() -> dict[str, str]:
    h = {"Accept": "application/vnd.github+json",
         "X-GitHub-Api-Version": "2022-11-28"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h

async def _get(client: httpx.AsyncClient, url: str, params=None) -> Any:
    for attempt in range(3):
        try:
            resp = await client.get(url, headers=_headers(), params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404: raise
            if exc.response.status_code in (403, 429):
                time.sleep(2 ** attempt); continue
            raise
        except httpx.RequestError:
            if attempt == 2: raise
            time.sleep(1)

async def fetch_user_profile(username: str) -> dict:
    async with httpx.AsyncClient() as client:
        return await _get(client, f"{GITHUB_API_BASE}/users/{username}")

async def fetch_repositories(username: str) -> list[dict]:
    repos, page = [], 1
    async with httpx.AsyncClient() as client:
        while len(repos) < MAX_REPOS:
            batch = await _get(client, f"{GITHUB_API_BASE}/users/{username}/repos",
                               {"sort":"pushed","direction":"desc","per_page":30,"page":page})
            if not batch: break
            repos.extend(batch); page += 1
    return repos[:MAX_REPOS]

async def fetch_all_languages(username: str, repos: list[dict]) -> dict[str, int]:
    totals: dict[str, int] = {}
    async with httpx.AsyncClient() as client:
        for repo in repos:
            try:
                data = await _get(client, f"{GITHUB_API_BASE}/repos/{username}/{repo['name']}/languages")
                for lang, b in data.items():
                    totals[lang] = totals.get(lang, 0) + b
            except Exception:
                pass
    return totals

async def fetch_commit_activity(username: str, repos: list[dict]) -> list[dict]:
    top = sorted(repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:10]
    all_weeks = []
    async with httpx.AsyncClient() as client:
        for repo in top:
            try:
                w = await _get(client, f"{GITHUB_API_BASE}/repos/{username}/{repo['name']}/stats/commit_activity")
                if isinstance(w, list): all_weeks.extend(w)
            except Exception:
                pass
    return all_weeks

async def collect_all_data(username: str) -> dict:
    profile   = await fetch_user_profile(username)
    repos     = await fetch_repositories(username)
    languages = await fetch_all_languages(username, repos)
    commits   = await fetch_commit_activity(username, repos)
    return {"profile": profile, "repos": repos, "languages": languages,
            "commits": commits, "fetched_at": datetime.now(timezone.utc).isoformat()}
