from __future__ import annotations

from typing import List

from .metrics import CropMetrics, Severity


def build_recommendations(metrics: CropMetrics) -> List[str]:
    recommendations: List[str] = []
    if metrics.temperature and metrics.temperature.current is not None:
        notes = ", ".join(metrics.temperature.notes)
        target = metrics.temperature.target
        target_part = f" / {target:.1f}°" if target is not None else ""
        recommendations.append(
            f"Температура {metrics.temperature.current:.1f}°{target_part} ({metrics.temperature.status.value}) {notes}".strip()
        )
    if metrics.water and metrics.water.required is not None:
        current = metrics.water.current if metrics.water.current is not None else 0.0
        water_line = f"Вода {current:.1f}/{metrics.water.required:.1f} л"
        recommendations.append(f"{water_line} ({metrics.water.status.value})")
    if metrics.fertilizer and metrics.fertilizer.recommended:
        dosage = metrics.fertilizer.dosage_l
        if dosage is not None:
            recommendations.append(
                f"Удобрение: {metrics.fertilizer.family} — {dosage:.1f} л ({metrics.fertilizer.rationale})"
            )
    if metrics.parasites and metrics.parasites.status != Severity.OK:
        if metrics.parasites.recommendation:
            recommendations.append(
                f"Паразиты: {metrics.parasites.detected} → {metrics.parasites.recommendation}"
            )
        else:
            recommendations.append(f"Паразиты: {metrics.parasites.detected} (требуется уточнение)")
    if metrics.genome:
        genome_effects = "; ".join(metrics.genome.effects)
        if metrics.genome.risk:
            genome_effects += f"; риск паразитов {metrics.genome.risk}"
        recommendations.append(f"Геном {metrics.genome.sequence}: {genome_effects}")
    return recommendations
