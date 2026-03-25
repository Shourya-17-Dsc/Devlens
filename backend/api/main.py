

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from backend.api.routes import router

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger(__name__).info("GitHub Skill Platform API starting …")
    yield
    logging.getLogger(__name__).info("API shutting down.")

app = FastAPI(
    title="GitHub Developer Skill Intelligence Platform",
    description="Analyses GitHub profiles with ML to estimate developer skill level.",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the Next.js frontend (port 3000) to call the API during local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourproductiondomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
