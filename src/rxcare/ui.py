"""Self-contained browser UI for the local synthetic-data prototype."""


def render_index(app_version: str) -> bytes:
    """Return the dependency-free single-page UI as UTF-8 bytes."""

    html = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Local synthetic prescription validation prototype">
  <title>RxCare Validation Workspace</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #142438;
      --muted: #5d6b7a;
      --line: #dce5e8;
      --surface: #ffffff;
      --canvas: #f3f7f7;
      --teal: #006d70;
      --teal-dark: #005457;
      --teal-soft: #e5f4f2;
      --navy: #173451;
      --success: #19704a;
      --success-soft: #e7f5ed;
      --danger: #a33131;
      --danger-soft: #fff0ef;
      --shadow: 0 18px 44px rgba(20, 48, 67, 0.09);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      background:
        radial-gradient(circle at 0 0, rgba(0, 109, 112, 0.10), transparent 32rem),
        var(--canvas);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }

    header {
      background: linear-gradient(120deg, var(--navy), #0b5963);
      color: white;
      padding: 1rem clamp(1rem, 5vw, 4rem);
    }

    .header-inner {
      max-width: 1180px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 0.8rem;
      font-weight: 750;
      letter-spacing: 0.01em;
    }

    .brand-mark {
      display: grid;
      width: 2.3rem;
      height: 2.3rem;
      place-items: center;
      border: 1px solid rgba(255, 255, 255, 0.55);
      border-radius: 0.75rem;
      background: rgba(255, 255, 255, 0.12);
    }

    .environment {
      border: 1px solid rgba(255, 255, 255, 0.35);
      border-radius: 999px;
      padding: 0.35rem 0.75rem;
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }

    main {
      max-width: 1180px;
      margin: 0 auto;
      padding: clamp(1.5rem, 4vw, 3.5rem) clamp(1rem, 4vw, 2rem) 4rem;
    }

    .intro {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: end;
      gap: 1.5rem;
      margin-bottom: 1.6rem;
    }

    h1 {
      max-width: 760px;
      margin: 0 0 0.5rem;
      font-size: clamp(2rem, 5vw, 3.2rem);
      line-height: 1.08;
      letter-spacing: -0.035em;
    }

    .intro p { max-width: 720px; margin: 0; color: var(--muted); }

    .version {
      color: var(--muted);
      font-size: 0.84rem;
      white-space: nowrap;
    }

    .notice {
      display: flex;
      gap: 0.8rem;
      align-items: flex-start;
      margin-bottom: 1.5rem;
      border: 1px solid #c6dfdc;
      border-radius: 0.85rem;
      background: var(--teal-soft);
      padding: 0.9rem 1rem;
      color: #174d50;
      font-size: 0.92rem;
    }

    .workspace {
      display: grid;
      grid-template-columns: minmax(0, 1.02fr) minmax(0, 0.98fr);
      gap: 1.4rem;
      align-items: start;
    }

    .card {
      border: 1px solid var(--line);
      border-radius: 1.1rem;
      background: var(--surface);
      box-shadow: var(--shadow);
      overflow: hidden;
    }

    .card-head {
      border-bottom: 1px solid var(--line);
      padding: 1.2rem 1.35rem;
    }

    .card-head h2, .panel h3 { margin: 0; font-size: 1.08rem; }
    .card-head p { margin: 0.25rem 0 0; color: var(--muted); font-size: 0.88rem; }

    form { padding: 1.35rem; }

    .field-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 1rem;
    }

    .field { display: flex; flex-direction: column; gap: 0.38rem; }
    .field.full { grid-column: 1 / -1; }

    label { font-size: 0.86rem; font-weight: 720; }

    input, textarea {
      width: 100%;
      border: 1px solid #bdcbd0;
      border-radius: 0.65rem;
      background: white;
      padding: 0.72rem 0.8rem;
      color: var(--ink);
      font: inherit;
      transition: border-color 120ms ease, box-shadow 120ms ease;
    }

    textarea { min-height: 6.3rem; resize: vertical; }

    input:focus, textarea:focus {
      outline: none;
      border-color: var(--teal);
      box-shadow: 0 0 0 3px rgba(0, 109, 112, 0.14);
    }

    .hint { color: var(--muted); font-size: 0.76rem; }

    .field-error {
      color: var(--danger);
      font-size: 0.78rem;
      font-weight: 720;
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 0.7rem;
      margin-top: 1.2rem;
    }

    button {
      border: 0;
      border-radius: 0.65rem;
      padding: 0.72rem 1rem;
      font: inherit;
      font-weight: 720;
      cursor: pointer;
    }

    button:focus-visible { outline: 3px solid rgba(0, 109, 112, 0.28); outline-offset: 2px; }
    button:disabled { cursor: wait; opacity: 0.65; }
    .primary { background: var(--teal); color: white; }
    .primary:hover:not(:disabled) { background: var(--teal-dark); }
    .secondary { border: 1px solid #b8c8cc; background: white; color: var(--navy); }
    .secondary:hover { background: #f4f8f8; }

    .results { display: grid; gap: 1rem; }

    .status-panel { padding: 1.25rem 1.35rem; }

    .status-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      margin-bottom: 0.85rem;
    }

    .status-row h2 { margin: 0; font-size: 1.08rem; }

    .badge {
      border-radius: 999px;
      background: #edf1f3;
      padding: 0.3rem 0.62rem;
      color: #4a5966;
      font-size: 0.75rem;
      font-weight: 800;
      letter-spacing: 0.035em;
    }

    .badge.accepted { background: var(--success-soft); color: var(--success); }
    .badge.rejected, .badge.error { background: var(--danger-soft); color: var(--danger); }

    #result-message { margin: 0 0 0.8rem; color: var(--muted); }

    .panel { border-top: 1px solid var(--line); padding: 1.05rem 1.35rem 1.25rem; }

    .panel-heading {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      margin-bottom: 0.65rem;
    }

    .panel-note { color: var(--muted); font-size: 0.76rem; }

    pre {
      max-height: 17rem;
      margin: 0;
      overflow: auto;
      border: 1px solid #dce4e8;
      border-radius: 0.7rem;
      background: #f7f9fa;
      padding: 0.85rem;
      color: #243b50;
      font: 0.78rem/1.55 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    footer {
      max-width: 1180px;
      margin: 0 auto;
      padding: 0 2rem 2rem;
      color: var(--muted);
      font-size: 0.78rem;
      text-align: center;
    }

    @media (max-width: 820px) {
      .intro, .workspace { grid-template-columns: 1fr; }
      .version { white-space: normal; }
    }

    @media (max-width: 560px) {
      .field-grid { grid-template-columns: 1fr; }
      .field.full { grid-column: auto; }
      .environment { display: none; }
      .actions button { width: 100%; }
    }
  </style>
</head>
<body>
  <header>
    <div class="header-inner">
      <div class="brand"><span class="brand-mark" aria-hidden="true">Rx</span> RxCare</div>
      <span class="environment">Local QA prototype</span>
    </div>
  </header>

  <main>
    <section class="intro" aria-labelledby="page-title">
      <div>
        <h1 id="page-title">Prescription validation workspace</h1>
        <p>Exercise the dosage-completeness rule, inspect canonical persistence, and review the privacy-safe audit trail in one local workflow.</p>
      </div>
      <span class="version">Prototype v{{APP_VERSION}}</span>
    </section>

    <aside class="notice" aria-label="Synthetic data notice">
      <strong>Synthetic data only.</strong>
      <span>Do not enter names, contact details, real prescriptions, or other personal health information. This educational prototype does not provide medical advice.</span>
    </aside>

    <div class="workspace">
      <section class="card" aria-labelledby="form-title">
        <div class="card-head">
          <h2 id="form-title">Validation input</h2>
          <p>Submit an accepted scenario or deliberately exercise a rejection.</p>
        </div>

        <form id="prescription-form" novalidate>
          <div class="field-grid">
            <div class="field">
              <label for="record_id">Record ID</label>
              <input id="record_id" name="record_id" type="text" autocomplete="off" spellcheck="false">
              <span class="hint">Use a synthetic identifier beginning with SYN-.</span>
            </div>

            <div class="field">
              <label for="patient_ref">Synthetic patient reference</label>
              <input id="patient_ref" name="patient_ref" type="text" autocomplete="off" spellcheck="false">
              <span class="hint">Never use a real patient identifier.</span>
            </div>

            <div class="field full">
              <label for="medication_name">Medication name</label>
              <input id="medication_name" name="medication_name" type="text" autocomplete="off">
            </div>

            <div class="field full">
              <label for="dosage_instruction">Dosage instruction</label>
              <textarea id="dosage_instruction" name="dosage_instruction" aria-describedby="dosage-hint dosage-error" aria-invalid="false"></textarea>
              <span id="dosage-hint" class="hint">Blank or whitespace-only dosage must be rejected by RXQA-5.</span>
              <span id="dosage-error" class="field-error" role="alert" hidden>Dosage is required</span>
            </div>
          </div>

          <div class="actions">
            <button id="submit-button" class="primary" type="submit">Validate and verify</button>
            <button id="accepted-scenario" class="secondary" type="button">Load accepted scenario</button>
            <button id="rejected-scenario" class="secondary" type="button">Load rejection scenario</button>
          </div>
        </form>
      </section>

      <section class="card results" aria-labelledby="result-title">
        <div class="status-panel" aria-live="polite">
          <div class="status-row">
            <h2 id="result-title">Validation result</h2>
            <span id="result-badge" class="badge">READY</span>
          </div>
          <p id="result-message">Submit a synthetic scenario to begin.</p>
          <pre id="validation-output" data-testid="validation-output">No validation response yet.</pre>
        </div>

        <div class="panel">
          <div class="panel-heading">
            <h3>Canonical record</h3>
            <span class="panel-note">SQLite verification</span>
          </div>
          <pre id="canonical-output" data-testid="canonical-output">Waiting for submission.</pre>
        </div>

        <div class="panel">
          <div class="panel-heading">
            <h3>Privacy-safe audit events</h3>
            <span class="panel-note">No patient or medication fields</span>
          </div>
          <pre id="audit-output" data-testid="audit-output">Waiting for submission.</pre>
        </div>
      </section>
    </div>
  </main>

  <footer>RxCare is a fictional, local educational prototype for software-quality demonstration.</footer>

  <script>
    "use strict";

    const form = document.getElementById("prescription-form");
    const submitButton = document.getElementById("submit-button");
    const badge = document.getElementById("result-badge");
    const resultMessage = document.getElementById("result-message");
    const validationOutput = document.getElementById("validation-output");
    const canonicalOutput = document.getElementById("canonical-output");
    const auditOutput = document.getElementById("audit-output");
    const dosageInput = document.getElementById("dosage_instruction");
    const dosageError = document.getElementById("dosage-error");
    window.__rxcareEvidence = null;

    function scenarioSuffix() {
      return Date.now().toString(36).toUpperCase() + "-" + Math.floor(Math.random() * 1000).toString().padStart(3, "0");
    }

    function loadScenario(accepted) {
      const suffix = scenarioSuffix();
      form.elements.record_id.value = "SYN-UI-" + suffix;
      form.elements.patient_ref.value = "SYN-PAT-" + suffix;
      form.elements.medication_name.value = "Synthetic Medicine";
      form.elements.dosage_instruction.value = accepted ? "Take one synthetic unit once daily" : "   ";
      setDosageError(false);
      form.elements.dosage_instruction.focus();
    }

    function setDosageError(isVisible) {
      dosageError.hidden = !isVisible;
      dosageInput.setAttribute("aria-invalid", isVisible ? "true" : "false");
    }

    function setBusy(isBusy) {
      submitButton.disabled = isBusy;
      submitButton.textContent = isBusy ? "Validating…" : "Validate and verify";
    }

    function showJson(element, payload) {
      element.textContent = JSON.stringify(payload, null, 2);
    }

    async function fetchJson(path, options) {
      const response = await fetch(path, options);
      const payload = await response.json();
      return { response, payload };
    }

    async function verifyRecord(recordId) {
      const encodedId = encodeURIComponent(recordId);
      const canonical = await fetchJson("/api/v1/prescriptions/" + encodedId);
      showJson(canonicalOutput, canonical.payload);

      const audit = await fetchJson("/api/v1/audit-events?record_id=" + encodedId);
      showJson(auditOutput, audit.payload);
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      setBusy(true);
      setDosageError(false);
      window.__rxcareEvidence = null;
      badge.className = "badge";
      badge.textContent = "RUNNING";
      resultMessage.textContent = "Submitting the synthetic record and checking persisted evidence.";
      validationOutput.textContent = "Waiting for API response…";
      canonicalOutput.textContent = "Waiting for canonical lookup…";
      auditOutput.textContent = "Waiting for audit lookup…";

      const formData = new FormData(form);
      const requestPayload = {
        record_id: formData.get("record_id"),
        patient_ref: formData.get("patient_ref"),
        medication_name: formData.get("medication_name"),
        dosage_instruction: formData.get("dosage_instruction")
      };

      try {
        const submission = await fetchJson("/api/v1/prescriptions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(requestPayload)
        });

        showJson(validationOutput, submission.payload);
        const outcome = submission.payload.status || "ERROR";
        const issues = Array.isArray(submission.payload.issues) ? submission.payload.issues : [];
        setDosageError(issues.some((issue) => issue.code === "DOSAGE_REQUIRED"));
        const dosageValue = String(requestPayload.dosage_instruction || "");
        window.__rxcareEvidence = {
          request: {
            record_id: String(requestPayload.record_id || "").trim(),
            dosage_length: dosageValue.length,
            dosage_code_points: Array.from(dosageValue, (character) => character.codePointAt(0))
          },
          http_status: submission.response.status,
          response: submission.payload
        };
        badge.textContent = outcome + " · HTTP " + submission.response.status;
        badge.className = "badge " + (outcome === "ACCEPTED" ? "accepted" : "rejected");
        resultMessage.textContent = submission.payload.message || "Validation completed.";

        const verificationId = submission.payload.record_id || String(requestPayload.record_id || "").trim();
        if (verificationId) {
          await verifyRecord(verificationId);
        } else {
          canonicalOutput.textContent = "No record ID is available for lookup.";
          auditOutput.textContent = "No record ID is available for lookup.";
        }
      } catch (error) {
        badge.textContent = "ERROR";
        badge.className = "badge error";
        resultMessage.textContent = "The local server could not complete the request.";
        validationOutput.textContent = String(error);
        canonicalOutput.textContent = "Verification was not completed.";
        auditOutput.textContent = "Verification was not completed.";
      } finally {
        setBusy(false);
      }
    });

    document.getElementById("accepted-scenario").addEventListener("click", () => loadScenario(true));
    document.getElementById("rejected-scenario").addEventListener("click", () => loadScenario(false));
    loadScenario(true);
  </script>
</body>
</html>
"""
    return html.replace("{{APP_VERSION}}", app_version).encode("utf-8")
