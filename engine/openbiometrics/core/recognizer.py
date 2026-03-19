"""Face recognition using ArcFace embedding models.

Extracts 512-dimensional face embeddings for comparison.
Models available via InsightFace model zoo:
- buffalo_l: w600k_r50 (best accuracy, ~99.86% LFW)
- buffalo_s: w600k_mbf (mobile/edge, ~99.5% LFW)
"""

import numpy as np

from openbiometrics.runtime.session import OnnxModelSession


class FaceRecognizer:
    """ArcFace-based face embedding extractor."""

    def __init__(self, model_path: str, ctx_id: int = 0):
        """
        Args:
            model_path: Path to .onnx recognition model
            ctx_id: GPU device ID (-1 for CPU)
        """
        self._model = OnnxModelSession(model_path, ctx_id=ctx_id)
        self.session = self._model.session
        self.input_name = self._model.input_name
        self.input_shape = self._model.input_shape  # e.g. [1, 3, 112, 112]

    def get_embedding(self, aligned_face: np.ndarray) -> np.ndarray:
        """Extract 512-d embedding from a 112x112 aligned face.

        Args:
            aligned_face: BGR 112x112 aligned face image

        Returns:
            Normalized 512-d float32 embedding
        """
        blob = _preprocess(aligned_face)
        embedding = self._model.run(blob)[0][0]
        # L2 normalize
        embedding = embedding / np.linalg.norm(embedding)
        return embedding.astype(np.float32)

    def get_embeddings_batch(self, aligned_faces: list[np.ndarray]) -> list[np.ndarray]:
        """Extract embeddings for a batch of aligned faces."""
        if not aligned_faces:
            return []
        batch = np.concatenate([_preprocess(f) for f in aligned_faces], axis=0)
        embeddings = self._model.run(batch)[0]
        # L2 normalize each
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms
        return [e.astype(np.float32) for e in embeddings]

    @staticmethod
    def compare(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Cosine similarity between two embeddings. Returns [-1, 1]."""
        return float(np.dot(embedding1, embedding2))

    @staticmethod
    def compare_to_threshold(similarity: float, threshold: float = 0.4) -> bool:
        """Check if similarity exceeds verification threshold.

        Default threshold 0.4 corresponds to ~FAR=1e-6 for ArcFace r50.
        Adjust based on your security requirements.
        """
        return similarity >= threshold


def _preprocess(aligned_face: np.ndarray) -> np.ndarray:
    """Preprocess aligned face for ArcFace inference.

    Args:
        aligned_face: BGR uint8 [112, 112, 3]

    Returns:
        Float32 blob [1, 3, 112, 112], normalized to [-1, 1]
    """
    img = aligned_face.astype(np.float32)
    # BGR -> RGB
    img = img[:, :, ::-1]
    # Normalize to [-1, 1] (standard for ArcFace)
    img = (img - 127.5) / 127.5
    # HWC -> CHW -> NCHW
    img = img.transpose(2, 0, 1)[np.newaxis, ...]
    return img
