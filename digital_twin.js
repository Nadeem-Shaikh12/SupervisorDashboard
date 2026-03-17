/**
 * frontend/digital_twin.js
 * =========================
 * UPGRADE 4 — Production Line Digital Twin
 *
 * Draws and animates four industrial stations:
 *   Forge → Heat Treatment → Cooling → Inspection
 *
 * Station colours:
 *   Green  (#4caf50) → OK
 *   Amber  (#fb8c00) → WARNING
 *   Red    (#ef5350) → NOK
 *   Grey   (#607d8b) → Idle / Unknown
 *
 * Receives real-time inspection results via the WebSocket already open in
 * script.js with the API_BASE + "/ws/inspections" endpoint.
 * Call  updateDigitalTwin(status)  from the ws.onmessage handler.
 */

// ── Station Definitions ───────────────────────────────────────────────────────
const DT_STATIONS = [
    { id: "dt-forge", label: "Forge", icon: "🔥" },
    { id: "dt-heattreat", label: "Heat Treatment", icon: "♨️" },
    { id: "dt-cooling", label: "Cooling", icon: "❄️" },
    { id: "dt-inspection", label: "Inspection", icon: "🔍" },
];

const DT_COLOURS = {
    OK: "#4caf50",
    WARNING: "#fb8c00",
    NOK: "#ef5350",
    IDLE: "#607d8b",
};

// Initialise all stations to IDLE; update when results arrive
const _stationStatus = {
    "dt-forge": "IDLE",
    "dt-heattreat": "IDLE",
    "dt-cooling": "IDLE",
    "dt-inspection": "IDLE",
};

// ── DOM Builder ───────────────────────────────────────────────────────────────
/**
 * Injects the digital twin HTML into an element with id="digital-twin-panel".
 * Call once after DOMContentLoaded.
 */
function buildDigitalTwin() {
    const panel = document.getElementById("digital-twin-panel");
    if (!panel) return;

    panel.innerHTML = `
        <div class="dt-header">
            <span class="dt-title">🏭 Production Line Digital Twin</span>
            <span class="dt-subtitle" id="dt-last-update">Last update: —</span>
        </div>
        <div class="dt-track">
            ${DT_STATIONS.map((s, idx) => `
                <div class="dt-station-wrap">
                    <div class="dt-station" id="${s.id}" title="${s.label}">
                        <div class="dt-icon">${s.icon}</div>
                        <div class="dt-label">${s.label}</div>
                        <div class="dt-badge" id="${s.id}-badge">IDLE</div>
                    </div>
                    ${idx < DT_STATIONS.length - 1
            ? '<div class="dt-arrow">&#9654;</div>'
            : ""}
                </div>
            `).join("")}
        </div>
        <div class="dt-legend">
            <span class="dt-legend-item"><span class="dt-dot" style="background:#4caf50"></span> OK</span>
            <span class="dt-legend-item"><span class="dt-dot" style="background:#fb8c00"></span> WARNING</span>
            <span class="dt-legend-item"><span class="dt-dot" style="background:#ef5350"></span> NOK</span>
            <span class="dt-legend-item"><span class="dt-dot" style="background:#607d8b"></span> IDLE</span>
        </div>
    `;

    _applyAllStyles();
    _renderAllStations();
}

// ── Public update API ─────────────────────────────────────────────────────────
/**
 * Called by ws.onmessage in script.js with the latest inspection status.
 * Cascades the status through the pipeline: Forge → Inspection all light up,
 * then only the Inspection node keeps the actual result colour.
 *
 * @param {string} status  "OK" | "WARNING" | "NOK"
 */
function updateDigitalTwin(status) {
    const norm = (status || "IDLE").toUpperCase();

    // Upstream stations all show OK (they passed before reaching inspection)
    _stationStatus["dt-forge"] = "OK";
    _stationStatus["dt-heattreat"] = "OK";
    _stationStatus["dt-cooling"] = "OK";
    // Inspection node reflects the actual AI result
    _stationStatus["dt-inspection"] = norm;

    _renderAllStations();

    const ts = new Date().toLocaleTimeString();
    const el = document.getElementById("dt-last-update");
    if (el) el.textContent = `Last update: ${ts}`;
}

