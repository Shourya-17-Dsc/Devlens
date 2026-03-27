"""
Skill Radar Scorer
==================
Estimates developer proficiency across 5 technical domains by analyzing
GitHub signals: programming languages, repository topics, descriptions,
detected files (Dockerfile, CI configs, test dirs, etc.).

Output: a dict with scores from 0-100 for each domain.
    {
        "backend":         82,
        "frontend":        60,
        "machine_learning":45,
        "devops":          35,
        "testing":         30
    }
"""

import math
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Language → domain mapping (primary signal, weighted by byte count)
# ---------------------------------------------------------------------------
LANG_WEIGHTS: dict[str, dict[str, float]] = {
    # Backend languages
    "Python":      {"backend": 0.5, "machine_learning": 0.4, "devops": 0.1},
    "Java":        {"backend": 0.9, "testing": 0.1},
    "Go":          {"backend": 0.7, "devops": 0.3},
    "Rust":        {"backend": 0.8, "devops": 0.2},
    "C":           {"backend": 0.7, "devops": 0.3},
    "C++":         {"backend": 0.7, "devops": 0.1, "machine_learning": 0.2},
    "C#":          {"backend": 0.8, "frontend": 0.1, "testing": 0.1},
    "Scala":       {"backend": 0.6, "machine_learning": 0.4},
    "Kotlin":      {"backend": 0.7, "frontend": 0.2, "testing": 0.1},
    "PHP":         {"backend": 0.9, "frontend": 0.1},
    "Ruby":        {"backend": 0.9, "testing": 0.1},
    "Elixir":      {"backend": 0.95, "testing": 0.05},
    "Swift":       {"backend": 0.5, "frontend": 0.5},
    "Dart":        {"frontend": 0.8, "backend": 0.2},
    "R":           {"machine_learning": 0.8, "backend": 0.2},
    "Julia":       {"machine_learning": 0.9, "backend": 0.1},
    "MATLAB":      {"machine_learning": 0.9, "backend": 0.1},
    # Frontend
    "JavaScript":  {"frontend": 0.6, "backend": 0.4},
    "TypeScript":  {"frontend": 0.55, "backend": 0.45},
    "HTML":        {"frontend": 1.0},
    "CSS":         {"frontend": 1.0},
    "SCSS":        {"frontend": 1.0},
    "Vue":         {"frontend": 1.0},
    # DevOps / Infra
    "HCL":         {"devops": 1.0},
    "Dockerfile":  {"devops": 1.0},
    "Shell":       {"devops": 0.7, "backend": 0.3},
    "Makefile":    {"devops": 0.6, "backend": 0.4},
    "PowerShell":  {"devops": 0.7, "backend": 0.3},
    "Nix":         {"devops": 1.0},
    # Notebooks / ML
    "Jupyter Notebook": {"machine_learning": 0.9, "backend": 0.1},
    # Testing
    "Gherkin":     {"testing": 1.0},
    "Robot Framework": {"testing": 1.0},
}

# ---------------------------------------------------------------------------
# Keyword banks for topic/description scanning
# ---------------------------------------------------------------------------
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "backend": [
        "api", "rest", "graphql", "grpc", "microservice", "server", "backend",
        "flask", "django", "fastapi", "spring", "express", "rails", "laravel",
        "gin", "echo", "actix", "tokio", "async", "database", "orm", "sql",
        "postgres", "mongodb", "redis", "kafka", "rabbitmq", "celery", "auth",
        "oauth", "jwt", "middleware", "websocket", "rpc",
    ],
    "frontend": [
        "react", "nextjs", "vue", "angular", "svelte", "frontend", "ui", "ux",
        "tailwind", "css", "html", "bootstrap", "webpack", "vite", "spa",
        "pwa", "responsive", "component", "design-system", "storybook",
        "animation", "threejs", "webgl", "canvas", "d3", "chart", "dashboard",
        "mobile", "ios", "android", "flutter", "react-native", "expo",
    ],
    "machine_learning": [
        "machine-learning", "ml", "deep-learning", "neural-network", "ai",
        "tensorflow", "pytorch", "keras", "sklearn", "scikit-learn", "nlp",
        "computer-vision", "data-science", "dataset", "kaggle", "model",
        "training", "inference", "transformer", "llm", "gpt", "bert",
        "reinforcement-learning", "generative", "diffusion", "embedding",
        "pandas", "numpy", "matplotlib", "seaborn", "notebook", "analytics",
        "big-data", "spark", "feature-engineering",
    ],
    "devops": [
        "docker", "kubernetes", "k8s", "helm", "terraform", "ansible",
        "ci-cd", "github-actions", "jenkins", "circleci", "travis",
        "infrastructure", "iac", "devops", "deployment", "container",
        "cloud", "aws", "gcp", "azure", "serverless", "lambda", "nginx",
        "prometheus", "grafana", "monitoring", "logging", "elk", "sre",
        "linux", "bash", "shell-script", "automation",
    ],
    "testing": [
        "testing", "test", "tdd", "bdd", "unit-test", "integration-test",
        "e2e", "pytest", "jest", "mocha", "cypress", "selenium", "playwright",
        "coverage", "quality", "linting", "sonar", "benchmark",
    ],
}

