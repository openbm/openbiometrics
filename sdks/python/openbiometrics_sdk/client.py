"""OpenBiometrics Python SDK.

Usage:
    from openbiometrics_sdk import OpenBiometrics

    ob = OpenBiometrics(api_key="ob_live_...")

    # Detect faces
    result = ob.faces.detect("photo.jpg")
    for face in result["faces"]:
        print(f"Age: {face['demographics']['age']}")

    # 1:1 verification
    result = ob.faces.verify("photo1.jpg", "photo2.jpg")
    print(f"Match: {result['is_match']} ({result['similarity']:.2%})")

    # Enroll & identify
    ob.watchlists.enroll("photo.jpg", label="Alice")
    result = ob.watchlists.identify("unknown.jpg")

    # Document scanning
    result = ob.documents.scan("id_card.jpg")
    print(result["mrz"]["parsed"]["surname"])

    # Interactive liveness
    session = ob.liveness.create_session(challenges=["blink", "turn_left"])
    ob.liveness.submit_frame(session["session_id"], frame_bytes)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx


class OpenBiometrics:
    """OpenBiometrics API client."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openbiometrics.dev",
    ):
        self._client = httpx.Client(
            base_url=base_url.rstrip("/") + "/api/v1",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
        self.faces = _Faces(self._client)
        self.watchlists = _Watchlists(self._client)
        self.liveness = _Liveness(self._client)
        self.documents = _Documents(self._client)
        self.video = _Video(self._client)
        self.events = _Events(self._client)
        self.admin = _Admin(self._client)

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _read_image(image: str | Path | bytes) -> tuple[str, bytes]:
    """Read image from path or bytes."""
    if isinstance(image, (str, Path)):
        path = Path(image)
        return (path.name, path.read_bytes())
    return ("image.jpg", image)


class _Faces:
    def __init__(self, client: httpx.Client):
        self._client = client

    def detect(self, image: str | Path | bytes) -> dict[str, Any]:
        """Detect faces in an image with quality, demographics, and liveness."""
        name, data = _read_image(image)
        res = self._client.post("/detect", files={"image": (name, data)})
        res.raise_for_status()
        return res.json()

    def verify(
        self,
        image1: str | Path | bytes,
        image2: str | Path | bytes,
        threshold: float = 0.4,
    ) -> dict[str, Any]:
        """1:1 face verification."""
        name1, data1 = _read_image(image1)
        name2, data2 = _read_image(image2)
        res = self._client.post(
            "/verify",
            files={"image1": (name1, data1), "image2": (name2, data2)},
            data={"threshold": str(threshold)},
        )
        res.raise_for_status()
        return res.json()


class _Watchlists:
    def __init__(self, client: httpx.Client):
        self._client = client

    def enroll(
        self,
        image: str | Path | bytes,
        label: str,
        watchlist: str = "default",
    ) -> dict[str, Any]:
        """Enroll a face into a watchlist."""
        name, data = _read_image(image)
        res = self._client.post(
            "/watchlist/enroll",
            files={"image": (name, data)},
            data={"label": label, "watchlist_name": watchlist},
        )
        res.raise_for_status()
        return res.json()

    def identify(
        self,
        image: str | Path | bytes,
        watchlist: str = "default",
        top_k: int = 5,
        threshold: float = 0.4,
    ) -> dict[str, Any]:
        """1:N identification against a watchlist."""
        name, data = _read_image(image)
        res = self._client.post(
            "/identify",
            files={"image": (name, data)},
            data={
                "watchlist_name": watchlist,
                "top_k": str(top_k),
                "threshold": str(threshold),
            },
        )
        res.raise_for_status()
        return res.json()

    def remove(self, identity_id: str, watchlist: str = "default") -> None:
        """Remove an identity from a watchlist."""
        res = self._client.delete(f"/watchlist/{identity_id}", params={"watchlist_name": watchlist})
        res.raise_for_status()

    def list(self) -> dict[str, Any]:
        """List all watchlists."""
        res = self._client.get("/watchlist")
        res.raise_for_status()
        return res.json()


class _Liveness:
    def __init__(self, client: httpx.Client):
        self._client = client

    def create_session(
        self,
        challenges: list[str] | None = None,
        ttl_seconds: int | None = None,
    ) -> dict[str, Any]:
        """Create an interactive liveness session with challenge-response flow."""
        body: dict[str, Any] = {}
        if challenges is not None:
            body["challenges"] = challenges
        if ttl_seconds is not None:
            body["ttl_seconds"] = ttl_seconds
        res = self._client.post("/liveness/sessions", json=body)
        res.raise_for_status()
        return res.json()

    def submit_frame(
        self,
        session_id: str,
        frame: str | Path | bytes,
    ) -> dict[str, Any]:
        """Submit a video frame to an active liveness session."""
        name, data = _read_image(frame)
        res = self._client.post(
            f"/liveness/sessions/{session_id}/frames",
            files={"image": (name, data)},
            data={"session_id": session_id},
        )
        res.raise_for_status()
        return res.json()

    def get_session(self, session_id: str) -> dict[str, Any]:
        """Get the current state of a liveness session."""
        res = self._client.get(f"/liveness/sessions/{session_id}")
        res.raise_for_status()
        return res.json()

    def delete_session(self, session_id: str) -> None:
        """Delete / cancel a liveness session."""
        res = self._client.delete(f"/liveness/sessions/{session_id}")
        res.raise_for_status()


class _Documents:
    def __init__(self, client: httpx.Client):
        self._client = client

    def scan(self, image: str | Path | bytes) -> dict[str, Any]:
        """Scan a document image — detect type, extract OCR text, and MRZ data."""
        name, data = _read_image(image)
        res = self._client.post("/documents/scan", files={"image": (name, data)})
        res.raise_for_status()
        return res.json()

    def ocr(self, image: str | Path | bytes) -> dict[str, Any]:
        """Extract text from a document image using OCR."""
        name, data = _read_image(image)
        res = self._client.post("/documents/ocr", files={"image": (name, data)})
        res.raise_for_status()
        return res.json()

    def mrz(self, image: str | Path | bytes) -> dict[str, Any]:
        """Read and parse the MRZ zone from an identity document."""
        name, data = _read_image(image)
        res = self._client.post("/documents/mrz", files={"image": (name, data)})
        res.raise_for_status()
        return res.json()

    def verify(
        self,
        face_image: str | Path | bytes,
        document_image: str | Path | bytes,
    ) -> dict[str, Any]:
        """Verify a face against the photo on a document."""
        fname, fdata = _read_image(face_image)
        dname, ddata = _read_image(document_image)
        res = self._client.post(
            "/documents/verify",
            files={"face_image": (fname, fdata), "document_image": (dname, ddata)},
        )
        res.raise_for_status()
        return res.json()


class _Video:
    def __init__(self, client: httpx.Client):
        self._client = client

    def add_camera(
        self,
        name: str,
        url: str,
        fps: int = 5,
    ) -> dict[str, Any]:
        """Add a camera source for real-time video processing."""
        res = self._client.post(
            "/video/cameras",
            json={"name": name, "url": url, "fps": fps},
        )
        res.raise_for_status()
        return res.json()

    def remove_camera(self, camera_id: str) -> None:
        """Remove a camera source."""
        res = self._client.delete(f"/video/cameras/{camera_id}")
        res.raise_for_status()

    def list_cameras(self) -> list[dict[str, Any]]:
        """List all configured cameras and their connection status."""
        res = self._client.get("/video/cameras")
        res.raise_for_status()
        return res.json()

    def get_snapshot(self, camera_id: str) -> bytes:
        """Get a snapshot from a camera as raw bytes."""
        res = self._client.get(f"/video/cameras/{camera_id}/snapshot")
        res.raise_for_status()
        return res.content


class _Events:
    def __init__(self, client: httpx.Client):
        self._client = client

    def register_webhook(
        self,
        url: str,
        events: list[str],
    ) -> dict[str, Any]:
        """Register a webhook to receive event notifications."""
        res = self._client.post(
            "/events/webhooks",
            json={"url": url, "events": events},
        )
        res.raise_for_status()
        return res.json()

    def delete_webhook(self, webhook_id: str) -> None:
        """Delete a registered webhook."""
        res = self._client.delete(f"/events/webhooks/{webhook_id}")
        res.raise_for_status()

    def list_webhooks(self) -> list[dict[str, Any]]:
        """List all registered webhooks."""
        res = self._client.get("/events/webhooks")
        res.raise_for_status()
        return res.json()

    def get_recent(
        self,
        event_type: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get recent events, optionally filtered by type."""
        params: dict[str, str] = {}
        if event_type is not None:
            params["type"] = event_type
        if limit is not None:
            params["limit"] = str(limit)
        res = self._client.get("/events/recent", params=params)
        res.raise_for_status()
        return res.json()


class _Admin:
    def __init__(self, client: httpx.Client):
        self._client = client

    def health(self) -> dict[str, Any]:
        """Get server health status including loaded models."""
        res = self._client.get("/admin/health")
        res.raise_for_status()
        return res.json()

    def models(self) -> list[dict[str, Any]]:
        """List all models and their loading status."""
        res = self._client.get("/admin/models")
        res.raise_for_status()
        return res.json()

    def config(self, **updates: Any) -> dict[str, Any]:
        """Get or update server configuration."""
        if updates:
            res = self._client.patch("/admin/config", json=updates)
        else:
            res = self._client.get("/admin/config")
        res.raise_for_status()
        return res.json()
