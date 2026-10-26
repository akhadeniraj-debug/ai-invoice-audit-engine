/**
 * DocAudit-Core | Enterprise SaaS Client Application
 * Handles document upload, live polling, HITL review actions, and ledger records.
 */

// ============================================================================
// CONFIGURATION & STATE MANAGEMENT
// ============================================================================
const state = {
  apiBaseUrl: localStorage.getItem("docaudit_api_url") || (window.location.port ? window.location.origin : "http://localhost:8000"),
  selectedFile: null,
  activeDocument: null,
  rawJsonData: null,
  demoMode: localStorage.getItem("docaudit_demo_mode") === "true",
  ledgerFilter: "ALL",
  ledgerSearch: "",
  localLedgerCache: JSON.parse(localStorage.getItem("docaudit_ledger_cache") || "[]"),
};

// ============================================================================
// DOM ELEMENTS
// ============================================================================
const dom = {
  connectionStatusPill: document.getElementById("connectionStatusPill"),
  statusPing: document.getElementById("statusPing"),
  statusDot: document.getElementById("statusDot"),
  statusText: document.getElementById("statusText"),
  demoToggleBtn: document.getElementById("demoToggleBtn"),
  demoModeLabel: document.getElementById("demoModeLabel"),
  openSettingsBtn: document.getElementById("openSettingsBtn"),
  errorBanner: document.getElementById("errorBanner"),
  errorBannerTitle: document.getElementById("errorBannerTitle"),
  errorBannerDesc: document.getElementById("errorBannerDesc"),
  dismissErrorBtn: document.getElementById("dismissErrorBtn"),

  // KPIs
  kpiTotalDocs: document.getElementById("kpiTotalDocs"),
  kpiApproved: document.getElementById("kpiApproved"),
  kpiPending: document.getElementById("kpiPending"),
  kpiTotalCapital: document.getElementById("kpiTotalCapital"),

  // Upload Cockpit
  dropZone: document.getElementById("dropZone"),
  fileInput: document.getElementById("fileInput"),
  selectedFileCard: document.getElementById("selectedFileCard"),
  selectedFileName: document.getElementById("selectedFileName"),
  selectedFileSize: document.getElementById("selectedFileSize"),
  clearFileBtn: document.getElementById("clearFileBtn"),
  auditDocBtn: document.getElementById("auditDocBtn"),
  sampleInvoiceBtn: document.getElementById("sampleInvoiceBtn"),

  // Pipeline Stepper
  pipelineProgressContainer: document.getElementById("pipelineProgressContainer"),
  pipelineProgressBar: document.getElementById("pipelineProgressBar"),
  pipelineStepTitle: document.getElementById("pipelineStepTitle"),
  pipelineStepPercent: document.getElementById("pipelineStepPercent"),
  stepS3: document.getElementById("stepS3"),
  stepOCR: document.getElementById("stepOCR"),
  stepRules: document.getElementById("stepRules"),

  // Inspection Views
  auditEmptyState: document.getElementById("auditEmptyState"),
  auditActiveState: document.getElementById("auditActiveState"),
  docTitle: document.getElementById("docTitle"),
  auditStatusBadge: document.getElementById("auditStatusBadge"),
  statusBadgeText: document.getElementById("statusBadgeText"),
  threadIdDisplay: document.getElementById("threadIdDisplay"),
  copyThreadBtn: document.getElementById("copyThreadBtn"),
  s3UriDisplay: document.getElementById("s3UriDisplay"),
  openRawJsonBtn: document.getElementById("openRawJsonBtn"),

  // Discrepancy Banner
  discrepancyBanner: document.getElementById("discrepancyBanner"),
  discrepancyCountText: document.getElementById("discrepancyCountText"),
  discrepancyList: document.getElementById("discrepancyList"),

  // Metadata Grid
  metaVendor: document.getElementById("metaVendor"),
  metaInvoiceNo: document.getElementById("metaInvoiceNo"),
  metaDate: document.getElementById("metaDate"),
  metaDueDate: document.getElementById("metaDueDate"),

  // Checklist
  checkMath: document.getElementById("checkMath"),
  checkTax: document.getElementById("checkTax"),
  checkDate: document.getElementById("checkDate"),
  checkItems: document.getElementById("checkItems"),

  // Line items & totals
  lineItemsTableBody: document.getElementById("lineItemsTableBody"),
  summarySubtotal: document.getElementById("summarySubtotal"),
  summaryTax: document.getElementById("summaryTax"),
  summaryGrandTotal: document.getElementById("summaryGrandTotal"),

  // HITL Review Bar
  reviewerNotesInput: document.getElementById("reviewerNotesInput"),
  hitlApproveBtn: document.getElementById("hitlApproveBtn"),
  hitlFlagBtn: document.getElementById("hitlFlagBtn"),
  hitlRejectBtn: document.getElementById("hitlRejectBtn"),

  // Ledger
  ledgerSearchInput: document.getElementById("ledgerSearchInput"),
  refreshLedgerBtn: document.getElementById("refreshLedgerBtn"),
  ledgerTableBody: document.getElementById("ledgerTableBody"),

  // Modals
  rawJsonModal: document.getElementById("rawJsonModal"),
  rawJsonCodeBlock: document.getElementById("rawJsonCodeBlock"),
  copyJsonBtn: document.getElementById("copyJsonBtn"),
  closeJsonModalBtn: document.getElementById("closeJsonModalBtn"),

  settingsModal: document.getElementById("settingsModal"),
  apiUrlInput: document.getElementById("apiUrlInput"),
  closeSettingsModalBtn: document.getElementById("closeSettingsModalBtn"),
  resetSettingsBtn: document.getElementById("resetSettingsBtn"),
  saveSettingsBtn: document.getElementById("saveSettingsBtn"),

  toastContainer: document.getElementById("toastContainer"),
};

