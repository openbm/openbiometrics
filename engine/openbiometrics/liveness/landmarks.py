"""Face mesh detection using MediaPipe Face Mesh (468 landmarks).

Provides eye aspect ratios, mouth aspect ratio, and head pose
estimation via solvePnP for active liveness challenge verification.

MediaPipe is an optional dependency — import errors are caught
and surfaced as a clear message.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import cv2
import numpy as np

logger = logging.getLogger(__name__)

try:
    import mediapipe as mp

    _MEDIAPIPE_AVAILABLE = True
except ImportError:
    _MEDIAPIPE_AVAILABLE = False

# ── Landmark index constants ────────────────────────────────────────────────
# MediaPipe Face Mesh landmark indices for EAR / MAR / head pose.

# Left eye (6 points for EAR)
_LEFT_EYE = [362, 385, 387, 263, 373, 380]
# Right eye (6 points for EAR)
_RIGHT_EYE = [33, 160, 158, 133, 153, 144]

# Mouth landmarks for MAR (outer lips, vertical + horizontal)
_MOUTH_TOP = 13
_MOUTH_BOTTOM = 14
_MOUTH_LEFT = 78
_MOUTH_RIGHT = 308
_MOUTH_UPPER_INNER = 82
_MOUTH_LOWER_INNER = 87

# Key landmarks for solvePnP head pose estimation
_POSE_LANDMARK_IDS = [
    1,    # Nose tip
    152,  # Chin
    33,   # Left eye left corner
    263,  # Right eye right corner
    78,   # Mouth left corner
    308,  # Mouth right corner
]

# Canonical 3D face model points (approximate, in arbitrary units).
# Coordinates follow OpenCV convention: X right, Y down, Z forward.
_3D_FACE_MODEL = np.array(
    [
        [0.0, 0.0, 0.0],         # Nose tip
        [0.0, 63.6, -12.5],      # Chin
        [-43.3, -32.7, -26.0],   # Left eye left corner
        [43.3, -32.7, -26.0],    # Right eye right corner
        [-28.9, 28.9, -24.1],    # Mouth left corner
        [28.9, 28.9, -24.1],     # Mouth right corner
    ],
    dtype=np.float64,
)


@dataclass
class FaceMesh:
    """Result from FaceMeshDetector.detect().

    Attributes:
        landmarks_468: Raw 468 landmarks as (468, 3) array, normalised [0, 1].
        left_eye_ar: Left eye aspect ratio (low when eye is closed).
        right_eye_ar: Right eye aspect ratio.
        mouth_ar: Mouth aspect ratio (high when mouth is open).
        head_yaw: Head yaw in degrees (positive = turned right).
        head_pitch: Head pitch in degrees (positive = looking down).
        head_roll: Head roll in degrees.
    """

    landmarks_468: np.ndarray
    left_eye_ar: float
    right_eye_ar: float
    mouth_ar: float
    head_yaw: float
    head_pitch: float
    head_roll: float


def _eye_aspect_ratio(landmarks: np.ndarray, eye_indices: list[int]) -> float:
    """Compute the Eye Aspect Ratio (EAR) for 6 eye landmarks.

    EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)

    where p1, p4 are the horizontal corners and p2-p3, p5-p6 are the
    vertical pairs.
    """
    pts = landmarks[eye_indices]
    # Vertical distances
    v1 = np.linalg.norm(pts[1] - pts[5])
    v2 = np.linalg.norm(pts[2] - pts[4])
    # Horizontal distance
    h = np.linalg.norm(pts[0] - pts[3])
    if h < 1e-6:
        return 0.0
    return float((v1 + v2) / (2.0 * h))


def _mouth_aspect_ratio(landmarks: np.ndarray) -> float:
    """Compute the Mouth Aspect Ratio (MAR).

    MAR = (||upper-lower|| + ||upper_inner-lower_inner||) / (2 * ||left-right||)
    """
    top = landmarks[_MOUTH_TOP]
    bottom = landmarks[_MOUTH_BOTTOM]
    left = landmarks[_MOUTH_LEFT]
    right = landmarks[_MOUTH_RIGHT]
    upper_inner = landmarks[_MOUTH_UPPER_INNER]
    lower_inner = landmarks[_MOUTH_LOWER_INNER]

    v1 = np.linalg.norm(top - bottom)
    v2 = np.linalg.norm(upper_inner - lower_inner)
    h = np.linalg.norm(left - right)

    if h < 1e-6:
        return 0.0
    return float((v1 + v2) / (2.0 * h))


def _estimate_head_pose(
    landmarks: np.ndarray,
    image_width: int,
    image_height: int,
) -> tuple[float, float, float]:
    """Estimate head yaw, pitch, roll using cv2.solvePnP.

    Args:
        landmarks: (468, 3) normalised landmarks from MediaPipe.
        image_width: Width of the source image in pixels.
        image_height: Height of the source image in pixels.

    Returns:
        (yaw, pitch, roll) in degrees.
    """
    # Convert normalised landmark positions to pixel coordinates
    image_points = np.array(
        [
            [
                landmarks[idx][0] * image_width,
                landmarks[idx][1] * image_height,
            ]
            for idx in _POSE_LANDMARK_IDS
        ],
        dtype=np.float64,
    )

    # Approximate camera matrix (focal length ~ image width)
    focal_length = float(image_width)
    center = (image_width / 2.0, image_height / 2.0)
    camera_matrix = np.array(
        [
            [focal_length, 0.0, center[0]],
            [0.0, focal_length, center[1]],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    dist_coeffs = np.zeros((4, 1), dtype=np.float64)

    success, rotation_vec, _ = cv2.solvePnP(
        _3D_FACE_MODEL,
        image_points,
        camera_matrix,
        dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE,
    )

    if not success:
        return 0.0, 0.0, 0.0

    rotation_mat, _ = cv2.Rodrigues(rotation_vec)

    # Decompose rotation matrix into Euler angles
    sy = np.sqrt(rotation_mat[0, 0] ** 2 + rotation_mat[1, 0] ** 2)
    singular = sy < 1e-6

    if not singular:
        pitch = np.degrees(np.arctan2(rotation_mat[2, 1], rotation_mat[2, 2]))
        yaw = np.degrees(np.arctan2(-rotation_mat[2, 0], sy))
        roll = np.degrees(np.arctan2(rotation_mat[1, 0], rotation_mat[0, 0]))
    else:
        pitch = np.degrees(np.arctan2(-rotation_mat[1, 2], rotation_mat[1, 1]))
        yaw = np.degrees(np.arctan2(-rotation_mat[2, 0], sy))
        roll = 0.0

    return float(yaw), float(pitch), float(roll)


class FaceMeshDetector:
    """Detects 468 face landmarks using MediaPipe Face Mesh.

    Requires the ``mediapipe`` package.  If it is not installed, the
    constructor raises ``RuntimeError`` with installation instructions.

    Usage:
        detector = FaceMeshDetector()
        mesh = detector.detect(bgr_image)
        if mesh is not None:
            print(mesh.head_yaw, mesh.left_eye_ar)
    """

    def __init__(
        self,
        *,
        static_image_mode: bool = False,
        max_num_faces: int = 1,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        """
        Args:
            static_image_mode: Treat every frame as independent (slower
                but more robust for single images).
            max_num_faces: Maximum number of faces to detect.
            min_detection_confidence: Minimum confidence for face detection.
            min_tracking_confidence: Minimum confidence for landmark tracking.

        Raises:
            RuntimeError: If MediaPipe is not installed.
        """
        if not _MEDIAPIPE_AVAILABLE:
            raise RuntimeError(
                "MediaPipe is required for active liveness but is not installed. "
                "Install it with:  pip install mediapipe"
            )

        self._face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=static_image_mode,
            max_num_faces=max_num_faces,
            refine_landmarks=True,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        logger.debug("FaceMeshDetector initialised (MediaPipe Face Mesh)")

    def detect(self, image: np.ndarray) -> FaceMesh | None:
        """Detect face landmarks in a BGR image.

        Args:
            image: BGR image (H, W, 3) as uint8.

        Returns:
            FaceMesh with computed metrics, or None if no face was found.
        """
        h, w = image.shape[:2]
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self._face_mesh.process(rgb)

        if not results.multi_face_landmarks:
            return None

        face = results.multi_face_landmarks[0]
        landmarks = np.array(
            [[lm.x, lm.y, lm.z] for lm in face.landmark],
            dtype=np.float64,
        )

        left_ear = _eye_aspect_ratio(landmarks, _LEFT_EYE)
        right_ear = _eye_aspect_ratio(landmarks, _RIGHT_EYE)
        mar = _mouth_aspect_ratio(landmarks)
        yaw, pitch, roll = _estimate_head_pose(landmarks, w, h)

        return FaceMesh(
            landmarks_468=landmarks,
            left_eye_ar=left_ear,
            right_eye_ar=right_ear,
            mouth_ar=mar,
            head_yaw=yaw,
            head_pitch=pitch,
            head_roll=roll,
        )

    def close(self) -> None:
        """Release MediaPipe resources."""
        self._face_mesh.close()

    def __enter__(self) -> FaceMeshDetector:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
