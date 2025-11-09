from farm_assistant.core.hud_parser import HUDParser


def test_temperature_parsing():
    parser = HUDParser()
    result = parser.parse_temperature("Температура 18.4° / 24.0°")
    assert result == (18.4, 24.0)


def test_water_parsing():
    parser = HUDParser()
    result = parser.parse_water("4.9 л. / 5.0 л.")
    assert result == (4.9, 5.0)


def test_stage_parsing():
    parser = HUDParser()
    stage, percent = parser.parse_stage("СТАДИЯ I (2%)")
    assert stage == "I"
    assert percent == 2.0


def test_genome_parsing():
    parser = HUDParser()
    genome = parser.parse_genome("G/G/G/G/X")
    assert genome == "GGGGX"


def test_crop_with_compound_name():
    parser = HUDParser()
    crop, status = parser._extract_crop_and_status("Виноград Белый Посажено")
    assert crop == "Виноград Белый"
    assert status == "Посажено"
