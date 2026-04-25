const state = window.__INITIAL_STATE__ || {};

const elements = {
  clockValue: document.getElementById("clockValue"),
  windowValue: document.getElementById("windowValue"),
  modePill: document.getElementById("modePill"),
  dispatchPill: document.getElementById("dispatchPill"),
  sectorPill: document.getElementById("sectorPill"),
  heroSignalState: document.getElementById("heroSignalState"),
  heroVerification: document.getElementById("heroVerification"),
  heroLane: document.getElementById("heroLane"),
  metricBand: document.getElementById("metricBand"),
  statusBanner: document.getElementById("statusBanner"),
  statusTitle: document.getElementById("statusTitle"),
  statusCaption: document.getElementById("statusCaption"),
  statusWindow: document.getElementById("statusWindow"),
  signalStack: document.getElementById("signalStack"),
  sensorGrid: document.getElementById("sensorGrid"),
  routeStrip: document.getElementById("routeStrip"),
  mapHudJunction: document.getElementById("mapHudJunction"),
  mapHudRoute: document.getElementById("mapHudRoute"),
  mapHudMode: document.getElementById("mapHudMode"),
  acousticGauge: document.getElementById("acousticGauge"),
  acousticValue: document.getElementById("acousticValue"),
  visionGauge: document.getElementById("visionGauge"),
  visionValue: document.getElementById("visionValue"),
  historyBars: document.getElementById("historyBars"),
  feedShell: document.getElementById("feedShell"),
  feedImage: document.getElementById("feedImage"),
  feedEmpty: document.getElementById("feedEmpty"),
  targetCard: document.getElementById("targetCard"),
  audioBlock: document.getElementById("audioBlock"),
  audioPlayer: document.getElementById("audioPlayer"),
  toggleButton: document.getElementById("toggleButton"),
  resetButton: document.getElementById("resetButton"),
  briefMode: document.getElementById("briefMode"),
  briefCopy: document.getElementById("briefCopy"),
  missionLog: document.getElementById("missionLog"),
  cameraToggle: document.getElementById("cameraToggle"),
  cameraStatus: document.getElementById("cameraStatus"),
  cameraVideo: document.getElementById("cameraVideo"),
  cameraOverlay: document.getElementById("cameraOverlay"),
  micToggle: document.getElementById("micToggle"),
  micStatus: document.getElementById("micStatus"),
};

let map;
let routeLine;
let routeGlow;
let markers = [];
let cameraStream = null;
let detectionModel = null;
let detectionLoopId = null;
let latestCameraDetection = null;
let latestVisionMetrics = null;
let detectionBusy = false;
let micStream = null;
let audioContext = null;
let audioAnalyser = null;
let audioDataArray = null;
let audioTimeDataArray = null;
let micLoopId = null;
let latestSirenDetection = null;
let sirenConfidence = 0;
let sirenPositiveFrames = 0;
let sirenNegativeFrames = 0;

// Auto-inject: wires real-time detections → backend signal preemption
let lastAutoInjectTime = 0;
const AUTO_INJECT_COOLDOWN_MS = 8000;
let autoInjectArmed = false;

function initMap(initial) {
  const center = initial.junctions?.[initial.junctionIndex]?.coords || [12.9177, 77.6238];
  map = L.map("map", { zoomControl: true, attributionControl: true }).setView(center, 13);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    subdomains: "abcd",
    maxZoom: 20,
  }).addTo(map);
  updateMap(initial);
}

