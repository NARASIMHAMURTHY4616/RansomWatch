/**
 * RansomWatch SOC Dashboard Controller
 * Real-time telemetry streaming, Chart.js updates, incident inspection, and AI triage.
 */

// State
let telemetryChart = null;
let activeIncidentId = null;
const MAX_CHART_POINTS = 30;

// DOM Elements
const systemStatusPill = document.getElementById("systemStatusPill");
const systemStatusDot = document.getElementById("systemStatusDot");
const systemStatusText = document.getElementById("systemStatusText");
const geminiDot = document.getElementById("geminiDot");
const geminiStatusText = document.getElementById("geminiStatusText");

const kpiRiskScore = document.getElementById("kpiRiskScore");
const kpiSeverityTag = document.getElementById("kpiSeverityTag");
const riskBarFill = document.getElementById("riskBarFill");
const kpiOpsRate = document.getElementById("kpiOpsRate");
const kpiBurst = document.getElementById("kpiBurst");
const kpiRenameRate = document.getElementById("kpiRenameRate");
const kpiModRate = document.getElementById("kpiModRate");
const kpiTotalIncidents = document.getElementById("kpiTotalIncidents");
const kpiCriticalTag = document.getElementById("kpiCriticalTag");
const kpiDirs = document.getElementById("kpiDirs");

const gaugeCircle = document.getElementById("gaugeCircle");
const gaugeScore = document.getElementById("gaugeScore");
const gaugeSeverity = document.getElementById("gaugeSeverity");
const activeReasonsList = document.getElementById("activeReasonsList");
const incidentsTableBody = document.getElementById("incidentsTableBody");

// Modal Elements
const incidentModal = document.getElementById("incidentModal");
const btnModalClose = document.getElementById("btnModalClose");
const modalIncidentId = document.getElementById("modalIncidentId");
const modalSeverityBadge = document.getElementById("modalSeverityBadge");
const modalTimestamp = document.getElementById("modalTimestamp");
const modalProcess = document.getElementById("modalProcess");
const modalMl = document.getElementById("modalMl");
const modalScore = document.getElementById("modalScore");
const modalPath = document.getElementById("modalPath");
const modalFeaturesGrid = document.getElementById("modalFeaturesGrid");
const modalReasonsList = document.getElementById("modalReasonsList");
const modalRagCards = document.getElementById("modalRagCards");
const aiAnalysisContent = document.getElementById("aiAnalysisContent");
const btnReanalyze = document.getElementById("btnReanalyze");

// Simulator Buttons
const btnRunBenign = document.getElementById("btnRunBenign");
const btnRunRansomware = document.getElementById("btnRunRansomware");
const btnCleanup = document.getElementById("btnCleanup");
const btnRefreshIncidents = document.getElementById("btnRefreshIncidents");
const btnClearIncidents = document.getElementById("btnClearIncidents");

// Initialize Chart
function initTelemetryChart() {
  const ctx = document.getElementById("telemetryChart").getContext("2d");
  const initialLabels = Array(MAX_CHART_POINTS).fill("");

  telemetryChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: initialLabels,
      datasets: [
        {
          label: "Operations Rate",
          data: Array(MAX_CHART_POINTS).fill(0),
          borderColor: "#06b6d4",
          backgroundColor: "rgba(6, 182, 212, 0.1)",
          borderWidth: 2,
          tension: 0.3,
          fill: true,
          pointRadius: 1,
        },
        {
          label: "Rename Rate (Extensions)",
          data: Array(MAX_CHART_POINTS).fill(0),
          borderColor: "#f59e0b",
          backgroundColor: "rgba(245, 158, 11, 0.05)",
          borderWidth: 2,
          tension: 0.3,
          fill: true,
          pointRadius: 1,
        },
        {
          label: "Modify Rate",
          data: Array(MAX_CHART_POINTS).fill(0),
          borderColor: "#a855f7",
          backgroundColor: "transparent",
          borderWidth: 1.5,
          borderDash: [4, 4],
          tension: 0.3,
          pointRadius: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(15, 23, 42, 0.9)",
          titleColor: "#94a3b8",
          bodyFont: { family: "monospace" },
        },
      },
      scales: {
        x: {
          grid: { color: "rgba(30, 44, 69, 0.4)" },
          ticks: { display: false },
        },
        y: {
          beginAtZero: true,
          suggestedMax: 20,
          grid: { color: "rgba(30, 44, 69, 0.4)" },
          ticks: {
            color: "#64748b",
            font: { family: "monospace" },
          },
        },
      },
    },
  });
}

