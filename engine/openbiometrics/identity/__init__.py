"""OpenBiometrics identity services — clustering and cross-watchlist resolution."""

from openbiometrics.identity.clustering import DuplicateGroup, FaceClusterer
from openbiometrics.identity.resolver import IdentityResolver, ResolvedIdentity

__all__ = ["FaceClusterer", "IdentityResolver", "DuplicateGroup", "ResolvedIdentity"]