function updateMap(payload) {
  const coords = payload.junctions.map((junction) => junction.coords);

  if (routeGlow) map.removeLayer(routeGlow);
  if (routeLine) map.removeLayer(routeLine);
  markers.forEach((marker) => map.removeLayer(marker));
  markers = [];

  routeGlow = L.polyline(coords, {
    color: "#5ee5ff",
    weight: 12,
    opacity: 0.13,
  }).addTo(map);

  routeLine = L.polyline(coords, {
    color: "#5ee5ff",
    weight: 4,
    opacity: 0.88,
    dashArray: "10 8",
  }).addTo(map);

  payload.junctions.forEach((junction, index) => {
    const active = index === payload.junctionIndex;
    const live = active && payload.isPreempted;
    const marker = L.circleMarker(junction.coords, {
      radius: active ? 11 : 7,
      color: live ? "#2ce39a" : active ? "#5ee5ff" : "#6a7c93",
      weight: 2,
      fillColor: live ? "#2ce39a" : active ? "#5ee5ff" : "#182233",
      fillOpacity: 0.95,
    }).bindPopup(`<strong>${junction.id}</strong><br>${junction.name}`);
    marker.addTo(map);
    markers.push(marker);

    if (live) {
      const halo = L.circleMarker(junction.coords, {
        radius: 20,
        color: "#2ce39a",
        weight: 1,
        fillColor: "#2ce39a",
        fillOpacity: 0.12,
      }).addTo(map);
      markers.push(halo);
    }
  });

  map.setView(payload.junctions[payload.junctionIndex].coords, map.getZoom(), { animate: true });
}

function percent(value) {
  return `${Math.round(value * 100)}%`;
}

function metricTile(label, value, caption) {
  return `
    <div class="metric-tile">
      <div class="panel-label">${label}</div>
      <div class="metric-value">${value}</div>
      <div class="metric-trend">${caption}</div>
    </div>
  `;
}

function signalLamp(name, signalState) {
  const activeClass = signalState === name ? `active-${name.toLowerCase()}` : "";
  return `
    <div class="signal-lamp ${activeClass}">
      <div class="signal-core"></div>
      <div class="signal-name">${name}</div>
    </div>
  `;
}

function sensorRow(name, detail, badge, badgeClass) {
  return `
    <div class="sensor-row">
      <div>
        <div class="sensor-name">${name}</div>
        <div class="sensor-detail">${detail}</div>
      </div>
      <div class="sensor-badge ${badgeClass}">${badge}</div>
    </div>
  `;
}

function routeStop(junction, active, live) {
  const suffix = live ? " open" : "";
  return `
    <div class="route-stop ${active ? "active" : ""}">
      <div class="route-id">${junction.id}${suffix}</div>
      <div class="route-name">${junction.name}</div>
    </div>
  `;
}

function setGauge(element, value, labelElement) {
  const degrees = Math.max(0, Math.min(360, value * 360));
  element.style.background = element.classList.contains("gauge-fill-green")
    ? `conic-gradient(#2ce39a ${degrees}deg, rgba(255,255,255,0.06) ${degrees}deg)`
    : `conic-gradient(#5ee5ff ${degrees}deg, rgba(255,255,255,0.06) ${degrees}deg)`;
  labelElement.textContent = percent(value);
}

function buildMissionLog(payload, verificationCount) {
  const entries = [
    {
      time: payload.clock.split(" ")[0],
      title: payload.isPreempted ? "Corridor override live" : "Corridor watch active",
    },
    {
      time: `T-${String(payload.countdown).padStart(2, "0")}s`,
      title: `${verificationCount}/3 sensor confirmations`,
    },
    {
      time: payload.activeSector,
      title: payload.junctions[payload.junctionIndex].name,
    },
  ];

  if (latestCameraDetection) {
    entries.unshift({
      time: "CAM",
      title: latestCameraDetection.heuristicLabel,
    });
  }

  return entries
    .slice(0, 4)
    .map((entry) => `
      <div class="log-row">
        <div class="log-time">${entry.time}</div>
        <div class="log-title">${entry.title}</div>
      </div>
    `)
    .join("");
}

function updateCameraStatus(text, mode = "") {
  elements.cameraStatus.textContent = text;
  elements.cameraStatus.className = `camera-status ${mode}`.trim();
}

function updateMicStatus(text, mode = "") {
  elements.micStatus.textContent = text;
  elements.micStatus.className = `camera-status ${mode}`.trim();
}

