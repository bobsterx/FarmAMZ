from __future__ import annotations

from typing import Dict, List, Optional

from .knowledge import KnowledgeBase
from .metrics import (
    BarReading,
    CropMetrics,
    FertilizerAdvice,
    GenomeInfo,
    ParasiteInfo,
    Severity,
)


class RuleEngine:
    def __init__(self, knowledge: Optional[KnowledgeBase] = None, settings: Optional[Dict] = None):
        self.knowledge = knowledge or KnowledgeBase.load_default()
        self.settings = settings or {}
        self.temp_delta_near = float(self.settings.get("temp_delta_near", 0.5))
        self.temp_delta_warn = float(self.settings.get("temp_delta_warn", 2.0))
        self.genome_water_multiplier = float(self.settings.get("genome_water_multiplier", 1.15))
        self.fertilizer_apply_factor = float(self.settings.get("fertilizer_apply_factor", 1.0))
        self.parasite_fuzzy_cutoff = int(self.settings.get("parasite_fuzzy_cutoff", 70))

    def evaluate(self, parse_result) -> CropMetrics:
        crop_info = self.knowledge.get_crop(parse_result.crop)
        from .hud_parser import HUDParser

        parser = HUDParser(parasite_fuzzy_cutoff=self.parasite_fuzzy_cutoff)
        stage, stage_percent = parser.parse_stage(parse_result.stage_text)
        genome_text = parser.parse_genome(parse_result.genome_text)
        genome = self._build_genome(genome_text)
        temperature = parser.parse_temperature(parse_result.temperature_text)
        water = parser.parse_water(parse_result.water_text)
        soil = parser.parse_soil(parse_result.soil_text)
        water_bar = self._evaluate_water(parse_result.crop, genome, crop_info, water)
        temperature_bar = self._evaluate_temperature(crop_info, temperature)
        parasites = self._evaluate_parasites(parse_result.crop, parse_result.parasites_text)
        fertilizer = self._evaluate_fertilizer(parse_result)
        alerts = self._collect_alerts([water_bar, temperature_bar, parasites])
        soil_pct = soil if soil is not None else None
        return CropMetrics(
            crop=parse_result.crop,
            status_text=parse_result.status_text,
            stage=stage,
            stage_percent=stage_percent,
            genome=genome,
            temperature=temperature_bar,
            water=water_bar,
            soil_pct=soil_pct,
            parasites=parasites,
            fertilizer=fertilizer,
            alerts=alerts,
        )

    def _build_genome(self, genome_text: Optional[str]) -> Optional[GenomeInfo]:
        if not genome_text:
            return None
        effects: List[str] = []
        water_multiplier = 1.0
        risk = None
        for gene in genome_text:
            description = self.knowledge.gene_effect(gene)
            if description:
                effects.append(f"{gene} — {description}")
            if gene.upper() == "W":
                water_multiplier *= self.genome_water_multiplier
            if gene.upper() == "X":
                risk = "повышен"
        return GenomeInfo(sequence=genome_text, effects=effects, risk=risk, water_multiplier=water_multiplier)

    def _evaluate_temperature(self, crop_info, temperature: Optional[tuple[float, float]]) -> Optional[BarReading]:
        if crop_info is None or temperature is None:
            return None
        current, target = temperature
        min_temp, max_temp = crop_info.temperature_range if crop_info.temperature_range else (None, None)
        notes: List[str] = []
        status = Severity.OK
        if min_temp is not None and max_temp is not None:
            if current < min_temp - self.temp_delta_warn or current > max_temp + self.temp_delta_warn:
                status = Severity.CRITICAL
            elif current < min_temp - self.temp_delta_near or current > max_temp + self.temp_delta_near:
                status = Severity.WARN
            elif current < min_temp or current > max_temp:
                status = Severity.NEAR
            else:
                status = Severity.OK
            notes.append(f"диапазон {min_temp}…{max_temp}°C")
        return BarReading(current=current, target=target, unit="°C", status=status, notes=notes)

    def _evaluate_water(
        self,
        crop_name: Optional[str],
        genome: Optional[GenomeInfo],
        crop_info,
        water_values: Optional[tuple[float, float]],
    ) -> Optional[BarReading]:
        if crop_info is None and water_values is None:
            return None
        current = required = None
        if water_values is not None:
            current, required = water_values
        elif crop_info is not None:
            required = crop_info.water_l
        if crop_info is not None and required is None:
            required = crop_info.water_l
        if genome is not None:
            if required is not None:
                required *= genome.water_multiplier
        status = Severity.OK
        notes: List[str] = []
        if required is not None and current is not None:
            if current < 0.5 * required:
                status = Severity.CRITICAL
                notes.append("критический дефицит воды")
            elif current < required:
                status = Severity.WARN
                notes.append("нехватка воды")
        elif current is None and required is not None:
            notes.append("нужно минимум {required:.1f} л".format(required=required))
        return BarReading(current=current, required=required, unit="л", status=status, notes=notes)

    def _evaluate_parasites(self, crop_name: Optional[str], parasite_text: Optional[str]) -> ParasiteInfo:
        if not parasite_text or parasite_text.upper() == "НЕТ":
            return ParasiteInfo(detected=parasite_text or "Нет", status=Severity.OK)
        chemical = self.knowledge.find_chemical(crop_name, parasite_text)
        if chemical:
            chem_class, info = chemical
            recommendation = f"{chem_class.title()} — {info.volume_l:.1f} л"
            return ParasiteInfo(
                detected=parasite_text,
                status=Severity.WARN,
                recommendation=recommendation,
                chemical_class=chem_class,
                volume_l=info.volume_l,
                confidence=1.0,
            )
        return ParasiteInfo(detected=parasite_text, status=Severity.WARN, confidence=0.0)

    def _evaluate_fertilizer(self, parse_result) -> FertilizerAdvice:
        advice = FertilizerAdvice()
        crop_info = self.knowledge.get_crop(parse_result.crop)
        if crop_info:
            advice.family = crop_info.fertilizer_family
            if parse_result.status_text and "УДОБ" in parse_result.status_text.upper():
                advice.recommended = True
                if crop_info.water_l is not None:
                    advice.dosage_l = crop_info.water_l * self.fertilizer_apply_factor
                    advice.rationale = "Рекомендуется добавить удобрения"
        return advice

    def _collect_alerts(self, components: List[Optional[object]]) -> List[str]:
        alerts: List[str] = []
        for component in components:
            if isinstance(component, BarReading) and component.status in {Severity.WARN, Severity.CRITICAL}:
                alerts.append(component.status.value)
            if isinstance(component, ParasiteInfo) and component.status != Severity.OK:
                alerts.append("Паразиты")
        return alerts
