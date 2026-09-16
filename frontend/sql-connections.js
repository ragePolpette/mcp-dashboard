function setDbTargetsFlash(message, kind = "info") {
  const flash = document.getElementById("dbTargetsFlash");
  if (!flash) return;
  flash.className = `settings-flash ${kind}`;
  flash.textContent = message;
}

// Passwords live only in the form until submit; never in target drafts or storage.
let sqlConnectionTargetId = null;
let sqlConnectionRequest = 0;

function renderSqlConnectionPanel(force = false) {
  const panel = document.getElementById("dbConnectionPanel");
  if (!panel) return;
  const targetId = dbTargetsState.selectedId;
  if (!force && panel.dataset.targetId === String(targetId)) return;
  sqlConnectionTargetId = targetId;
  panel.dataset.targetId = String(targetId);
  const request = ++sqlConnectionRequest;
  if (!targetId || targetId === "__new__") {
    panel.innerHTML = '<h4>Connessione SQL Server</h4><p class="muted">Crea il target, poi configura qui server, database e credenziali.</p>';
    return;
  }
  panel.innerHTML = '<h4>Connessione SQL Server</h4><p class="muted">Caricamento della connessione dal Vault…</p>';
  void loadSqlConnectionProfile(targetId, request);
}

async function loadSqlConnectionProfile(targetId, request) {
  const panel = document.getElementById("dbConnectionPanel");
  try {
    const profile = await apiJson(`/api/db-targets/${encodeURIComponent(targetId)}/connection`);
    if (request !== sqlConnectionRequest || targetId !== sqlConnectionTargetId) return;
    panel.innerHTML = `
      <h4>Connessione SQL Server</h4>
      <p class="muted">Autenticazione SQL con utente e password. Le credenziali vengono salvate cifrate nel Vault.</p>
      <form id="sqlConnectionForm" autocomplete="off">
        <div class="db-target-field-grid">
          <div class="db-target-field"><label for="sqlServer">Server o istanza</label><input id="sqlServer" name="server" required maxlength="4096" value="${escapeHtml(profile.server || "")}" placeholder="sql.example.local oppure host.docker.internal"></div>
          <div class="db-target-field"><label for="sqlPort">Porta (facoltativa)</label><input id="sqlPort" name="port" type="number" min="1" max="65535" value="${escapeHtml(profile.port ?? "")}" placeholder="1433"></div>
          <div class="db-target-field"><label for="sqlDatabase">Database</label><input id="sqlDatabase" name="database" required maxlength="4096" value="${escapeHtml(profile.database || "")}"></div>
          <div class="db-target-field"><label for="sqlUsername">Utente SQL</label><input id="sqlUsername" name="username" required maxlength="4096" autocomplete="off" value="${escapeHtml(profile.username || "")}"></div>
          <div class="db-target-field"><label for="sqlPassword">Password</label><input id="sqlPassword" name="password" type="password" maxlength="4096" autocomplete="new-password" ${profile.password_set ? "" : "required"} placeholder="${profile.password_set ? "Già salvata: lascia vuoto per conservarla" : "Password SQL"}"></div>
        </div>
        <div class="db-target-field-grid">
          <label class="settings-toggle"><input name="encrypt" type="checkbox" ${profile.encrypt !== false ? "checked" : ""}>Cifra la connessione (TLS)</label>
          <label class="settings-toggle"><input name="trust_server_certificate" type="checkbox" ${profile.trust_server_certificate ? "checked" : ""}>Accetta il certificato senza verificarlo</label>
        </div>
        <p class="muted">Per SQL Server su questo PC Windows usa host.docker.internal. Il salvataggio non verifica la connessione al database.</p>
        <div class="db-target-editor-actions"><button type="submit" class="btn-ok">Salva connessione nel Vault</button><button type="button" id="sqlConnectionReload">Ricarica connessione</button></div>
        <p id="sqlConnectionFeedback" class="muted" role="status" aria-live="polite"></p>
      </form>`;
    panel.querySelector("#sqlConnectionReload").addEventListener("click", () => renderSqlConnectionPanel(true));
    panel.querySelector("form").addEventListener("submit", event => saveSqlConnection(event, targetId));
  } catch (error) {
    if (request !== sqlConnectionRequest) return;
    panel.innerHTML = `<h4>Connessione SQL Server</h4><p class="muted">${escapeHtml(error.message)}</p><button type="button" id="sqlConnectionUnlock">Apri Vault</button> <button type="button" id="sqlConnectionRetry">Riprova</button><p class="muted">Il riferimento manuale al Vault resta disponibile nella sezione Avanzate del target.</p>`;
    panel.querySelector("#sqlConnectionUnlock").addEventListener("click", async () => { await toggleSettingsPanel(true); setSettingsTab("vault"); });
    panel.querySelector("#sqlConnectionRetry").addEventListener("click", () => renderSqlConnectionPanel(true));
  }
}

async function saveSqlConnection(event, targetId) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector('button[type="submit"]');
  const feedback = form.querySelector("#sqlConnectionFeedback");
  const fields = new FormData(form);
  const payload = {
    server: fields.get("server"), port: fields.get("port"), database: fields.get("database"),
    username: fields.get("username"), password: fields.get("password"),
    encrypt: fields.has("encrypt"), trust_server_certificate: fields.has("trust_server_certificate")
  };
  button.disabled = true;
  feedback.textContent = "Salvataggio…";
  try {
    await apiJson(`/api/db-targets/${encodeURIComponent(targetId)}/connection`, {
      method: "PUT", headers: {"Content-Type":"application/json"}, body: JSON.stringify(payload)
    });
    form.elements.password.value = "";
    form.elements.password.required = false;
    form.elements.password.placeholder = "Già salvata: lascia vuoto per conservarla";
    feedback.textContent = "Connessione salvata. Abilita il target quando pronto, poi premi Applica al server SQL.";
    await loadDbTargets();
  } catch (error) {
    feedback.textContent = error.message;
  } finally {
    // Do not retain a failed password submission in the form or payload either.
    payload.password = "";
    form.elements.password.value = "";
    button.disabled = false;
  }
}

async function applySqlTargetConfiguration() {
  const button = document.getElementById("dbTargetsApplyBtn");
  button.disabled = true;
  try {
    const result = await apiJson("/api/db-targets/runtime/apply", {method:"POST"});
    setDbTargetsFlash(result.message || "Configurazione applicata al server SQL.", "success");
    await loadDbTargets();
  } catch (error) {
    setDbTargetsFlash(error.message, "error");
  } finally {
    button.disabled = false;
  }
}

document.getElementById("dbTargetsApplyBtn")?.addEventListener("click", applySqlTargetConfiguration);
document.getElementById("closeSettingsBtn")?.addEventListener("click", () => {
  const password = document.getElementById("sqlPassword");
  if (password) password.value = "";
  if (advancedServiceId === "llm-sql-db-mcp") renderSqlConnectionPanel(true);
});
renderSqlConnectionPanel();