function drawDetections(predictions) {
  const canvas = elements.cameraOverlay;
  const video = elements.cameraVideo;
  const context = canvas.getContext("2d");

  const width = video.videoWidth;
  const height = video.videoHeight;
  if (!width || !height) return;

  canvas.width = width;
  canvas.height = height;
  context.clearRect(0, 0, width, height);
  context.lineWidth = 3;
  context.font = "600 18px Inter";

  predictions.forEach((prediction) => {
    const [x, y, boxWidth, boxHeight] = prediction.bbox;
    const isVehicle = ["car", "truck", "bus", "motorcycle"].includes(prediction.class);
    context.strokeStyle = isVehicle ? "#2ce39a" : "#5ee5ff";
    context.fillStyle = isVehicle ? "rgba(44, 227, 154, 0.16)" : "rgba(94, 229, 255, 0.16)";
    context.strokeRect(x, y, boxWidth, boxHeight);
    context.fillRect(x, y, boxWidth, boxHeight);

    const promoted =
      latestSirenDetection &&
      latestSirenDetection.active &&
      ["car", "truck", "bus"].includes(prediction.class);
    const label = `${promoted ? "ambulance candidate" : prediction.class} ${Math.round(prediction.score * 100)}%`;
    const labelWidth = context.measureText(label).width + 16;
    context.fillStyle = "rgba(5, 9, 17, 0.88)";
    context.fillRect(x, Math.max(0, y - 28), labelWidth, 24);
    context.fillStyle = "#edf5ff";
    context.fillText(label, x + 8, Math.max(18, y - 10));
  });
}

function getEmergencyHeuristic(predictions) {
  const vehicle = predictions
    .filter((prediction) => ["car", "truck", "bus", "motorcycle"].includes(prediction.class))
    .sort((a, b) => b.score - a.score)[0];

  if (!vehicle) {
    return null;
  }

  const confidence = vehicle.score;
  const sirenAssist = Boolean(latestSirenDetection && latestSirenDetection.active);
  const probableEmergency =
    sirenAssist ||
    vehicle.class === "truck" ||
    (vehicle.class === "car" && confidence > 0.72);
  const displayLabel = sirenAssist
    ? "ambulance candidate"
    : probableEmergency
      ? "emergency vehicle candidate"
      : vehicle.class;

  return {
    label: vehicle.class,
    displayLabel,
    confidence,
    heuristicLabel: probableEmergency
      ? sirenAssist
        ? "Ambulance candidate (vehicle + siren)"
        : `Potential emergency vehicle (${vehicle.class})`
      : `Vehicle detected (${vehicle.class})`,
    probableEmergency,
  };
}

function frequencyForBin(index, sampleRate, fftSize) {
  return (index * sampleRate) / fftSize;
}

