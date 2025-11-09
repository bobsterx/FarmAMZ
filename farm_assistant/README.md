# Farm Assistant

Stage-1 visual agronomy assistant for SAMP-like farming HUDs.

## Setup

1. Install Python 3.10+
2. Install system packages for OpenCV and Tesseract OCR.
3. Install Tesseract language packs for Russian and Ukrainian.
4. Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Analyze a static screenshot:

```bash
python -m farm_assistant.cli analyze-image --path /path/to/hud.png
```

Live capture (requires `dxcam` or `mss`):

```bash
python -m farm_assistant.cli watch --fps 10 --roi preset_right_panel
```

Configuration lives in `settings.yaml`.
