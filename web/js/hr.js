/** Heart rate estimation from green channel series */

import { detrend } from "./signal.js";
import { bandpass } from "./filter.js";

export function estimateBpm(greenValues, fps, config) {
  const lowHz = config.bandpass_low_hz;
  const highHz = config.bandpass_high_hz;
  const snrThreshold = config.snr_threshold;
  const trendWindow = config.trend_window_seconds;

  if (greenValues.length < fps * 4) {
    return { bpm: null, confidence: 0, filtered: [] };
  }

  const detrended = detrend(greenValues, fps, trendWindow);
  const filtered = bandpass(detrended, fps, lowHz, highHz);

  const n = filtered.length;
  const real = new Float64Array(n);
  const imag = new Float64Array(n);
  for (let i = 0; i < n; i++) real[i] = filtered[i];

  // Inline FFT for spectrum
  const size = 1;
  let p2 = 1;
  while (p2 < n) p2 <<= 1;
  const rr = new Float64Array(p2);
  const ii = new Float64Array(p2);
  for (let i = 0; i < n; i++) rr[i] = filtered[i];

  // Simple DFT for band only (more stable for variable n)
  let peakHz = 0;
  let peakMag = 0;
  const bandMags = [];

  for (let k = 0; k < p2 / 2; k++) {
    const hz = (k * fps) / p2;
    if (hz < lowHz || hz > highHz) continue;

    let re = 0;
    let im = 0;
    for (let t = 0; t < n; t++) {
      const angle = (-2 * Math.PI * k * t) / p2;
      re += filtered[t] * Math.cos(angle);
      im += filtered[t] * Math.sin(angle);
    }
    const mag = Math.sqrt(re * re + im * im);
    bandMags.push(mag);
    if (mag > peakMag) {
      peakMag = mag;
      peakHz = hz;
    }
  }

  if (bandMags.length === 0) {
    return { bpm: null, confidence: 0, filtered };
  }

  const sorted = [...bandMags].sort((a, b) => a - b);
  const median = sorted[Math.floor(sorted.length / 2)] + 1e-9;
  const snr = peakMag / median;
  const confidence = Math.min(1, snr / (snrThreshold * 2));

  if (snr < snrThreshold) {
    return { bpm: null, confidence, filtered };
  }

  return { bpm: peakHz * 60, confidence, filtered };
}

export function smoothBpm(current, raw, alpha) {
  if (raw == null) return current;
  if (current == null) return raw;
  return alpha * raw + (1 - alpha) * current;
}
