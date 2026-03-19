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
