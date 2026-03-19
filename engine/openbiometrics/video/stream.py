"""Real-time video stream processing.

Handles RTSP, USB cameras, and video files.
Runs face pipeline on each frame with configurable skip/throttle.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from threading import Event, Thread

import cv2
import numpy as np

from openbiometrics.core.pipeline import FacePipeline, FaceResult


@dataclass
class StreamConfig:
    """Video stream configuration."""

    source: str | int  # RTSP URL, file path, or camera index
    process_every_n: int = 3  # Process every Nth frame (skip others)
    max_fps: float = 30.0
    resize_width: int = 0  # Resize before processing (0 = no resize)


class VideoStream:
    """Threaded video stream processor.

    Usage:
        stream = VideoStream(pipeline, StreamConfig(source=0))
        stream.start(callback=on_faces_detected)
        # ... later
        stream.stop()
    """

    def __init__(self, pipeline: FacePipeline, config: StreamConfig):
        self.pipeline = pipeline
        self.config = config
        self._stop_event = Event()
        self._thread: Thread | None = None

    def start(self, callback: Callable[[np.ndarray, list[FaceResult]], None]) -> None:
        """Start processing video stream in a background thread.

        Args:
            callback: Called with (frame, face_results) for each processed frame
        """
        self._stop_event.clear()
        self._thread = Thread(
            target=self._run, args=(callback,), daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the video stream."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self, callback: Callable[[np.ndarray, list[FaceResult]], None]) -> None:
        cap = cv2.VideoCapture(self.config.source)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video source: {self.config.source}")

        frame_interval = 1.0 / self.config.max_fps
        frame_count = 0

        try:
            while not self._stop_event.is_set():
                t0 = time.monotonic()

                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1
                if frame_count % self.config.process_every_n != 0:
                    continue

                # Optional resize
                if self.config.resize_width > 0:
                    h, w = frame.shape[:2]
                    scale = self.config.resize_width / w
                    frame = cv2.resize(frame, (self.config.resize_width, int(h * scale)))

                results = self.pipeline.process(frame)
                callback(frame, results)

                # Throttle
                elapsed = time.monotonic() - t0
                if elapsed < frame_interval:
                    time.sleep(frame_interval - elapsed)
        finally:
            cap.release()

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
