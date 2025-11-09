from farm_assistant.core.compare import RuleEngine
from farm_assistant.core.metrics import HUDParseResult, Severity


def build_parse_result(**overrides):
    base = HUDParseResult(
        crop="Кукуруза",
        status_text="Рекомендуется добавить удобрения",
        stage_text="СТАДИЯ I (2%)",
        genome_text="GGGGX",
        temperature_text="18.4° / 24.0°",
        water_text="4.0 л. / 5.0 л.",
        soil_text="0%",
        parasites_text="Нет",
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def test_engine_evaluates_water_deficit():
    engine = RuleEngine(settings={"genome_water_multiplier": 1.1})
    result = engine.evaluate(build_parse_result())
    assert result.water.status == Severity.WARN
    assert result.fertilizer.recommended is True
    assert result.fertilizer.dosage_l == 5.0


def test_parasite_matching():
    engine = RuleEngine()
    parsed = build_parse_result(parasites_text="Тля")
    result = engine.evaluate(parsed)
    assert result.parasites.status == Severity.WARN
    assert result.parasites.chemical_class == "БИОЛОГИЧЕСКИЕ"
    assert result.parasites.volume_l == 2.1