# CI/CD and special files that indicate specific domains
FILE_SIGNALS: dict[str, dict[str, float]] = {
    "dockerfile":         {"devops": 15},
    "docker-compose.yml": {"devops": 12},
    "docker-compose.yaml":{"devops": 12},
    "kubernetes":         {"devops": 15},
    "helm":               {"devops": 10},
    ".github":            {"devops": 8},
    "terraform":          {"devops": 10},
    "ansible":            {"devops": 10},
    ".travis.yml":        {"devops": 8},
    "jenkinsfile":        {"devops": 8},
    "circleci":           {"devops": 8},
    "makefile":           {"devops": 5},
    "requirements.txt":   {"backend": 5, "machine_learning": 3},
    "package.json":       {"frontend": 5, "backend": 3},
    "pyproject.toml":     {"backend": 5, "machine_learning": 3},
    "cargo.toml":         {"backend": 8},
    "go.mod":             {"backend": 8},
    "pom.xml":            {"backend": 8},
    "build.gradle":       {"backend": 8},
    "tests":              {"testing": 15},
    "test":               {"testing": 12},
    "__tests__":          {"testing": 12},
    "spec":               {"testing": 10},
    "pytest.ini":         {"testing": 10},
    "jest.config":        {"testing": 10},
    ".eslintrc":          {"testing": 5, "frontend": 3},
    "cypress":            {"testing": 12},
    "notebooks":          {"machine_learning": 15},
    "notebook":           {"machine_learning": 12},
    "model":              {"machine_learning": 8},
    ".ipynb":             {"machine_learning": 10},
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _safe_log(x: float) -> float:
    return math.log1p(max(0, x))


def _scan_text(text: str, keywords: list[str]) -> int:
    """Count how many keywords appear in the lowercased text."""
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


# ---------------------------------------------------------------------------
# Core extractor
# ---------------------------------------------------------------------------

def extract_skill_radar(raw_data: dict) -> dict[str, int]:
    """
    Analyse raw GitHub data and return skill scores for 5 domains.
    All scores are clamped to [0, 100].
    """
    repos     = raw_data.get("repos", []) or []
    languages = raw_data.get("languages", {}) or {}
    repo_files= raw_data.get("repo_files", []) or []  # list of file/dir name strings

    # Accumulate raw domain scores
    scores: dict[str, float] = defaultdict(float)

    # ── 1. Language signal (strongest signal) ──────────────────────────────
    total_bytes = sum(languages.values())
    if total_bytes > 0:
        for lang, byte_count in languages.items():
            share = byte_count / total_bytes  # 0→1
            weights = LANG_WEIGHTS.get(lang)
            if weights:
                for domain, w in weights.items():
                    scores[domain] += share * w * 60  # up to 60 pts from languages

    # ── 2. Topic / description keyword scan ───────────────────────────────
    for repo in repos:
        if not isinstance(repo, dict):
            continue
        # Combine all text signals
        text_blob = " ".join(filter(None, [
            repo.get("description", ""),
            repo.get("language", ""),
            " ".join(repo.get("topics", []) or []),
        ]))
        for domain, keywords in TOPIC_KEYWORDS.items():
            hits = _scan_text(text_blob, keywords)
            if hits:
                # Logarithmic boost so a single keyword adds less than 5
                scores[domain] += _safe_log(hits) * 4

    # ── 3. Repository file detection ───────────────────────────────────────
    repo_file_set = {f.lower() for f in repo_files}
    for sig, domain_pts in FILE_SIGNALS.items():
        # Check if any collected file/dir name matches this signal
        if any(sig in f for f in repo_file_set):
            for domain, pts in domain_pts.items():
                scores[domain] += pts

    # ── 4. Activity multiplier ─────────────────────────────────────────────
    # Developers who have more repos get a slight boost so the scores scale
    repo_count = len([r for r in repos if isinstance(r, dict)])
    repo_mult = min(1.0, _safe_log(repo_count) / _safe_log(30))  # saturates at ~30 repos

    final: dict[str, int] = {}
    for domain in ["backend", "frontend", "machine_learning", "devops", "testing"]:
        raw = scores.get(domain, 0.0) * repo_mult
        final[domain] = int(_clamp(raw, 0, 100))

    logger.info("Radar scores for user: %s", final)
    return final