// ============================================================================
// INITIALIZATION
// ============================================================================
document.addEventListener("DOMContentLoaded", () => {
  initLucideIcons();
  bindEventListeners();
  updateDemoModeUI();
  checkBackendHealth();
  fetchAuditMetrics();
  fetchAuditLedger();

  // Periodic health check
  setInterval(checkBackendHealth, 20000);
});

function initLucideIcons() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

// ============================================================================
// EVENT LISTENERS BINDING
// ============================================================================
function bindEventListeners() {
  // File upload drag & drop
  dom.dropZone.addEventListener("click", () => dom.fileInput.click());
  dom.dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dom.dropZone.classList.add("border-emerald-500", "bg-slate-900/90");
  });
  dom.dropZone.addEventListener("dragleave", () => {
    dom.dropZone.classList.remove("border-emerald-500", "bg-slate-900/90");
  });
  dom.dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dom.dropZone.classList.remove("border-emerald-500", "bg-slate-900/90");
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  dom.fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  });

  dom.clearFileBtn.addEventListener("click", () => clearSelectedFile());
  dom.auditDocBtn.addEventListener("click", () => executeDocumentAudit());
  dom.sampleInvoiceBtn.addEventListener("click", () => loadSampleDummyInvoice());

  // Copy buttons
  dom.copyThreadBtn.addEventListener("click", () => {
    const threadId = dom.threadIdDisplay.textContent;
    copyToClipboard(threadId, "Thread ID copied to clipboard!");
  });

  dom.copyJsonBtn.addEventListener("click", () => {
    if (state.rawJsonData) {
      copyToClipboard(JSON.stringify(state.rawJsonData, null, 2), "Raw JSON copied to clipboard!");
    }
  });

  // Modal toggles
  dom.openRawJsonBtn.addEventListener("click", () => openRawJsonModal());
  dom.closeJsonModalBtn.addEventListener("click", () => dom.rawJsonModal.classList.add("hidden"));
  dom.rawJsonModal.addEventListener("click", (e) => {
    if (e.target === dom.rawJsonModal) dom.rawJsonModal.classList.add("hidden");
  });

  dom.openSettingsBtn.addEventListener("click", () => {
    dom.apiUrlInput.value = state.apiBaseUrl;
    dom.settingsModal.classList.remove("hidden");
  });
  dom.closeSettingsModalBtn.addEventListener("click", () => dom.settingsModal.classList.add("hidden"));
  dom.settingsModal.addEventListener("click", (e) => {
    if (e.target === dom.settingsModal) dom.settingsModal.classList.add("hidden");
  });

  dom.resetSettingsBtn.addEventListener("click", () => {
    dom.apiUrlInput.value = "http://localhost:8000";
  });
  dom.saveSettingsBtn.addEventListener("click", () => saveSettings());

  // Demo toggle
  dom.demoToggleBtn.addEventListener("click", () => toggleDemoMode());

  // Error dismiss
  dom.dismissErrorBtn.addEventListener("click", () => dom.errorBanner.classList.add("hidden"));

  // HITL decision buttons
  dom.hitlApproveBtn.addEventListener("click", () => submitAuditorDecision("APPROVE"));
  dom.hitlFlagBtn.addEventListener("click", () => submitAuditorDecision("FLAG"));
  dom.hitlRejectBtn.addEventListener("click", () => submitAuditorDecision("REJECT"));

  // Ledger filters & search
  document.querySelectorAll(".ledger-filter-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".ledger-filter-btn").forEach((b) => {
        b.classList.remove("bg-slate-800", "text-slate-200", "font-medium");
        b.classList.add("text-slate-400");
      });
      btn.classList.add("bg-slate-800", "text-slate-200", "font-medium");
      btn.classList.remove("text-slate-400");
      state.ledgerFilter = btn.dataset.filter;
      fetchAuditLedger();
    });
  });

  dom.ledgerSearchInput.addEventListener("input", (e) => {
    state.ledgerSearch = e.target.value.trim().toLowerCase();
    fetchAuditLedger();
  });

  dom.refreshLedgerBtn.addEventListener("click", () => {
    fetchAuditLedger();
    fetchAuditMetrics();
    showToast("Audit ledger refreshed", "info");
  });
}

