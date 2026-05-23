import { loadConfig } from "./config.js";
import { landmarksToForeheadPolygon, drawPolygon, greenMeanFromPolygon } from "./roi.js";
import { SignalBuffer } from "./signal.js";
import { estimateBpm, smoothBpm } from "./hr.js";

const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const bpmEl = document.getElementById("bpm");
const statusEl = document.getElementById("status");

let config = null;
let landmarker = null;
let buffer = null;
let smoothedPolygon = null;
let bpmDisplay = null;
let animationId = null;
let stream = null;
const WAVEFORM_H = 100;

async function initLandmarker() {
  const vision = await import(
    "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/+esm"
  );
  const { FaceLandmarker, FilesetResolver } = vision;

  const fileset = await FilesetResolver.forVisionTasks(
    "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm"
  );

  landmarker = await FaceLandmarker.createFromOptions(fileset, {
    baseOptions: {
      modelAssetPath:
        "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
      delegate: "GPU",
    },
    runningMode: "VIDEO",
    numFaces: 1,
    minFaceDetectionConfidence: config.min_face_confidence,
    minFacePresenceConfidence: config.min_face_confidence,
    minTrackingConfidence: config.min_face_confidence,
  });
}

function drawWaveform(filtered, w, h, y0) {
  if (!filtered || filtered.length < 2) return;

  const n = filtered.length;
  let mean = 0;
  for (const v of filtered) mean += v;
  mean /= n;

  let variance = 0;
  for (const v of filtered) variance += (v - mean) ** 2;
  const std = Math.sqrt(variance / n) + 1e-9;

  ctx.fillStyle = "rgba(20, 20, 28, 0.75)";
  ctx.fillRect(0, y0, w, h);

  ctx.strokeStyle = "#00dcff";
  ctx.lineWidth = 2;
  ctx.beginPath();

  const mid = y0 + h / 2;
  const scale = h * 0.35;

  for (let i = 0; i < n; i++) {
    const x = (i / (n - 1)) * (w - 1);
    const z = Math.max(-3, Math.min(3, (filtered[i] - mean) / std));
    const y = mid - z * scale;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();
}

function processFrame(now) {
  if (!landmarker || video.readyState < 2) return;

  const w = video.videoWidth;
  const h = video.videoHeight;
  if (w === 0 || h === 0) return;

  canvas.width = w;
  canvas.height = h + WAVEFORM_H;

  ctx.save();
  ctx.scale(-1, 1);
  ctx.drawImage(video, -w, 0, w, h);
  ctx.restore();

  const timestamp = performance.now();
  const result = landmarker.detectForVideo(video, timestamp);

  let faceDetected = false;
  let greenMean = 0;

  if (result.faceLandmarks && result.faceLandmarks.length > 0) {
    const lm = result.faceLandmarks[0];
    const { polygon, smoothed } = landmarksToForeheadPolygon(
      lm,
      w,
      h,
      config.forehead_landmark_indices,
      smoothedPolygon
    );
    smoothedPolygon = smoothed;

    if (polygon) {
      drawPolygon(ctx, polygon);
      const imageData = ctx.getImageData(0, 0, w, h);
      const gm = greenMeanFromPolygon(imageData, w, h, polygon);
      if (gm != null) {
        faceDetected = true;
        greenMean = gm;
      }
    }
  }

  buffer.add({
    timestamp: now / 1000,
    greenMean,
    faceDetected,
  });

  let status = "Settling...";
  let bpm = null;

  if (!faceDetected) {
    status = "Face not detected";
  } else if (buffer.duration < config.warmup_seconds) {
    status = "Settling...";
  } else {
    const { values } = buffer.greenSeries();
    const fps = buffer.estimateFps();
    if (values.length >= fps * 4) {
      const hr = estimateBpm(values, fps, config);
      if (hr.bpm != null) {
        bpmDisplay = smoothBpm(bpmDisplay, hr.bpm, config.bpm_smooth_alpha);
        bpm = bpmDisplay;
        status = "Measuring";
      } else {
        status = "Low signal";
      }
      drawWaveform(hr.filtered, w, WAVEFORM_H, h);
    }
  }

  bpmEl.textContent = bpm != null ? `${Math.round(bpm)} BPM` : "-- BPM";
  bpmEl.style.color = bpm != null ? "#00ff88" : "#888";
  statusEl.textContent = status;
}

function loop() {
  processFrame(performance.now());
  animationId = requestAnimationFrame(loop);
}

async function start() {
  startBtn.disabled = true;
  config = await loadConfig();
  buffer = new SignalBuffer(config.buffer_seconds);

  stream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
    audio: false,
  });

  video.srcObject = stream;
  await video.play();

  await initLandmarker();
  loop();

  stopBtn.disabled = false;
  statusEl.textContent = "Settling...";
}

function stop() {
  if (animationId) cancelAnimationFrame(animationId);
  if (stream) {
    stream.getTracks().forEach((t) => t.stop());
    stream = null;
  }
  video.srcObject = null;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  bpmEl.textContent = "-- BPM";
  statusEl.textContent = "Stopped";
  startBtn.disabled = false;
  stopBtn.disabled = true;
  bpmDisplay = null;
  smoothedPolygon = null;
}

startBtn.addEventListener("click", () => start().catch((e) => {
  console.error(e);
  statusEl.textContent = "Camera error. Use HTTPS or localhost.";
  startBtn.disabled = false;
}));
stopBtn.addEventListener("click", stop);
