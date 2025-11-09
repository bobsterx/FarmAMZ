from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class Severity(str, Enum):
    OK = "OK"
    NEAR = "NEAR"
    WARN = "WARN"
    CRITICAL = "CRITICAL"


@dataclass
class BarReading:
    current: Optional[float] = None
    target: Optional[float] = None
    required: Optional[float] = None
    unit: str = ""
    status: Severity = Severity.OK
    notes: List[str] = field(default_factory=list)


@dataclass
class GenomeInfo:
    sequence: str
    effects: List[str] = field(default_factory=list)
    risk: Optional[str] = None
    water_multiplier: float = 1.0


@dataclass
class ParasiteInfo:
    detected: str
    status: Severity = Severity.OK
    recommendation: Optional[str] = None
    chemical_class: Optional[str] = None
    volume_l: Optional[float] = None
    confidence: float = 0.0


@dataclass
class FertilizerAdvice:
    family: Optional[str] = None
    recommended: bool = False
    dosage_l: Optional[float] = None
    rationale: Optional[str] = None


@dataclass
class CropMetrics:
    crop: Optional[str]
    status_text: Optional[str]
    stage: Optional[str]
    stage_percent: Optional[float]
    genome: Optional[GenomeInfo]
    temperature: Optional[BarReading]
    water: Optional[BarReading]
    soil_pct: Optional[float]
    parasites: Optional[ParasiteInfo]
    fertilizer: Optional[FertilizerAdvice]
    alerts: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class HUDParseResult:
    crop: Optional[str]
    status_text: Optional[str]
    stage_text: Optional[str]
    genome_text: Optional[str]
    temperature_text: Optional[str]
    water_text: Optional[str]
    soil_text: Optional[str]
    parasites_text: Optional[str]
