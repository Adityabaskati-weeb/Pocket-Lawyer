const SAMPLE_TEXT = {
  employment: `All intellectual property created during employment, including outside work hours and side projects, belongs to the employer.

The employee agrees to a non-compete for 24 months after employment and cannot work in the same technology sector.

The company may revise or reduce salary with seven days notice.

Either party may terminate this agreement by giving 30 days notice.`,
  freelancer: `The freelancer assigns all rights and intellectual property to the client immediately before payment.

The client may request unlimited revisions until fully satisfied.

Payment is due within 15 days of each approved milestone invoice.`,
  rent: `This is an 11-month rent agreement.

The landlord may retain the security deposit at sole discretion and enter the premises without notice.

Early termination during lock-in requires the tenant to pay remaining rent for the entire term.`,
  nda: `All information shared by the company is confidential forever with no exceptions.

The recipient shall not use general knowledge, skills, or experience learned during discussions.

Disclosure required by law is permitted after notice.`,
  vendor: `The vendor has unlimited liability for all losses including indirect and consequential losses.

The customer may change the scope without additional charges.

Invoices are paid within 30 days.`,
  loan: `The borrower shall provide a blank cheque as security.

The lender may increase the interest rate at its sole discretion without consent.

The EMI schedule is attached as Annexure A.`,
};

const form = document.querySelector("#scan-form");
const contractType = document.querySelector("#contract-type");
const contractPills = document.querySelectorAll(".contract-pill");
const textarea = document.querySelector("#contract-text");
const fileInput = document.querySelector("#contract-file");
const uploadZone = document.querySelector("#upload-zone");
const scanButton = document.querySelector("#scan-button");
const sampleButton = document.querySelector("#sample-button");
const statusPill = document.querySelector("#status-pill");
const emptyState = document.querySelector("#empty-state");
const reportContent = document.querySelector("#report-content");
const overallRisk = document.querySelector("#overall-risk");
const scoreNumber = document.querySelector("#score-number");
const scoreFill = document.querySelector("#score-fill");
const summary = document.querySelector("#summary");
const redCount = document.querySelector("#red-count");
const yellowCount = document.querySelector("#yellow-count");
const greenCount = document.querySelector("#green-count");
const findingsContainer = document.querySelector("#findings");
const negotiationScript = document.querySelector("#negotiation-script");
const copyScript = document.querySelector("#copy-script");
const disclaimer = document.querySelector("#disclaimer");
const refreshHistory = document.querySelector("#refresh-history");
const historyList = document.querySelector("#history-list");
const SCORE_CIRCUMFERENCE = 326.73;

syncContractPills();

sampleButton.addEventListener("click", () => {
  textarea.value = SAMPLE_TEXT[contractType.value] || SAMPLE_TEXT.employment;
  textarea.focus();
});

contractType.addEventListener("change", () => {
  syncContractPills();
  textarea.value = SAMPLE_TEXT[contractType.value] || SAMPLE_TEXT.employment;
});

contractPills.forEach((pill) => {
  pill.addEventListener("click", () => {
    contractType.value = pill.dataset.contractType;
    contractType.dispatchEvent(new Event("change"));
  });
});

["dragenter", "dragover"].forEach((eventName) => {
  uploadZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    uploadZone.classList.add("drag-over");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  uploadZone.addEventListener(eventName, () => {
    uploadZone.classList.remove("drag-over");
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const text = textarea.value.trim();
  const file = fileInput.files[0];
  if (!text && !file) {
    setStatus("Paste contract text first", "error");
    return;
  }

  setStatus("Scanning", "loading");
  setScanButtonState("loading");

  try {
    const body = file
      ? await buildFilePayload(file)
      : { text, source_name: "Pasted contract", contract_type: contractType.value };

    const response = await fetch("/contracts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Unable to analyze contract.");
    }

    renderReport(payload.report);
    setStatus("Saved", payload.report.overall_risk_level);
    setScanButtonState("success");
    await loadHistory();
  } catch (error) {
    setStatus("Scan failed", "error");
    setScanButtonState("idle");
    emptyState.classList.remove("hidden");
    reportContent.classList.add("hidden");
  }
});

refreshHistory.addEventListener("click", loadHistory);

copyScript.addEventListener("click", async () => {
  const text = negotiationScript.textContent.trim();
  if (!text) return;

  try {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(text);
    }
  } catch (error) {
    return;
  }

  copyScript.textContent = "✓ Copied";
  copyScript.classList.add("copied");
  window.setTimeout(() => {
    copyScript.textContent = "Copy message";
    copyScript.classList.remove("copied");
  }, 1400);
});

loadHistory();