function analyzeSirenFrame() {
  if (!audioAnalyser || !audioDataArray || !audioContext) {
    return;
  }

  audioAnalyser.getByteFrequencyData(audioDataArray);
  audioAnalyser.getFloatTimeDomainData(audioTimeDataArray);
  const sampleRate = audioContext.sampleRate;
  const fftSize = audioAnalyser.fftSize;
  let totalEnergy = 0;
  let sirenBandEnergy = 0;
  let upperBandEnergy = 0;
  let lowBandEnergy = 0;   // speech rejection: sub-600 Hz energy
  let peakValue = 0;
  let peakFrequency = 0;
  let rmsSum = 0;

  for (let index = 0; index < audioDataArray.length; index += 1) {
    const value = audioDataArray[index] / 255;
    const frequency = frequencyForBin(index, sampleRate, fftSize);
    totalEnergy += value;
    if (frequency < 600) {
      lowBandEnergy += value;  // speech fundamentals live here
    }
    if (frequency >= 600 && frequency <= 1800) {
      sirenBandEnergy += value;
    }
    if (frequency >= 1800 && frequency <= 3200) {
      upperBandEnergy += value;
    }
    if (value > peakValue) {
      peakValue = value;
      peakFrequency = frequency;
    }
  }

  for (let index = 0; index < audioTimeDataArray.length; index += 1) {
    const sample = audioTimeDataArray[index];
    rmsSum += sample * sample;
  }

  const bandRatio = totalEnergy ? sirenBandEnergy / totalEnergy : 0;
  const upperRatio = totalEnergy ? upperBandEnergy / totalEnergy : 0;
  const lowRatio = totalEnergy ? lowBandEnergy / totalEnergy : 0;
  const normalizedEnergy = audioDataArray.length ? totalEnergy / audioDataArray.length : 0;
  const rms = Math.sqrt(rmsSum / audioTimeDataArray.length);
  const peakInSirenRange = peakFrequency >= 600 && peakFrequency <= 2200;

  // Speech rejection: sirens concentrate energy in siren band with little low-freq content.
  // Speech has strong energy below 600 Hz (vocal fundamentals ~85-300 Hz).
  // spectralConcentration > 1.5 means siren band dominates over low band → likely siren.
  const spectralConcentration = lowBandEnergy > 0 ? sirenBandEnergy / lowBandEnergy : (sirenBandEnergy > 0 ? 10 : 0);
  const speechLikely = lowRatio > 0.20 && spectralConcentration < 1.2;

  const rawScore = Math.min(
    1,
    bandRatio * 2.2 + upperRatio * 1.1 + normalizedEnergy * 0.25 + peakValue * 0.2 + rms * 2.2,
  );

  analyzeSirenFrame._dbgCount = (analyzeSirenFrame._dbgCount || 0) + 1;
  if (analyzeSirenFrame._dbgCount % 10 === 0) {
    console.debug(`[Mic] rms=${rms.toFixed(4)} energy=${normalizedEnergy.toFixed(4)} bandRatio=${bandRatio.toFixed(3)} lowRatio=${lowRatio.toFixed(3)} specConc=${spectralConcentration.toFixed(2)} speech=${speechLikely} rawScore=${rawScore.toFixed(3)} peakFreq=${peakFrequency.toFixed(0)}Hz conf=${sirenConfidence.toFixed(3)} posFrames=${sirenPositiveFrames}`);
  }

  // Require: peak in siren range AND not speech-like spectrum AND minimum band concentration
  const strongSirenPulse =
    !speechLikely &&
    peakInSirenRange &&
    rms > 0.010 &&
    normalizedEnergy > 0.05 &&
    bandRatio > 0.18 &&
    spectralConcentration > 1.5 &&
    rawScore > 0.45;

  const likelySiren =
    !speechLikely &&
    peakInSirenRange &&
    rms > 0.006 &&
    normalizedEnergy > 0.03 &&
    bandRatio > 0.14 &&
    spectralConcentration > 1.2 &&
    rawScore > 0.32;

  if (strongSirenPulse) {
    sirenPositiveFrames += 2;
    sirenNegativeFrames = 0;
  } else if (likelySiren) {
    sirenPositiveFrames += 1;
    sirenNegativeFrames = 0;
  } else {
    sirenNegativeFrames += 1;
    // Fast decay — drop by 2 so system clears within ~1.5s of silence
    sirenPositiveFrames = Math.max(0, sirenPositiveFrames - 2);
  }

  const confirmedSiren = sirenPositiveFrames >= 3;
  sirenConfidence = confirmedSiren
    ? Math.min(1, sirenConfidence * 0.72 + rawScore * 0.55)
    : Math.max(0, sirenConfidence * 0.45 - 0.08);
  const isSiren = confirmedSiren && sirenConfidence > 0.42;

  latestSirenDetection = {
    active: isSiren,
    score: sirenConfidence,
    bandRatio,
    energy: normalizedEnergy,
    rms,
    peakFrequency,
    heuristicLabel: isSiren ? "Possible ambulance siren" : "Ambient roadway audio",
  };

  if (isSiren) {
    updateMicStatus(`Siren live — ${(sirenConfidence * 100).toFixed(0)}%`, "live");
    if (sirenConfidence > 0.55) {
      tryAutoInject("Ambulance");
    }
  } else {
    const pct = (sirenConfidence * 100).toFixed(0);
    updateMicStatus(
      sirenConfidence > 0.15
        ? `Building… ${pct}% confidence`
        : "Listening for siren",
      "warn",
    );
  }
}

function startMicLoop() {
  if (micLoopId) {
    return;
  }
  const tick = () => {
    try {
      analyzeSirenFrame();
    } catch (error) {
      updateMicStatus("Mic analyzer error", "warn");
      console.error(error);
    }
    micLoopId = window.setTimeout(tick, 160);
  };
  tick();
}

function stopMicLoop() {
  if (micLoopId) {
    clearTimeout(micLoopId);
    micLoopId = null;
  }
  latestSirenDetection = null;
  sirenConfidence = 0;
  sirenPositiveFrames = 0;
  sirenNegativeFrames = 0;
}

/**
 * Auto-inject: fires a backend signal preemption when real-time
 * mic or camera detection exceeds confidence threshold.
 * Uses a cooldown to avoid flooding the backend.
 */
