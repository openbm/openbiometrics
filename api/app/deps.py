"""FastAPI dependency injection for OpenBiometrics services.

Provides get_kernel() and get_event_bus() dependencies that are
initialized once during application lifespan via init_services().
"""

from __future__ import annotations

from fastapi import HTTPException

from openbiometrics.config import BiometricConfig
from openbiometrics.kernel import BiometricKernel

_kernel: BiometricKernel | None = None


def init_services(config: BiometricConfig) -> None:
    """Initialize the kernel and all configured modules.

    Called once from the FastAPI lifespan handler.

    Args:
        config: Engine configuration.
    """
    global _kernel

    _kernel = BiometricKernel(config)
    _kernel.load()


def shutdown_services() -> None:
    """Shut down services gracefully. Called on app shutdown."""
    global _kernel

    if _kernel is not None:
        _kernel.shutdown()
        _kernel = None


def get_kernel() -> BiometricKernel:
    """FastAPI dependency -- returns the loaded BiometricKernel."""
    if _kernel is None:
        raise HTTPException(status_code=503, detail="Kernel not initialized")
    return _kernel


def get_event_bus():
    """FastAPI dependency -- returns the EventBus from the kernel.

    Returns the kernel's event bus instance, or raises 503 if unavailable.
    """
    kernel = get_kernel()
    bus = kernel.events
    if bus is None:
        raise HTTPException(status_code=503, detail="Event bus not available")
    return bus
