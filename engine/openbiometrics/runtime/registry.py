"""Central model registry for OpenBiometrics.

Manages model metadata, paths, and downloads for all ONNX models
used across the engine. Ensures models are available before inference.
"""

from __future__ import annotations

import logging
import urllib.request
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_MODELS_DIR = Path("./models")


@dataclass(frozen=True)
class ModelInfo:
    """Metadata for a registered model."""

    name: str
    filename: str
    url: str
    description: str
    size_mb: float  # Approximate size in megabytes


# Model catalog — covers current and planned models.
# URLs point to publicly hosted ONNX files (InsightFace, GitHub releases, etc.)
_MODEL_CATALOG: dict[str, ModelInfo] = {
    "det_10g": ModelInfo(
        name="det_10g",
        filename="det_10g.onnx",
        url="https://huggingface.co/openbiometrics/models/resolve/main/det_10g.onnx",
        description="SCRFD 10G face detector (highest accuracy, server deployment)",
        size_mb=16.1,
    ),
    "w600k_r50": ModelInfo(
        name="w600k_r50",
        filename="w600k_r50.onnx",
        url="https://huggingface.co/openbiometrics/models/resolve/main/w600k_r50.onnx",
        description="ArcFace ResNet-50 face recognition (~99.86% LFW)",
        size_mb=166.0,
    ),
    "genderage": ModelInfo(
        name="genderage",
        filename="genderage.onnx",
        url="https://huggingface.co/openbiometrics/models/resolve/main/genderage.onnx",
        description="InsightFace age and gender estimation model",
        size_mb=1.3,
    ),
    "antispoofing": ModelInfo(
        name="antispoofing",
        filename="antispoofing.onnx",
        url="https://huggingface.co/openbiometrics/models/resolve/main/antispoofing.onnx",
        description="MiniFASNet passive liveness / anti-spoofing model",
        size_mb=2.0,
    ),
    "yolov8n": ModelInfo(
        name="yolov8n",
        filename="yolov8n.onnx",
        url="https://huggingface.co/openbiometrics/models/resolve/main/yolov8n.onnx",
        description="YOLOv8 nano for person/object detection (Phase 2)",
        size_mb=12.0,
    ),
    "face_mesh": ModelInfo(
        name="face_mesh",
        filename="face_mesh.onnx",
        url="https://huggingface.co/openbiometrics/models/resolve/main/face_mesh.onnx",
        description="MediaPipe face mesh 468-point landmark model (Phase 2)",
        size_mb=2.8,
    ),
}


class ModelRegistry:
    """Central registry for managing biometric model files.

    Provides a single place to query model metadata, check availability,
    and download missing models.

    Usage:
        registry = ModelRegistry(models_dir="./models")
        rec_path = registry.ensure_model("w600k_r50")
        # rec_path is now guaranteed to exist on disk
    """

    def __init__(self, models_dir: str | Path = _DEFAULT_MODELS_DIR):
        """
        Args:
            models_dir: Directory where model files are stored / downloaded to
        """
        self._models_dir = Path(models_dir)

    @property
    def models_dir(self) -> Path:
        """Base directory for model storage."""
        return self._models_dir

    def ensure_model(self, name: str) -> Path:
        """Ensure a model is available on disk, downloading if necessary.

        Args:
            name: Model name from the catalog (e.g. "w600k_r50")

        Returns:
            Absolute path to the model file

        Raises:
            KeyError: If model name is not in the catalog
            RuntimeError: If download fails
        """
        info = self._get_info(name)
        path = self._models_dir / info.filename

        if path.exists():
            logger.debug("Model '%s' found at %s", name, path)
            return path

        logger.info("Model '%s' not found locally, downloading from %s", name, info.url)
        self._download(info.url, path)
        return path

    def model_path(self, name: str) -> Path:
        """Get the expected local path for a model (without downloading).

        Args:
            name: Model name from the catalog

        Returns:
            Expected path (may or may not exist)
        """
        info = self._get_info(name)
        return self._models_dir / info.filename

    def is_available(self, name: str) -> bool:
        """Check if a model file exists on disk.

        Args:
            name: Model name from the catalog
        """
        info = self._get_info(name)
        return (self._models_dir / info.filename).exists()

    def list_models(self) -> list[ModelInfo]:
        """Return metadata for all registered models."""
        return list(_MODEL_CATALOG.values())

    def register(self, info: ModelInfo) -> None:
        """Register a custom model in the catalog.

        Args:
            info: ModelInfo for the new model. Overwrites if name already exists.
        """
        _MODEL_CATALOG[info.name] = info

    def _get_info(self, name: str) -> ModelInfo:
        if name not in _MODEL_CATALOG:
            available = ", ".join(sorted(_MODEL_CATALOG.keys()))
            raise KeyError(f"Unknown model '{name}'. Available: {available}")
        return _MODEL_CATALOG[name]

    def _download(self, url: str, dest: Path) -> None:
        """Download a file from url to dest."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".part")
        try:
            logger.info("Downloading %s -> %s", url, dest)
            urllib.request.urlretrieve(url, str(tmp))
            tmp.rename(dest)
            logger.info("Download complete: %s (%.1f MB)", dest.name, dest.stat().st_size / 1e6)
        except Exception as exc:
            if tmp.exists():
                tmp.unlink()
            raise RuntimeError(f"Failed to download model from {url}: {exc}") from exc
