# Study protocol

Compare webcam BPM to a pulse oximeter or manual count.

## You need

- Webcam
- Pulse oximeter (optional but better)
- Same seat and distance (~50 cm) for each person

## Steps

1. Anonymous ID only (e.g. `S01`).
2. Fitzpatrick skin type (I-VI).
3. Reference BPM from oximeter or 30 s manual count.
4. Lighting: `normal`, `dim`, or `bright_torch`.
5. Sit still, 60 s:

```bash
python scripts/record_study.py \
  --subject-id S01 \
  --fitzpatrick IV \
  --reference-bpm 72 \
  --reference-source oximeter \
  --lighting normal
```

6. Analyze:

```bash
python scripts/analyze_study.py
```

Output in `data/reports/`.

## Privacy

- Ask before recording.
- Do not commit files that name people.
- Share summary stats only.
