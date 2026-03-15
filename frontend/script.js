const API_BASE = "http://127.0.0.1:8002";
let currentModalUid = null;
let chartInstance = null;

async function fetchStats() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/stats`);
        const data = await res.json();

        document.getElementById('stat-total').innerText = data.total_inspections;
        document.getElementById('stat-ok-rate').innerText = `${((data.ok_count / Math.max(1, data.total_inspections)) * 100).toFixed(1)}%`;
        document.getElementById('stat-defect-rate').innerText = `${data.defect_rate_percent}%`;
        document.getElementById('stat-warning').innerText = data.warning_count;

        updateChart(data);
    } catch (e) { console.error("Stats fetching failed", e); }
}

async function fetchFeed(query = "") {
    try {
        const url = query ? `${API_BASE}/dashboard/inspections?search=${query}` : `${API_BASE}/dashboard/inspections`;
        const res = await fetch(url);
        const data = await res.json();
        const tbody = document.getElementById('tableBody');
        tbody.innerHTML = "";

        data.forEach(row => {
            let statusColor = row.status === 'OK' ? '#4caf50' : (row.status === 'WARNING' ? '#fb8c00' : '#ef5350');

            let tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${row.part_uid}</td>
                <td>${row.component_name}</td>
                <td>${row.temperature.toFixed(1)}</td>
                <td style="color: ${statusColor}; font-weight: bold;">${row.status}</td>
                <td>${row.verified_status}</td>
                <td>${row.timestamp}</td>
                <td><button onclick="openModal('${row.part_uid}')">Details</button></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) { console.error("Feed fetch failed", e); }
}

function searchInspections() {
    const q = document.getElementById('searchInput').value;
    fetchFeed(q);
}

function resetSearch() {
    document.getElementById('searchInput').value = "";
    fetchFeed();
}

async function openModal(uid) {
    try {
        const res = await fetch(`${API_BASE}/dashboard/inspection/${uid}`);
        const data = await res.json();
        currentModalUid = uid;

        document.getElementById('modal-uid').innerText = data.part_uid;
        document.getElementById('modal-component').innerText = data.component_name;
        document.getElementById('modal-temp').innerText = data.temperature;
        document.getElementById('modal-status').innerText = data.status;
        document.getElementById('modal-status').style.color = data.status === 'OK' ? '#4caf50' : '#ef5350';
        document.getElementById('modal-time').innerText = data.timestamp;
        document.getElementById('modal-verified').innerText = data.verified_status;

        // Correctly route the image mapping using server static mount
        document.getElementById('modal-img').src = `${API_BASE}/${data.image_path}`;

        document.getElementById('detailModal').style.display = 'block';
    } catch (e) {
        alert("Failed to load details");
    }
}

function closeModal() {
    document.getElementById('detailModal').style.display = 'none';
    currentModalUid = null;
}

async function submitVerification() {
    if (!currentModalUid) return;

    const status = document.getElementById('verify-select').value;
    const user = document.getElementById('logged-user').innerText;

    try {
        const res = await fetch(`${API_BASE}/dashboard/verify/${currentModalUid}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ verified_status: status, verified_by: user })
        });

        if (res.ok) {
            alert("Verification Saved successfully");
            closeModal();
            fetchFeed();
        } else {
            alert("Failed to save verification.");
        }
    } catch (e) {
        alert("Network Error during verification");
    }
}

function updateChart(data) {
    const ctx = document.getElementById('defectChart').getContext('2d');

    if (chartInstance) { chartInstance.destroy(); }

    chartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['OK', 'WARNING', 'NOK'],
            datasets: [{
                data: [data.ok_count, data.warning_count, data.nok_count],
                backgroundColor: ['#4caf50', '#fb8c00', '#ef5350'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom', labels: { color: "#ffffff" } }
            }
        }
    });
}


// --- Digital Twin & WebSockets Phase-5 ---
const dtwinNodes = [
    { id: "forge", x: 60, title: "Forge", color: "#666" },
    { id: "heattreat", x: 250, title: "Heat Treat", color: "#666" },
    { id: "cooling", x: 440, title: "Cooling", color: "#666" },
    { id: "inspection", x: 630, title: "Inspection Node", color: "#666" }
];

function drawDigitalTwin(activeStatus = "OK") {
    const svg = document.getElementById("factory-svg");
    svg.innerHTML = "";

    // Draw edges
    for (let i = 0; i < dtwinNodes.length - 1; i++) {
        let line = `<line x1="${dtwinNodes[i].x + 10}" y1="40" x2="${dtwinNodes[i + 1].x - 10}" y2="40" stroke="#555" stroke-width="3" />`;
        svg.innerHTML += line;
    }

    // Determine color of inspection node dynamically
    const colors = { "OK": "#4caf50", "WARNING": "#fb8c00", "NOK": "#ef5350" };
    dtwinNodes[3].color = colors[activeStatus] || "#666";

    // Draw nodes
    dtwinNodes.forEach(node => {
        let circle = `<circle cx="${node.x}" cy="40" r="15" fill="${node.color}" stroke="#fff" stroke-width="2" />`;
        let text = `<text x="${node.x}" y="70" fill="#fff" font-size="12" text-anchor="middle">${node.title}</text>`;
        svg.innerHTML += circle + text;
    });
}
drawDigitalTwin();

const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws/inspections`);

ws.onmessage = (event) => {
    // Realtime Factory Event Triggered (Step 6)
    const data = JSON.parse(event.data);

    // Append a new row to the inspection table
    const tbody = document.getElementById('tableBody');
    const tr = document.createElement("tr");
    
    // Color mapping (Step 6)
    const statusColors = { 
        "OK": "var(--status-ok)", 
        "WARNING": "var(--status-warn)", 
        "NOK": "var(--status-nok)" 
    };
    const color = statusColors[data.status] || "white";

    tr.innerHTML = `
        <td>${data.part_uid}</td>
        <td>${data.component_name}</td>
        <td>${data.temperature.toFixed(1)}</td>
        <td style="color: ${color}; font-weight: bold;">${data.status}</td>
        <td>Pending</td>
        <td>${data.timestamp}</td>
        <td><button onclick="openModal('${data.part_uid}')">Details</button></td>
    `;
    
    // Insert at the top
    tbody.insertBefore(tr, tbody.firstChild);

    // Limit table rows to prevent bloat
    if (tbody.children.length > 50) {
        tbody.removeChild(tbody.lastChild);
    }

    drawDigitalTwin(data.status);
    fetchStats();
};


async function fetchCaptureStatus() {
    try {
        const res = await fetch("http://127.0.0.1:8001/status");
        const data = await res.json();
        document.getElementById('feed-device-id').innerText = data.device_id;
        document.getElementById('feed-backend').innerText = data.backend;
        
        const feedTitle = document.querySelector('.live-feed-container h3');
        if (data.backend === "SIMULATOR") {
            feedTitle.innerHTML = "🧪 SIMULATOR Thermal Feed";
            feedTitle.style.color = "#4fc3f7"; // Light blue for simulator
        } else {
            feedTitle.innerHTML = "🔴 ESP32 Live Thermal Feed";
            feedTitle.style.color = "#fff";
        }
    } catch (e) {
        document.getElementById('feed-backend').innerText = "Offline";
    }
}

// Initial loads and auto-refresh
fetchStats();
fetchFeed();
fetchCaptureStatus();
setInterval(() => {
    if (!document.getElementById('searchInput').value && !currentModalUid) {
        fetchStats();
        fetchFeed();
        fetchCaptureStatus();
    }
}, 5000);
