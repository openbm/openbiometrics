"""Camera manager for multi-stream video processing.

Manages multiple VideoStream instances with thread-safe operations.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock

import cv2
import numpy as np

from openbiometrics.video.stream import StreamConfig, VideoStream

logger = logging.getLogger(__name__)


@dataclass
class CameraStatus:
    """Status of a managed camera.

    Attributes:
        camera_id: Unique identifier for the camera.
        source: Video source (RTSP URL, file path, or device index).
        is_running: Whether the stream is currently active.
        fps: Measured frames per second (0 if not running).
        frame_count: Total frames processed.
    """

    camera_id: str
    source: str | int
    is_running: bool
    fps: float
    frame_count: int


class _ManagedCamera:
    """Internal state for a managed camera."""

    def __init__(
        self,
        camera_id: str,
        source: str | int,
        pipeline_fn: Callable | None,
    ):
        self.camera_id = camera_id
        self.source = source
        self.pipeline_fn = pipeline_fn
        self.stream: VideoStream | None = None
        self.last_frame: np.ndarray | None = None
        self.frame_count: int = 0
        self.fps: float = 0.0
        self._last_time: float = 0.0
        self._fps_frame_count: int = 0
        self._fps_interval: float = 1.0  # Calculate FPS over 1 second

    def on_frame(self, frame: np.ndarray, results: object) -> None:
        """Callback for processed frames."""
        self.last_frame = frame
        self.frame_count += 1
        self._fps_frame_count += 1

        now = time.monotonic()
        elapsed = now - self._last_time
        if elapsed >= self._fps_interval:
            self.fps = self._fps_frame_count / elapsed
            self._fps_frame_count = 0
            self._last_time = now

        if self.pipeline_fn is not None:
            self.pipeline_fn(self.camera_id, frame, results)


class CameraManager:
    """Manages multiple video streams with thread-safe access.

    Usage:
        manager = CameraManager()
        manager.add_camera("cam1", "rtsp://...", pipeline_fn=my_callback)
        manager.add_camera("cam2", 0)

        for status in manager.list_cameras():
            print(f"{status.camera_id}: running={status.is_running}")

        snapshot = manager.get_snapshot("cam1")
        manager.remove_camera("cam1")
    """

    def __init__(self, default_pipeline: object | None = None):
        """
        Args:
            default_pipeline: Optional FacePipeline (or compatible) used
                for cameras that don't specify their own pipeline_fn.
        """
        self._cameras: dict[str, _ManagedCamera] = {}
        self._default_pipeline = default_pipeline
        self._lock = Lock()

    def add_camera(
        self,
        camera_id: str,
        source: str | int,
        pipeline_fn: Callable | None = None,
        stream_config: StreamConfig | None = None,
    ) -> None:
        """Add and start a camera stream.

        Args:
            camera_id: Unique identifier for the camera.
            source: RTSP URL, file path, or device index.
            pipeline_fn: Optional callback(camera_id, frame, results) for
                each processed frame. If None, frames are captured but
                only snapshots are available.
            stream_config: Optional stream configuration. If None, defaults
                are used with the given source.
        """
        with self._lock:
            if camera_id in self._cameras:
                raise ValueError(f"Camera '{camera_id}' already exists")

            managed = _ManagedCamera(camera_id, source, pipeline_fn)

            if self._default_pipeline is not None:
                config = stream_config or StreamConfig(source=source)
                stream = VideoStream(self._default_pipeline, config)
                stream.start(callback=managed.on_frame)
                managed.stream = stream

            self._cameras[camera_id] = managed
            logger.info("Added camera %s (source=%s)", camera_id, source)

    def remove_camera(self, camera_id: str) -> None:
        """Stop and remove a camera stream.

        Args:
            camera_id: ID of the camera to remove.
        """
        with self._lock:
            managed = self._cameras.pop(camera_id, None)

        if managed is None:
            logger.warning("Camera '%s' not found", camera_id)
            return

        if managed.stream is not None:
            managed.stream.stop()
        logger.info("Removed camera %s", camera_id)

    def list_cameras(self) -> list[CameraStatus]:
        """List all managed cameras and their status.

        Returns:
            List of CameraStatus for each managed camera.
        """
        with self._lock:
            result: list[CameraStatus] = []
            for cam_id, managed in self._cameras.items():
                is_running = managed.stream is not None and managed.stream.is_running
                result.append(
                    CameraStatus(
                        camera_id=cam_id,
                        source=managed.source,
                        is_running=is_running,
                        fps=managed.fps,
                        frame_count=managed.frame_count,
                    )
                )
            return result

    def get_snapshot(self, camera_id: str) -> np.ndarray | None:
        """Get the latest frame from a camera.

        If the camera has a running stream, returns the last processed
        frame. Otherwise, attempts a single capture from the source.

        Args:
            camera_id: ID of the camera.

        Returns:
            BGR image as numpy array, or None if unavailable.
        """
        with self._lock:
            managed = self._cameras.get(camera_id)
            if managed is None:
                return None

            # Return cached frame if available
            if managed.last_frame is not None:
                return managed.last_frame.copy()

            source = managed.source

        # Fallback: single capture (outside lock to avoid blocking)
        cap = cv2.VideoCapture(source)
        try:
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    return frame
        finally:
            cap.release()

        return None

    def stop_all(self) -> None:
        """Stop and remove all cameras."""
        with self._lock:
            camera_ids = list(self._cameras.keys())

        for cam_id in camera_ids:
            self.remove_camera(cam_id)

    def __repr__(self) -> str:
        with self._lock:
            return f"CameraManager(cameras={list(self._cameras.keys())})"

    def __del__(self) -> None:
        self.stop_all()
