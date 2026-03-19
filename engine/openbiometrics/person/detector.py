"""Person detection using YOLO models.

Wraps ultralytics YOLO for person-only detection with lazy model loading.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DetectedPerson:
    """A single detected person in an image.

    Attributes:
        bbox: Bounding box as (x1, y1, x2, y2) in pixel coordinates.
        confidence: Detection confidence score [0, 1].
        class_name: Always "person" for this detector.
        track_id: Optional tracking ID, set by PersonTracker.
    """

    bbox: tuple[float, float, float, float]
    confidence: float
    class_name: str = "person"
    track_id: int | None = None

    @property
    def center(self) -> tuple[float, float]:
        """Center point of the bounding box."""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    @property
    def area(self) -> float:
        """Area of the bounding box in pixels."""
        x1, y1, x2, y2 = self.bbox
        return max(0.0, x2 - x1) * max(0.0, y2 - y1)


class PersonDetector:
    """YOLO-based person detector.

    Uses ultralytics YOLO to detect people in images. The model is
    loaded lazily on the first call to detect().

    Usage:
        detector = PersonDetector(model_path="yolov8n.pt", ctx_id=0)
        persons = detector.detect(image)
    """

    _PERSON_CLASS_ID = 0

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        ctx_id: int = 0,
        confidence_threshold: float = 0.5,
    ):
        """
        Args:
            model_path: Path to YOLO model weights (.pt file).
            ctx_id: GPU device ID (>= 0) or -1 for CPU.
            confidence_threshold: Minimum confidence for detections.
        """
        self._model_path = model_path
        self._ctx_id = ctx_id
        self._confidence_threshold = confidence_threshold
        self._model = None

    def _load_model(self) -> None:
        """Load the YOLO model (lazy, called on first detect)."""
        try:
            from ultralytics import YOLO
        except ImportError:
            raise ImportError(
                "ultralytics is required for PersonDetector. "
                "Install it with: pip install ultralytics"
            )

        device = f"cuda:{self._ctx_id}" if self._ctx_id >= 0 else "cpu"
        self._model = YOLO(self._model_path)
        self._model.to(device)
        logger.info(
            "Loaded YOLO model %s on %s", self._model_path, device
        )

    def detect(self, image: np.ndarray) -> list[DetectedPerson]:
        """Detect people in an image.

        Args:
            image: BGR image as numpy array (H, W, 3).

        Returns:
            List of DetectedPerson instances for each detected person.
        """
        if self._model is None:
            self._load_model()

        results = self._model(image, conf=self._confidence_threshold, verbose=False)

        persons: list[DetectedPerson] = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for i in range(len(boxes)):
                cls_id = int(boxes.cls[i].item())
                if cls_id != self._PERSON_CLASS_ID:
                    continue
                conf = float(boxes.conf[i].item())
                x1, y1, x2, y2 = boxes.xyxy[i].tolist()
                persons.append(
                    DetectedPerson(
                        bbox=(x1, y1, x2, y2),
                        confidence=conf,
                    )
                )

        return persons

    def __repr__(self) -> str:
        loaded = self._model is not None
        return (
            f"PersonDetector(model={self._model_path!r}, "
            f"ctx_id={self._ctx_id}, loaded={loaded})"
        )
