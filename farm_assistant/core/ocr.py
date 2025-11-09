from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import cv2
import numpy as np
import pytesseract


@dataclass
class OCRConfig:
    psm: int = 6
    oem: int = 3
    language: str = "rus+ukr+eng"
    invert: bool = False
    adaptive: bool = True
    clahe_clip: float = 2.0
    clahe_grid: int = 8


class OCRProcessor:
    def __init__(self, config: OCRConfig):
        self.config = config

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
        clahe = cv2.createCLAHE(clipLimit=self.config.clahe_clip, tileGridSize=(self.config.clahe_grid, self.config.clahe_grid))
        gray = clahe.apply(gray)
        if self.config.adaptive:
            processed = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 35, 11)
        else:
            _, processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        if self.config.invert:
            processed = cv2.bitwise_not(processed)
        kernel = np.ones((2, 2), np.uint8)
        processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)
        return processed

    def ocr(self, image: np.ndarray) -> str:
        config = f"--psm {self.config.psm} --oem {self.config.oem}"
        processed = self.preprocess(image)
        text = pytesseract.image_to_string(processed, lang=self.config.language, config=config)
        return text.strip()


def batch_ocr(rois: Dict[str, np.ndarray], config: Optional[OCRConfig] = None) -> Dict[str, str]:
    processor = OCRProcessor(config or OCRConfig())
    results: Dict[str, str] = {}
    for key, image in rois.items():
        results[key] = processor.ocr(image)
    return results
