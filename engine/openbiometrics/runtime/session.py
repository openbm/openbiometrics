"""ONNX Runtime session wrapper with automatic provider selection.

Encapsulates the CUDA vs CPU provider logic that was previously
duplicated across recognizer, liveness, and demographics modules.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import onnxruntime as ort


class OnnxModelSession:
    """Wrapper around ort.InferenceSession with provider selection.

    Handles CUDA/CPU provider configuration based on ctx_id and
    exposes convenient properties for model input metadata.

    Usage:
        session = OnnxModelSession("model.onnx", ctx_id=0)
        output = session.run({session.input_name: input_data})
    """

    def __init__(
        self,
        model_path: str | Path,
        ctx_id: int = 0,
        providers: list | None = None,
    ):
        """
        Args:
            model_path: Path to .onnx model file
            ctx_id: GPU device ID (>= 0) or -1 for CPU
            providers: Optional explicit provider list. If None,
                       providers are selected based on ctx_id.
        """
        self._model_path = str(model_path)

        if providers is not None:
            self._providers = providers
        elif ctx_id >= 0:
            self._providers = [
                ("CUDAExecutionProvider", {"device_id": ctx_id}),
                "CPUExecutionProvider",
            ]
        else:
            self._providers = ["CPUExecutionProvider"]

        self._session = ort.InferenceSession(self._model_path, providers=self._providers)

        input_cfg = self._session.get_inputs()[0]
        self._input_name = input_cfg.name
        self._input_shape = input_cfg.shape

    @property
    def input_name(self) -> str:
        """Name of the first input tensor."""
        return self._input_name

    @property
    def input_shape(self) -> list:
        """Shape of the first input tensor, e.g. [1, 3, 112, 112]."""
        return self._input_shape

    @property
    def session(self) -> ort.InferenceSession:
        """Underlying ONNX Runtime InferenceSession."""
        return self._session

    def run(self, input_data: np.ndarray) -> list[np.ndarray]:
        """Run inference with the first input tensor.

        Args:
            input_data: Input array matching the model's expected shape

        Returns:
            List of output arrays from the model
        """
        return self._session.run(None, {self._input_name: input_data})

    def __repr__(self) -> str:
        return (
            f"OnnxModelSession(model={self._model_path!r}, "
            f"input={self._input_name}, shape={self._input_shape})"
        )
