const el = id => document.getElementById(id);

// --- Stats + chart ---
async function loadStats() {
    const res = await fetch("/api/security/stats");
    if (!res.ok) return;
    const data = await res.json();
    el("stat-total").textContent = data.total_attempts_24h;
    el("stat-failed").textContent = data.failed_attempts_24h;
    el("stat-suspicious").textContent = data.suspicious_events_24h;
    el("stat-bruteforce").textContent = data.brute_force_events_24h;
    el("stat-locked").textContent = data.currently_locked_accounts;
    drawChart(data.hourly_failed_attempts);
}

function drawChart(buckets) {
    const canvas = el("chart");
    const dpr = window.devicePixelRatio || 1;
    const cssWidth = canvas.clientWidth || canvas.parentElement.clientWidth;
    const cssHeight = 140;
    canvas.width = cssWidth * dpr;
    canvas.height = cssHeight * dpr;
    canvas.style.height = cssHeight + "px";
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cssWidth, cssHeight);

    if (!buckets.length) {
        ctx.fillStyle = "#4a5563";
        ctx.font = "13px monospace";
        ctx.fillText("No failed attempts in the last 24h", 4, cssHeight / 2);
        return;
    }

    const max = Math.max(...buckets.map(b => b.count), 1);
    const barGap = 4;
    const barWidth = Math.max(4, (cssWidth - barGap * (buckets.length - 1)) / buckets.length);
    const baseline = cssHeight - 18;

    buckets.forEach((bucket, i) => {
        const barHeight = (bucket.count / max) * (baseline - 10);
        const x = i * (barWidth + barGap);
        const y = baseline - barHeight;
        ctx.fillStyle = bucket.count >= 10 ? "#ff5c6c" : bucket.count >= 5 ? "#ff9f45" : "#4dd6a8";
        ctx.fillRect(x, y, barWidth, barHeight);
    });

    ctx.fillStyle = "#7f8b99";
    ctx.font = "10px monospace";
    const first = buckets[0].hour.slice(5, 13);
    const last = buckets[buckets.length - 1].hour.slice(5, 13);
    ctx.fillText(first, 0, cssHeight - 4);
    ctx.fillText(last, cssWidth - ctx.measureText(last).width, cssHeight - 4);
}

// --- Tables ---
function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

async function loadEvents() {
    const res = await fetch("/api/security/events?limit=25");
    if (!res.ok) return;
    const rows = await res.json();
    const tbody = document.querySelector("#events-table tbody");
    if (!rows.length) {
        tbody.innerHTML = '<tr class="empty-row"><td colspan="5">No security events yet.</td></tr>';
        return;
    }
    tbody.innerHTML = rows.map(r => `
        <tr>
            <td>${escapeHtml(r.event_type)}</td>
            <td>${escapeHtml(r.identifier)}</td>
            <td class="severity-${escapeHtml(r.severity)}">${escapeHtml(r.severity)}</td>
            <td>${escapeHtml(r.details || "")}</td>
            <td>${escapeHtml(r.timestamp)}</td>
        </tr>`).join("");
}

async function loadAttempts() {
    const res = await fetch("/api/security/attempts?limit=25");
    if (!res.ok) return;
    const rows = await res.json();
    const tbody = document.querySelector("#attempts-table tbody");
    if (!rows.length) {
        tbody.innerHTML = '<tr class="empty-row"><td colspan="4">No login attempts yet.</td></tr>';
        return;
    }
    tbody.innerHTML = rows.map(r => `
        <tr>
            <td>${escapeHtml(r.identifier)}</td>
            <td>${escapeHtml(r.ip_address)}</td>
            <td class="${r.success ? "success" : "fail"}">${r.success ? "success" : "failed"}</td>
            <td>${escapeHtml(r.timestamp)}</td>
        </tr>`).join("");
}

function refreshAll() {
    loadStats();
    loadEvents();
    loadAttempts();
}

// --- Simulate failed logins ---
el("simulate-form").addEventListener("submit", async e => {
    e.preventDefault();
    const identifier = el("simulate-identifier").value.trim();
    const count = Math.min(15, Math.max(1, parseInt(el("simulate-count").value, 10) || 1));
    const status = el("simulate-status");
    const submitBtn = el("simulate-submit");
    if (!identifier) return;

    submitBtn.disabled = true;
    status.classList.remove("success");
    for (let i = 0; i < count; i++) {
        status.textContent = `Sending attempt ${i + 1} of ${count}…`;
        try {
            const res = await fetch("/api/simulate/failed-login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ identifier }),
            });
            const data = await res.json();
            if (!res.ok) {
                status.textContent = data.error || "Simulation failed.";
                break;
            }
            if (data.status === "brute_force") {
                status.textContent = `Brute-force detected after ${data.failed_count} failed attempts — account locked.`;
            } else if (data.status === "suspicious") {
                status.textContent = `Suspicious activity flagged (${data.failed_count} failed attempts).`;
            }
        } catch (err) {
            status.textContent = "Could not reach the server.";
            break;
        }
        await refreshDashboardQuietly();
        await new Promise(r => setTimeout(r, 150));
    }
    if (!status.textContent.startsWith("Brute-force") && !status.textContent.startsWith("Suspicious")) {
        status.textContent = `Sent ${count} simulated failed attempts.`;
        status.classList.add("success");
    }
    submitBtn.disabled = false;
});

async function refreshDashboardQuietly() {
    await Promise.all([loadStats(), loadEvents(), loadAttempts()]);
}

refreshAll();
setInterval(refreshAll, 8000);
