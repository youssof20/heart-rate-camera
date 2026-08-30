# Heart Rate Camera

Estimates heart rate from webcam video using remote photoplethysmography (rPPG).

It tracks color changes in the forehead, filters the pulse signal, and estimates BPM.

Not a medical device.

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/live.py
```

The first run downloads the face model into `models/`.

Optional:

```bash
python scripts/live.py --reference-bpm 72
python scripts/live.py --signal-method green
```

## Browser

```bash
cd web
python -m http.server 8080
```

Open `http://localhost:8080`.

Camera data stays in the browser.

## How it works

* MediaPipe tracks the face and forehead region.
* RGB values are sampled from the forehead.
* Python uses CHROM by default.
* The signal is band-pass filtered from 0.75–2.5 Hz.
* BPM is estimated from the dominant frequency.

## Evaluation

Record sessions against a reference pulse oximeter:

```bash
python scripts/record_study.py
python scripts/analyze_study.py
```

See `docs/STUDY_PROTOCOL.md`.

## Limits

Motion and poor lighting can make the estimate unreliable.

A finger sensor is more accurate.

## License

MIT
