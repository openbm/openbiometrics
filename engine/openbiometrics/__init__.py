from openbiometrics.config import BiometricConfig, FaceConfig
from openbiometrics.core.pipeline import FacePipeline, PipelineConfig
from openbiometrics.kernel import BiometricKernel
from openbiometrics.runtime import ModelRegistry, OnnxModelSession

__all__ = [
    "BiometricConfig",
    "BiometricKernel",
    "FaceConfig",
    "FacePipeline",
    "ModelRegistry",
    "OnnxModelSession",
    "PipelineConfig",
]

# Optional module re-exports -- available when dependencies are installed.
# Users can import directly from subpackages for full access:
#   from openbiometrics.document import DocumentPipeline
#   from openbiometrics.liveness import ActiveLivenessManager
#   from openbiometrics.person import PersonDetector, PersonTracker
#   from openbiometrics.events import EventBus
#   from openbiometrics.identity import FaceClusterer, IdentityResolver

try:
    from openbiometrics.document.pipeline import DocumentPipeline
    __all__.append("DocumentPipeline")
except ImportError:
    pass

try:
    from openbiometrics.liveness.session import ActiveLivenessManager
    __all__.append("ActiveLivenessManager")
except ImportError:
    pass

try:
    from openbiometrics.person.detector import PersonDetector
    from openbiometrics.person.tracker import PersonTracker
    __all__.extend(["PersonDetector", "PersonTracker"])
except ImportError:
    pass

try:
    from openbiometrics.events.bus import EventBus
    __all__.append("EventBus")
except ImportError:
    pass

try:
    from openbiometrics.identity.clustering import FaceClusterer
    from openbiometrics.identity.resolver import IdentityResolver
    __all__.extend(["FaceClusterer", "IdentityResolver"])
except ImportError:
    pass