// ============================================================================
// FILE SELECTION & UPLOAD COCKPIT
// ============================================================================
function handleFileSelected(file) {
  // Validate file size (max 25MB)
  if (file.size > 25 * 1024 * 1024) {
    showToast("File exceeds maximum allowed size (25MB)", "error");
    return;
  }

  state.selectedFile = file;
  dom.selectedFileName.textContent = file.name;
  dom.selectedFileSize.textContent = formatBytes(file.size);

  dom.selectedFileCard.classList.remove("hidden");
  dom.auditDocBtn.disabled = false;
  initLucideIcons();
}

function clearSelectedFile() {
  state.selectedFile = null;
  dom.fileInput.value = "";
  dom.selectedFileCard.classList.add("hidden");
  dom.auditDocBtn.disabled = true;
  hidePipelineProgress();
}

async function loadSampleDummyInvoice() {
  showToast("Loading sample dummy invoice...", "info");
  try {
    const res = await fetch("/dummy_invoice.pdf");
    if (res.ok) {
      const blob = await res.blob();
      const file = new File([blob], "dummy_invoice.pdf", { type: "application/pdf" });
      handleFileSelected(file);
      showToast("Loaded dummy_invoice.pdf into Cockpit", "success");
      return;
    }
  } catch (e) {
    // Fallback if served separately
  }

  // Create virtual sample file
  const sampleContent = `
TAX INVOICE
Vendor: TechSupply Solutions Pvt Ltd
Invoice No: INV-2026-0891
Date: 26-Oct-2026
Cloud Infrastructure Setup 1 35000.00 35000.00
FastAPI Backend Optimization 2 15000.00 30000.00
Subtotal 65000.00
GST (18%) 11700.00
Grand Total 76700.00
  `;
  const file = new File([sampleContent], "sample_invoice.txt", { type: "text/plain" });
  handleFileSelected(file);
  showToast("Loaded sample invoice into Cockpit", "success");
}

