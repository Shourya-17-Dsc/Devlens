"""
GitHub API Client Service
=========================
Handles all communication with the GitHub REST API.
"""

import os, time, logging
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

# Load .env from backend/ regardless of the CWD the server was launched from
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_FILE)

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN    = os.getenv("GITHUB_TOKEN", "")

if not GITHUB_TOKEN:
    logger.warning(
        "⚠️  GITHUB_TOKEN is not set! Running unauthenticated (60 req/hr limit). "
        "Set GITHUB_TOKEN in backend/.env to get 5000 req/hr."
    )
else:
    logger.info("✅ GitHub token loaded — authenticated API calls (5000 req/hr).")
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
            # GitHub stats endpoints return 202 while computing — treat as empty
            if resp.status_code == 202:
                return None
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404: raise
            if exc.response.status_code in (403, 429):
                logger.warning(
                    "GitHub rate-limit / auth error %s on %s (attempt %d/3) — "
                    "check GITHUB_TOKEN in backend/.env",
                    exc.response.status_code, url, attempt + 1
                )
                time.sleep(2 ** attempt); continue
            raise
        except httpx.RequestError as exc:
            logger.warning("GitHub request error on %s: %s (attempt %d/3)", url, exc, attempt + 1)
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
                # w is None when GitHub returns 202 (stats still computing) — skip safely
                if w is not None and isinstance(w, list):
                    all_weeks.extend(w)
            except Exception:
                pass
    return all_weeks

async def fetch_repo_file_names(username: str, repos: list[dict]) -> list[str]:
    """
    Fetch root-level file names from the top 10 most-starred repos.
    Returns a flat, deduplicated list of file/directory names (lowercased).
    This is used by the radar scorer to detect signals like Dockerfile,
    .github/workflows, tests/, requirements.txt, etc.
    """
    top = sorted(repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:10]
    all_files: set[str] = set()
    async with httpx.AsyncClient() as client:
        for repo in top:
            try:
                repo_name = repo.get("name", "")
                branch = repo.get("default_branch", "main")
                tree = await _get(
                    client,
                    f"{GITHUB_API_BASE}/repos/{username}/{repo_name}/git/trees/{branch}",
                    params={"recursive": "0"},  # root level only
                )
                if tree and isinstance(tree.get("tree"), list):
                    for entry in tree["tree"]:
                        name = entry.get("path", "")
                        if name:
                            all_files.add(name.lower())
            except Exception:
                pass
    return list(all_files)


async def collect_all_data(username: str) -> dict:
    profile   = await fetch_user_profile(username)
    repos     = await fetch_repositories(username)
    languages = await fetch_all_languages(username, repos)
    commits   = await fetch_commit_activity(username, repos)
    repo_files= await fetch_repo_file_names(username, repos)

    logger.info(
        "Collected data for '%s': %d repos, %d languages, %d commit-week records",
        username, len(repos), len(languages), len(commits)
    )

    return {
        "profile":    profile,
        "repos":      repos,
        "languages":  languages,
        "commits":    commits,
        "repo_files": repo_files,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }

