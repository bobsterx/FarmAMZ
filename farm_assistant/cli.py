from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Optional

import cv2
import numpy as np
import typer
import yaml

from .core.logger import FarmLogger
from .core.metrics import CropMetrics
from .core.ocr import OCRConfig, OCRProcessor
from .core.hud_parser import HUDParser
from .core.compare import RuleEngine
from .core.recommender import build_recommendations

app = typer.Typer(add_completion=False)


def load_settings(path: Optional[Path]) -> Dict:
    if path is None:
        path = Path(__file__).resolve().parent / "settings.yaml"
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def extract_rois(image: np.ndarray, rois_config: Dict[str, Dict[str, float]]) -> Dict[str, np.ndarray]:
    h, w = image.shape[:2]
    extracted: Dict[str, np.ndarray] = {}
    for name, roi in rois_config.items():
        x = int(roi["x"] * w)
        y = int(roi["y"] * h)
        width = int(roi["width"] * w)
        height = int(roi["height"] * h)
        extracted[name] = image[y : y + height, x : x + width]
    return extracted


def parse_frame(image: np.ndarray, settings: Dict) -> CropMetrics:
    ocr_settings = settings.get("ocr", {})
    rois = settings.get("rois", {})
    ocr_config = OCRConfig(
        psm=ocr_settings.get("psm", 6),
        oem=ocr_settings.get("oem", 3),
        language=ocr_settings.get("language", "rus+ukr+eng"),
        invert=ocr_settings.get("invert", False),
        adaptive=ocr_settings.get("adaptive", True),
        clahe_clip=ocr_settings.get("clahe_clip", 2.0),
        clahe_grid=ocr_settings.get("clahe_grid", 8),
    )
    processor = OCRProcessor(ocr_config)
    rois_images = extract_rois(image, rois)
    ocr_results = {name: processor.ocr(img) for name, img in rois_images.items()}
    parser = HUDParser(parasite_fuzzy_cutoff=settings.get("parasite_fuzzy_cutoff", 70))
    parse_result = parser.parse(ocr_results)
    engine = RuleEngine(settings=settings)
    metrics = engine.evaluate(parse_result)
    return metrics


def render_output(metrics: CropMetrics, logger: FarmLogger, save_json: Optional[Path] = None) -> None:
    summary = {
        "timestamp": metrics.timestamp.isoformat(),
        "crop": metrics.crop,
        "stage": metrics.stage,
        "stage_percent": metrics.stage_percent,
        "genome": metrics.genome.sequence if metrics.genome else None,
        "temperature": asdict(metrics.temperature) if metrics.temperature else None,
        "water": asdict(metrics.water) if metrics.water else None,
        "soil_pct": metrics.soil_pct,
        "parasites": asdict(metrics.parasites) if metrics.parasites else None,
        "fertilizer": asdict(metrics.fertilizer) if metrics.fertilizer else None,
        "alerts": metrics.alerts,
    }
    logger.log_json(summary)
    crop_name = metrics.crop or "Неизвестная культура"
    temp_status = metrics.temperature.status.value if metrics.temperature else "OK"
    headline = f"[{temp_status}] {crop_name}"
    logger.log("INFO", headline, payload=summary)
    for rec in build_recommendations(metrics):
        logger.log("ADVICE", rec)
    if save_json:
        save_json.parent.mkdir(parents=True, exist_ok=True)
        save_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


@app.command()
def analyze_image(
    path: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, readable=True),
    settings_path: Optional[Path] = typer.Option(None, exists=True, file_okay=True, dir_okay=False),
    save_json: Optional[Path] = typer.Option(None, file_okay=True, dir_okay=False),
    log_file: Path = typer.Option(Path("logs/farm_log.txt")),
) -> None:
    """Analyze a HUD screenshot."""
    settings = load_settings(settings_path)
    image = cv2.imread(str(path))
    if image is None:
        raise typer.BadParameter("Не удалось загрузить изображение")
    metrics = parse_frame(image, settings)
    logger = FarmLogger(log_file=log_file)
    render_output(metrics, logger, save_json)


@app.command()
def watch(
    fps: int = typer.Option(5, help="Target FPS for capture"),
    roi: Optional[str] = typer.Option(None, help="ROI preset name"),
    settings_path: Optional[Path] = typer.Option(None),
) -> None:
    """Start live capture (requires dxcam or mss)."""
    settings = load_settings(settings_path)
    from .core.capture import CaptureConfig, get_frame_provider

    capture_region = None
    if roi and roi in settings.get("capture_rois", {}):
        capture_region = tuple(settings["capture_rois"][roi])  # type: ignore[arg-type]
    config = CaptureConfig(region=capture_region, fps=fps)
    provider = get_frame_provider(config)
    logger = FarmLogger()
    for frame in provider:
        metrics = parse_frame(frame, settings)
        render_output(metrics, logger)


if __name__ == "__main__":
    app()