function renderReport(report) {
  emptyState.classList.add("hidden");
  reportContent.classList.remove("hidden");

  overallRisk.textContent = titleCase(report.overall_risk_level);
  animateScore(report.overall_risk_score, report.overall_risk_level);
  summary.textContent = report.summary;
  negotiationScript.textContent = report.negotiation_script;
  disclaimer.textContent = report.disclaimer;

  const counts = countFindings(report.findings);
  animateNumber(redCount, counts.red);
  animateNumber(yellowCount, counts.yellow);
  animateNumber(greenCount, counts.green);

  findingsContainer.replaceChildren(
    ...report.findings.map((finding) => createFindingCard(finding))
  );
}

function createFindingCard(finding) {
  const article = document.createElement("article");
  article.className = `finding ${finding.risk_level}`;

  const tag = document.createElement("p");
  tag.className = "finding-tag";
  tag.textContent = `${finding.risk_level} / ${finding.category.replaceAll("_", " ")}`;

  const title = document.createElement("h2");
  title.textContent = finding.title;

  const original = document.createElement("blockquote");
  original.textContent = finding.original_text;

  const summary = document.createElement("p");
  summary.textContent = finding.plain_language_summary;

  const replacement = document.createElement("p");
  replacement.className = "replacement";
  replacement.textContent = `Ask for: ${finding.suggested_replacement}`;

  article.append(tag, title, original, summary, replacement);
  return article;
}

function syncContractPills() {
  contractPills.forEach((pill) => {
    const isActive = pill.dataset.contractType === contractType.value;
    pill.classList.toggle("active", isActive);
    pill.setAttribute("aria-pressed", String(isActive));
  });
}

function setScanButtonState(state) {
  scanButton.classList.remove("loading", "success");

  if (state === "loading") {
    scanButton.classList.add("loading");
    scanButton.textContent = "Scanning";
    return;
  }

  if (state === "success") {
    scanButton.classList.add("success");
    scanButton.textContent = "Saved ✓";
    window.setTimeout(() => setScanButtonState("idle"), 1400);
    return;
  }

  scanButton.textContent = "Scan contract";
}

function animateScore(target, level) {
  const score = Math.max(0, Math.min(100, Number(target) || 0));
  const offset = SCORE_CIRCUMFERENCE - (SCORE_CIRCUMFERENCE * score) / 100;

  scoreFill.setAttribute("class", `score-fill ${level}`);
  scoreFill.style.strokeDashoffset = SCORE_CIRCUMFERENCE;

  window.requestAnimationFrame(() => {
    scoreFill.style.strokeDashoffset = offset;
  });

  animateNumber(scoreNumber, score, "%");
}

function animateNumber(element, target, suffix = "") {
  const finalValue = Number(target) || 0;
  const duration = 800;
  const startedAt = performance.now();

  function tick(now) {
    const progress = Math.min(1, (now - startedAt) / duration);
    const eased = 1 - Math.pow(1 - progress, 3);
    element.textContent = `${Math.round(finalValue * eased)}${suffix}`;

    if (progress < 1) {
      window.requestAnimationFrame(tick);
    }
  }

  window.requestAnimationFrame(tick);
}

async function buildFilePayload(file) {
  const contentBase64 = await readAsBase64(file);
  return {
    filename: file.name,
    content_base64: contentBase64,
    contract_type: contractType.value,
  };
}

function readAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.addEventListener("load", () => {
      const result = String(reader.result || "");
      resolve(result.split(",").pop());
    });
    reader.addEventListener("error", () => reject(reader.error));
    reader.readAsDataURL(file);
  });
}

async function loadHistory() {
  try {
    const response = await fetch("/contracts");
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Unable to load history.");
    renderHistory(payload.contracts || []);
  } catch (error) {
    historyList.textContent = "Recent scans unavailable.";
  }
}

function renderHistory(contracts) {
  historyList.replaceChildren();

  if (!contracts.length) {
    const empty = document.createElement("p");
    empty.className = "history-empty";
    empty.textContent = "Saved scans will appear here.";
    historyList.append(empty);
    return;
  }

  contracts.slice(0, 6).forEach((contract) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `history-item ${contract.overall_risk_level}`;
    button.innerHTML = `
      <span>${escapeHtml(contract.source_name)}</span>
      <strong>${contract.overall_risk_score}/100</strong>
    `;
    button.addEventListener("click", async () => {
      await openSavedReport(contract.id);
    });
    historyList.append(button);
  });
}

async function openSavedReport(id) {
  const response = await fetch(`/contracts/${id}`);
  const payload = await response.json();
  if (!response.ok) {
    setStatus("Load failed", "error");
    return;
  }

  renderReport(payload.report);
  setStatus("Loaded", payload.overall_risk_level);
}

function countFindings(findings) {
  return findings.reduce(
    (counts, finding) => {
      counts[finding.risk_level] += 1;
      return counts;
    },
    { red: 0, yellow: 0, green: 0 }
  );
}

function setStatus(label, level) {
  statusPill.textContent = label;
  statusPill.className = `status-pill ${level}`;
}

function titleCase(value) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