// Severity color helpers
function getSeverityColors(severity) {
  switch (severity) {
    case "CRITICAL":
      return { border: "#ef4444", glow: "rgba(239, 68, 68, 0.4)", tagClass: "danger-tag", badgeClass: "sev-critical" };
    case "HIGH":
      return { border: "#f59e0b", glow: "rgba(245, 158, 11, 0.3)", tagClass: "warning-tag", badgeClass: "sev-high" };
    case "MEDIUM":
      return { border: "#eab308", glow: "rgba(234, 179, 8, 0.25)", tagClass: "warning-tag", badgeClass: "sev-medium" };
    default:
      return { border: "#10b981", glow: "rgba(16, 185, 129, 0.2)", tagClass: "neutral-tag", badgeClass: "sev-low" };
  }
}

// Fetch System Status
async function fetchStatus() {
  try {
    const res = await fetch("/api/status");
    if (!res.ok) return;
    const data = await res.json();

    // AI Status Pill
    if (data.ai_engine && data.ai_engine.configured) {
      geminiDot.style.background = "#10b981";
      geminiDot.classList.add("pulse-green");
      geminiStatusText.innerText = `GEMINI AI: READY (${data.ai_engine.model})`;
    } else {
      geminiDot.style.background = "#64748b";
      geminiDot.classList.remove("pulse-green");
      geminiStatusText.innerText = "GEMINI AI: UNCONFIGURED (FALLBACK ACTIVE)";
    }
  } catch (e) {
    console.debug("Status fetch error:", e);
  }
}

// Fetch Live Metrics and update Charts
async function fetchLiveMetrics() {
  try {
    const res = await fetch("/api/live-metrics");
    if (!res.ok) return;
    const data = await res.json();

    const feat = data.current_features || {};
    const risk = data.current_risk || { risk_score: 0, severity: "LOW", reasons: [] };

    // Update KPI Card: Risk Level
    kpiRiskScore.innerText = risk.risk_score;
    kpiSeverityTag.innerText = risk.severity;
    riskBarFill.style.width = `${risk.risk_score}%`;

    const colors = getSeverityColors(risk.severity);
    riskBarFill.style.backgroundColor = colors.border;
    kpiSeverityTag.className = `kpi-tag ${colors.tagClass}`;

    // Update KPI Card: Operations
    kpiOpsRate.innerText = (feat.operations_rate || 0).toFixed(1);
    kpiBurst.innerText = `${Math.round(feat.activity_burst || 0)} ops`;

    // Update KPI Card: Renames
    kpiRenameRate.innerText = (feat.rename_rate || 0).toFixed(1);
    kpiModRate.innerText = `${(feat.modified_rate || 0).toFixed(1)}/s`;
    kpiDirs.innerText = feat.directories_affected || 0;

    // Update Gauge
    gaugeScore.innerText = risk.risk_score;
    gaugeSeverity.innerText = `${risk.severity} THREAT`;
    gaugeCircle.style.borderColor = colors.border;
    gaugeCircle.style.boxShadow = `0 0 25px ${colors.glow}`;

    // System Alert Status
    if (risk.severity === "CRITICAL" || risk.severity === "HIGH") {
      systemStatusDot.className = "status-dot pulse-red";
      systemStatusDot.style.background = "#ef4444";
      systemStatusText.innerText = "RANSOMWARE ACTIVITY DETECTED";
      systemStatusPill.style.borderColor = "#ef4444";
    } else {
      systemStatusDot.className = "status-dot pulse-green";
      systemStatusDot.style.background = "#10b981";
      systemStatusText.innerText = "SYSTEM ACTIVE / MONITORING";
      systemStatusPill.style.borderColor = "var(--border-color)";
    }

    // Active reasons list
    if (risk.reasons && risk.reasons.length > 0) {
      activeReasonsList.innerHTML = risk.reasons
        .map((r) => `<li class="reason-item">${r}</li>`)
        .join("");
    } else {
      activeReasonsList.innerHTML = `<li class="reason-item">System idle. Baseline parameters nominal.</li>`;
    }

    // Update Chart with latest history
    if (telemetryChart && data.history && data.history.length > 0) {
      const history = data.history.slice(-MAX_CHART_POINTS);
      const opsData = history.map((h) => h.operations_rate);
      const renameData = history.map((h) => h.rename_rate);
      const modData = history.map((h) => h.modified_rate);

      while (opsData.length < MAX_CHART_POINTS) {
        opsData.unshift(0);
        renameData.unshift(0);
        modData.unshift(0);
      }

      telemetryChart.data.datasets[0].data = opsData;
      telemetryChart.data.datasets[1].data = renameData;
      telemetryChart.data.datasets[2].data = modData;
      telemetryChart.update();
    }
  } catch (e) {
    console.debug("Live metrics fetch error:", e);
  }
}

