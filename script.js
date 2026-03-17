/* ================================================================
   DreamVision Supervisor Dashboard — script.js
   Fixed: API routing, Digital Twin updates, status pills, toasts
   ================================================================ */

// ── API Endpoints ───────────────────────────────────────────────
const API_BASE      = "http://localhost:3000";   // Express backend (MongoDB history + stats)
const EDGE_API_BASE = "http://localhost:8002";   // FastAPI edge server (inspections, verify)

// ── Component Thresholds ────────────────────────────────────────
const COMPONENT_THRESHOLDS = {
    crankcase:        { label: "Crankcase",        normal_min:  60, normal_max: 120, critical: 140, failure: 150 },
    exhaust_manifold: { label: "Exhaust Manifold", normal_min: 200, normal_max: 400, critical: 450, failure: 500 },
    brake_rotor:      { label: "Brake Rotor",      normal_min:  50, normal_max: 250, critical: 300, failure: 350 },
    cylinder_head:    { label: "Cylinder Head",    normal_min:  80, normal_max: 130, critical: 150, failure: 160 },
    battery_pack:     { label: "Battery Pack",     normal_min:  20, normal_max:  45, critical:  55, failure:  65 }
};

// ── State ───────────────────────────────────────────────────────
let currentModalUid = null;
let chartInstance   = null;
let toastTimer      = null;

// ── Toast Notification ──────────────────────────────────────────
function showToast(message, type = "info") {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.textContent = message;
    toast.className   = `toast ${type}`;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toast.className = "toast hidden"; }, 3500);
}

// ── Stats Helper ────────────────────────────────────────────────
function animateValue(el, newVal) {
    if (!el) return;
    el.style.transform = "scale(1.15)";
    el.style.transition = "transform 0.2s";
    el.textContent = newVal;
    setTimeout(() => { el.style.transform = ""; }, 200);
}

// ── Fetch Stats ─────────────────────────────────────────────────
async function fetchStats() {
    try {
        const res  = await fetch(`${API_BASE}/stats`);
        const data = await res.json();

        const yieldPct = data.total_inspections > 0
            ? (((data.ok_count + data.warning_count) / data.total_inspections) * 100).toFixed(1)
            : "0.0";

        animateValue(document.getElementById("stat-total"),       data.total_inspections);
        animateValue(document.getElementById("stat-ok-rate"),     `${yieldPct}%`);
        animateValue(document.getElementById("stat-defect-rate"), `${data.defect_rate_percent ?? data.defect_percent ?? 0}%`);
        animateValue(document.getElementById("stat-warning"),     data.warning_count);

        updateChart(data);
    } catch (e) {
        console.warn("Stats fetch failed — backend may be offline.", e);
    }
}

// ── Status Pill HTML ────────────────────────────────────────────
function statusPill(status) {
    const map = {
        OK:      { cls: "ok",     icon: "✅" },
        WARNING: { cls: "warn",   icon: "⚠️" },
        NOK:     { cls: "danger", icon: "❌" },
    };
    const s = map[status] ?? { cls: "", icon: "❓" };
    return `<span class="status-pill ${s.cls}">${s.icon} ${status}</span>`;
}

// ── Fetch Inspection Feed ───────────────────────────────────────
async function fetchFeed(query = "") {
    try {
        const url = query
            ? `${API_BASE}/results?search=${encodeURIComponent(query)}`
            : `${API_BASE}/results`;

        const res  = await fetch(url);
        const data = await res.json();
        renderTable(data);
    } catch (e) {
        console.warn("Feed fetch failed — backend may be offline.", e);
        renderTable([]);
    }
}

function renderTable(data) {
    const tbody = document.getElementById("tableBody");
    if (!tbody) return;

    if (!data || data.length === 0) {
        tbody.innerHTML = `
            <tr class="empty-row">
                <td colspan="7">
                    <div class="empty-state">
                        <span>🌡️</span>
                        <p>No inspections yet. Run an assessment to populate data.</p>
                    </div>
                </td>
            </tr>`;
        return;
    }

    tbody.innerHTML = "";
    data.forEach(row => {
        // Update Digital Twin with the latest entry status
        if (typeof updateDigitalTwin === "function") {
            updateDigitalTwin(row.status);
        }

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td style="font-family:monospace; color:#94a3b8; font-size:0.78rem;">${row.part_uid ?? "—"}</td>
            <td style="font-weight:600; color:#e5e7eb;">${row.component_name ?? "—"}</td>
            <td style="color:#f59e0b; font-weight:700;">${(row.temperature ?? 0).toFixed(1)}</td>
            <td>${statusPill(row.status)}</td>
            <td><span class="verified-badge">${row.verified_status ?? "Pending"}</span></td>
            <td style="color:#64748b; font-size:0.78rem;">${row.timestamp ?? "—"}</td>
            <td><button onclick="openModal('${row.part_uid}')">Details</button></td>
        `;
        tbody.appendChild(tr);
    });
}

// ── Search ──────────────────────────────────────────────────────
let searchDebounce = null;
function searchInspections() {
    clearTimeout(searchDebounce);
    const q = document.getElementById("searchInput")?.value ?? "";
    searchDebounce = setTimeout(() => fetchFeed(q), 300);
}

function resetSearch() {
    const inp = document.getElementById("searchInput");
    if (inp) inp.value = "";
    fetchFeed();
}

// ── Open Detail Modal ───────────────────────────────────────────
async function openModal(uid) {
    try {
        // Dashboard inspection details live on the edge server
        const res  = await fetch(`${EDGE_API_BASE}/dashboard/inspection/${uid}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        currentModalUid = uid;

        document.getElementById("modal-uid").textContent       = data.part_uid;
        document.getElementById("modal-component").textContent = data.component_name;
        document.getElementById("modal-temp").textContent      = Number(data.temperature).toFixed(1);
        document.getElementById("modal-time").textContent      = data.timestamp;
        document.getElementById("modal-verified").textContent  = data.verified_status ?? "Pending";

        const statusEl  = document.getElementById("modal-status");
        const colorMap  = { OK: "#22c55e", WARNING: "#f59e0b", NOK: "#ef4444" };
        statusEl.textContent   = data.status;
        statusEl.style.background = colorMap[data.status] ?? "#64748b";
        statusEl.style.color      = "#000";

        const imgEl = document.getElementById("modal-img");
        if (data.image_path) {
            imgEl.src = `${EDGE_API_BASE}/${data.image_path}`;
            imgEl.style.display = "block";
        } else {
            imgEl.src = "";
            imgEl.style.display = "none";
        }

        document.getElementById("detailModal").style.display = "block";
    } catch (e) {
        showToast("⚠️ Could not load inspection details.", "warn");
    }
}

function closeModal() {
    document.getElementById("detailModal").style.display = "none";
    currentModalUid = null;
}

// Close modal on backdrop click
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("detailModal")?.addEventListener("click", (e) => {
        if (e.target === e.currentTarget) closeModal();
    });

    // Build the digital twin
    if (typeof buildDigitalTwin === "function") buildDigitalTwin();
});