async function tryAutoInject(vehicleType) {
  const now = Date.now();
  if (now - lastAutoInjectTime < AUTO_INJECT_COOLDOWN_MS) return;
  lastAutoInjectTime = now;
  autoInjectArmed = true;
  try {
    const response = await fetch("/api/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "inject", vehicleType }),
    });
    const payload = await response.json();
    render(payload);
  } catch (err) {
    console.error("Auto-inject failed:", err);
  } finally {
    autoInjectArmed = false;
  }
}

async function ensureDetectionModel() {
  if (detectionModel) {
    return detectionModel;
  }
  updateCameraStatus("Loading detector", "warn");
  detectionModel = await cocoSsd.load();
  return detectionModel;
}

async function runDetectionFrame() {
  if (!cameraStream || !detectionModel || detectionBusy) {
    return;
  }

  detectionBusy = true;
  try {
    const predictions = await detectionModel.detect(elements.cameraVideo, 10);
    drawDetections(predictions);
    latestCameraDetection = getEmergencyHeuristic(predictions);
    const topPrediction = [...predictions].sort((a, b) => b.score - a.score)[0] || null;
    latestVisionMetrics = topPrediction
      ? {
          score: topPrediction.score,
          label: topPrediction.class,
        }
      : {
          score: 0,
          label: "no target",
        };

    if (latestCameraDetection) {
      updateCameraStatus(
        latestCameraDetection.probableEmergency ? "Emergency candidate" : "Vehicle detected",
        latestCameraDetection.probableEmergency ? "live" : "warn",
      );
      // Auto-trigger backend preemption when camera locks an emergency vehicle
      if (latestCameraDetection.probableEmergency) {
        const isAmbulance = latestSirenDetection && latestSirenDetection.active;
        const isTruck = latestCameraDetection.label === "truck";
        const vehicleType = isAmbulance ? "Ambulance" : isTruck ? "Firetruck" : "Ambulance";
        tryAutoInject(vehicleType);
      }
    } else {
      updateCameraStatus("Scanning live feed", "warn");
    }
  } finally {
    detectionBusy = false;
  }
}

function startDetectionLoop() {
  if (detectionLoopId) {
    return;
  }
  const tick = async () => {
    try {
      await runDetectionFrame();
    } catch (error) {
      updateCameraStatus("Detector error", "warn");
      console.error(error);
    }
    detectionLoopId = window.setTimeout(tick, 180);
  };
  tick();
}

function stopDetectionLoop() {
  if (detectionLoopId) {
    clearTimeout(detectionLoopId);
    detectionLoopId = null;
  }
  latestCameraDetection = null;
  latestVisionMetrics = null;
  const context = elements.cameraOverlay.getContext("2d");
  context.clearRect(0, 0, elements.cameraOverlay.width, elements.cameraOverlay.height);
}

async function startCamera() {
  if (cameraStream) {
    return;
  }

  await ensureDetectionModel();
  updateCameraStatus("Awaiting permission", "warn");
  cameraStream = await navigator.mediaDevices.getUserMedia({
    video: {
      facingMode: "user",
      width: { ideal: 1280 },
      height: { ideal: 720 },
    },
    audio: false,
  });

  elements.cameraVideo.srcObject = cameraStream;
  await elements.cameraVideo.play();
  elements.feedShell.classList.add("has-camera");
  elements.feedEmpty.style.display = "none";
  elements.feedImage.style.display = "none";
  elements.cameraToggle.textContent = "Stop laptop camera";
  updateCameraStatus("Camera live", "live");
  startDetectionLoop();
}

function stopCamera() {
  if (!cameraStream) {
    return;
  }
  cameraStream.getTracks().forEach((track) => track.stop());
  cameraStream = null;
  elements.cameraVideo.srcObject = null;
  elements.feedShell.classList.remove("has-camera");
  elements.cameraToggle.textContent = "Start laptop camera";
  elements.feedEmpty.style.display = "grid";
  updateCameraStatus("Camera offline");
  stopDetectionLoop();
}

