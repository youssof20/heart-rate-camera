/** Bandpass via FFT masking (matches Python band for demo) */

function nextPow2(n) {
  let p = 1;
  while (p < n) p <<= 1;
  return p;
}

function fft(real, imag) {
  const n = real.length;
  if (n <= 1) return;

  const evenR = new Float64Array(n / 2);
  const evenI = new Float64Array(n / 2);
  const oddR = new Float64Array(n / 2);
  const oddI = new Float64Array(n / 2);

  for (let i = 0; i < n / 2; i++) {
    evenR[i] = real[2 * i];
    evenI[i] = imag[2 * i];
    oddR[i] = real[2 * i + 1];
    oddI[i] = imag[2 * i + 1];
  }

  fft(evenR, evenI);
  fft(oddR, oddI);

  for (let k = 0; k < n / 2; k++) {
    const angle = (-2 * Math.PI * k) / n;
    const wr = Math.cos(angle);
    const wi = Math.sin(angle);
    const tr = wr * oddR[k] - wi * oddI[k];
    const ti = wr * oddI[k] + wi * oddR[k];
    real[k] = evenR[k] + tr;
    imag[k] = evenI[k] + ti;
    real[k + n / 2] = evenR[k] - tr;
    imag[k + n / 2] = evenI[k] - ti;
  }
}

function ifft(real, imag) {
  for (let i = 0; i < imag.length; i++) imag[i] = -imag[i];
  fft(real, imag);
  const n = real.length;
  for (let i = 0; i < n; i++) {
    real[i] /= n;
    imag[i] = -imag[i] / n;
  }
}

export function bandpass(signal, fps, lowHz, highHz) {
  const n = signal.length;
  if (n < 8) return [...signal];

  const size = nextPow2(n);
  const real = new Float64Array(size);
  const imag = new Float64Array(size);
  for (let i = 0; i < n; i++) real[i] = signal[i];

  fft(real, imag);

  const nyquist = fps / 2;
  const high = Math.min(highHz, nyquist * 0.95);

  for (let k = 0; k < size; k++) {
    let freq = k;
    if (k > size / 2) freq = size - k;
    const hz = (freq * fps) / size;
    if (hz < lowHz || hz > high) {
      real[k] = 0;
      imag[k] = 0;
    }
  }

  ifft(real, imag);
  return Array.from(real.slice(0, n));
}
