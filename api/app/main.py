"""OpenBiometrics — FastAPI application entry point.

Run with: uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import routes
from openbiometrics.core.pipeline import FacePipeline, PipelineConfig
from openbiometrics.watchlist.store import WatchlistManager

DASHBOARD_DIR = Path(__file__).parent.parent.parent / "packages" / "dashboard" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = PipelineConfig(
        models_dir=str(Path(__file__).parent.parent.parent / "engine" / "models"),
        ctx_id=-1,  # CPU on Mac, set to 0 for GPU
    )
    pipeline = FacePipeline(config)
    pipeline.load()

    watchlist_mgr = WatchlistManager(storage_dir="./watchlists")

    routes.pipeline = pipeline
    routes.watchlist_mgr = watchlist_mgr

    print("OpenBiometrics ready.")
    print(f"  Models: {config.models_dir}")
    print(f"  Device: {'GPU:' + str(config.ctx_id) if config.ctx_id >= 0 else 'CPU'}")
    print(f"  Watchlists: {watchlist_mgr.list_watchlists()}")

    yield

    watchlist_mgr.save_all()
    print("Watchlists saved. Shutting down.")


app = FastAPI(
    title="OpenBiometrics",
    description="Open-source biometric platform — face detection, recognition, liveness, quality",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(routes.router, prefix="/api/v1")

# Serve React dashboard
if DASHBOARD_DIR.exists():
    app.mount("/", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard")