async function startMic() {
  if (micStream) {
    return;
  }

  updateMicStatus("Awaiting permission", "warn");
  micStream = await navigator.mediaDevices.getUserMedia({
    audio: {
      echoCancellation: false,
      noiseSuppression: false,
      autoGainControl: false,
      channelCount: 1,
    },
    video: false,
  });

  audioContext = new (window.AudioContext || window.webkitAudioContext)();
  await audioContext.resume();
  const source = audioContext.createMediaStreamSource(micStream);
  audioAnalyser = audioContext.createAnalyser();
  audioAnalyser.fftSize = 2048;
  audioAnalyser.smoothingTimeConstant = 0.7;
  audioDataArray = new Uint8Array(audioAnalyser.frequencyBinCount);
  audioTimeDataArray = new Float32Array(audioAnalyser.fftSize);
  source.connect(audioAnalyser);

  elements.micToggle.textContent = "Stop microphone";
  updateMicStatus("Mic live", "live");
  startMicLoop();
}

function stopMic() {
  if (!micStream) {
    return;
  }
  micStream.getTracks().forEach((track) => track.stop());
  micStream = null;
  if (audioContext) {
    audioContext.close().catch(() => {});
  }
  audioContext = null;
  audioAnalyser = null;
  audioDataArray = null;
  audioTimeDataArray = null;
  elements.micToggle.textContent = "Start microphone";
  updateMicStatus("Mic offline");
  stopMicLoop();
}