// ── Submit Verification ─────────────────────────────────────────
async function submitVerification() {
    if (!currentModalUid) return;

    const status = document.getElementById("verify-select")?.value;
    const user   = document.getElementById("logged-user")?.textContent ?? "Supervisor";

    try {
        const res = await fetch(`${EDGE_API_BASE}/dashboard/verify/${currentModalUid}`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ verified_status: status, verified_by: user })
        });

        if (res.ok) {
            showToast(`✅ Verified as ${status} by ${user}`, "ok");
            closeModal();
            fetchFeed();
        } else {
            showToast("❌ Failed to save verification.", "err");
        }
    } catch (e) {
        showToast("🌐 Network error during verification.", "err");
    }
}

// ── Chart.js Donut ──────────────────────────────────────────────
function updateChart(data) {
    const canvas = document.getElementById("defectChart");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: ["OK", "WARNING", "NOK"],
            datasets: [{
                data: [
                    data.ok_count      ?? 0,
                    data.warning_count ?? 0,
                    data.nok_count     ?? 0
                ],
                backgroundColor: ["#22c55e", "#f59e0b", "#ef4444"],
                borderColor:     ["#16a34a", "#d97706", "#dc2626"],
                borderWidth: 2,
                hoverOffset: 10
            }]
        },
        options: {
            responsive:   true,
            cutout:       "68%",
            animation:    { duration: 600, easing: "easeOutQuart" },
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        color:      "#94a3b8",
                        font:       { size: 11, family: "Inter" },
                        padding:    14,
                        usePointStyle: true,
                        pointStyle: "circle"
                    }
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ` ${ctx.label}: ${ctx.raw}`
                    }
                }
            }
        }
    });
}

// ── Trigger Assessment ──────────────────────────────────────────
async function triggerAssessment() {
    const comp = document.getElementById("component-select")?.value;
    const rule = COMPONENT_THRESHOLDS[comp];
    const btn  = document.getElementById("assess-btn");

    let temp;
    if (rule) {
        const rand = Math.random();
        if (rand < 0.70)      temp = rule.normal_min + Math.random() * (rule.normal_max - rule.normal_min);
        else if (rand < 0.90) temp = rule.normal_max + Math.random() * (rule.critical - rule.normal_max);
        else                  temp = rule.critical   + Math.random() * 20;
    } else {
        temp = 50 + Math.random() * 100;
    }

    if (btn) {
        btn.classList.add("loading");
        btn.innerHTML = `<span class="btn-icon">⏳</span> Assessing...`;
    }

    try {
        const res = await fetch(`${EDGE_API_BASE}/inspect`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({
                device_id:            "Supervisor-Dashboard",
                timestamp:            new Date().toISOString(),
                component_name:       comp,
                simulated_temperature: temp
            })
        });

        if (res.ok) {
            showToast(`⚡ Assessment: ${rule?.label ?? comp} @ ${temp.toFixed(1)}°C`, "ok");
            fetchFeed();
            fetchStats();
        } else {
            showToast("❌ Assessment failed. Check edge server.", "err");
        }
    } catch (e) {
        showToast("🌐 Edge server offline. Assessment could not run.", "err");
        console.error("Assessment error:", e);
    } finally {
        if (btn) {
            btn.classList.remove("loading");
            btn.innerHTML = `<span class="btn-icon">⚡</span> Assess Component`;
        }
    }
}

// ── SSE — Server-Sent Events (real-time updates) ────────────────
try {
    const evtSource = new EventSource(`${API_BASE}/stream`);
    evtSource.onmessage = () => {
        const si = document.getElementById("searchInput");
        if (!si?.value && !currentModalUid) {
            fetchFeed();
            fetchStats();
        }
    };
    evtSource.onerror = () => {
        // Silently fall back to polling — server may not support SSE
        evtSource.close();
    };
} catch (_) {}

// ── Polling Fallback (5s) ───────────────────────────────────────
setInterval(() => {
    const si = document.getElementById("searchInput");
    if (!si?.value && !currentModalUid) {
        fetchStats();
        fetchFeed();
    }
}, 5000);

// ── Initial Load ────────────────────────────────────────────────
fetchStats();
fetchFeed();
