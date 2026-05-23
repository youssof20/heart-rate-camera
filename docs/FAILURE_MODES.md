# Failure Modes — Stress Test Log

Document what breaks the demo and why. Update this file as you film the video.

## How to tag events (desktop)

While running `python scripts/live.py`, press:

| Key | Tag | Expected failure |
|-----|-----|------------------|
| `m` | motion | Head shake, sprint — motion artifacts dominate |
| `b` | breath_hold | HR may drift; signal morphology changes |
| `o` | occlusion | Hand over forehead — face/ROI lost |
| `d` | dark | Low SNR, missed peaks, unstable BPM |
| `t` | torch | Saturation, clipping, wrong dominant frequency |

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
- **Why:** CO₂ response changes perfusion; rPPG sees hemodynamics, not “heart stopped.”

### Partial face cover

- **What happened:**
- **BPM behavior:**
- **Why:** ROI no longer tracks forehead skin; green mean reflects clothing/hand.

### Lights off

- **What happened:**
- **BPM behavior:**
- **Why:** camera noise dominates; SNR below threshold.

### Torch / bright glare

- **What happened:**
- **BPM behavior:**
- **Why:** auto-exposure and saturation destroy subtle color fluctuations.

### Skin tone bias (study)

- **Fitzpatrick groups tested:**
- **MAE trend:**
- **Why:** green-channel rPPG assumes certain optical absorption; melanin and lighting interact. Document quantitatively in `analyze_study.py` output.

---

## Clinical context (for video outro)

Research hospitals use **remote photoplethysmography (rPPG)** in ICU and post-op monitoring to detect pulse without contact sensors. The technology exists; barriers include **lighting**, **motion**, and **skin tone bias** in training data and simple algorithms.

This demo uses the simplest method (forehead green-channel mean). It is instructive, not clinical-grade.
