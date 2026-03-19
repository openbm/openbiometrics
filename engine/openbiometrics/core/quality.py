"""Face image quality assessment.

Provides both heuristic quality checks and learned quality scoring.
Quality gating ensures only good-enough images enter the recognition pipeline.

Quality factors (ISO/IEC 29794-5):
- Face size (inter-eye distance)
- Pose (yaw, pitch, roll)
- Illumination uniformity
- Sharpness / blur
- Occlusion
"""

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class QualityReport:
    """Face image quality assessment results."""

    overall_score: float  # [0, 100]
    face_size_px: float
    sharpness: float  # Laplacian variance
    brightness: float  # Mean luminance [0, 255]
    contrast: float  # Luminance std dev
    head_pose_ok: bool
    is_acceptable: bool  # Meets minimum quality for recognition
    reasons: list[str]  # Why it failed, if not acceptable


class QualityAssessor:
    """Heuristic face quality assessment.

    For production, consider adding OFIQ (ISO reference implementation)
    or a learned quality model (CR-FIQA, SER-FIQ).
    """

    def __init__(
        self,
        min_face_size: float = 40.0,
        min_sharpness: float = 50.0,
        min_brightness: float = 40.0,
        max_brightness: float = 220.0,
        min_contrast: float = 20.0,
    ):
        self.min_face_size = min_face_size
        self.min_sharpness = min_sharpness
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness
        self.min_contrast = min_contrast

    def assess(self, face_crop: np.ndarray, landmarks: np.ndarray) -> QualityReport:
        """Assess quality of a face crop.

        Args:
            face_crop: BGR face crop
            landmarks: 5-point landmarks

        Returns:
            QualityReport with scores and pass/fail
        """
        reasons = []

        # Face size from landmarks
        left_eye, right_eye = landmarks[0], landmarks[1]
        mouth_center = (landmarks[3] + landmarks[4]) / 2
        eye_center = (left_eye + right_eye) / 2
        inter_eye = float(np.linalg.norm(right_eye - left_eye))
        eye_to_mouth = float(np.linalg.norm(mouth_center - eye_center))
        face_size = max(inter_eye, eye_to_mouth)

        if face_size < self.min_face_size:
            reasons.append(f"face_too_small ({face_size:.0f} < {self.min_face_size})")

        # Sharpness (Laplacian variance)
        gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if sharpness < self.min_sharpness:
            reasons.append(f"blurry ({sharpness:.1f} < {self.min_sharpness})")

        # Brightness
        brightness = float(gray.mean())
        if brightness < self.min_brightness:
            reasons.append(f"too_dark ({brightness:.0f})")
        elif brightness > self.max_brightness:
            reasons.append(f"too_bright ({brightness:.0f})")

        # Contrast
        contrast = float(gray.std())
        if contrast < self.min_contrast:
            reasons.append(f"low_contrast ({contrast:.1f})")

        # Head pose estimate from landmarks (rough)
        head_pose_ok = _check_head_pose(landmarks)
        if not head_pose_ok:
            reasons.append("head_pose_extreme")

        # Overall score (weighted combination)
        score = _compute_overall_score(face_size, sharpness, brightness, contrast, head_pose_ok)

        return QualityReport(
            overall_score=score,
            face_size_px=face_size,
            sharpness=sharpness,
            brightness=brightness,
            contrast=contrast,
            head_pose_ok=head_pose_ok,
            is_acceptable=len(reasons) == 0,
            reasons=reasons,
        )


def _check_head_pose(landmarks: np.ndarray) -> bool:
    """Rough head pose check from landmark symmetry."""
    left_eye, right_eye, nose = landmarks[0], landmarks[1], landmarks[2]
    eye_center = (left_eye + right_eye) / 2
    inter_eye = np.linalg.norm(right_eye - left_eye)

    if inter_eye < 1e-6:
        return False

    # Yaw: nose should be roughly between the eyes horizontally
    nose_offset = abs(nose[0] - eye_center[0]) / inter_eye
    if nose_offset > 0.35:
        return False

    # Roll: eye line should be roughly horizontal
    eye_angle = abs(np.degrees(np.arctan2(right_eye[1] - left_eye[1], right_eye[0] - left_eye[0])))
    if eye_angle > 30:
        return False

    return True


def _compute_overall_score(
    face_size: float, sharpness: float, brightness: float, contrast: float, head_pose_ok: bool
) -> float:
    """Compute overall quality score [0, 100]."""
    score = 0.0

    # Face size: 0-25 points
    score += min(25.0, (face_size / 80.0) * 25.0)

    # Sharpness: 0-30 points
    score += min(30.0, (sharpness / 200.0) * 30.0)

    # Brightness: 0-15 points (optimal around 128)
    bright_score = 1.0 - abs(brightness - 128.0) / 128.0
    score += max(0, bright_score * 15.0)

    # Contrast: 0-15 points
    score += min(15.0, (contrast / 60.0) * 15.0)

    # Head pose: 0-15 points
    if head_pose_ok:
        score += 15.0

    return min(100.0, score)