// Fetch Stats for Cards
async function fetchStats() {
  try {
    const res = await fetch("/api/stats");
    if (!res.ok) return;
    const stats = await res.json();
    kpiTotalIncidents.innerText = stats.total_incidents || 0;
    kpiCriticalTag.innerText = `${stats.critical_incidents || 0} CRITICAL`;
  } catch (e) {
    console.debug("Stats fetch error:", e);
  }
}

// Fetch Incidents Table
async function fetchIncidents() {
  try {
    const res = await fetch("/api/incidents?limit=25");
    if (!res.ok) return;
    const incidents = await res.json();

    if (!incidents || incidents.length === 0) {
      incidentsTableBody.innerHTML = `
        <tr>
          <td colspan="8" class="text-center empty-state">
            No incidents detected yet. Run the Ransomware simulation above to test.
          </td>
        </tr>`;
      return;
    }

    incidentsTableBody.innerHTML = incidents
      .map((inc) => {
        const timeStr = new Date(inc.timestamp * 1000).toLocaleTimeString();
        const colors = getSeverityColors(inc.severity);
        const topReason = inc.reasons && inc.reasons.length > 0 ? inc.reasons[0] : "Behavioral threshold anomaly";
        const confPercent = `${(inc.confidence * 100).toFixed(1)}%`;

        return `
          <tr>
            <td><strong style="font-family: monospace; color: #38bdf8;">${inc.id}</strong></td>
            <td style="color: #94a3b8; font-family: monospace;">${timeStr}</td>
            <td><span class="sev-badge ${colors.badgeClass}">${inc.severity}</span></td>
            <td><strong style="font-family: monospace;">${inc.risk_score}</strong> / 100</td>
            <td style="color: #94a3b8; font-family: monospace;">${inc.label} (${confPercent})</td>
            <td><code style="color: #cbd5e1;">${inc.process_name} [PID:${inc.pid}]</code></td>
            <td style="max-width: 280px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #94a3b8;">
              ${topReason}
            </td>
            <td>
              <button class="btn btn-sm btn-secondary" onclick="openIncidentModal('${inc.id}')">
                Inspect & Triage
              </button>
            </td>
          </tr>
        `;
      })
      .join("");
  } catch (e) {
    console.debug("Incidents fetch error:", e);
  }
}

