"""Download required models for OpenBiometrics.

Downloads InsightFace buffalo_l model pack which includes:
- det_10g.onnx (SCRFD face detector)
- w600k_r50.onnx (ArcFace recognition)
- genderage.onnx (age/gender estimation)
- 2d106det.onnx (landmark detection)
- 1k3d68.onnx (3D landmark detection)

For liveness, you need to separately download a MiniFASNet model.
"""

import os
import sys
from pathlib import Path


def download_insightface_models(models_dir: str = "./models") -> None:
    """Download InsightFace buffalo_l model pack."""
    from insightface.app import FaceAnalysis

    print("Downloading InsightFace buffalo_l models...")
    # This triggers automatic download to ~/.insightface/models/buffalo_l/
    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=-1, det_size=(640, 640))

    # Copy/symlink models to our models directory
    src = Path.home() / ".insightface" / "models" / "buffalo_l"
    dst = Path(models_dir)
    dst.mkdir(parents=True, exist_ok=True)

    for model_file in src.glob("*.onnx"):
        target = dst / model_file.name
        if not target.exists():
            os.symlink(model_file, target)
            print(f"  Linked: {model_file.name}")
        else:
            print(f"  Exists: {model_file.name}")

    print(f"\nModels ready in {dst.resolve()}")
    print("\nFor liveness detection, download a MiniFASNet ONNX model:")
    print("  https://github.com/minivision-ai/Silent-Face-Anti-Spoofing")
    print("  Place as: models/antispoofing.onnx")


if __name__ == "__main__":
    models_dir = sys.argv[1] if len(sys.argv) > 1 else "./models"
    download_insightface_models(models_dir)