function render(payload) {
  const verificationCount = [payload.rfid.authenticated, payload.acoustic.siren_detected, payload.vision.detected]
    .filter(Boolean).length;
  const sirenActive = Boolean(latestSirenDetection && latestSirenDetection.active);
  const cameraActive = Boolean(cameraStream);
  const visualEmergency = Boolean(latestCameraDetection && latestCameraDetection.probableEmergency);
  const effectivePreempted = payload.isPreempted || sirenActive || visualEmergency;
  const effectiveSignalState = effectivePreempted ? "GREEN" : payload.signalState;
  const laneLabels = [
    "Silk Board outbound",
    "Madiwala relief lane",
    "Adugodi fast corridor",
    "Shantinagar emergency spine",
    "Richmond final approach",
  ];
  const laneLabel = laneLabels[payload.junctionIndex] || "Bengaluru priority lane";
  const corridorName = "Bengaluru South-Central";

  elements.clockValue.textContent = payload.clock;
  elements.windowValue.textContent = effectivePreempted ? "Live" : `${payload.countdown}s`;

  // Show AUTO indicator when real-time detection is armed and mic/cam are active
  const autoDetecting = Boolean(micStream || cameraStream);
  elements.modePill.textContent = effectivePreempted
    ? "Preemption live"
    : autoDetecting
      ? "AUTO detection armed"
      : "Monitoring all lanes";
  elements.modePill.style.color = autoDetecting && !effectivePreempted ? "#2ce39a" : "";

  elements.dispatchPill.textContent = `Dispatch: ${payload.emergencyType || "none"}`;
  if (sirenActive && !payload.emergencyType) {
    elements.dispatchPill.textContent = "Dispatch: siren priority";
  }
  elements.sectorPill.textContent = `Corridor: ${corridorName}`;
  elements.heroSignalState.textContent = effectiveSignalState;
  elements.heroVerification.textContent = `${verificationCount + (sirenActive ? 1 : 0) + (visualEmergency ? 1 : 0)} of ${3 + (sirenActive ? 1 : 0) + (visualEmergency ? 1 : 0)} live`;
  elements.heroLane.textContent = laneLabel;
  elements.toggleButton.textContent = payload.simRunning ? "Halt system" : "Initiate system";
  elements.mapHudJunction.textContent = payload.activeSector;
  elements.mapHudRoute.textContent = `${payload.junctions.length} nodes`;
  elements.mapHudMode.textContent = effectivePreempted ? "Priority lock" : "Watch mode";
  elements.briefMode.textContent = effectivePreempted ? "Bengaluru corridor open" : "Standby corridor watch";
  elements.briefCopy.textContent = effectivePreempted
    ? `Holding a clear lane for ${(payload.emergencyType || "audio-priority")} across ${payload.junctions[payload.junctionIndex].name}.`
    : "Waiting for authenticated dispatch, siren confidence, and visual confirmation across Bengaluru roads.";
  if (visualEmergency && !sirenActive && !payload.isPreempted) {
    elements.briefCopy.textContent = `Camera locked onto ${latestCameraDetection.displayLabel} near ${payload.junctions[payload.junctionIndex].name}. Signal priority raised immediately.`;
  }
  elements.missionLog.innerHTML = buildMissionLog(payload, verificationCount);

  elements.metricBand.innerHTML = [
    metricTile("ETA reduction", `+${payload.metrics.eta_reduction.toFixed(1)}%`, "Priority corridor gain"),
    metricTile("Detection accuracy", `${payload.metrics.detection_accuracy.toFixed(2)}%`, "Cross-sensor agreement"),
    metricTile("Node latency", `${payload.metrics.latency_ms.toFixed(0)} ms`, "Signal response window"),
    metricTile(
      effectivePreempted ? "Clearance" : "Countdown",
      effectivePreempted ? "Live" : `${payload.countdown}s`,
      `Active sector ${payload.activeSector}`,
    ),
  ].join("");

  elements.statusBanner.className = `status-banner ${effectivePreempted ? "live" : payload.signalState === "YELLOW" ? "warn" : ""}`;
  elements.statusTitle.textContent = effectivePreempted ? "Preemption lock engaged" : "Standard flow routine";
  elements.statusCaption.textContent = effectivePreempted
    ? "Emergency vehicle path is being held open across the active corridor."
    : "Monitoring RFID, acoustic, and visual confirmation before signal override.";
  if (sirenActive && !payload.isPreempted) {
    elements.statusCaption.textContent = "Microphone picked up a siren pattern and raised immediate junction priority.";
  }
  if (visualEmergency && !sirenActive && !payload.isPreempted) {
    elements.statusCaption.textContent = `Vision model locked onto ${latestCameraDetection.displayLabel} and raised immediate junction priority.`;
  }
  elements.statusWindow.textContent = effectivePreempted ? "Live" : `${payload.countdown}s`;

  elements.signalStack.innerHTML = ["RED", "YELLOW", "GREEN"].map((name) => signalLamp(name, effectiveSignalState)).join("");

  const visionDetail = latestCameraDetection
    ? `${latestCameraDetection.heuristicLabel} | ${(latestCameraDetection.confidence * 100).toFixed(1)}%`
    : cameraActive
      ? `Live camera active | ${latestVisionMetrics ? latestVisionMetrics.label : "scanning scene"}`
      : "Camera offline | visual analysis unavailable";

  elements.sensorGrid.innerHTML = [
    sensorRow(
      "RFID handshake",
      payload.rfid.vehicle_id,
      payload.rfid.authenticated ? "Verified" : "Awaiting auth",
      payload.rfid.authenticated ? "live" : "idle",
    ),
    sensorRow(
      "Acoustic model",
      sirenActive
        ? `${latestSirenDetection.heuristicLabel} | on-device mic`
        : `${payload.acoustic.label} | ${payload.acoustic.decibel.toFixed(0)} dB`,
      sirenActive
        ? `${(latestSirenDetection.score * 100).toFixed(1)}% siren score`
        : `${(payload.acoustic.confidence * 100).toFixed(1)}% confidence`,
      sirenActive || payload.acoustic.siren_detected ? "live" : "warn",
    ),
    sensorRow(
      "Vision model",
      visionDetail,
      latestCameraDetection
        ? latestCameraDetection.probableEmergency ? latestCameraDetection.displayLabel : "Live object"
        : cameraActive ? "Scanning live video" : "Camera required",
      latestCameraDetection
        ? latestCameraDetection.probableEmergency ? "live" : "warn"
        : cameraActive ? "warn" : "idle",
    ),
  ].join("");

  elements.routeStrip.innerHTML = payload.junctions
    .map((junction, index) => routeStop(junction, index === payload.junctionIndex, index === payload.junctionIndex && payload.isPreempted))
    .join("");

  setGauge(elements.acousticGauge, payload.acoustic.confidence, elements.acousticValue);
  if (sirenActive) {
    setGauge(elements.acousticGauge, Math.max(payload.acoustic.confidence, latestSirenDetection.score), elements.acousticValue);
  }
  const liveVisionScore = latestCameraDetection
    ? latestCameraDetection.confidence
    : cameraActive
      ? (latestVisionMetrics ? latestVisionMetrics.score : 0)
      : 0;
  setGauge(
    elements.visionGauge,
    liveVisionScore,
    elements.visionValue,
  );

  elements.historyBars.innerHTML = payload.history
    .map((value) => `<div class="history-bar ${value ? "active" : ""}" style="height:${value ? 100 : 26}%"></div>`)
    .join("");

  if (cameraActive) {
    elements.targetCard.classList.remove("hidden");
    elements.targetCard.innerHTML = latestCameraDetection
      ? `
        <div class="panel-label">Live camera target</div>
        <div class="target-name">${latestCameraDetection.heuristicLabel}</div>
        <div class="target-meta">Browser-side detection confidence ${(latestCameraDetection.confidence * 100).toFixed(1)}% | base class ${latestCameraDetection.label}</div>
      `
      : `
        <div class="panel-label">Live camera target</div>
        <div class="target-name">Scanning scene</div>
        <div class="target-meta">Point the laptop camera at a vehicle for live detection.</div>
      `;
  } else {
    elements.feedShell.classList.remove("has-image");
    elements.feedImage.removeAttribute("src");
    elements.feedImage.style.display = "none";
    elements.feedEmpty.style.display = "grid";
    elements.targetCard.classList.remove("hidden");
    if (sirenActive) {
      elements.targetCard.innerHTML = `
        <div class="panel-label">Audio trigger</div>
        <div class="target-name">Possible ambulance siren</div>
        <div class="target-meta">Microphone-only mode is active. Start the laptop camera for visual confirmation.</div>
      `;
    } else if (micStream) {
      elements.targetCard.innerHTML = `
        <div class="panel-label">Audio trigger</div>
        <div class="target-name">Listening live</div>
        <div class="target-meta">Microphone is active. Start the laptop camera if you also want visual detection.</div>
      `;
    } else {
      elements.targetCard.classList.add("hidden");
      elements.targetCard.innerHTML = "";
    }
  }

  if (payload.acoustic.audioUrl && !micStream) {
    elements.audioBlock.classList.remove("hidden");
    if (!elements.audioPlayer.src || !elements.audioPlayer.src.endsWith(payload.acoustic.audioUrl)) {
      elements.audioPlayer.src = payload.acoustic.audioUrl;
    }
  } else {
    elements.audioBlock.classList.add("hidden");
    if (elements.audioPlayer.src) {
      elements.audioPlayer.pause();
      elements.audioPlayer.removeAttribute("src");
      elements.audioPlayer.load();
    }
  }

  updateMap(payload);
}