// Open Incident Detail Modal
async function openIncidentModal(incidentId) {
  activeIncidentId = incidentId;
  incidentModal.classList.add("active");
  aiAnalysisContent.innerHTML = `<p class="text-muted">Loading incident evidence and RAG intelligence...</p>`;

  try {
    const res = await fetch(`/api/incidents/${incidentId}`);
    if (!res.ok) return;
    const inc = await res.json();

    // Populate Headers
    modalIncidentId.innerText = inc.id;
    modalSeverityBadge.innerText = inc.severity;
    const colors = getSeverityColors(inc.severity);
    modalSeverityBadge.className = `badge ${colors.badgeClass}`;
    modalTimestamp.innerText = new Date(inc.timestamp * 1000).toLocaleString();

    modalProcess.innerText = `${inc.process_name} (PID: ${inc.pid})`;
    modalMl.innerText = `${inc.label} (${(inc.confidence * 100).toFixed(1)}%)`;
    modalScore.innerText = `${inc.risk_score} / 100 (${inc.severity})`;
    modalPath.innerText = inc.affected_path || "test_data/";

    // Populate Features Grid
    const f = inc.features || {};
    modalFeaturesGrid.innerHTML = `
      <div class="feature-pill"><span class="f-name">Create Rate</span><span class="f-val">${f.create_rate || 0} /s</span></div>
      <div class="feature-pill"><span class="f-name">Modified Rate</span><span class="f-val">${f.modified_rate || 0} /s</span></div>
      <div class="feature-pill"><span class="f-name">Rename Rate</span><span class="f-val text-amber">${f.rename_rate || 0} /s</span></div>
      <div class="feature-pill"><span class="f-name">Delete Rate</span><span class="f-val">${f.delete_rate || 0} /s</span></div>
      <div class="feature-pill"><span class="f-name">Operations Rate</span><span class="f-val">${f.operations_rate || 0} /s</span></div>
      <div class="feature-pill"><span class="f-name">Directories Touched</span><span class="f-val">${f.directories_affected || 0}</span></div>
      <div class="feature-pill"><span class="f-name">1s Burst Peak</span><span class="f-val text-red">${f.activity_burst || 0} ops</span></div>
    `;

    // Populate Reasons
    modalReasonsList.innerHTML = (inc.reasons || [])
      .map((r) => `<li class="indicator-row">${r}</li>`)
      .join("");

    // Populate RAG Knowledge Cards
    const ragChunks = inc.rag_context || [];
    if (ragChunks.length > 0) {
      modalRagCards.innerHTML = ragChunks
        .map(
          (c) => `
          <div class="rag-card">
            <div class="rag-card-header">
              <span>${c.source} &bull; ${c.section}</span>
              <span class="badge info-badge">Relevance: ${(c.relevance_score * 100).toFixed(1)}%</span>
            </div>
            <div class="rag-card-body">${c.content}</div>
          </div>
        `
        )
        .join("");
    } else {
      modalRagCards.innerHTML = `<p class="text-muted">No external RAG chunks attached yet. Click "Run Gemini AI Triage" to retrieve.</p>`;
    }

    // Populate AI Analysis
    renderAiAnalysis(inc.ai_analysis);
  } catch (e) {
    aiAnalysisContent.innerHTML = `<p class="text-red">Error loading incident data: ${e.message}</p>`;
  }
}

// Render AI Analysis Blocks
function renderAiAnalysis(ai) {
  if (!ai || (!ai.summary && !ai.raw_text)) {
    aiAnalysisContent.innerHTML = `
      <div class="ai-block">
        <p class="text-muted">Post-detection AI triage not generated yet.</p>
        <p style="font-size: 0.8rem; margin-top: 6px; color: #64748b;">Click "Run Gemini AI Triage" to execute RAG retrieval and generate structured SOC guidance.</p>
      </div>`;
    return;
  }

  const isConfigured = ai.available !== false;
  const disclaimerNotice = !isConfigured
    ? `<div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); padding: 8px 12px; border-radius: 6px; margin-bottom: 12px; font-size: 0.75rem; color: #f59e0b;">
         <strong>OFFLINE FALLBACK ACTIVE:</strong> Gemini API key not configured in .env. Showing local rule-based defensive analysis and MITRE ATT&CK guidance.
       </div>`
    : "";

  const stepsList = (ai.investigation_steps || [])
    .map((s) => `<li>${s}</li>`)
    .join("");

  const containmentList = (ai.containment_recommendations || [])
    .map((c) => `<li>${c}</li>`)
    .join("");

  aiAnalysisContent.innerHTML = `
    ${disclaimerNotice}
    <div class="ai-block">
      <div class="ai-block-title">Executive Summary</div>
      <div class="ai-block-text">${ai.summary || ai.raw_text || "Analysis complete."}</div>
    </div>

    <div class="ai-block">
      <div class="ai-block-title">MITRE ATT&CK Technique Mapping</div>
      <div class="ai-block-text"><strong style="color: #38bdf8;">${ai.likely_technique || "T1486 (Data Encrypted for Impact)"}</strong></div>
    </div>

    <div class="ai-block">
      <div class="ai-block-title">Immediate Tier-1 Investigation Steps</div>
      <ul class="ai-steps-list">${stepsList || "<li>Inspect open file descriptors and running process memory.</li>"}</ul>
    </div>

    <div class="ai-block">
      <div class="ai-block-title">Containment & Defensive Actions</div>
      <ul class="ai-steps-list" style="color: #f87171;">${containmentList || "<li>Isolate host from local network subnet immediately.</li>"}</ul>
    </div>

    ${ai.defensive_posture ? `
    <div class="ai-block">
      <div class="ai-block-title">Long-Term Posture & Hardening</div>
      <div class="ai-block-text">${ai.defensive_posture}</div>
    </div>` : ""}
  `;
}

