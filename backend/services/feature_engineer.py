"""
feature_engineer.py
===================
Converts raw GitHub API data into a flat feature vector for ML scoring.

Every feature is documented with its purpose and expected range.
The output is a dict that maps directly to the ML model's input.
"""

import math
import logging
from collections import Counter
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Domains we recognise from repo topics / language combos
DOMAIN_KEYWORDS = {
    "backend":      ["api", "server", "rest", "graphql", "microservice", "backend", "django", "fastapi", "flask", "express", "rails"],
    "frontend":     ["react", "vue", "angular", "nextjs", "svelte", "frontend", "ui", "css", "tailwind", "webpack"],
    "devops":       ["docker", "kubernetes", "ci", "cd", "terraform", "ansible", "helm", "devops", "deploy", "infrastructure"],
    "ml_ai":        ["machine-learning", "deep-learning", "neural", "nlp", "cv", "pytorch", "tensorflow", "sklearn", "ai", "llm"],
    "data":         ["pandas", "spark", "etl", "pipeline", "analytics", "jupyter", "datascience", "sql", "database"],
    "mobile":       ["android", "ios", "flutter", "react-native", "swift", "kotlin", "mobile"],
    "security":     ["security", "crypto", "auth", "jwt", "oauth", "pentest", "vulnerability"],
    "open_source":  ["hacktoberfest", "contributions", "community", "oss"],
}


