"""OpenBiometrics API routes package.

Assembles sub-routers into a single APIRouter that is mounted
by main.py under the /api/v1 prefix.
"""

from fastapi import APIRouter

from app.routes.faces import router as faces_router
from app.routes.watchlists import router as watchlists_router
from app.routes.documents import router as documents_router
from app.routes.liveness import router as liveness_router
from app.routes.video import router as video_router
from app.routes.events import router as events_router
from app.routes.admin import router as admin_router

router = APIRouter()

router.include_router(faces_router)
router.include_router(watchlists_router)
router.include_router(documents_router, prefix="/documents", tags=["documents"])
router.include_router(liveness_router, prefix="/liveness", tags=["liveness"])
router.include_router(video_router, prefix="/video", tags=["video"])
router.include_router(events_router, prefix="/events", tags=["events"])
router.include_router(admin_router, prefix="/admin", tags=["admin"])
