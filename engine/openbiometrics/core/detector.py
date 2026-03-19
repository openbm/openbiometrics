"""Face detection using InsightFace SCRFD models.

Supports multiple model sizes for server vs edge deployment:
- scrfd_10g: highest accuracy (server)
- scrfd_2.5g: balanced (Jetson)
- scrfd_500m: fastest (embedded ARM)
"""

from dataclasses import dataclass

import cv2
import numpy as np
from insightface.app import FaceAnalysis
from insightface.data import get_image


@dataclass
class DetectedFace:
    """A detected face with bounding box, landmarks, and confidence."""

    bbox: np.ndarray  # [x1, y1, x2, y2]
    landmarks: np.ndarray  # 5-point landmarks (left_eye, right_eye, nose, left_mouth, right_mouth)
    confidence: float
    aligned: np.ndarray  # 112x112 aligned face crop
    embedding: np.ndarray | None = None  # 512-d embedding (filled by recognizer)
    age: int | None = None
    gender: str | None = None
    liveness_score: float | None = None
    quality_score: float | None = None

    @property
    def face_size(self) -> float:
        """Face size as defined by biometric standards:
        max(inter-eye distance, eye-center-to-mouth distance)."""
        left_eye = self.landmarks[0]
        right_eye = self.landmarks[1]
        mouth_center = (self.landmarks[3] + self.landmarks[4]) / 2
        eye_center = (left_eye + right_eye) / 2

        inter_eye = np.linalg.norm(right_eye - left_eye)
        eye_to_mouth = np.linalg.norm(mouth_center - eye_center)
        return float(max(inter_eye, eye_to_mouth))


class FaceDetector:
    """SCRFD-based face detector with alignment."""

    def __init__(
        self,
        model_name: str = "buffalo_l",
        ctx_id: int = 0,
        det_thresh: float = 0.5,
        det_size: tuple[int, int] = (640, 640),
    ):
        self.app = FaceAnalysis(
            name=model_name,
            allowed_modules=["detection"],
            providers=_get_providers(ctx_id),
        )
        self.app.prepare(ctx_id=ctx_id, det_thresh=det_thresh, det_size=det_size)
        self.det_thresh = det_thresh

    def detect(self, image: np.ndarray, max_faces: int = 0) -> list[DetectedFace]:
        """Detect faces in a BGR image.

        Args:
            image: BGR numpy array (OpenCV format)
            max_faces: Maximum faces to return (0 = unlimited)

        Returns:
            List of DetectedFace sorted by confidence descending.
        """
        faces = self.app.get(image)

        if max_faces > 0:
            faces = sorted(faces, key=lambda f: f.det_score, reverse=True)[:max_faces]

        results = []
        for face in faces:
            aligned = _align_face(image, face.kps)
            results.append(
                DetectedFace(
                    bbox=face.bbox.astype(np.float32),
                    landmarks=face.kps.astype(np.float32),
                    confidence=float(face.det_score),
                    aligned=aligned,
                )
            )

        return sorted(results, key=lambda f: f.confidence, reverse=True)


def _align_face(
    image: np.ndarray, landmarks: np.ndarray, output_size: tuple[int, int] = (112, 112)
) -> np.ndarray:
    """Align face using 5-point landmarks via affine transform."""
    # Standard alignment targets for 112x112 (from InsightFace)
    dst = np.array(
        [
            [38.2946, 51.6963],
            [73.5318, 51.5014],
            [56.0252, 71.7366],
            [41.5493, 92.3655],
            [70.7299, 92.2041],
        ],
        dtype=np.float32,
    )
    src = landmarks.astype(np.float32)
    M = cv2.estimateAffinePartial2D(src, dst)[0]
    if M is None:
        # Fallback: just crop and resize
        x1, y1 = landmarks.min(axis=0).astype(int)
        x2, y2 = landmarks.max(axis=0).astype(int)
        pad = int((x2 - x1) * 0.3)
        h, w = image.shape[:2]
        crop = image[max(0, y1 - pad) : min(h, y2 + pad), max(0, x1 - pad) : min(w, x2 + pad)]
        return cv2.resize(crop, output_size)
    return cv2.warpAffine(image, M, output_size, borderValue=0)


def _get_providers(ctx_id: int) -> list[str]:
    """Select ONNX Runtime providers based on context."""
    if ctx_id >= 0:
        return [
            ("CUDAExecutionProvider", {"device_id": ctx_id}),
            "CPUExecutionProvider",
        ]
    return ["CPUExecutionProvider"]
