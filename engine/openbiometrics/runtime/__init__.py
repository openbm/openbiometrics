"""Runtime abstraction layer for OpenBiometrics.

Provides ONNX session management and model registry.
"""

from openbiometrics.runtime.registry import ModelInfo, ModelRegistry
from openbiometrics.runtime.session import OnnxModelSession

__all__ = ["ModelInfo", "ModelRegistry", "OnnxModelSession"]
