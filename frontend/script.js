const API_BASE = "http://localhost:8002/dashboard";
let currentModalUid = null;
let chartInstance = null;

async function fetchStats() {
    try {
        const res = await fetch(`${API_BASE}/stats`);
        const data = await res.json();

        document.getElementById('stat-total').innerText = data.total_inspections;
        document.getElementById('stat-ok-rate').innerText = `${data.yield_percent}%`;
        document.getElementById('stat-defect-rate').innerText = `${data.defect_percent}%`;
        document.getElementById('stat-warning').innerText = data.warning_count;

        updateChart(data);
    } catch (e) { console.error("Stats fetching failed", e); }
}

async function fetchFeed(query = "") {
    try {
        const url = query ? `${API_BASE}/inspections?search=${query}` : `${API_BASE}/inspections`;
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
        const res = await fetch(`${API_BASE}/inspection/${uid}`);
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
        const res = await fetch(`${API_BASE}/verify/${currentModalUid}`, {
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


// (Removed WebSocket dependency since we are polling every 5s per user request)

// Initial loads
fetchStats();
fetchFeed();

// Server-Sent Events (SSE) for instant zero-refresh updates
const evtSource = new EventSource(`${API_BASE}/stream`);
evtSource.onmessage = function(event) {
    if (!document.getElementById('searchInput').value && !currentModalUid) {
        fetchFeed();
        fetchStats();
    }
};
