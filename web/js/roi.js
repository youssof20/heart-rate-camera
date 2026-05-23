/** Forehead ROI from MediaPipe face landmarks */

export function landmarksToForeheadPolygon(landmarks, width, height, indices, smoothedRef) {
  const points = [];
  for (const idx of indices) {
    if (idx >= landmarks.length) continue;
    const lm = landmarks[idx];
    points.push({ x: lm.x * width, y: lm.y * height });
  }
  if (points.length < 3) return { polygon: null, smoothed: smoothedRef };

  const hull = convexHull(points);
  let smoothed = smoothedRef;
  const alpha = 0.3;

  if (!smoothed || smoothed.length !== hull.length) {
    smoothed = hull.map((p) => ({ ...p }));
  } else {
    smoothed = hull.map((p, i) => ({
      x: alpha * p.x + (1 - alpha) * smoothed[i].x,
      y: alpha * p.y + (1 - alpha) * smoothed[i].y,
    }));
  }

  return { polygon: smoothed, smoothed };
}

function convexHull(points) {
  const sorted = [...points].sort((a, b) => (a.x === b.x ? a.y - b.y : a.x - b.x));
  const cross = (o, a, b) => (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);

  const lower = [];
  for (const p of sorted) {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) {
      lower.pop();
    }
    lower.push(p);
  }

  const upper = [];
  for (let i = sorted.length - 1; i >= 0; i--) {
    const p = sorted[i];
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) {
      upper.pop();
    }
    upper.push(p);
  }

  upper.pop();
  lower.pop();
  return lower.concat(upper);
}

export function drawPolygon(ctx, polygon, color = "rgba(0, 255, 136, 0.9)") {
  if (!polygon || polygon.length < 3) return;
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(polygon[0].x, polygon[0].y);
  for (let i = 1; i < polygon.length; i++) {
    ctx.lineTo(polygon[i].x, polygon[i].y);
  }
  ctx.closePath();
  ctx.stroke();
}

export function greenMeanFromPolygon(imageData, width, height, polygon) {
  if (!polygon || polygon.length < 3) return null;

  const xs = polygon.map((p) => p.x);
  const ys = polygon.map((p) => p.y);
  const minX = Math.max(0, Math.floor(Math.min(...xs)));
  const maxX = Math.min(width - 1, Math.ceil(Math.max(...xs)));
  const minY = Math.max(0, Math.floor(Math.min(...ys)));
  const maxY = Math.min(height - 1, Math.ceil(Math.max(...ys)));

  let sum = 0;
  let count = 0;
  const data = imageData.data;

  for (let y = minY; y <= maxY; y++) {
    for (let x = minX; x <= maxX; x++) {
      if (!pointInPolygon(x, y, polygon)) continue;
      const i = (y * width + x) * 4;
      sum += data[i + 1]; // green channel
      count++;
    }
  }

  return count > 0 ? sum / count : null;
}

function pointInPolygon(x, y, poly) {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const xi = poly[i].x,
      yi = poly[i].y;
    const xj = poly[j].x,
      yj = poly[j].y;
    const intersect = yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
}