/**
 * Reset all stations to IDLE (e.g., production shift change).
 */
function resetDigitalTwin() {
    Object.keys(_stationStatus).forEach(k => { _stationStatus[k] = "IDLE"; });
    _renderAllStations();
}

// ── Rendering helpers ─────────────────────────────────────────────────────────
function _renderAllStations() {
    DT_STATIONS.forEach(s => _renderStation(s.id, _stationStatus[s.id]));
}

function _renderStation(stationId, status) {
    const el = document.getElementById(stationId);
    const badge = document.getElementById(`${stationId}-badge`);
    if (!el || !badge) return;

    const colour = DT_COLOURS[status] || DT_COLOURS.IDLE;

    // Update border glow and background
    el.style.borderColor = colour;
    el.style.boxShadow = `0 0 16px ${colour}88, 0 0 4px ${colour}`;
    el.style.backgroundColor = `${colour}18`;

    // Badge text + colour
    badge.textContent = status;
    badge.style.backgroundColor = colour;
    badge.style.color = "#fff";

    // Pulse animation on active states
    if (status !== "IDLE") {
        el.classList.add("dt-pulse");
        setTimeout(() => el.classList.remove("dt-pulse"), 600);
    }
}

// ── Inject required CSS (avoids an extra HTTP request) ───────────────────────
function _applyAllStyles() {
    if (document.getElementById("dt-styles")) return;

    const style = document.createElement("style");
    style.id = "dt-styles";
    style.textContent = `
        /* ── Digital Twin panel ──────────────────────────────────── */
        #digital-twin-panel {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            font-family: 'Roboto', sans-serif;
        }

        .dt-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 18px;
        }

        .dt-title {
            font-size: 1rem;
            font-weight: 700;
            color: #e6edf3;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .dt-subtitle {
            font-size: 0.75rem;
            color: #8b949e;
        }

        /* ── Station track ──────────────────────────────────────── */
        .dt-track {
            display: flex;
            align-items: center;
            justify-content: space-evenly;
            flex-wrap: wrap;
            gap: 10px;
            padding: 10px 0;
        }

        .dt-station-wrap {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .dt-station {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            width: 120px;
            height: 110px;
            border: 2px solid #607d8b;
            border-radius: 10px;
            background: #607d8b18;
            cursor: default;
            transition: all 0.3s ease;
            position: relative;
        }

        .dt-icon {
            font-size: 2rem;
            margin-bottom: 4px;
        }

        .dt-label {
            font-size: 0.7rem;
            color: #c9d1d9;
            font-weight: 600;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        .dt-badge {
            position: absolute;
            bottom: -12px;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 0.65rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            background: #607d8b;
            color: #fff;
            box-shadow: 0 2px 6px #00000055;
        }

        /* ── Arrow connector ────────────────────────────────────── */
        .dt-arrow {
            font-size: 1.4rem;
            color: #444d56;
            user-select: none;
        }

        /* ── Legend ─────────────────────────────────────────────── */
        .dt-legend {
            display: flex;
            gap: 16px;
            margin-top: 24px;
            justify-content: center;
        }

        .dt-legend-item {
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 0.72rem;
            color: #8b949e;
        }

        .dt-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
        }

        /* ── Pulse keyframe ─────────────────────────────────────── */
        @keyframes dtpulse {
            0%   { transform: scale(1);    }
            50%  { transform: scale(1.04); }
            100% { transform: scale(1);    }
        }

        .dt-pulse {
            animation: dtpulse 0.5s ease;
        }
    `;
    document.head.appendChild(style);
}

// ── Auto-init when DOM is ready ───────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", buildDigitalTwin);