// ============================================================================
// PIPELINE EXECUTION & AUDITING
// ============================================================================
async function executeDocumentAudit() {
  if (!state.selectedFile) return;

  dom.auditDocBtn.disabled = true;
  showPipelineProgress();

  // If Demo Mode is active, simulate realistic pipeline
  if (state.demoMode) {
    await simulateAuditPipeline(state.selectedFile);
    return;
  }

  // Step 1: Uploading to S3
  updatePipelineStep(1, "1. Archiving immutable asset to S3...", 35);

  const formData = new FormData();
  formData.append("file", state.selectedFile);

  const endpoint = `${state.apiBaseUrl}/api/v1/invoices/process`;

  try {
    // Step 2: OCR Extraction
    setTimeout(() => {
      updatePipelineStep(2, "2. Running OCR & In-Memory Text Extraction...", 70);
    }, 600);

    // Step 3: Rules & StateGraph
    setTimeout(() => {
      updatePipelineStep(3, "3. Evaluating Deterministic Rules in LangGraph...", 90);
    }, 1300);

    const response = await fetch(endpoint, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Server returned HTTP ${response.status}`);
    }

    const data = await response.json();
    state.rawJsonData = data;
    state.activeDocument = data;

    // Conclude progress bar
    updatePipelineStep(3, "Audit Complete!", 100);
    setTimeout(() => {
      renderActiveAuditView(data);
      hidePipelineProgress();
      dom.auditDocBtn.disabled = false;
      fetchAuditMetrics();
      fetchAuditLedger();
      showToast(`Document audited: ${data.status}`, data.status === "APPROVED" ? "success" : "warning");
    }, 600);

  } catch (error) {
    loggerError("Audit execution failed", error);
    hidePipelineProgress();
    dom.auditDocBtn.disabled = false;
    showErrorBanner(
      "Audit Pipeline Failure",
      `${error.message}. Verify that the backend is active at ${state.apiBaseUrl} or enable Demo Mode.`
    );
    showToast(`Audit failed: ${error.message}`, "error");
  }
}

// Multi-step progress animation helper
function showPipelineProgress() {
  dom.pipelineProgressContainer.classList.remove("hidden");
  dom.pipelineProgressBar.style.width = "10%";
  resetPipelineSteps();
}

function hidePipelineProgress() {
  dom.pipelineProgressContainer.classList.add("hidden");
}

function resetPipelineSteps() {
  [dom.stepS3, dom.stepOCR, dom.stepRules].forEach((el) => {
    el.classList.remove("step-complete", "step-in-progress");
    el.classList.add("text-slate-400");
  });
}

function updatePipelineStep(stepNumber, title, percent) {
  dom.pipelineStepTitle.textContent = title;
  dom.pipelineStepPercent.textContent = `${percent}%`;
  dom.pipelineProgressBar.style.width = `${percent}%`;

  if (stepNumber >= 1) {
    dom.stepS3.classList.add("step-complete");
    dom.stepS3.querySelector(".step-icon").setAttribute("data-lucide", "check-circle");
  }
  if (stepNumber >= 2) {
    dom.stepOCR.classList.add("step-complete");
    dom.stepOCR.querySelector(".step-icon").setAttribute("data-lucide", "check-circle");
  }
  if (stepNumber >= 3) {
    dom.stepRules.classList.add("step-complete");
    dom.stepRules.querySelector(".step-icon").setAttribute("data-lucide", "check-circle");
  }
  initLucideIcons();
}

// ============================================================================
// ACTIVE AUDIT INSPECTION VIEW RENDERING
// ============================================================================
function renderActiveAuditView(doc) {
  dom.auditEmptyState.classList.add("hidden");
  dom.auditActiveState.classList.remove("hidden");

  // Title & Status
  dom.docTitle.textContent = doc.filename || "Uploaded Document";
  dom.threadIdDisplay.textContent = doc.thread_id || "doc_unknown";
  dom.s3UriDisplay.textContent = doc.s3_uri || `s3://docaudit-storage/documents/${doc.filename}`;

  const status = doc.status || "APPROVED";
  dom.statusBadgeText.textContent = status.replace("_", " ");
  dom.auditStatusBadge.className = "px-2.5 py-0.5 rounded-full text-xs font-bold border flex items-center space-x-1 ";

  if (status === "APPROVED") {
    dom.auditStatusBadge.classList.add("badge-approved");
  } else if (status === "PENDING_REVIEW" || status === "FLAGGED") {
    dom.auditStatusBadge.classList.add("badge-pending");
  } else {
    dom.auditStatusBadge.classList.add("badge-rejected");
  }

  // Metadata Grid
  dom.metaVendor.textContent = doc.vendor_name || "Unknown Vendor";
  dom.metaInvoiceNo.textContent = doc.invoice_number || "N/A";
  dom.metaDate.textContent = doc.invoice_date || doc.created_at?.split("T")[0] || new Date().toISOString().split("T")[0];
  dom.metaDueDate.textContent = doc.due_date || "Net 30 Days";

  // Discrepancies Banner
  const discrepancies = doc.discrepancies || [];
  if (discrepancies.length > 0) {
    dom.discrepancyBanner.classList.remove("hidden");
    dom.discrepancyCountText.textContent = `${discrepancies.length} Accounting Rule Violation${discrepancies.length > 1 ? "s" : ""} Flagged`;
    dom.discrepancyList.innerHTML = discrepancies
      .map((d) => `<li><strong>[${d.discrepancy_type || "DISCREPANCY"}]:</strong> ${escapeHtml(d.message)}</li>`)
      .join("");
  } else {
    dom.discrepancyBanner.classList.add("hidden");
  }

  // Checklist 4 Pillars evaluation
  updateChecklistStatus(discrepancies);

  // Line items rendering
  renderLineItems(doc);

  // Totals Breakdown
  const subtotalVal = doc.subtotal !== undefined && doc.subtotal !== null ? Number(doc.subtotal) : 0;
  const taxVal = doc.tax_amount !== undefined && doc.tax_amount !== null ? Number(doc.tax_amount) : 0;
  const grandTotalVal = doc.grand_total !== undefined && doc.grand_total !== null ? Number(doc.grand_total) : (subtotalVal + taxVal);
  const currency = doc.currency || "USD";

  dom.summarySubtotal.textContent = formatCurrency(subtotalVal, currency);
  dom.summaryTax.textContent = formatCurrency(taxVal, currency);
  dom.summaryGrandTotal.textContent = formatCurrency(grandTotalVal, currency);

  initLucideIcons();
}

function updateChecklistStatus(discrepancies) {
  const types = discrepancies.map((d) => d.discrepancy_type);

  // Math Balance
  const mathOk = !types.includes("SUBTOTAL_MISMATCH");
  renderCheckPillar(dom.checkMath, mathOk, "Math Balance", "Σ(Items) = Subtotal");

  // Tax Check
  const taxOk = !types.includes("GRAND_TOTAL_MISMATCH");
  renderCheckPillar(dom.checkTax, taxOk, "Tax Parity", "Subtotal + Tax = Total");

  // Date Check
  const dateOk = !types.includes("FUTURE_DATE") && !types.includes("STALE_DATE");
  renderCheckPillar(dom.checkDate, dateOk, "Date Freshness", "< 180 Days, Not Future");

  // Item Check
  const itemsOk = !types.includes("INVALID_QUANTITY") && !types.includes("NEGATIVE_PRICE") && !types.includes("LINE_ITEM_CALCULATION_MISMATCH");
  renderCheckPillar(dom.checkItems, itemsOk, "Item Integrity", "Qty > 0 & Price ≥ 0");
}

function renderCheckPillar(element, isOk, title, desc) {
  const icon = element.querySelector(".check-icon");
  const titleSpan = element.querySelector("span");

  if (isOk) {
    element.className = "p-2.5 rounded-lg border border-emerald-500/20 bg-emerald-950/20 text-xs";
    titleSpan.className = "font-medium text-[11px] text-emerald-400";
    titleSpan.textContent = title;
    icon.setAttribute("data-lucide", "check");
    icon.className = "w-3.5 h-3.5 text-emerald-400 check-icon";
  } else {
    element.className = "p-2.5 rounded-lg border border-amber-500/30 bg-amber-950/30 text-xs";
    titleSpan.className = "font-medium text-[11px] text-amber-400";
    titleSpan.textContent = `${title} Failed`;
    icon.setAttribute("data-lucide", "alert-circle");
    icon.className = "w-3.5 h-3.5 text-amber-400 check-icon";
  }
}

function renderLineItems(doc) {
  const items = doc.line_items || [];
  const currency = doc.currency || "USD";

  if (items.length === 0) {
    // Generate default breakdown row if raw array wasn't passed in minimal status response
    const grand = doc.grand_total || doc.subtotal || 0;
    dom.lineItemsTableBody.innerHTML = `
      <tr>
        <td class="py-2.5 px-3 text-slate-300 font-sans">General Invoiced Services / Items</td>
        <td class="py-2.5 px-3 text-right">1</td>
        <td class="py-2.5 px-3 text-right">${formatCurrency(grand, currency)}</td>
        <td class="py-2.5 px-3 text-right font-semibold text-slate-100">${formatCurrency(grand, currency)}</td>
      </tr>
    `;
    return;
  }

  dom.lineItemsTableBody.innerHTML = items
    .map((item) => {
      const q = Number(item.quantity || 1);
      const p = Number(item.unit_price || 0);
      const t = Number(item.total_price || (q * p));
      return `
        <tr class="hover:bg-slate-900/60 transition-colors">
          <td class="py-2 px-3 text-slate-200 font-sans">${escapeHtml(item.description || "Line Item")}</td>
          <td class="py-2 px-3 text-right text-slate-400">${q}</td>
          <td class="py-2 px-3 text-right text-slate-400">${formatCurrency(p, currency)}</td>
          <td class="py-2 px-3 text-right font-semibold text-slate-100">${formatCurrency(t, currency)}</td>
        </tr>
      `;
    })
    .join("");
}

// ============================================================================
// HITL REVIEW DECISION RESOLUTION
// ============================================================================
async function submitAuditorDecision(action) {
  if (!state.activeDocument || !state.activeDocument.thread_id) {
    showToast("No active document selected for review", "warning");
    return;
  }

  const threadId = state.activeDocument.thread_id;
  const notes = dom.reviewerNotesInput.value.trim() || `Auditor ${action.toLowerCase()}ed record.`;

  showToast(`Submitting ${action} decision...`, "info");

  // In Demo Mode
  if (state.demoMode) {
    state.activeDocument.status = action === "APPROVE" ? "APPROVED" : (action === "FLAG" ? "PENDING_REVIEW" : "REJECTED");
    state.activeDocument.reviewer_decision = action;
    state.activeDocument.reviewer_notes = notes;
    renderActiveAuditView(state.activeDocument);
    updateLedgerItemInStorage(state.activeDocument);
    fetchAuditLedger();
    fetchAuditMetrics();
    showToast(`Invoice successfully marked as ${state.activeDocument.status}`, "success");
    return;
  }

  try {
    const res = await fetch(`${state.apiBaseUrl}/api/v1/invoices/review/${threadId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: action === "FLAG" ? "REJECT" : action,
        reviewer_notes: notes,
      }),
    });

    if (!res.ok) {
      throw new Error(`Review submission failed: ${res.statusText}`);
    }

    const updated = await res.json();
    state.activeDocument.status = updated.status;
    state.activeDocument.reviewer_decision = updated.reviewer_decision;
    state.activeDocument.reviewer_notes = updated.reviewer_notes;

    renderActiveAuditView(state.activeDocument);
    fetchAuditLedger();
    fetchAuditMetrics();
    showToast(`Audit resolution posted: ${updated.status}`, "success");

  } catch (err) {
    showToast(`Failed to submit review: ${err.message}`, "error");
  }
}

// ============================================================================
// HISTORICAL AUDIT LEDGER
// ============================================================================
async function fetchAuditLedger() {
  if (state.demoMode) {
    renderLedgerTable(filterLedgerRecords(state.localLedgerCache));
    return;
  }

  try {
    let url = `${state.apiBaseUrl}/api/v1/invoices/ledger`;
    const params = new URLSearchParams();
    if (state.ledgerFilter && state.ledgerFilter !== "ALL") {
      params.append("status", state.ledgerFilter);
    }
    if (state.ledgerSearch) {
      params.append("search", state.ledgerSearch);
    }
    if (params.toString()) {
      url += `?${params.toString()}`;
    }

    const res = await fetch(url);
    if (res.ok) {
      const records = await res.json();
      renderLedgerTable(records);
      return;
    }
  } catch (e) {
    // Fallback to local cache
  }

  // Fallback to local cache if offline or error
  renderLedgerTable(filterLedgerRecords(state.localLedgerCache));
}

function filterLedgerRecords(records) {
  return records.filter((r) => {
    const matchesFilter = state.ledgerFilter === "ALL" || r.status === state.ledgerFilter;
    const s = state.ledgerSearch;
    const matchesSearch =
      !s ||
      (r.vendor_name && r.vendor_name.toLowerCase().includes(s)) ||
      (r.invoice_number && r.invoice_number.toLowerCase().includes(s)) ||
      (r.thread_id && r.thread_id.toLowerCase().includes(s));
    return matchesFilter && matchesSearch;
  });
}

function renderLedgerTable(records) {
  if (!records || records.length === 0) {
    dom.ledgerTableBody.innerHTML = `
      <tr>
        <td colspan="7" class="py-8 text-center text-slate-500 font-sans">
          No audit records found matching current criteria.
        </td>
      </tr>
    `;
    return;
  }

  dom.ledgerTableBody.innerHTML = records
    .map((r) => {
      const status = r.status || "APPROVED";
      let badgeClass = "badge-approved";
      if (status === "PENDING_REVIEW" || status === "FLAGGED") badgeClass = "badge-pending";
      if (status === "REJECTED") badgeClass = "badge-rejected";

      const total = Number(r.grand_total || r.subtotal || 0);
      const dateStr = r.created_at ? new Date(r.created_at).toLocaleDateString() : new Date().toLocaleDateString();

      return `
        <tr class="hover:bg-slate-900/50 transition-colors">
          <td class="py-2.5 px-3">
            <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${badgeClass}">
              ${status.replace("_", " ")}
            </span>
          </td>
          <td class="py-2.5 px-3 font-semibold text-slate-200">${escapeHtml(r.invoice_number || "INV-NEW")}</td>
          <td class="py-2.5 px-3 font-sans text-slate-300 truncate max-w-[140px]">${escapeHtml(r.vendor_name || "Unknown Vendor")}</td>
          <td class="py-2.5 px-3 text-right font-bold text-slate-100">${formatCurrency(total, r.currency || "USD")}</td>
          <td class="py-2.5 px-3 text-slate-500 text-[11px]">${escapeHtml(r.thread_id || "-")}</td>
          <td class="py-2.5 px-3 text-slate-400 font-sans text-[11px]">${dateStr}</td>
          <td class="py-2.5 px-3 text-center">
            <button onclick="inspectLedgerItem('${r.thread_id}')" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-[11px] text-emerald-400 border border-slate-700 transition-colors">
              Inspect
            </button>
          </td>
        </tr>
      `;
    })
    .join("");
}

window.inspectLedgerItem = async function (threadId) {
  showToast(`Loading document ${threadId}...`, "info");
  try {
    const res = await fetch(`${state.apiBaseUrl}/api/v1/invoices/status/${threadId}`);
    if (res.ok) {
      const doc = await res.json();
      state.activeDocument = doc;
      state.rawJsonData = doc;
      renderActiveAuditView(doc);
      window.scrollTo({ top: 320, behavior: "smooth" });
      return;
    }
  } catch (e) {
    // Check local cache
  }

  const cached = state.localLedgerCache.find((r) => r.thread_id === threadId);
  if (cached) {
    state.activeDocument = cached;
    state.rawJsonData = cached;
    renderActiveAuditView(cached);
    window.scrollTo({ top: 320, behavior: "smooth" });
  } else {
    showToast(`Could not find document details for ${threadId}`, "error");
  }
};

function updateLedgerItemInStorage(doc) {
  const existingIdx = state.localLedgerCache.findIndex((r) => r.thread_id === doc.thread_id);
  if (existingIdx !== -1) {
    state.localLedgerCache[existingIdx] = doc;
  } else {
    state.localLedgerCache.unshift(doc);
  }
  localStorage.setItem("docaudit_ledger_cache", JSON.stringify(state.localLedgerCache));
}

// ============================================================================
// SYSTEM HEALTH & METRICS
// ============================================================================
async function checkBackendHealth() {
  if (state.demoMode) {
    setSystemStatus(true, "DEMO SIMULATOR ACTIVE");
    return;
  }

  try {
    const res = await fetch(`${state.apiBaseUrl}/health`, { method: "GET" });
    if (res.ok) {
      const data = await res.json();
      setSystemStatus(true, `API CONNECTED (${data.version || "v1.0"})`);
      dom.errorBanner.classList.add("hidden");
    } else {
      setSystemStatus(false, "API DEGRADED");
    }
  } catch (e) {
    setSystemStatus(false, "API OFFLINE");
  }
}

function setSystemStatus(isOnline, text) {
  dom.statusText.textContent = text;
  if (isOnline) {
    dom.statusDot.className = "relative inline-flex rounded-full h-2 w-2 bg-emerald-500";
    dom.statusPing.className = "animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75";
  } else {
    dom.statusDot.className = "relative inline-flex rounded-full h-2 w-2 bg-amber-500";
    dom.statusPing.className = "hidden";
  }
}

async function fetchAuditMetrics() {
  if (state.demoMode) {
    const docs = state.localLedgerCache;
    const totalDocs = docs.length;
    const approved = docs.filter((d) => d.status === "APPROVED").length;
    const pending = docs.filter((d) => d.status === "PENDING_REVIEW").length;
    const sumCapital = docs.reduce((acc, d) => acc + (d.grand_total || d.subtotal || 0), 0);

    dom.kpiTotalDocs.textContent = totalDocs;
    dom.kpiApproved.textContent = approved;
    dom.kpiPending.textContent = pending;
    dom.kpiTotalCapital.textContent = formatCurrency(sumCapital, "USD");
    return;
  }

  try {
    const res = await fetch(`${state.apiBaseUrl}/api/v1/invoices/metrics`);
    if (res.ok) {
      const m = await res.json();
      dom.kpiTotalDocs.textContent = m.total_documents || 0;
      dom.kpiApproved.textContent = m.approved_count || 0;
      dom.kpiPending.textContent = m.pending_review_count || 0;
      dom.kpiTotalCapital.textContent = formatCurrency(m.total_audited_amount_usd || 0, "USD");
    }
  } catch (e) {
    loggerError("Metrics poll failed", e);
  }
}

// ============================================================================
// SIMULATION & DEMO MODE
// ============================================================================
function toggleDemoMode() {
  state.demoMode = !state.demoMode;
  localStorage.setItem("docaudit_demo_mode", state.demoMode);
  updateDemoModeUI();
  checkBackendHealth();
  fetchAuditMetrics();
  fetchAuditLedger();
  showToast(state.demoMode ? "Demo Mode Enabled (Simulated Data)" : "Demo Mode Disabled (Live API)", "info");
}

function updateDemoModeUI() {
  if (state.demoMode) {
    dom.demoModeLabel.textContent = "Demo ON";
    dom.demoToggleBtn.classList.add("border-amber-500/50", "text-amber-300", "bg-amber-950/40");
  } else {
    dom.demoModeLabel.textContent = "Demo Off";
    dom.demoToggleBtn.classList.remove("border-amber-500/50", "text-amber-300", "bg-amber-950/40");
  }
}

async function simulateAuditPipeline(file) {
  updatePipelineStep(1, "1. Simulating S3 Storage Archival...", 35);
  await delay(400);

  updatePipelineStep(2, "2. Simulating Textract OCR Extraction...", 70);
  await delay(500);

  updatePipelineStep(3, "3. Running Deterministic Math Audit...", 100);
  await delay(400);

  const isDiscrepant = file.name.includes("faulty") || file.name.includes("error");
  const threadId = `sim_${Math.random().toString(16).substring(2, 10)}`;

  const simulatedDoc = {
    thread_id: threadId,
    filename: file.name,
    s3_uri: `s3://docaudit-demo-bucket/documents/${file.name}`,
    status: isDiscrepant ? "PENDING_REVIEW" : "APPROVED",
    vendor_name: isDiscrepant ? "Faulty Ledger Corp" : "TechSupply Solutions Pvt Ltd",
    invoice_number: isDiscrepant ? "INV-ERR-992" : "INV-2026-0891",
    invoice_date: new Date().toISOString().split("T")[0],
    due_date: new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0],
    subtotal: isDiscrepant ? 350.0 : 65000.0,
    tax_amount: isDiscrepant ? 20.0 : 11700.0,
    grand_total: isDiscrepant ? 500.0 : 76700.0,
    currency: isDiscrepant ? "USD" : "INR",
    discrepancies: isDiscrepant
      ? [
          {
            discrepancy_type: "SUBTOTAL_MISMATCH",
            message: "Sum of line items (200.00) does not match declared subtotal (350.00)",
            expected_value: 200.0,
            actual_value: 350.0,
            field_name: "subtotal",
          },
          {
            discrepancy_type: "GRAND_TOTAL_MISMATCH",
            message: "Subtotal (350.00) + Tax (20.00) = 370.00, which does not match declared grand total (500.00)",
            expected_value: 370.0,
            actual_value: 500.0,
            field_name: "grand_total",
          },
        ]
      : [],
    line_items: isDiscrepant
      ? [
          { description: "Industrial Relay A", quantity: 1, unit_price: 100.0, total_price: 100.0 },
          { description: "Relay Controller Unit", quantity: 2, unit_price: 50.0, total_price: 100.0 },
        ]
      : [
          { description: "Cloud Infrastructure Setup", quantity: 1, unit_price: 35000.0, total_price: 35000.0 },
          { description: "FastAPI Backend Optimization", quantity: 2, unit_price: 15000.0, total_price: 30000.0 },
        ],
    created_at: new Date().toISOString(),
  };

  state.activeDocument = simulatedDoc;
  state.rawJsonData = simulatedDoc;
  updateLedgerItemInStorage(simulatedDoc);

  renderActiveAuditView(simulatedDoc);
  hidePipelineProgress();
  dom.auditDocBtn.disabled = false;
  fetchAuditMetrics();
  fetchAuditLedger();
  showToast(`Simulated audit complete: ${simulatedDoc.status}`, simulatedDoc.status === "APPROVED" ? "success" : "warning");
}

// ============================================================================
// MODALS & SETTINGS
// ============================================================================
function openRawJsonModal() {
  if (!state.rawJsonData) {
    showToast("No active JSON response available", "warning");
    return;
  }
  dom.rawJsonCodeBlock.textContent = JSON.stringify(state.rawJsonData, null, 2);
  dom.rawJsonModal.classList.remove("hidden");
}

function saveSettings() {
  const newUrl = dom.apiUrlInput.value.trim().replace(/\/+$/, "");
  if (!newUrl) {
    showToast("Please enter a valid API URL", "error");
    return;
  }
  state.apiBaseUrl = newUrl;
  localStorage.setItem("docaudit_api_url", newUrl);
  dom.settingsModal.classList.add("hidden");
  showToast(`API URL updated: ${newUrl}`, "success");
  checkBackendHealth();
  fetchAuditMetrics();
  fetchAuditLedger();
}

// ============================================================================
// TOAST NOTIFICATIONS & UTILITIES
// ============================================================================
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = "toast-enter flex items-center space-x-2 px-3.5 py-2.5 rounded-lg border text-xs shadow-xl backdrop-blur-md ";

  if (type === "success") {
    toast.className += "bg-emerald-950/90 border-emerald-500/40 text-emerald-200";
    toast.innerHTML = `<i data-lucide="check-circle" class="w-4 h-4 text-emerald-400"></i><span>${escapeHtml(message)}</span>`;
  } else if (type === "error") {
    toast.className += "bg-rose-950/90 border-rose-500/40 text-rose-200";
    toast.innerHTML = `<i data-lucide="alert-octagon" class="w-4 h-4 text-rose-400"></i><span>${escapeHtml(message)}</span>`;
  } else if (type === "warning") {
    toast.className += "bg-amber-950/90 border-amber-500/40 text-amber-200";
    toast.innerHTML = `<i data-lucide="alert-triangle" class="w-4 h-4 text-amber-400"></i><span>${escapeHtml(message)}</span>`;
  } else {
    toast.className += "bg-slate-900/90 border-slate-700 text-slate-200";
    toast.innerHTML = `<i data-lucide="info" class="w-4 h-4 text-sky-400"></i><span>${escapeHtml(message)}</span>`;
  }

  dom.toastContainer.appendChild(toast);
  initLucideIcons();

  setTimeout(() => {
    toast.classList.remove("toast-enter");
    toast.classList.add("toast-exit");
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

function showErrorBanner(title, desc) {
  dom.errorBannerTitle.textContent = title;
  dom.errorBannerDesc.textContent = desc;
  dom.errorBanner.classList.remove("hidden");
}

function copyToClipboard(text, successMsg = "Copied to clipboard!") {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => showToast(successMsg, "success"));
  } else {
    const el = document.createElement("textarea");
    el.value = text;
    document.body.appendChild(el);
    el.select();
    document.execCommand("copy");
    document.body.removeChild(el);
    showToast(successMsg, "success");
  }
}

function formatCurrency(amount, currency = "USD") {
  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency || "USD",
      minimumFractionDigits: 2,
    }).format(amount);
  } catch (e) {
    return `$${Number(amount).toFixed(2)}`;
  }
}

function formatBytes(bytes) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function loggerError(msg, err) {
  console.error(`[DocAudit Client] ${msg}:`, err);
}
