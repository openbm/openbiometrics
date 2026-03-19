"""Unified face processing pipeline.

Orchestrates: detect -> quality check -> align -> embed -> liveness -> demographics
Single entry point for all face operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from openbiometrics.core.detector import DetectedFace, FaceDetector
from openbiometrics.core.demographics import DemographicsEstimator
from openbiometrics.core.liveness import LivenessDetector
from openbiometrics.core.quality import QualityAssessor, QualityReport
from openbiometrics.core.recognizer import FaceRecognizer


@dataclass
class FaceResult:
    """Complete result for a single detected face."""

    face: DetectedFace
    quality: QualityReport | None = None
    embedding: np.ndarray | None = None
    age: int | None = None
    gender: str | None = None
    is_live: bool | None = None
    liveness_score: float | None = None
    identity: str | None = None  # Matched identity from watchlist
    identity_score: float | None = None


@dataclass
class PipelineConfig:
    """Configuration for the face pipeline."""

    models_dir: str = "./models"
    ctx_id: int = 0  # GPU device (-1 for CPU)
    det_thresh: float = 0.5
    det_size: tuple[int, int] = (640, 640)
    max_faces: int = 0
    enable_liveness: bool = True
    enable_demographics: bool = True
    enable_quality: bool = True
    quality_gate: bool = False  # Skip recognition if quality fails


class FacePipeline:
    """End-to-end face processing pipeline.

    Usage:
        pipeline = FacePipeline(PipelineConfig(models_dir="./models"))
        results = pipeline.process(image)
        for r in results:
            print(f"Face: age={r.age}, gender={r.gender}, live={r.is_live}")
            print(f"Embedding shape: {r.embedding.shape}")
    """

    def __init__(self, config: PipelineConfig | None = None):
        self.config = config or PipelineConfig()
        self._detector: FaceDetector | None = None
        self._recognizer: FaceRecognizer | None = None
        self._liveness: LivenessDetector | None = None
        self._demographics: DemographicsEstimator | None = None
        self._quality = QualityAssessor()

    def load(self) -> None:
        """Load all models. Call once before processing."""
        models = Path(self.config.models_dir)
        ctx = self.config.ctx_id

        # Detector (uses InsightFace model pack)
        self._detector = FaceDetector(
            model_name="buffalo_l",
            ctx_id=ctx,
            det_thresh=self.config.det_thresh,
            det_size=self.config.det_size,
        )

        # Recognizer
        rec_path = models / "w600k_r50.onnx"
        if rec_path.exists():
            self._recognizer = FaceRecognizer(str(rec_path), ctx_id=ctx)

        # Liveness
        if self.config.enable_liveness:
            liv_path = models / "antispoofing.onnx"
            if liv_path.exists():
                self._liveness = LivenessDetector(str(liv_path), ctx_id=ctx)

        # Demographics
        if self.config.enable_demographics:
            dem_path = models / "genderage.onnx"
            if dem_path.exists():
                self._demographics = DemographicsEstimator(str(dem_path), ctx_id=ctx)

    def process(self, image: np.ndarray) -> list[FaceResult]:
        """Process an image through the full pipeline.

        Args:
            image: BGR numpy array

        Returns:
            List of FaceResult for each detected face
        """
        if self._detector is None:
            raise RuntimeError("Pipeline not loaded. Call pipeline.load() first.")

        faces = self._detector.detect(image, max_faces=self.config.max_faces)
        results = []

        for face in faces:
            result = FaceResult(face=face)

            # Quality assessment
            if self.config.enable_quality:
                result.quality = self._quality.assess(face.aligned, face.landmarks)
                if self.config.quality_gate and not result.quality.is_acceptable:
                    results.append(result)
                    continue

            # Embedding extraction
            if self._recognizer is not None:
                result.embedding = self._recognizer.get_embedding(face.aligned)

            # Liveness
            if self._liveness is not None:
                result.is_live, result.liveness_score = self._liveness.check(face.aligned)

            # Demographics
            if self._demographics is not None:
                result.age, result.gender = self._demographics.estimate(face.aligned)

            results.append(result)

        return results

    def verify(self, image1: np.ndarray, image2: np.ndarray) -> tuple[bool, float]:
        """1:1 verification — do two images show the same person?

        Args:
            image1: BGR image of person A
            image2: BGR image of person B

        Returns:
            (is_match, similarity_score)
        """
        results1 = self.process(image1)
        results2 = self.process(image2)

        if not results1 or not results2:
            return False, 0.0

        if results1[0].embedding is None or results2[0].embedding is None:
            return False, 0.0

        score = FaceRecognizer.compare(results1[0].embedding, results2[0].embedding)
        is_match = FaceRecognizer.compare_to_threshold(score)
        return is_match, score

    def process_file(self, image_path: str) -> list[FaceResult]:
        """Process an image file."""
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Cannot read image: {image_path}")
        return self.process(image)
