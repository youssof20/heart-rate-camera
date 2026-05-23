# Failure Modes: Stress Test Log

What breaks the demo and why. Update as you film.

## How to tag events (desktop)

While running `python scripts/live.py`, press:

| Key | Tag | Expected failure |
|-----|-----|------------------|
| `m` | motion | Head shake or sprint; motion artifacts swamp the pulse |
| `b` | breath_hold | HR may drift; waveform shape changes |
| `o` | occlusion | Hand over forehead; face or ROI lost |
| `d` | dark | Low SNR, missed peaks, unstable BPM |
| `t` | torch | Saturation, clipping, wrong peak frequency |

Optional log file: `python scripts/live.py --events-log data/events.csv`

---

## Template (fill in during filming)

### Motion / sprint

- **What happened:**
- **BPM behavior:**
- **Why (physics):** bulk tissue motion adds low-frequency noise unrelated to blood volume pulse.

### Breath-hold

- **What happened:**
- **BPM behavior:**
- **Why:** CO2 response changes perfusion; rPPG sees hemodynamics, not a stopped heart.

### Partial face cover

- **What happened:**
- **BPM behavior:**
- **Why:** ROI no longer tracks forehead skin; green mean picks up clothing or hand.

### Lights off

- **What happened:**
- **BPM behavior:**
- **Why:** camera noise dominates; SNR below threshold.

### Torch / bright glare

- **What happened:**
- **BPM behavior:**
- **Why:** auto-exposure and saturation wipe out small color swings.

### Skin tone bias (study)

- **Fitzpatrick groups tested:**
- **MAE trend:**
- **Why:** green-channel rPPG assumes certain optical absorption; melanin and lighting interact. Put numbers in `analyze_study.py` output.

---

## Clinical context (for video outro)

Research hospitals use remote photoplethysmography (rPPG) in ICU and post-op monitoring to detect pulse without contact sensors. It works in papers; in practice you fight lighting, motion, and skin tone bias in training data and simple algorithms.

This repo uses forehead green-channel mean. Demo only, not clinical grade.
