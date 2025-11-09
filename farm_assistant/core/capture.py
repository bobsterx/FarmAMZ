from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterator, Optional, Tuple

import numpy as np

try:
    import dxcam  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    dxcam = None

try:
    from mss import mss  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    mss = None


@dataclass
class CaptureConfig:
    monitor_index: int = 0
    region: Optional[Tuple[int, int, int, int]] = None
    fps: int = 10


class FrameProvider:
    def __iter__(self) -> Iterator[np.ndarray]:
        raise NotImplementedError


class DXFrameProvider(FrameProvider):  # pragma: no cover - hardware dependent
    def __init__(self, config: CaptureConfig):
        if dxcam is None:
            raise RuntimeError("dxcam is not available")
        self.config = config
        self.camera = dxcam.create(device_index=config.monitor_index)
        self.camera.start(region=config.region, target_fps=config.fps)

    def __iter__(self) -> Iterator[np.ndarray]:
        frame = self.camera.get_latest_frame()
        if frame is None:
            raise StopIteration
        yield frame


class MSSFrameProvider(FrameProvider):  # pragma: no cover - hardware dependent
    def __init__(self, config: CaptureConfig):
        if mss is None:
            raise RuntimeError("mss is not available")
        self.config = config
        self._sct = mss()

    def __iter__(self) -> Iterator[np.ndarray]:
        region = None
        if self.config.region:
            x1, y1, x2, y2 = self.config.region
            region = {"left": x1, "top": y1, "width": x2 - x1, "height": y2 - y1}
        while True:
            frame = np.array(self._sct.grab(region))
            yield frame
            time.sleep(1 / self.config.fps)


def get_frame_provider(config: CaptureConfig) -> FrameProvider:
    if dxcam is not None:
        return DXFrameProvider(config)
    if mss is not None:
        return MSSFrameProvider(config)
    raise RuntimeError("No capture backend available; install dxcam or mss")
