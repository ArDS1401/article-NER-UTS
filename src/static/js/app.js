document.addEventListener("DOMContentLoaded", function () {
  let currentResponseData = null;
  let activeLabelFilter = "ALL";
  let submittedText = "";
  let highlightMode = 2;

  const MODES = [
    { mode: 0, label: "Highlight: Off", className: "highlight-mode-0" },
    { mode: 1, label: "Highlight: Mode 1 (Underline)", className: "highlight-mode-1" },
    { mode: 2, label: "Highlight: Mode 2 (Badges)", className: "highlight-mode-2" }
  ];

  const titleInput = document.getElementById("titleInput");
  const bodyInput = document.getElementById("bodyInput");
  const titleCount = document.getElementById("titleCount");
  const bodyCount = document.getElementById("bodyCount");
  const submitBtn = document.getElementById("submitBtn");
  const btnText = document.getElementById("btnText");
  const spinner = document.getElementById("btnSpinner");
  const clearBtn = document.getElementById("clearBtn");
  const loadSampleBtn = document.getElementById("loadSampleBtn");
  const copyJsonBtn = document.getElementById("copyJsonBtn");
  const exportJsonBtn = document.getElementById("exportJsonBtn");
  const alertBox = document.getElementById("statusAlert");
  const emptyState = document.getElementById("emptyState");
  const resultsContainer = document.getElementById("resultsContainer");
  const tableBody = document.getElementById("entitiesTableBody");
  const metaCount = document.getElementById("metaCount");
  const metaModel = document.getElementById("metaModel");
  const filterPills = document.getElementById("filterPills");
  const annotatedText = document.getElementById("annotatedText");
  const highlightToggleBtn = document.getElementById("highlightToggleBtn");

  function updateCharCounts() {
    titleCount.textContent = `${titleInput.value.length} / 10000`;
    bodyCount.textContent = `${bodyInput.value.length} / 10000`;
  }

  function showAlert(msg) {
    alertBox.textContent = msg;
    alertBox.style.display = "block";
  }

  function hideAlert() {
    alertBox.style.display = "none";
    alertBox.textContent = "";
  }

  function getTagKey(label) {
    const n = (label || "").toUpperCase();
    if (n.includes("PER")) return "PER";
    if (n.includes("ORG")) return "ORG";
    if (n.includes("LOC")) return "LOC";
    if (n.includes("GPE")) return "GPE";
    if (n.includes("MISC")) return "MISC";
    return "DEFAULT";
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function cycleHighlightMode() {
    highlightMode = (highlightMode + 1) % MODES.length;
    applyHighlightMode();
  }

  function applyHighlightMode() {
    const current = MODES[highlightMode];
    MODES.forEach(m => annotatedText.classList.remove(m.className));
    annotatedText.classList.add(current.className);
    highlightToggleBtn.textContent = current.label;
  }

  function renderFilters(entities) {
    filterPills.innerHTML = "";
    const counts = {};
    for (let i = 0; i < entities.length; i++) {
      const lbl = entities[i].label;
      counts[lbl] = (counts[lbl] || 0) + 1;
    }

    const labels = Object.keys(counts);
    if (labels.length <= 1) return;

    const allPill = document.createElement("button");
    allPill.type = "button";
    allPill.className = `pill${activeLabelFilter === "ALL" ? " active" : ""}`;
    allPill.textContent = `All (${entities.length})`;
    allPill.addEventListener("click", function () {
      activeLabelFilter = "ALL";
      renderResults();
    });
    filterPills.appendChild(allPill);

    labels.forEach(function (lbl) {
      const pill = document.createElement("button");
      pill.type = "button";
      pill.className = `pill${activeLabelFilter === lbl ? " active" : ""}`;
      pill.textContent = `${lbl} (${counts[lbl]})`;
      pill.addEventListener("click", function () {
        activeLabelFilter = lbl;
        renderResults();
      });
      filterPills.appendChild(pill);
    });
  }

  function renderAnnotatedDocument(fullText, entities) {
    if (!fullText) {
      annotatedText.innerHTML = "";
      return;
    }

    const sorted = entities.slice().sort(function (a, b) {
      return a.start - b.start;
    });

    let html = "";
    let lastIdx = 0;

    for (let i = 0; i < sorted.length; i++) {
      const ent = sorted[i];
      if (ent.start < lastIdx || ent.start >= fullText.length) continue;

      html += escapeHtml(fullText.substring(lastIdx, ent.start));

      const entText = fullText.substring(ent.start, ent.end);
      const tagKey = getTagKey(ent.label);

      html += `<mark id="mark-${i}" data-label="${tagKey}">` +
        `<strong>${escapeHtml(entText)}</strong>` +
        `<span class="mark-tag">${escapeHtml(ent.label)}</span>` +
        `</mark>`;

      lastIdx = ent.end;
    }

    if (lastIdx < fullText.length) {
      html += escapeHtml(fullText.substring(lastIdx));
    }

    annotatedText.innerHTML = html;
  }

  function renderResults() {
    if (!currentResponseData) return;

    const entities = currentResponseData.entities || [];
    tableBody.innerHTML = "";
    renderFilters(entities);

    const filtered = activeLabelFilter === "ALL"
      ? entities
      : entities.filter(function (e) { return e.label === activeLabelFilter; });

    if (filtered.length === 0) {
      const row = document.createElement("tr");
      row.innerHTML = '<td colspan="4" style="text-align:center; color:#64748b; padding:20px;">No entities match this filter.</td>';
      tableBody.appendChild(row);
    } else {
      filtered.forEach(function (ent, idx) {
        const row = document.createElement("tr");
        const tagKey = getTagKey(ent.label);
        row.style.cursor = "pointer";
        row.innerHTML =
          `<td><strong>${escapeHtml(ent.text)}</strong></td>` +
          `<td><span class="badge badge-${tagKey}">${escapeHtml(ent.label)}</span></td>` +
          `<td class="mono">${ent.start}</td>` +
          `<td class="mono">${ent.end}</td>`;

        row.addEventListener("mouseenter", function () {
          if (highlightMode === 0) return;
          const targetMark = document.getElementById(`mark-${idx}`);
          if (targetMark) {
            targetMark.classList.add("focused");
            targetMark.scrollIntoView({ behavior: "smooth", block: "nearest" });
          }
        });

        row.addEventListener("mouseleave", function () {
          const targetMark = document.getElementById(`mark-${idx}`);
          if (targetMark) targetMark.classList.remove("focused");
        });

        tableBody.appendChild(row);
      });
    }

    renderAnnotatedDocument(submittedText, filtered);
  }

  async function handleExtract() {
    const title = titleInput.value.trim();
    const body = bodyInput.value.trim();

    hideAlert();

    if (!title || !body) {
      showAlert("Error 400: Both Article Title and Article Body are required.");
      return;
    }

    submitBtn.disabled = true;
    spinner.style.display = "inline-block";
    btnText.textContent = "Processing...";

    try {
      const response = await fetch("/extract-entities", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: title, body: body })
      });

      const data = await response.json();

      if (!response.ok) {
        const detailMsg = data.detail || "Failed to process article text.";
        showAlert(`Error ${response.status}: ${detailMsg}`);
        return;
      }

      currentResponseData = data;
      activeLabelFilter = "ALL";

      submittedText = (data.full_text && typeof data.full_text === "string")
        ? data.full_text
        : `${title}\n\n${body}`;

      metaCount.textContent = data.meta ? data.meta.entity_count : (data.entities ? data.entities.length : 0);
      metaModel.textContent = data.meta ? data.meta.model : "NER";

      emptyState.style.display = "none";
      resultsContainer.style.display = "block";
      copyJsonBtn.style.display = "inline-flex";
      exportJsonBtn.style.display = "inline-flex";

      renderResults();
    } catch (err) {
      showAlert(`Client network error: ${err.message}`);
    } finally {
      submitBtn.disabled = false;
      spinner.style.display = "none";
      btnText.textContent = "Extract Entities";
    }
  }

  function loadSample() {
    titleInput.value = "OpenAI and Microsoft Expand European Cloud Infrastructure into Zurich and Dublin";
    bodyInput.value = "Zurich — OpenAI CEO Sam Altman and Microsoft Chief Technology Officer Kevin Scott announced an expanded partnership on Thursday to deploy advanced AI computing clusters across Western Europe. Under the initiative, new enterprise data facilities will be commissioned near Zurich and Dublin to support compliance with the European Union Artificial Intelligence Act.";
    updateCharCounts();
    hideAlert();
  }

  function clearForm() {
    titleInput.value = "";
    bodyInput.value = "";
    updateCharCounts();
    hideAlert();
    currentResponseData = null;
    submittedText = "";
    resultsContainer.style.display = "none";
    copyJsonBtn.style.display = "none";
    exportJsonBtn.style.display = "none";
    emptyState.style.display = "block";
  }

  async function copyRawJson() {
    if (!currentResponseData) return;
    await navigator.clipboard.writeText(JSON.stringify(currentResponseData, null, 2));
    const original = copyJsonBtn.textContent;
    copyJsonBtn.textContent = "Copied!";
    setTimeout(function () { copyJsonBtn.textContent = original; }, 1500);
  }

  function exportRawJson() {
    if (!currentResponseData) return;
    const jsonStr = JSON.stringify(currentResponseData, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `ner_extraction_${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  titleInput.addEventListener("input", updateCharCounts);
  bodyInput.addEventListener("input", updateCharCounts);
  submitBtn.addEventListener("click", handleExtract);
  clearBtn.addEventListener("click", clearForm);
  loadSampleBtn.addEventListener("click", loadSample);
  copyJsonBtn.addEventListener("click", copyRawJson);
  exportJsonBtn.addEventListener("click", exportRawJson);
  highlightToggleBtn.addEventListener("click", cycleHighlightMode);

  applyHighlightMode();
  updateCharCounts();
});