async function postAction(action, extra = {}) {
  const response = await fetch("/api/action", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, ...extra }),
  });
  const payload = await response.json();
  render(payload);
}

async function refreshState() {
  const response = await fetch("/api/state", { cache: "no-store" });
  const payload = await response.json();
  render(payload);
}

elements.toggleButton.addEventListener("click", () => postAction("toggle"));
elements.resetButton.addEventListener("click", () => postAction("reset"));
elements.cameraToggle.addEventListener("click", async () => {
  try {
    if (cameraStream) {
      stopCamera();
    } else {
      await startCamera();
    }
  } catch (error) {
    if (error && (error.name === "NotAllowedError" || error.name === "SecurityError")) {
      updateCameraStatus("Permission denied", "warn");
    } else if (error && error.name === "NotFoundError") {
      updateCameraStatus("No camera found", "warn");
    } else {
      updateCameraStatus("Camera blocked", "warn");
    }
    console.error(error);
  }
});
elements.micToggle.addEventListener("click", async () => {
  try {
    if (micStream) {
      stopMic();
    } else {
      await startMic();
    }
  } catch (error) {
    if (error && (error.name === "NotAllowedError" || error.name === "SecurityError")) {
      updateMicStatus("Permission denied", "warn");
    } else if (error && error.name === "NotFoundError") {
      updateMicStatus("No mic found", "warn");
    } else {
      updateMicStatus("Mic blocked", "warn");
    }
    console.error(error);
  }
});

document.querySelectorAll("[data-action='inject']").forEach((button) => {
  button.addEventListener("click", () => postAction("inject", { vehicleType: button.dataset.vehicle }));
});

initMap(state);
render(state);
setInterval(refreshState, 1000);
