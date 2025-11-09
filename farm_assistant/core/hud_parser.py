from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, Optional

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover - fallback for environments without rapidfuzz
    def _simple_ratio(a: str, b: str) -> float:
        a = a.upper()
        b = b.upper()
        matches = sum(1 for ch1, ch2 in zip(a, b) if ch1 == ch2)
        return 100.0 * matches / max(len(a), len(b), 1)

    class _Fuzz:
        @staticmethod
        def partial_ratio(a: str, b: str) -> float:
            return _simple_ratio(a, b)

    fuzz = _Fuzz()

from .metrics import HUDParseResult
from .knowledge import DEFAULT_KNOWLEDGE

KNOWN_CROPS = sorted(DEFAULT_KNOWLEDGE["CROPS"].keys(), key=len, reverse=True)


NORMALIZATION_MAP = {
    "л.": "л",
    "л .": "л",
}


@dataclass
class HUDParser:
    parasite_fuzzy_cutoff: int = 70

    temperature_regex: re.Pattern = re.compile(
        r"(-?\d+(?:[\.,]\d+)?)\s*°\s*/\s*(-?\d+(?:[\.,]\d+)?)\s*°"
    )
    water_regex: re.Pattern = re.compile(
        r"(\d+(?:[\.,]\d+)?)\s*л\.?\s*/\s*(\d+(?:[\.,]\d+)?)\s*л\.?"
    )
    soil_regex: re.Pattern = re.compile(r"(\d+)\s*%")
    stage_regex: re.Pattern = re.compile(r"СТАДИЯ\s*([IVXLC]+)\s*\((\d+)%\)")

    def normalize_text(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKC", text)
        normalized = normalized.replace("\n", " ").replace("\r", " ")
        for key, value in NORMALIZATION_MAP.items():
            normalized = normalized.replace(key, value)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def parse(self, ocr_results: Dict[str, str]) -> HUDParseResult:
        normalized = {key: self.normalize_text(value) for key, value in ocr_results.items()}
        crop_block = normalized.get("crop")
        crop, status_text = self._extract_crop_and_status(crop_block)
        stage_text = normalized.get("stage")
        genome_text = normalized.get("genome")
        temperature_text = normalized.get("temperature")
        water_text = normalized.get("water")
        soil_text = normalized.get("soil")
        parasites_text = normalized.get("parasites")
        return HUDParseResult(
            crop=crop,
            status_text=status_text,
            stage_text=stage_text,
            genome_text=genome_text,
            temperature_text=temperature_text,
            water_text=water_text,
            soil_text=soil_text,
            parasites_text=parasites_text,
        )

    def _extract_crop_and_status(self, text: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        if not text:
            return None, None
        upper_text = text.upper()
        for crop in KNOWN_CROPS:
            if upper_text.startswith(crop):
                status = text[len(crop) :].strip()
                return crop.title(), status if status else None
        parts = text.split(" ")
        if len(parts) >= 2:
            crop = parts[0]
            status = " ".join(parts[1:]).strip()
            return crop.title() if crop else None, status or None
        return text.title(), None

    def parse_temperature(self, text: Optional[str]) -> Optional[tuple[float, float]]:
        if not text:
            return None
        match = self.temperature_regex.search(text.upper().replace(",", "."))
        if not match:
            return None
        current = float(match.group(1))
        target = float(match.group(2))
        return current, target

    def parse_water(self, text: Optional[str]) -> Optional[tuple[float, float]]:
        if not text:
            return None
        match = self.water_regex.search(text.replace(",", "."))
        if not match:
            return None
        current = float(match.group(1))
        required = float(match.group(2))
        return current, required

    def parse_soil(self, text: Optional[str]) -> Optional[float]:
        if not text:
            return None
        match = self.soil_regex.search(text)
        if not match:
            return None
        return float(match.group(1))

    def parse_stage(self, text: Optional[str]) -> tuple[Optional[str], Optional[float]]:
        if not text:
            return None, None
        match = self.stage_regex.search(text.upper())
        if not match:
            return text, None
        stage = match.group(1)
        percent = float(match.group(2))
        return stage, percent

    def parse_genome(self, text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        letters = re.findall(r"[GWYHX]", text.upper())
        if not letters:
            return None
        return "".join(letters)

    def fuzzy_match_parasite(self, text: Optional[str], candidates: list[str]) -> Optional[str]:
        if not text:
            return None
        best_match = None
        best_score = 0
        for candidate in candidates:
            score = fuzz.partial_ratio(text.upper(), candidate.upper())
            if score > best_score:
                best_match = candidate
                best_score = score
        if best_score >= self.parasite_fuzzy_cutoff:
            return best_match
        return None
