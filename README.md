# My Camera Is Taking Your Pulse Right Now

Remote photoplethysmography (rPPG) from a webcam: MediaPipe finds your forehead, the green channel averages subtle color changes from blood volume pulse, a Butterworth bandpass keeps the 0.75-2.5 Hz band, and FFT returns beats per minute.

The study side tracks error across Fitzpatrick skin types and lighting. Publish the numbers you get, including bad runs.

**Not a medical device.** Research and education only.

## Quick start

### Python (desktop)

```bash
cd heart-rate-camera
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python scripts/live.py
```

First run downloads the MediaPipe face landmarker model into `models/`.

Controls: `q` quit, `m` motion, `b` breath-hold, `o` occlusion, `d` dark, `t` torch

### Browser (audience demo)

Serve from the **web/** folder (required for ES modules):

```bash
cd web
python -m http.server 8080
```

Open [http://localhost:8080](http://localhost:8080). Camera access needs **localhost** or **HTTPS**.

All processing runs in the browser. No video is uploaded.

## How it works

```
Webcam → MediaPipe face mesh → forehead ROI → green channel mean
      → detrend → Butterworth 0.75-2.5 Hz → FFT peak → BPM × 60
```

Shared parameters: [`config/pipeline.json`](config/pipeline.json) (Python) and [`web/config/pipeline.json`](web/config/pipeline.json) (browser). Keep both files in sync when you tune settings.

## Study workflow

1. Read [`docs/STUDY_PROTOCOL.md`](docs/STUDY_PROTOCOL.md)
2. Record sessions: `python scripts/record_study.py`
3. Analyze: `python scripts/analyze_study.py`
4. Log stress tests: [`docs/FAILURE_MODES.md`](docs/FAILURE_MODES.md)

### Results (fill after data collection)

| Fitzpatrick | n | MAE (BPM) | RMSE (BPM) |
|-------------|---|-----------|------------|
| *pending* | | | |

Run `analyze_study.py` after recording and paste aggregate stats here.

## Private notes (not on GitHub)

Personal shoot notes, drafts, and internal scripts go in `internal/` (gitignored). See [`templates/internal/README.md`](templates/internal/README.md). Only aggregate, anonymized study results belong in the public repo.

## Project layout

```
config/pipeline.json     # Shared DSP + ROI settings
src/rppg/                # Python library
scripts/live.py          # Live demo
scripts/record_study.py  # Study capture
scripts/analyze_study.py # MAE / RMSE / plots
web/                     # Browser demo
docs/                    # Protocol + failure modes
data/sessions/           # Recordings (gitignored)
```

## Limitations

- Green-channel mean is the simplest rPPG method. It skews under uneven light and across skin tones.
- Motion, occlusion, darkness, and glare break estimation. See [`docs/FAILURE_MODES.md`](docs/FAILURE_MODES.md).
- Web and Python share config but can disagree slightly because of camera and FPS differences.

CHROM or POS in Python would be a fairer follow-up if you extend the project.

## Clinical context

Hospitals use contactless rPPG in ICU and post-op research to watch pulse without stick-on sensors. Lighting, motion, and skin tone still limit real deployments. Simple green-channel methods inherit that bias.

References:

- Verkruysse et al., *Remote plethysmographic imaging using ambient light* (2008)
- de Haan & Jeanne, *Robust pulse rate from chrominance-based rPPG* (CHROM, 2013)
- Surveys on bias and dataset diversity in rPPG ML

## Stack

Python, OpenCV, MediaPipe, SciPy, Matplotlib, vanilla JS (browser)

## License

MIT (add `LICENSE` if publishing to GitHub)
