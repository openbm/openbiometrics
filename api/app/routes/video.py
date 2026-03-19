"""Video camera management endpoints."""

from __future__ import annotations

import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.deps import get_kernel
from app.schemas import CameraRequest, CameraStatusSchema
from openbiometrics.kernel import BiometricKernel

router = APIRouter()


def _get_camera_manager(kernel: BiometricKernel = Depends(get_kernel)):
    """Get the camera manager from the kernel, or 503 if unavailable."""
    manager = kernel.cameras
    if manager is None:
        raise HTTPException(
            status_code=503,
            detail="Video/camera module not available",
        )
    return manager


@router.post("/cameras", response_model=CameraStatusSchema)
async def add_camera(
    req: CameraRequest,
    manager=Depends(_get_camera_manager),
):
    """Add and start a camera stream."""
    source: str | int = req.source
    # If the source looks like an integer device index, convert it
    if isinstance(source, str) and source.isdigit():
        source = int(source)

    try:
        manager.add_camera(req.camera_id, source)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    # Return status of the newly added camera
    for cam in manager.list_cameras():
        if cam.camera_id == req.camera_id:
            return CameraStatusSchema(
                camera_id=cam.camera_id,
                source=str(cam.source),
                is_running=cam.is_running,
                fps=cam.fps,
                frame_count=cam.frame_count,
            )

    return CameraStatusSchema(
        camera_id=req.camera_id,
        source=str(source),
        is_running=False,
        fps=0.0,
        frame_count=0,
    )


@router.delete("/cameras/{camera_id}")
async def remove_camera(
    camera_id: str,
    manager=Depends(_get_camera_manager),
):
    """Stop and remove a camera stream."""
    cameras = {c.camera_id for c in manager.list_cameras()}
    if camera_id not in cameras:
        raise HTTPException(status_code=404, detail="Camera not found")

    manager.remove_camera(camera_id)
    return {"removed": camera_id}


@router.get("/cameras", response_model=list[CameraStatusSchema])
async def list_cameras(
    manager=Depends(_get_camera_manager),
):
    """List all cameras and their status."""
    return [
        CameraStatusSchema(
            camera_id=cam.camera_id,
            source=str(cam.source),
            is_running=cam.is_running,
            fps=cam.fps,
            frame_count=cam.frame_count,
        )
        for cam in manager.list_cameras()
    ]


@router.get("/cameras/{camera_id}/snapshot")
async def get_snapshot(
    camera_id: str,
    manager=Depends(_get_camera_manager),
):
    """Get the latest frame from a camera as JPEG."""
    frame = manager.get_snapshot(camera_id)
    if frame is None:
        raise HTTPException(status_code=404, detail="Camera not found or no frame available")

    success, jpeg_bytes = cv2.imencode(".jpg", frame)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to encode frame as JPEG")

    return Response(content=jpeg_bytes.tobytes(), media_type="image/jpeg")
