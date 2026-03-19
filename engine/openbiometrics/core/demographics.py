"""Age and gender estimation from face images.

Uses InsightFace's genderage model (part of buffalo model pack).
"""

import cv2
import numpy as np

from openbiometrics.runtime.session import OnnxModelSession


class DemographicsEstimator:
    """Estimate age and gender from aligned face images."""

    def __init__(self, model_path: str, ctx_id: int = 0):
        self._model = OnnxModelSession(model_path, ctx_id=ctx_id)
        self.session = self._model.session
        self.input_name = self._model.input_name
        self.input_size = (self._model.input_shape[3], self._model.input_shape[2])  # (W, H)

    def estimate(self, aligned_face: np.ndarray) -> tuple[int, str]:
        """Estimate age and gender from an aligned face.

        Args:
            aligned_face: BGR aligned face (any size, will be resized)

        Returns:
            (age, gender) where gender is "M" or "F"
        """
        img = cv2.resize(aligned_face, self.input_size)
        blob = img.astype(np.float32)
        blob = (blob - 127.5) / 127.5
        blob = blob.transpose(2, 0, 1)[np.newaxis, ...]

        output = self._model.run(blob)[0][0]

        # InsightFace genderage model: output is [female_score, male_score, age_normalized]
        gender = "F" if output[0] > output[1] else "M"
        age = int(np.round(output[2] * 100))

        return age, gender
