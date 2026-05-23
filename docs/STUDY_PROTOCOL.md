# Study Protocol — rPPG Accuracy Across Skin Tones

## Purpose

Measure how accurately green-channel webcam rPPG estimates heart rate across Fitzpatrick skin types and lighting conditions. Report results honestly, including failures.

## Equipment

- Laptop webcam (same device for all subjects when possible)
- Optional finger pulse oximeter (preferred ground truth)
- Consistent indoor seating position (~50 cm from screen)

## Per-subject procedure

1. **Label subject** with anonymous ID (e.g. `S01`), not real name in files.
2. **Fitzpatrick scale (I–VI)** — record whether self-reported or researcher-assigned.
3. **Reference heart rate**
   - **Preferred:** pulse oximeter, note BPM at start, middle, and end of capture; use median as `reference_bpm`.
   - **Fallback:** manual count for 30 s immediately before recording; multiply by 2 for BPM.
4. **Lighting condition** — one session per condition when possible:
   - `normal` — typical indoor light
   - `dim` — overhead lights off, screen-only
   - `bright_torch` — phone torch pointed at face (stress test)
5. **Capture** — sit still, forehead visible, 60 s:
   ```bash
   python scripts/record_study.py
   ```
6. Repeat steps 4–5 for additional lighting conditions.

## Recording command

```bash
python scripts/record_study.py \
  --subject-id S01 \
  --fitzpatrick IV \
  --reference-bpm 72 \
  --reference-source oximeter \
  --lighting normal \
  --duration 60
```

Output: `data/sessions/{subject_id}_{timestamp}.csv` and matching `.json` metadata.

## Analysis

```bash
python scripts/analyze_study.py
```

Produces:

- `data/reports/summary.csv` — per-session errors
- `data/reports/accuracy_by_skin_tone.png` — boxplot by Fitzpatrick group

## Minimum sample (week 2 goal)

- ≥ 5 subjects
- ≥ 3 distinct Fitzpatrick groups
- At least one dim or torch condition per subject when possible

## Ethics & privacy

- Obtain verbal consent before recording.
- Do not commit raw session CSVs to public repos if they could identify individuals.
- Publish aggregate statistics only.

## What to report in README

| Fitzpatrick | n | MAE (BPM) | RMSE (BPM) | Notes |
|-------------|---|-----------|------------|-------|
| (fill after study) | | | | |

Do not fabricate numbers. Placeholder table until real sessions exist.
