# Heart Rate Camera

Estimates your heart rate (BPM) from a webcam.

1. Finds your face and forehead.
2. Reads small color changes in the skin (blood pulse).
3. Filters the signal and shows BPM.

Not a medical device. For learning and experiments only.

## Run (Python)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/live.py
```

First run downloads the face model into `models/`.

Keys: `q` quit, `m` motion, `b` breath-hold, `o` cover face, `d` dark, `t` bright light

Optional:

```bash
python scripts/live.py --reference-bpm 72
python scripts/live.py --signal-method green
```

## Run (browser)

```bash
cd web
python -m http.server 8080
```

Open http://localhost:8080. Needs localhost or HTTPS for camera access. Nothing is uploaded.

## How it works

- **Face:** MediaPipe face mesh, forehead region.
- **Signal:** RGB from forehead. Python uses CHROM by default; browser uses green channel.
- **Rate:** Bandpass filter (0.75-2.5 Hz), FFT peak, convert to BPM.

Settings: [`config/pipeline.json`](config/pipeline.json)

## Study (optional)

Record sessions and compare to a pulse oximeter:

```bash
python scripts/record_study.py
python scripts/analyze_study.py
```

See [`docs/STUDY_PROTOCOL.md`](docs/STUDY_PROTOCOL.md).

## Limits

- Sit still, normal indoor light works best.
- Motion, dark rooms, and bright torch break the reading.
- Not as accurate as a finger sensor.

## Code

```
src/rppg/       library
scripts/        live demo and study tools
web/            browser demo
config/         settings
```

Private notes go in `internal/` (not in git). See [`templates/internal/README.md`](templates/internal/README.md).

## Uses

Python, OpenCV, MediaPipe, SciPy, Matplotlib, JavaScript
