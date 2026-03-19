"""Passive liveness detection (presentation attack detection).

Uses MiniFASNet-based models for silent anti-spoofing.
No user interaction required — works on a single image.

Models:
- MiniFASNetV2SE: ~600KB, ~98% accuracy (edge-friendly)
- MiniFASNetV1SE: ~2MB, slightly higher accuracy
"""

import cv2
import numpy as np

from openbiometrics.runtime.session import OnnxModelSession


class LivenessDetector:
    """Passive liveness detection from a single face image."""

    def __init__(self, model_path: str, ctx_id: int = 0):
        """
        Args:
            model_path: Path to anti-spoofing .onnx model
            ctx_id: GPU device ID (-1 for CPU)
        """
        self._model = OnnxModelSession(model_path, ctx_id=ctx_id)
        self.session = self._model.session
        self.input_name = self._model.input_name
        self.input_size = (self._model.input_shape[3], self._model.input_shape[2])  # (W, H)

    def check(self, face_crop: np.ndarray) -> tuple[bool, float]:
        """Check if a face is live (real) or a presentation attack (spoof).

        Args:
            face_crop: BGR face crop (any size, will be resized)

        Returns:
            (is_live, confidence) where confidence is in [0, 1]
        """
        blob = self._preprocess(face_crop)
        output = self._model.run(blob)[0][0]

        # Softmax over [spoof, live] logits
        exp_output = np.exp(output - np.max(output))
        probs = exp_output / exp_output.sum()

        live_score = float(probs[1])
        is_live = live_score > 0.5

        return is_live, live_score

    def _preprocess(self, face_crop: np.ndarray) -> np.ndarray:
        """Resize and normalize for MiniFASNet."""
        img = cv2.resize(face_crop, self.input_size)
        img = img.astype(np.float32)
        img = (img / 255.0 - np.array([0.485, 0.456, 0.406])) / np.array([0.229, 0.224, 0.225])
        img = img.transpose(2, 0, 1)[np.newaxis, ...]
        return img.astype(np.float32)
