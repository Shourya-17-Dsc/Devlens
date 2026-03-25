

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.services.ml_scorer import MLScorer

# ── Logging Setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan: runs on startup & shutdown ──────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Code BEFORE yield → runs at startup.
    Code AFTER yield  → runs at shutdown.
    We warm up the ML model here so the first request is fast.
    """
    logger.info("🚀 Starting GitHub Skill Intelligence Platform API...")
    # Pre-load the ML model into memory
    scorer = MLScorer()
    scorer.load()
    logger.info("✅ ML model loaded and ready.")
    yield
    logger.info("🛑 Shutting down API server.")


# ── FastAPI App Instance ───────────────────────────────────────────────────────
app = FastAPI(
    title="GitHub Developer Skill Intelligence Platform",
    description=(
        "Analyzes a GitHub profile and returns a structured ML-powered "
        "skill assessment including score, language breakdown, strengths, "
        "and code complexity metrics."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS Configuration ────────────────────────────────────────────────────────
# Allow the Next.js dev server (port 3000) and any production domain.
# In production, replace "*" with your actual frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # Next.js dev
        "https://your-app.vercel.app",  # Production (update this)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount Route Handlers ───────────────────────────────────────────────────────
app.include_router(router, prefix="/api/v1")


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    """Simple liveness probe. Returns 200 OK if the server is running."""
    return {"status": "healthy", "service": "github-skill-platform"}


# ── Dev entrypoint ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