class FeatureEngineer:
    """
    Transforms raw collected GitHub data → numerical feature dict.

    The output dict is the input to the ML scoring model.
    All features are normalised to avoid scale issues.
    """

    def extract(self, raw: dict) -> dict:
        """
        Main entry point. Takes the dict returned by GitHubClient.collect_all()
        and returns a flat feature dict.
        """
        profile   = raw.get("profile", {})
        repos     = raw.get("repos", [])
        lang_data = raw.get("language_data", {})
        topics    = raw.get("topics_data", {})
        commits   = raw.get("commit_data", {})

        features = {}
        features.update(self._repo_features(repos))
        features.update(self._language_features(lang_data))
        features.update(self._activity_features(profile, repos, commits))
        features.update(self._popularity_features(repos))
        features.update(self._quality_signals(repos, topics))
        features.update(self._domain_features(repos, topics, lang_data))

        logger.debug(f"Extracted {len(features)} features")
        return features

    # ------------------------------------------------------------------
    # Feature groups
    # ------------------------------------------------------------------

    def _repo_features(self, repos: list) -> dict:
        """
        Measures breadth and volume of repository work.

        Features:
          repo_count          – total public repos owned
          non_fork_ratio      – fraction that are original (not forks)
          avg_repo_size_kb    – average repo size (proxy for code volume)
          has_large_project   – 1 if any repo > 1 MB (signals serious project)
        """
        if not repos:
            return {"repo_count": 0, "non_fork_ratio": 0.0,
                    "avg_repo_size_kb": 0.0, "has_large_project": 0}

        non_forks = [r for r in repos if not r.get("fork")]
        sizes = [r.get("size", 0) for r in repos]

        return {
            "repo_count":       len(repos),
            "non_fork_ratio":   len(non_forks) / len(repos),
            "avg_repo_size_kb": sum(sizes) / len(sizes) if sizes else 0.0,
            "has_large_project": int(any(s > 1000 for s in sizes)),
        }

    def _language_features(self, lang_data: dict) -> dict:
        """
        Measures language breadth and depth.

        Features:
          language_diversity    – number of distinct languages used
          primary_language_pct  – byte % in the most-used language (specialization)
          uses_typed_language   – 1 if TypeScript/Go/Rust/Java used (type discipline)
          uses_systems_language – 1 if C/C++/Rust/Go used (low-level skill)
        """
        # Aggregate byte counts across all repos
        totals: Counter = Counter()
        for lang_map in lang_data.values():
            totals.update(lang_map)

        if not totals:
            return {"language_diversity": 0, "primary_language_pct": 0.0,
                    "uses_typed_language": 0, "uses_systems_language": 0}

        total_bytes   = sum(totals.values())
        top_lang_bytes = totals.most_common(1)[0][1]

        typed_langs   = {"TypeScript", "Go", "Rust", "Java", "Kotlin", "Swift", "C#"}
        systems_langs = {"C", "C++", "Rust", "Go", "Assembly"}
        known_langs   = set(totals.keys())

        return {
            "language_diversity":    len(totals),
            "primary_language_pct":  top_lang_bytes / total_bytes if total_bytes else 0.0,
            "uses_typed_language":   int(bool(known_langs & typed_langs)),
            "uses_systems_language": int(bool(known_langs & systems_langs)),
        }

    def _activity_features(self, profile: dict, repos: list, commit_data: dict) -> dict:
        """
        Measures how actively the developer codes.

        Features:
          account_age_years    – years since account creation
          recent_push_count    – repos with pushes in last 30 days
          weekly_commit_avg    – average weekly commits (from stats endpoint)
          commit_consistency   – fraction of weeks with ≥1 commit (0–1)
        """
        # Account age
        created = profile.get("created_at", "")
        try:
            created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            age_years  = (datetime.now(timezone.utc) - created_dt).days / 365.0
        except Exception:
            age_years = 1.0

        # Repos updated recently (within 90 days)
        now_ts  = datetime.now(timezone.utc).timestamp()
        recent  = 0
        for r in repos:
            pushed = r.get("pushed_at") or ""
            try:
                pushed_dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
                if (now_ts - pushed_dt.timestamp()) < 90 * 86400:
                    recent += 1
            except Exception:
                pass

        # Weekly commit stats
        all_weekly_totals = []
        for weekly_buckets in commit_data.values():
            for bucket in (weekly_buckets or []):
                all_weekly_totals.append(bucket.get("total", 0))

        if all_weekly_totals:
            weekly_avg = sum(all_weekly_totals) / len(all_weekly_totals)
            active_weeks = sum(1 for t in all_weekly_totals if t > 0)
            consistency = active_weeks / len(all_weekly_totals)
        else:
            weekly_avg  = 0.0
            consistency = 0.0

        return {
            "account_age_years":   round(age_years, 2),
            "recent_push_count":   recent,
            "weekly_commit_avg":   round(weekly_avg, 2),
            "commit_consistency":  round(consistency, 2),
        }

    def _popularity_features(self, repos: list) -> dict:
        """
        Social signals that correlate with code quality and impact.

        Features:
          total_stars        – sum of stars across all repos
          total_forks        – sum of forks (people found it useful enough to fork)
          avg_stars_per_repo – average stars, normalised by repo count
          has_viral_repo     – 1 if any single repo has >100 stars
          watcher_score      – log-scaled watcher count (avoids outlier skew)
        """
        if not repos:
            return {"total_stars": 0, "total_forks": 0,
                    "avg_stars_per_repo": 0.0, "has_viral_repo": 0, "watcher_score": 0.0}

        stars  = [r.get("stargazers_count", 0) for r in repos]
        forks  = [r.get("forks_count", 0) for r in repos]
        watchers = [r.get("watchers_count", 0) for r in repos]

        total_stars = sum(stars)
        total_watchers = sum(watchers)

        return {
            "total_stars":        total_stars,
            "total_forks":        sum(forks),
            "avg_stars_per_repo": total_stars / len(repos),
            "has_viral_repo":     int(max(stars) > 100),
            "watcher_score":      math.log1p(total_watchers),
        }

    def _quality_signals(self, repos: list, topics: dict) -> dict:
        """
        Heuristic quality signals derived from repo metadata.

        Features:
          has_readme_ratio    – fraction of repos likely to have a README
                                (approximated by description presence)
          has_license_ratio   – fraction with an open-source license
          has_topics_ratio    – fraction with ≥1 topic tag
          description_avg_len – average description length (documentation effort)
        """
        if not repos:
            return {"has_readme_ratio": 0.0, "has_license_ratio": 0.0,
                    "has_topics_ratio": 0.0, "description_avg_len": 0.0}

        n = len(repos)
        desc_lens  = []
        has_license = 0

        for r in repos:
            desc = r.get("description") or ""
            desc_lens.append(len(desc))
            if r.get("license"):
                has_license += 1

        repos_with_topics = sum(1 for r in repos if topics.get(r["name"]))

        return {
            "has_readme_ratio":   sum(1 for d in desc_lens if d > 0) / n,
            "has_license_ratio":  has_license / n,
            "has_topics_ratio":   repos_with_topics / n,
            "description_avg_len": sum(desc_lens) / n,
        }

    def _domain_features(self, repos: list, topics: dict, lang_data: dict) -> dict:
        """
        One-hot style domain presence flags + strength scores.

        For each domain (backend, frontend, ml_ai, etc.) we compute
        a score 0–1 based on keyword overlap with topics and repo names.
        """
        # Gather all topic strings and repo names
        all_tags = []
        for tag_list in topics.values():
            all_tags.extend(t.lower() for t in tag_list)
        for r in repos:
            all_tags.append(r.get("name", "").lower())
            all_tags.extend((r.get("description") or "").lower().split())

        # Flatten all known languages
        all_langs = set()
        for lang_map in lang_data.values():
            all_langs.update(k.lower() for k in lang_map.keys())

        domain_scores = {}
        for domain, keywords in DOMAIN_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in all_tags or kw in all_langs)
            domain_scores[f"domain_{domain}"] = min(1.0, matches / max(len(keywords) * 0.4, 1))

        return domain_scores

    # ------------------------------------------------------------------
    # Derived analysis helpers (used by the API, not the ML model)
    # ------------------------------------------------------------------

    def get_top_languages(self, lang_data: dict, n: int = 5) -> list[str]:
        """Return top-N languages by total byte count across all repos."""
        totals: Counter = Counter()
        for lang_map in lang_data.values():
            totals.update(lang_map)
        return [lang for lang, _ in totals.most_common(n)]

    def get_strengths_weaknesses(self, features: dict) -> tuple[list[str], list[str]]:
        """
        Derive human-readable strength and weakness labels from features.

        Strength  = domain score > 0.4
        Weakness  = domain score < 0.15 OR specific low signal
        """
        strengths  = []
        weaknesses = []

        domain_map = {
            "domain_backend":   "Backend Development",
            "domain_frontend":  "Frontend Development",
            "domain_devops":    "DevOps & Infrastructure",
            "domain_ml_ai":     "Machine Learning / AI",
            "domain_data":      "Data Engineering",
            "domain_mobile":    "Mobile Development",
            "domain_security":  "Security Engineering",
        }

        for key, label in domain_map.items():
            score = features.get(key, 0.0)
            if score >= 0.4:
                strengths.append(label)
            elif score < 0.15:
                weaknesses.append(label)

        # Documentation
        if features.get("has_readme_ratio", 0) < 0.3:
            weaknesses.append("Documentation")
        else:
            strengths.append("Documentation Practices")

        # Testing (no direct GitHub signal — use topics as proxy)
        if features.get("has_topics_ratio", 0) < 0.2:
            weaknesses.append("Project Organisation")

        if features.get("has_license_ratio", 0) > 0.5:
            strengths.append("Open Source Practices")

        # Deduplicate and cap
        return list(dict.fromkeys(strengths))[:5], list(dict.fromkeys(weaknesses))[:4]

    def get_activity_level(self, features: dict) -> str:
        """Classify overall activity as Low / Medium / High / Very High."""
        score = (
            min(features.get("weekly_commit_avg", 0) / 10.0, 1.0) * 40
            + features.get("commit_consistency", 0.0) * 30
            + min(features.get("recent_push_count", 0) / 10.0, 1.0) * 30
        )
        if score >= 70:
            return "Very High"
        elif score >= 45:
            return "High"
        elif score >= 20:
            return "Medium"
        return "Low"
