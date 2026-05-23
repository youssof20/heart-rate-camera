/** Rolling signal buffer and detrending */

export class SignalBuffer {
  constructor(bufferSeconds) {
    this.bufferSeconds = bufferSeconds;
    this.samples = [];
  }

  add(sample) {
    this.samples.push(sample);
    const cutoff = sample.timestamp - this.bufferSeconds;
    while (this.samples.length && this.samples[0].timestamp < cutoff) {
      this.samples.shift();
    }
  }

  get duration() {
    if (this.samples.length < 2) return 0;
    return this.samples[this.samples.length - 1].timestamp - this.samples[0].timestamp;
  }

  greenSeries() {
    const ts = [];
    const vals = [];
    for (const s of this.samples) {
      if (s.faceDetected) {
        ts.push(s.timestamp);
        vals.push(s.greenMean);
      }
    }
    return { timestamps: ts, values: vals };
  }

  estimateFps() {
    const { timestamps } = this.greenSeries();
    if (timestamps.length < 2) return 30;
    const duration = timestamps[timestamps.length - 1] - timestamps[0];
    return duration > 0 ? (timestamps.length - 1) / duration : 30;
  }
}

export function detrend(signal, fps, windowSeconds = 1.5) {
  if (signal.length < 3) return [...signal];
  let window = Math.max(3, Math.round(fps * windowSeconds));
  if (window % 2 === 0) window++;
  if (window >= signal.length) {
    window = signal.length % 2 === 0 ? signal.length - 1 : signal.length;
    if (window < 3) {
      const mean = signal.reduce((a, b) => a + b, 0) / signal.length;
      return signal.map((v) => v - mean);
    }
  }

  const half = Math.floor(window / 2);
  const out = new Array(signal.length);
  for (let i = 0; i < signal.length; i++) {
    let sum = 0;
    let count = 0;
    for (let j = Math.max(0, i - half); j <= Math.min(signal.length - 1, i + half); j++) {
      sum += signal[j];
      count++;
    }
    out[i] = signal[i] - sum / count;
  }
  return out;
}
