"""Watchlist management endpoints.

Backward-compatible with the original routes — same paths and contracts.
"""

from __future__ import annotations

import uuid

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.deps import get_kernel
from app.routes.faces import _decode_image, _face_to_response
from app.schemas import DeduplicateResponse, DuplicateGroupSchema
from openbiometrics.kernel import BiometricKernel

router = APIRouter(tags=["watchlists"])


def _get_watchlist_mgr():
    """Get the WatchlistManager singleton."""
    from openbiometrics.watchlist.store import WatchlistManager
    return WatchlistManager(storage_dir="./watchlists")


@router.post("/watchlist/enroll")
async def enroll_face(
    image: UploadFile = File(...),
    identity_id: str = Form(default=""),
    label: str = Form(...),
    watchlist_name: str = Form("default"),
    kernel: BiometricKernel = Depends(get_kernel),
):
    """Enroll a face into a watchlist."""
    img = _decode_image(await image.read())
    results = kernel.face.process(img)

    if not results:
        raise HTTPException(status_code=400, detail="No face detected")

    r = results[0]
    if r.embedding is None:
        raise HTTPException(status_code=500, detail="Recognition model not loaded")

    if not identity_id:
        identity_id = str(uuid.uuid4())

    watchlist_mgr = _get_watchlist_mgr()
    wl = watchlist_mgr.get(watchlist_name)
    wl.add(identity_id, label, r.embedding)
    wl.save(watchlist_mgr.storage_dir)

    return {
        "identity_id": identity_id,
        "label": label,
        "watchlist": watchlist_name,
        "face": _face_to_response(r),
    }


@router.delete("/watchlist/{identity_id}")
async def remove_from_watchlist(identity_id: str, watchlist_name: str = "default"):
    """Remove an identity from a watchlist."""
    watchlist_mgr = _get_watchlist_mgr()
    wl = watchlist_mgr.get(watchlist_name)
    if not wl.remove(identity_id):
        raise HTTPException(status_code=404, detail="Identity not found")
    wl.save(watchlist_mgr.storage_dir)
    return {"removed": identity_id}


@router.get("/watchlist")
async def list_watchlists():
    """List all watchlists and their sizes."""
    watchlist_mgr = _get_watchlist_mgr()
    names = watchlist_mgr.list_watchlists()
    return {
        "watchlists": [{"name": n, "size": watchlist_mgr.get(n).size} for n in names]
    }


@router.post("/watchlists/{name}/deduplicate", response_model=DeduplicateResponse)
async def deduplicate_watchlist(
    name: str,
    threshold: float = 0.7,
):
    """Find duplicate identities in a watchlist using face clustering."""
    watchlist_mgr = _get_watchlist_mgr()

    try:
        wl = watchlist_mgr.get(name)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Watchlist '{name}' not found")

    if wl.size == 0:
        return DeduplicateResponse(watchlist=name, total_entries=0, duplicate_groups=[])

    from app.deps import get_kernel as _get_kernel

    _kernel = _get_kernel()
    clusterer = _kernel.clusterer
    if clusterer is None:
        from openbiometrics.identity.clustering import FaceClusterer
        clusterer = FaceClusterer()

    # Extract embeddings and labels from the watchlist
    embeddings = np.array([entry.embedding for entry in wl.entries])
    labels = [entry.label for entry in wl.entries]

    duplicate_groups = clusterer.deduplicate(embeddings, labels, threshold=threshold)

    return DeduplicateResponse(
        watchlist=name,
        total_entries=wl.size,
        duplicate_groups=[
            DuplicateGroupSchema(
                indices=group.indices,
                labels=group.labels,
                mean_similarity=group.mean_similarity,
            )
            for group in duplicate_groups
        ],
    )