// Trigger Re-Analyze
btnReanalyze.addEventListener("click", async () => {
  if (!activeIncidentId) return;
  btnReanalyze.disabled = true;
  btnReanalyze.innerText = "Analyzing...";
  aiAnalysisContent.innerHTML = `<p class="text-muted">Retrieving knowledge chunks and running Gemini defensive analysis...</p>`;

  try {
    const res = await fetch(`/api/analyze/${activeIncidentId}`, { method: "POST" });
    const data = await res.json();
    btnReanalyze.disabled = false;
    btnReanalyze.innerText = "Run Gemini AI Triage";

    if (data.ai_analysis) {
      renderAiAnalysis(data.ai_analysis);
      // Also refresh RAG cards
      if (data.rag_context && data.rag_context.length > 0) {
        modalRagCards.innerHTML = data.rag_context
          .map(
            (c) => `
            <div class="rag-card">
              <div class="rag-card-header">
                <span>${c.source} &bull; ${c.section}</span>
                <span class="badge info-badge">Relevance: ${(c.relevance_score * 100).toFixed(1)}%</span>
              </div>
              <div class="rag-card-body">${c.content}</div>
            </div>`
          )
          .join("");
      }
    }
  } catch (e) {
    btnReanalyze.disabled = false;
    btnReanalyze.innerText = "Run Gemini AI Triage";
    aiAnalysisContent.innerHTML = `<p class="text-red">Analysis error: ${e.message}</p>`;
  }
});

// Close Modal
btnModalClose.addEventListener("click", () => {
  incidentModal.classList.remove("active");
  activeIncidentId = null;
});

incidentModal.addEventListener("click", (e) => {
  if (e.target === incidentModal) {
    incidentModal.classList.remove("active");
    activeIncidentId = null;
  }
});

// Simulator Action Triggers
btnRunBenign.addEventListener("click", async () => {
  btnRunBenign.disabled = true;
  btnRunBenign.innerText = "Simulating Benign...";
  try {
    await fetch("/api/simulator/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: "benign", duration: 8 }),
    });
  } finally {
    setTimeout(() => {
      btnRunBenign.disabled = false;
      btnRunBenign.innerText = "Simulate Benign Activity";
    }, 8000);
  }
});

btnRunRansomware.addEventListener("click", async () => {
  btnRunRansomware.disabled = true;
  btnRunRansomware.innerText = "Bursting Simulation...";
  try {
    await fetch("/api/simulator/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: "ransomware", duration: 8, intensity: "high" }),
    });
  } finally {
    setTimeout(() => {
      btnRunRansomware.disabled = false;
      btnRunRansomware.innerText = "Simulate Ransomware Burst";
    }, 8000);
  }
});

btnCleanup.addEventListener("click", async () => {
  if (!confirm("Safely wipe all simulation test files inside test_data/?")) return;
  await fetch("/api/simulator/cleanup", { method: "POST" });
  fetchLiveMetrics();
});

btnRefreshIncidents.addEventListener("click", () => {
  fetchIncidents();
  fetchStats();
});

btnClearIncidents.addEventListener("click", async () => {
  if (!confirm("Clear all recorded incident history from SQLite?")) return;
  await fetch("/api/incidents/clear-all", { method: "POST" });
  fetchIncidents();
  fetchStats();
});

// Main Loop Setup
window.addEventListener("DOMContentLoaded", () => {
  initTelemetryChart();
  fetchStatus();
  fetchStats();
  fetchLiveMetrics();
  fetchIncidents();

  // Periodic Polling
  setInterval(fetchLiveMetrics, 1000);
  setInterval(fetchStats, 3000);
  setInterval(fetchIncidents, 3000);
  setInterval(fetchStatus, 10000);
});
