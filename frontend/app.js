const widgetGrid = document.getElementById("widgetGrid");
const dashboardPidText = document.getElementById("dashboardPidText");
const killAllBtn = document.getElementById("killAllBtn");
const refreshAllBtn = document.getElementById("refreshAllBtn");
const settingsFab = document.getElementById("settingsFab");
const settingsPanel = document.getElementById("settingsPanel");
const saveSettingsBtn = document.getElementById("saveSettingsBtn");
const closeSettingsBtn = document.getElementById("closeSettingsBtn");
const settingsServicesList = document.getElementById("settingsServicesList");
const settingsPreferencesForm = document.getElementById("settingsPreferencesForm");

const advancedPanel = document.getElementById("advancedPanel");
const advancedTitle = document.getElementById("advancedTitle");
const advancedMeta = document.getElementById("advancedMeta");
const tabOptionsBtn = document.getElementById("tabOptionsBtn");
const tabLogsBtn = document.getElementById("tabLogsBtn");
const tabInspectorBtn = document.getElementById("tabInspectorBtn");
const advancedOptionsView = document.getElementById("advancedOptionsView");
const advancedLogsView = document.getElementById("advancedLogsView");
const advancedInspectorView = document.getElementById("advancedInspectorView");
const tailInput = document.getElementById("tailInput");
const filterLevel = document.getElementById("filterLevel");
const filterEvent = document.getElementById("filterEvent");
const filterChannel = document.getElementById("filterChannel");
const filterSource = document.getElementById("filterSource");
const filterText = document.getElementById("filterText");
const applyFilterBtn = document.getElementById("applyFilterBtn");
const clearFilterBtn = document.getElementById("clearFilterBtn");
const clearLogsBtn = document.getElementById("clearLogsBtn");
const loadBtn = document.getElementById("loadBtn");
const streamBtn = document.getElementById("streamBtn");
const stopBtn = document.getElementById("stopBtn");
const logBody = document.getElementById("logBody");
const queryPanel = document.getElementById("queryPanel");
const queryBody = document.getElementById("queryBody");
const reloadQueriesBtn = document.getElementById("reloadQueriesBtn");
const activityPanel = document.getElementById("activityPanel");
const activityBody = document.getElementById("activityBody");
const reloadActivityBtn = document.getElementById("reloadActivityBtn");
const alertPanel = document.getElementById("alertPanel");
const alertSummary = document.getElementById("alertSummary");
const alertList = document.getElementById("alertList");
const reloadAlertsBtn = document.getElementById("reloadAlertsBtn");

const optionsPanel = document.getElementById("optionsPanel");
const optionsForm = document.getElementById("optionsForm");
const saveOptionsBtn = document.getElementById("saveOptionsBtn");

let services = [];
let advancedServiceId = null;
let advancedEventSource = null;
let advancedActiveTab = "options";
let dashboardStatus = { pid: null };
let dashboardSettings = {
  preferences: {
    refresh_interval_sec: 5,
    show_stopped_services: true,
    default_advanced_tab: "automatic",
    service_order: "manual",
    show_alerts_in_home: true,
    log_retention_days: 15,
    recent_rows_limit: 30
  },
  service_visibility: {}
};
let refreshTimer = null;
const stateByService = new Map();
const statusByService = new Map();
const optionsByService = new Map();
const metricsByService = new Map();
const queriesByService = new Map();
const activityByService = new Map();
const alertsByService = new Map();
const advancedFilters = { level: "", event: "", channel: "", source: "", text: "" };

function normalizeServiceDefinition(service) {
  return {
    ...service,
    kind: String(service?.kind || "custom").toLowerCase(),
    group: String(service?.group || "custom").toLowerCase(),
    capabilities: Array.isArray(service?.capabilities)
      ? [...new Set(service.capabilities.map(cap => String(cap).toLowerCase()).filter(Boolean))]
      : []
  };
}

function serviceKind(serviceOrId) {
  if (!serviceOrId) {
    return "custom";
  }
  if (typeof serviceOrId === "string") {
    return serviceKind(services.find(service => service.id === serviceOrId));
  }
  return String(serviceOrId.kind || "custom").toLowerCase();
}

function serviceGroup(serviceOrId) {
  if (!serviceOrId) {
    return "custom";
  }
  if (typeof serviceOrId === "string") {
    return serviceGroup(services.find(service => service.id === serviceOrId));
  }
  return String(serviceOrId.group || "custom").toLowerCase();
}

function hasCapability(serviceOrId, capability) {
  const requested = String(capability || "").toLowerCase();
  if (!requested) {
    return false;
  }
  if (typeof serviceOrId === "string") {
    return hasCapability(services.find(service => service.id === serviceOrId), requested);
  }
  return Array.isArray(serviceOrId?.capabilities) && serviceOrId.capabilities.includes(requested);
}

function supportsQueryInspector(serviceOrId) {
  return hasCapability(serviceOrId, "query_inspector");
}

function supportsActivity(serviceOrId) {
  return hasCapability(serviceOrId, "activity");
}

function supportsAlerts(serviceOrId) {
  return hasCapability(serviceOrId, "alerts");
}

function supportsRuntimeOptions(serviceOrId) {
  return hasCapability(serviceOrId, "runtime_options");
}

function supportsInspector(serviceOrId) {
  return supportsQueryInspector(serviceOrId) || supportsActivity(serviceOrId);
}

function getServiceState(serviceId) {
  if (!stateByService.has(serviceId)) {
    stateByService.set(serviceId, {
      entries: [],
      loading: false,
      actionBusy: false,
      pendingAction: "",
      optionsBusy: false
    });
  }
  return stateByService.get(serviceId);
}

function getRuntimeStatus(serviceId) {
  if (!statusByService.has(serviceId)) {
    statusByService.set(serviceId, {
      control_available: false,
      running: false,
      pid: null,
      host: null,
      port: null,
      health_ok: null,
      health_details: null,
      last_error: "status_not_loaded"
    });
  }
  return statusByService.get(serviceId);
}

function getServiceMetrics(serviceId) {
  if (!metricsByService.has(serviceId)) {
    metricsByService.set(serviceId, {
      requests_per_minute: 0,
      error_rate: 0,
      db_avg_row_count: null,
      db_queries_count: 0,
      memory_saved_today: 0,
      memory_retrieved_today: 0,
      context_retrieved_today: 0,
      context_retrieval_series: []
    });
  }
  return metricsByService.get(serviceId);
}

function getServiceAlerts(serviceId) {
  if (!alertsByService.has(serviceId)) {
    alertsByService.set(serviceId, {
      service_id: serviceId,
      status: "ok",
      triggered_count: 0,
      triggered: [],
      evaluated_at: null
    });
  }
  return alertsByService.get(serviceId);
}

function effectiveRuntimeState(runtime, uiState = null) {
  const pendingAction = String(uiState?.pendingAction || "");
  if (uiState?.actionBusy) {
    if (pendingAction === "start") {
      return "starting";
    }
    if (pendingAction === "stop") {
      return "stopping";
    }
    if (pendingAction === "restart") {
      return "restarting";
    }
  }
  if (!runtime.control_available) {
    return "unmanaged";
  }
  if (!runtime.running) {
    return "stopped";
  }
  if (runtime.health_ok === false) {
    return "unhealthy";
  }
  return "running";
}

function runtimeDotClass(runtime, uiState = null) {
  const state = effectiveRuntimeState(runtime, uiState);
  if (state === "running") {
    return "ok";
  }
  if (state === "unhealthy") {
    return "error";
  }
  if (state === "starting" || state === "restarting" || state === "unmanaged") {
    return "info";
  }
  return "warn";
}

function runtimeLabel(runtime, uiState = null) {
  const state = effectiveRuntimeState(runtime, uiState);
  if (state === "unmanaged") {
    return "Control non configurato";
  }
  if (state === "stopped") {
    return "Stopped";
  }
  if (state === "starting") {
    return "Starting";
  }
  if (state === "stopping") {
    return "Stopping";
  }
  if (state === "restarting") {
    return "Restarting";
  }
  if (state === "unhealthy") {
    return "Unhealthy";
  }
  return "Running";
}

function healthLabel(runtime) {
  if (!runtime.control_available) {
    return "n/d";
  }
  if (!runtime.running) {
    return "stopped";
  }
  if (runtime.health_ok === null || runtime.health_ok === undefined) {
    return "n/d";
  }
  return runtime.health_ok ? "ok" : "ko";
}

function llmContextModeLabel(runtime) {
  if (!runtime?.health_details || typeof runtime.health_details !== "object") {
    return "";
  }
  const writeEnabled = runtime.health_details.write_enabled;
  const ingestEnabled = runtime.health_details.ingest_enabled;
  if (writeEnabled === undefined && ingestEnabled === undefined) {
    return "";
  }
  return `Write ${writeEnabled ? "ON" : "OFF"} | Ingest ${ingestEnabled ? "ON" : "OFF"}`;
}

function sourceScopeLabel(source) {
  const tags = Array.isArray(source?.tags) ? source.tags.map(tag => String(tag).toLowerCase()) : [];
  if (tags.includes("dev")) {
    return "DEV";
  }
  if (tags.includes("runtime")) {
    return "RUNTIME";
  }
  if (tags.includes("service-log")) {
    return "SERVICE";
  }
  return "OTHER";
}

function levelTooltip(level) {
  const normalized = String(level || "INFO").toUpperCase();
  const labels = {
    DEBUG: "Debug: dettagli tecnici utili per diagnosi",
    INFO: "Info: evento operativo normale",
    WARN: "Warning: anomalia non bloccante",
    ERROR: "Error: errore applicativo o operativo",
    CRITICAL: "Critical: errore critico"
  };
  return labels[normalized] || normalized;
}

function channelTooltip(channel) {
  const normalized = String(channel || "stdout").toLowerCase();
  if (normalized === "stdout") {
    return "STDOUT: output standard del processo";
  }
  if (normalized === "stderr") {
    return "STDERR: error output del processo";
  }
  return normalized.toUpperCase();
}

function sourceScopeTooltip(scope) {
  const normalized = String(scope || "").toUpperCase();
  if (normalized === "DEV") {
    return "DEV: log letti dall'ambiente di sviluppo Yetzirah";
  }
  if (normalized === "RUNTIME") {
    return "RUNTIME: log letti dall'ambiente di deploy Binah";
  }
  if (normalized === "SERVICE") {
    return "SERVICE: log scritti direttamente dal servizio";
  }
  return normalized || "Origine log";
}

function sourceSummaryLabel(source) {
  const channel = String(source?.channel || "stdout").toUpperCase();
  const scope = sourceScopeLabel(source);
  const path = String(source?.path || "");
  const parts = path.split(/[\\/]/).filter(Boolean);
  const fileName = parts.length ? parts[parts.length - 1] : path || "n/d";
  return `${scope} ${channel} - ${fileName}`;
}

function serviceGroupLabel(service) {
  const labels = {
    database: "Database",
    knowledge: "Knowledge",
    runtime: "Runtime",
    custom: "Custom"
  };
  return labels[serviceGroup(service)] || "Custom";
}

function serviceLatestEventSummary(entry) {
  if (!entry) {
    return "Ultimo evento: n/d";
  }
  const level = String(entry.level || "INFO").toUpperCase();
  const eventName = entry.event || "log.line";
  const message = compactPreviewText(entryDisplayMessage(entry), 110);
  return `${formatTimestamp(entry.timestamp)} | ${level} ${eventName} | ${message}`;
}

function serviceSummaryLine(service, metrics, runtime) {
  const reqMin = Number(metrics.requests_per_minute || 0);
  const errRate = Number(metrics.error_rate || 0) * 100;

  if (serviceKind(service) === "db") {
    return `Req/min ${reqMin} | Error ${errRate.toFixed(1)}% | Query ${metrics.db_queries_count || 0} | Avg rows ${formatNumber(metrics.db_avg_row_count)}`;
  }
  if (serviceKind(service) === "memory") {
    return `Req/min ${reqMin} | Error ${errRate.toFixed(1)}% | Saved oggi ${metrics.memory_saved_today || 0} | Retrieved oggi ${metrics.memory_retrieved_today || 0}`;
  }
  if (serviceKind(service) === "rag") {
    const contextMode = llmContextModeLabel(runtime);
    const retrievals = `Retrieved oggi ${metrics.context_retrieved_today || 0}`;
    return contextMode ? `${retrievals} | ${contextMode}` : retrievals;
  }
  return `Req/min ${reqMin} | Error ${errRate.toFixed(1)}%`;
}

function serviceOrderWeight(service) {
  const group = serviceGroup(service);
  const groupWeight = {
    knowledge: 10,
    database: 20,
    runtime: 30,
    custom: 40
  };
  return groupWeight[group] ?? 99;
}

function preferenceValue(key, fallback = null) {
  if (!dashboardSettings || !dashboardSettings.preferences) {
    return fallback;
  }
  return dashboardSettings.preferences[key] ?? fallback;
}

function isServiceVisible(service) {
  if (!service) {
    return false;
  }
  const visibilityMap = dashboardSettings?.service_visibility || {};
  if (Object.prototype.hasOwnProperty.call(visibilityMap, service.id)) {
    return Boolean(visibilityMap[service.id]);
  }
  return service.visible !== false;
}

function shouldRenderServiceCard(service) {
  if (!isServiceVisible(service)) {
    return false;
  }
  if (preferenceValue("show_stopped_services", true)) {
    return true;
  }
  const runtime = getRuntimeStatus(service.id);
  return Boolean(runtime.running);
}

function currentRecentRowsLimit() {
  return Number(preferenceValue("recent_rows_limit", 30) || 30);
}

function currentRefreshIntervalMs() {
  return Number(preferenceValue("refresh_interval_sec", 5) || 5) * 1000;
}

function compareServices(left, right) {
  const orderMode = String(preferenceValue("service_order", "manual") || "manual");

  if (orderMode === "status") {
    const stateWeight = service => {
      const runtime = getRuntimeStatus(service.id);
      const uiState = getServiceState(service.id);
      const state = effectiveRuntimeState(runtime, uiState);
      const weights = { running: 10, unhealthy: 20, starting: 30, restarting: 40, stopped: 50, stopping: 60, unmanaged: 70 };
      return weights[state] ?? 99;
    };
    const weightDiff = stateWeight(left) - stateWeight(right);
    if (weightDiff !== 0) {
      return weightDiff;
    }
  }

  if (orderMode === "group" || orderMode === "status") {
    const groupDiff = serviceOrderWeight(left) - serviceOrderWeight(right);
    if (groupDiff !== 0) {
      return groupDiff;
    }
    return String(left.name || left.id).localeCompare(String(right.name || right.id));
  }

  return Number(left.registryIndex || 0) - Number(right.registryIndex || 0);
}

function pickDefaultAdvancedTab(service, runtime) {
  const preference = String(preferenceValue("default_advanced_tab", "automatic") || "automatic");
  if (preference !== "automatic") {
    if (preference === "inspector" && !supportsInspector(service)) {
      return runtime?.running ? "logs" : "options";
    }
    if (preference === "logs" && !runtime?.running) {
      return "options";
    }
    return preference;
  }
  if (!runtime?.running) {
    return "options";
  }
  return "logs";
}

function setAdvancedTab(tabName) {
  advancedActiveTab = tabName;
  const tabs = [
    { name: "options", button: tabOptionsBtn, view: advancedOptionsView, enabled: true },
    { name: "logs", button: tabLogsBtn, view: advancedLogsView, enabled: true },
    {
      name: "inspector",
      button: tabInspectorBtn,
      view: advancedInspectorView,
      enabled: supportsInspector(advancedServiceId)
    }
  ];

  for (const tab of tabs) {
    if (!tab.button || !tab.view) {
      continue;
    }
    if (!tab.enabled) {
      tab.button.classList.add("hidden");
      tab.view.classList.add("hidden");
      tab.button.setAttribute("aria-selected", "false");
      tab.button.classList.remove("active");
      continue;
    }
    tab.button.classList.remove("hidden");
    const active = tab.name === tabName;
    tab.button.classList.toggle("active", active);
    tab.button.setAttribute("aria-selected", active ? "true" : "false");
    tab.view.classList.toggle("hidden", !active);
  }
}

function toDisplayText(value) {
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value, null, 2);
}

function formatNumber(value, decimals = 1) {
  const num = Number(value);
  if (!Number.isFinite(num)) {
    return "n/d";
  }
  return num.toFixed(decimals);
}

const dateTimeFormatter = new Intl.DateTimeFormat("it-IT", {
  dateStyle: "short",
  timeStyle: "medium"
});

function applyTooltip(element, text) {
  const tooltipText = String(text || "").trim();
  if (!element || !tooltipText) {
    return element;
  }
  element.title = tooltipText;
  element.setAttribute("data-tooltip", tooltipText);
  element.setAttribute("aria-label", tooltipText);
  element.classList.add("has-tooltip");
  if (!element.hasAttribute("tabindex")) {
    element.tabIndex = 0;
  }
  return element;
}

function formatTimestamp(value) {
  if (value === null || value === undefined) {
    return "n/d";
  }
  const text = String(value).trim();
  if (!text) {
    return "n/d";
  }
  const parsed = new Date(text);
  if (Number.isNaN(parsed.getTime())) {
    return text;
  }
  return dateTimeFormatter.format(parsed);
}

function alertClass(status) {
  if (status === "alert") return "alert-alert";
  if (status === "warn") return "alert-warn";
  return "alert-ok";
}

function alertLabel(status) {
  if (status === "alert") return "ALERT";
  if (status === "warn") return "WARN";
  return "OK";
}

function sparklineSvg(points, color = "#73c2ff", width = 220, height = 44) {
  const values = (points || []).map(v => Number(v)).filter(v => Number.isFinite(v));
  if (!values.length) {
    return `<div class="sparkline-empty">trend n/d</div>`;
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const spread = max - min || 1;
  const padding = 3;
  const innerW = width - padding * 2;
  const innerH = height - padding * 2;

  const coords = values.map((value, idx) => {
    const x = padding + (values.length === 1 ? innerW : (idx * innerW) / (values.length - 1));
    const y = padding + innerH - ((value - min) / spread) * innerH;
    return `${x.toFixed(2)},${y.toFixed(2)}`;
  });

  return `
    <svg class="sparkline-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
      <polyline points="${coords.join(" ")}" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></polyline>
    </svg>
  `;
}

function syncAdvancedFiltersFromInputs() {
  advancedFilters.level = (filterLevel?.value || "").trim().toUpperCase();
  advancedFilters.event = (filterEvent?.value || "").trim();
  advancedFilters.channel = (filterChannel?.value || "").trim().toLowerCase();
  advancedFilters.source = (filterSource?.value || "").trim();
  advancedFilters.text = (filterText?.value || "").trim().toLowerCase();
}

function entryMatchesAdvancedFilters(entry) {
  if (advancedFilters.level) {
    const entryLevel = String(entry?.level || "").toUpperCase();
    if (entryLevel !== advancedFilters.level) {
      return false;
    }
  }
  if (advancedFilters.event) {
    const entryEvent = String(entry?.event || "");
    if (entryEvent !== advancedFilters.event) {
      return false;
    }
  }
  if (advancedFilters.channel) {
    const entryChannel = String(entry?.channel || "").toLowerCase();
    if (entryChannel !== advancedFilters.channel) {
      return false;
    }
  }
  if (advancedFilters.source) {
    const sourcePath = String(entry?.source_path || "");
    if (sourcePath !== advancedFilters.source) {
      return false;
    }
  }
  if (advancedFilters.text) {
    const serialized = JSON.stringify(entry || {}).toLowerCase();
    if (!serialized.includes(advancedFilters.text)) {
      return false;
    }
  }
  return true;
}

function filteredEntries(entries) {
  return (entries || []).filter(entry => entryMatchesAdvancedFilters(entry));
}

function rebuildEventFilterOptions(entries) {
  if (!filterEvent) {
    return;
  }
  const current = filterEvent.value || "";
  const events = Array.from(new Set((entries || []).map(entry => String(entry?.event || "")).filter(Boolean))).sort();
  filterEvent.innerHTML = "";

  const all = document.createElement("option");
  all.value = "";
  all.textContent = "Tutti";
  filterEvent.appendChild(all);

  for (const eventName of events) {
    const opt = document.createElement("option");
    opt.value = eventName;
    opt.textContent = eventName;
    filterEvent.appendChild(opt);
  }

  if (events.includes(current)) {
    filterEvent.value = current;
  } else {
    filterEvent.value = "";
  }
}

function rebuildSourceFilterOptions(service) {
  if (!filterSource) {
    return;
  }
  const current = filterSource.value || "";
  filterSource.innerHTML = "";

  const all = document.createElement("option");
  all.value = "";
  all.textContent = "Tutte";
  filterSource.appendChild(all);

  const sources = Array.isArray(service?.log_sources) ? service.log_sources : [];
  for (const source of sources) {
    const option = document.createElement("option");
    option.value = String(source?.path || "");
    option.textContent = sourceSummaryLabel(source);
    filterSource.appendChild(option);
  }

  const available = sources.map(source => String(source?.path || ""));
  filterSource.value = available.includes(current) ? current : "";
}

function clearQueryRows() {
  while (queryBody.firstChild) {
    queryBody.removeChild(queryBody.firstChild);
  }
}

function clearActivityRows() {
  while (activityBody.firstChild) {
    activityBody.removeChild(activityBody.firstChild);
  }
}

function queryMatchesAdvancedFilters(query) {
  if (advancedFilters.level) {
    const level = String(query?.level || "").toUpperCase();
    if (level !== advancedFilters.level) {
      return false;
    }
  }
  if (advancedFilters.event && advancedFilters.event !== "db.query.executed") {
    return false;
  }
  if (advancedFilters.source) {
    const sourcePath = String(query?.source_path || "");
    if (sourcePath !== advancedFilters.source) {
      return false;
    }
  }
  if (advancedFilters.text) {
    const serialized = JSON.stringify(query || {}).toLowerCase();
    if (!serialized.includes(advancedFilters.text)) {
      return false;
    }
  }
  return true;
}

function truncateText(text, maxLength = 180) {
  const normalized = String(text || "");
  if (normalized.length <= maxLength) {
    return normalized;
  }
  return `${normalized.slice(0, Math.max(0, maxLength - 1))}…`;
}

function compactPreviewText(text, maxLength = 120) {
  const singleLine = String(text || "").replace(/\s+/g, " ").trim();
  return truncateText(singleLine, maxLength);
}

function isDbQueryEvent(entry) {
  const eventName = String(entry?.event || "");
  return eventName === "db.query.executed" || eventName === "query_in" || eventName === "query_out";
}

function entryDisplayMessage(entry) {
  const eventName = String(entry?.event || "");
  const fields = entry?.fields || {};

  if (eventName === "query_in") {
    return `${fields.tool || "db"} | query ricevuta`;
  }

  if (eventName === "query_out") {
    const response = fields.response || {};
    const tool = fields.tool || response.tool || "db";
    const rowCount = response.rowCount ?? "n/d";
    const suffix = response.truncated ? " | risultato troncato" : "";
    return `${tool} | ${rowCount} rows${suffix}`;
  }

  if (eventName === "db.query.executed") {
    const tool = fields.tool || "db";
    const rowCount = fields.row_count ?? "n/d";
    const suffix = fields.result_truncated ? " | risultato troncato" : "";
    return `${tool} | ${rowCount} rows${suffix}`;
  }

  return entry?.message || "";
}

function entryMetaPayload(entry) {
  const fields = entry?.fields || {};
  const tags = entry?.tags || [];
  const eventName = String(entry?.event || "");
  const base = {
    timestamp: entry?.timestamp || null,
    logger: entry?.logger || null,
    channel: entry?.channel || null,
    source_path: entry?.source_path || null,
    tags
  };

  if (eventName === "query_in") {
    const parameters = fields.parameters;
    return {
      ...base,
      tool: fields.tool || null,
      parameter_keys: parameters && typeof parameters === "object" ? Object.keys(parameters).sort() : []
    };
  }

  if (eventName === "query_out") {
    const response = fields.response || {};
    return {
      ...base,
      tool: fields.tool || response.tool || null,
      mode: response.mode || null,
      row_count: response.rowCount ?? null,
      result_truncated: response.truncated ?? null
    };
  }

  if (eventName === "db.query.executed") {
    return {
      ...base,
      tool: fields.tool || null,
      mode: fields.mode || null,
      row_count: fields.row_count ?? null,
      result_truncated: fields.result_truncated ?? null,
      parameter_keys: fields.parameter_keys ?? []
    };
  }

  const compactFields = Object.fromEntries(
    Object.entries(fields).filter(([key]) => !key.endsWith("_full"))
  );
  return {
    ...base,
    ...compactFields
  };
}

function renderQueriesForAdvanced(serviceId) {
  const allQueries = queriesByService.get(serviceId) || [];
  const rows = allQueries.filter(query => queryMatchesAdvancedFilters(query));
  clearQueryRows();

  const frag = document.createDocumentFragment();
  for (const query of rows.slice(0, 200)) {
    const tr = document.createElement("tr");

    const timeTd = document.createElement("td");
    timeTd.textContent = formatTimestamp(query.timestamp);
    applyTooltip(timeTd, query.timestamp || "Timestamp non disponibile");

    const toolTd = document.createElement("td");
    toolTd.textContent = `${query.tool || "n/d"}${query.mode ? ` (${query.mode})` : ""}`;

    const rowsTd = document.createElement("td");
    rowsTd.textContent = String(query.row_count ?? "n/d");

    const queryTd = document.createElement("td");
    const preview = document.createElement("pre");
    preview.className = "message-preview";
    preview.textContent = query.query_preview || "";
    queryTd.appendChild(preview);

    const full = String(query.query_full || "");
    if (full && full !== query.query_preview) {
      const details = document.createElement("details");
      details.className = "message-details";
      const summary = document.createElement("summary");
      summary.textContent = "Mostra query completa";
      details.appendChild(summary);
      const fullPre = document.createElement("pre");
      fullPre.className = "message-full";
      fullPre.textContent = full;
      details.appendChild(fullPre);
      queryTd.appendChild(details);
    }

    tr.appendChild(timeTd);
    tr.appendChild(toolTd);
    tr.appendChild(rowsTd);
    tr.appendChild(queryTd);
    frag.appendChild(tr);
  }
  queryBody.appendChild(frag);
}

function renderActivityForAdvanced(serviceId) {
  const rows = activityByService.get(serviceId) || [];
  clearActivityRows();

  const frag = document.createDocumentFragment();
  for (const item of rows.slice(0, 200)) {
    const tr = document.createElement("tr");

    const timeTd = document.createElement("td");
    timeTd.textContent = formatTimestamp(item.timestamp);
    applyTooltip(timeTd, item.timestamp || "Timestamp non disponibile");

    const toolTd = document.createElement("td");
    toolTd.textContent = item.tool || "n/d";

    const modeTd = document.createElement("td");
    const chip = document.createElement("span");
    const kind = String(item.kind || "read").toLowerCase();
    chip.className = `mode-chip ${kind === "write" ? "mode-write" : "mode-read"}`;
    chip.textContent = kind;
    modeTd.appendChild(chip);

    const requestTd = document.createElement("td");
    const requestPre = document.createElement("pre");
    requestPre.className = "message-preview";
    requestPre.textContent = item.request_text || "";
    requestTd.appendChild(requestPre);

    const responseTd = document.createElement("td");
    const responsePre = document.createElement("pre");
    responsePre.className = "message-preview";
    responsePre.textContent = item.response_text || "";
    responseTd.appendChild(responsePre);

    tr.append(timeTd, toolTd, modeTd, requestTd, responseTd);
    frag.appendChild(tr);
  }

  activityBody.appendChild(frag);
}

function clearAlertList() {
  while (alertList.firstChild) {
    alertList.removeChild(alertList.firstChild);
  }
}

function renderAlertsForAdvanced(serviceId) {
  const payload = getServiceAlerts(serviceId);
  if (!payload || !payload.triggered_count) {
    alertSummary.textContent = "Nessun alert attivo.";
    clearAlertList();
    return;
  }
  alertSummary.textContent = `Stato: ${String(payload.status || "ok").toUpperCase()} | Trigger: ${payload.triggered_count}`;
  clearAlertList();

  const frag = document.createDocumentFragment();
  for (const item of payload.triggered || []) {
    const li = document.createElement("li");
    const sev = String(item.severity || "warn").toLowerCase();
    li.innerHTML = `
      <div><span class="alert-chip ${alertClass(sev)}">${alertLabel(sev)}</span> ${item.name || item.id}</div>
      <div class="muted">Valore: ${item.current_value} ${item.op} soglia ${item.threshold}</div>
      <div>${item.message || ""}</div>
    `;
    frag.appendChild(li);
  }
  alertList.appendChild(frag);
}

function appendPreviewField(container, label, previewValue, fullValue) {
  const previewText = toDisplayText(previewValue);
  const fullText = toDisplayText(fullValue);
  if (!previewText && !fullText) {
    return;
  }

  const block = document.createElement("div");
  block.className = "message-block";

  const blockLabel = document.createElement("div");
  blockLabel.className = "message-label";
  blockLabel.textContent = label;
  block.appendChild(blockLabel);

  const previewPre = document.createElement("pre");
  previewPre.className = "message-preview";
  previewPre.textContent = previewText || fullText;
  block.appendChild(previewPre);

  if (fullText && fullText !== previewText) {
    const details = document.createElement("details");
    details.className = "message-details";
    const summary = document.createElement("summary");
    summary.textContent = "Mostra testo completo";
    details.appendChild(summary);

    const fullPre = document.createElement("pre");
    fullPre.className = "message-full";
    fullPre.textContent = fullText;
    details.appendChild(fullPre);
    block.appendChild(details);
  }

  container.appendChild(block);
}

function appendPreviewBlocks(container, fields) {
  if (!fields || typeof fields !== "object") {
    return;
  }

  const predefined = [
    { preview: "memory_preview", full: "memory_full", label: "Memoria" },
    { preview: "context_preview", full: "context_full", label: "Contesto" },
    { preview: "query_preview", full: "query_full", label: "Query" },
    { preview: "top_entry_preview", full: "top_entry_full", label: "Top risultato memoria" }
  ];
  const used = new Set();

  for (const item of predefined) {
    if (fields[item.preview] !== undefined || fields[item.full] !== undefined) {
      appendPreviewField(container, item.label, fields[item.preview], fields[item.full]);
      used.add(item.preview);
      used.add(item.full);
    }
  }

  for (const [key, value] of Object.entries(fields)) {
    if (!key.endsWith("_preview") || used.has(key)) {
      continue;
    }
    const fullKey = key.replace(/_preview$/, "_full");
    const label = key.replace(/_preview$/, "").replace(/_/g, " ");
    appendPreviewField(container, label, value, fields[fullKey]);
    used.add(key);
    used.add(fullKey);
  }
}

function rowFor(entry) {
  const tr = document.createElement("tr");
  const level = entry.level || "INFO";
  const fields = entry.fields || {};
  const tags = entry.tags || [];

  const timeTd = document.createElement("td");
  timeTd.textContent = formatTimestamp(entry.timestamp);
  applyTooltip(timeTd, entry.timestamp || "Timestamp stimato dalla dashboard");

  const levelTd = document.createElement("td");
  const levelBadge = document.createElement("span");
  levelBadge.className = `badge lvl-${level}`;
  levelBadge.textContent = level;
  applyTooltip(levelBadge, levelTooltip(level));
  levelTd.appendChild(levelBadge);

  const eventTd = document.createElement("td");
  eventTd.textContent = entry.event || "log.line";

  const channelTd = document.createElement("td");
  const channelWrap = document.createElement("div");
  channelWrap.className = "channel-cell";
  const channelValue = String(entry.channel || "stdout").toLowerCase();
  const channelChip = document.createElement("span");
  channelChip.className = `channel-chip ${channelValue}`;
  channelChip.textContent = channelValue.toUpperCase();
  applyTooltip(channelChip, channelTooltip(channelValue));
  channelWrap.appendChild(channelChip);
  const sourceChip = document.createElement("span");
  sourceChip.className = "source-chip";
  const sourceScope = sourceScopeLabel({ tags, channel: channelValue, path: entry.source_path });
  sourceChip.textContent = sourceScope;
  applyTooltip(sourceChip, sourceScopeTooltip(sourceScope));
  channelWrap.appendChild(sourceChip);
  channelTd.appendChild(channelWrap);

  const msgTd = document.createElement("td");
  const msgWrap = document.createElement("div");
  msgWrap.className = "message-cell";
  const msgText = document.createElement("div");
  msgText.className = "message-main";
  msgText.textContent = entryDisplayMessage(entry);
  msgWrap.appendChild(msgText);
  if (!isDbQueryEvent(entry)) {
    appendPreviewBlocks(msgWrap, fields);
  }
  msgTd.appendChild(msgWrap);

  const metaTd = document.createElement("td");
  const meta = entryMetaPayload(entry);
  const clean = Object.fromEntries(
    Object.entries(meta).filter(([, v]) => v !== null && v !== "" && !(Array.isArray(v) && v.length === 0))
  );
  const pre = document.createElement("pre");
  pre.className = "meta-json";
  pre.textContent = JSON.stringify(clean, null, 2);
  metaTd.appendChild(pre);

  tr.appendChild(timeTd);
  tr.appendChild(levelTd);
  tr.appendChild(eventTd);
  tr.appendChild(channelTd);
  tr.appendChild(msgTd);
  tr.appendChild(metaTd);
  return tr;
}

function clearAdvancedLogs() {
  while (logBody.firstChild) {
    logBody.removeChild(logBody.firstChild);
  }
}

function appendAdvancedEntries(entries, { prepend = false } = {}) {
  const frag = document.createDocumentFragment();
  for (const entry of entries) {
    frag.appendChild(rowFor(entry));
  }
  if (prepend) {
    logBody.prepend(frag);
    return;
  }
  logBody.appendChild(frag);
}

function renderAdvancedEntriesForService(serviceId) {
  const state = getServiceState(serviceId);
  const entries = filteredEntries(state.entries || []);
  clearAdvancedLogs();
  appendAdvancedEntries(entries);
}

async function apiJson(url, options = undefined) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload?.detail || payload?.message || `HTTP ${response.status}`;
    throw new Error(detail);
  }
  return payload;
}

async function loadDashboardStatus() {
  const payload = await apiJson("/api/dashboard/status");
  dashboardStatus = payload || { pid: null };
  dashboardPidText.textContent = `PID: ${dashboardStatus.pid || "n/d"}`;
}

async function loadDashboardSettings() {
  const payload = await apiJson("/api/settings");
  dashboardSettings = {
    preferences: { ...dashboardSettings.preferences, ...(payload.preferences || {}) },
    service_visibility: { ...(payload.service_visibility || {}) }
  };
  services = services.map(service => ({
    ...service,
    visible: dashboardSettings.service_visibility[service.id] ?? service.visible ?? true
  }));
  tailInput.value = String(currentRecentRowsLimit());
}

function renderSettingsPanel() {
  settingsServicesList.innerHTML = "";
  settingsPreferencesForm.innerHTML = "";

  const sortedServices = [...services].sort((left, right) =>
    String(left.name || left.id).localeCompare(String(right.name || right.id))
  );
  for (const service of sortedServices) {
    const row = document.createElement("div");
    row.className = "settings-row";
    row.innerHTML = `
      <div class="settings-row-head">
        <div>
          <div class="settings-row-title">${service.name}</div>
          <div class="settings-row-meta">${serviceGroupLabel(service)} | ${service.control?.port ? `Port ${service.control.port}` : "Port n/d"}</div>
        </div>
      </div>
    `;

    const toggle = document.createElement("label");
    toggle.className = "settings-toggle";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.dataset.serviceVisibility = service.id;
    input.checked = isServiceVisible(service);
    const text = document.createElement("span");
    text.textContent = "Visibile in dashboard";
    toggle.appendChild(input);
    toggle.appendChild(text);
    row.appendChild(toggle);
    settingsServicesList.appendChild(row);
  }

  const preferenceDefinitions = [
    {
      id: "refresh_interval_sec",
      label: "Intervallo refresh",
      type: "select",
      options: [
        { value: "0", label: "Manuale" },
        { value: "5", label: "5s" },
        { value: "10", label: "10s" },
        { value: "30", label: "30s" }
      ],
      hint: "Aggiornamento automatico della dashboard."
    },
    {
      id: "show_stopped_services",
      label: "Mostra servizi spenti",
      type: "boolean",
      hint: "Se OFF, in home restano visibili solo i servizi attivi."
    },
    {
      id: "default_advanced_tab",
      label: "Tab iniziale pannello avanzato",
      type: "select",
      options: [
        { value: "automatic", label: "Automatico" },
        { value: "options", label: "Opzioni" },
        { value: "logs", label: "Log" },
        { value: "inspector", label: "Inspector" }
      ],
      hint: "Tab aperta di default quando entri nel pannello avanzato."
    },
    {
      id: "service_order",
      label: "Ordine servizi",
      type: "select",
      options: [
        { value: "manual", label: "Manuale" },
        { value: "group", label: "Per gruppo" },
        { value: "status", label: "Per stato" }
      ],
      hint: "Ordine delle card in home."
    },
    {
      id: "show_alerts_in_home",
      label: "Mostra alert in home",
      type: "boolean",
      hint: "Mostra badge alert sulle card solo se attivo."
    },
    {
      id: "log_retention_days",
      label: "Retention log dashboard (giorni)",
      type: "integer",
      hint: "Pruning automatico dei log più vecchi."
    },
    {
      id: "recent_rows_limit",
      label: "Massimo righe recenti in UI",
      type: "integer",
      hint: "Numero di righe recenti caricate nella home e nello stream live."
    }
  ];

  for (const definition of preferenceDefinitions) {
    const row = document.createElement("div");
    row.className = "settings-row";

    const label = document.createElement("label");
    label.className = "option-label";
    label.htmlFor = `setting-${definition.id}`;
    label.textContent = definition.label;
    row.appendChild(label);

    let input;
    const current = preferenceValue(definition.id, null);
    if (definition.type === "boolean") {
      input = document.createElement("input");
      input.type = "checkbox";
      input.checked = Boolean(current);
    } else if (definition.type === "integer") {
      input = document.createElement("input");
      input.type = "number";
      input.value = String(current ?? "");
      input.min = definition.id === "recent_rows_limit" ? "10" : "1";
      input.max = definition.id === "log_retention_days" ? "365" : "500";
    } else {
      input = document.createElement("select");
      for (const optionDef of definition.options) {
        const option = document.createElement("option");
        option.value = optionDef.value;
        option.textContent = optionDef.label;
        if (String(current ?? "") === optionDef.value) {
          option.selected = true;
        }
        input.appendChild(option);
      }
    }
    input.id = `setting-${definition.id}`;
    input.dataset.preferenceId = definition.id;
    input.dataset.preferenceType = definition.type;
    row.appendChild(input);

    const hint = document.createElement("div");
    hint.className = "option-hint";
    hint.textContent = definition.hint;
    row.appendChild(hint);

    settingsPreferencesForm.appendChild(row);
  }
}

function collectDashboardSettingsPayload() {
  const preferences = {};
  const visibility = {};

  for (const input of settingsPreferencesForm.querySelectorAll("[data-preference-id]")) {
    const key = input.dataset.preferenceId;
    const type = input.dataset.preferenceType;
    if (!key || !type) {
      continue;
    }
    if (type === "boolean") {
      preferences[key] = Boolean(input.checked);
    } else if (type === "integer") {
      preferences[key] = Number(input.value);
    } else {
      preferences[key] = String(input.value || "");
    }
  }

  for (const input of settingsServicesList.querySelectorAll("[data-service-visibility]")) {
    visibility[input.dataset.serviceVisibility] = Boolean(input.checked);
  }

  return { preferences, service_visibility: visibility };
}

function applyDashboardSettingsPayload(payload) {
  dashboardSettings = {
    preferences: { ...dashboardSettings.preferences, ...(payload.preferences || {}) },
    service_visibility: { ...(payload.service_visibility || {}) }
  };
  services = services
    .map(service => ({
      ...service,
      visible: dashboardSettings.service_visibility[service.id] ?? true
    }))
    .sort(compareServices);
  tailInput.value = String(currentRecentRowsLimit());
  scheduleAutoRefresh();
}

async function saveDashboardSettings() {
  saveSettingsBtn.disabled = true;
  try {
    const payload = collectDashboardSettingsPayload();
    const result = await apiJson("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    applyDashboardSettingsPayload(result);
    if (advancedServiceId && !isServiceVisible(services.find(service => service.id === advancedServiceId))) {
      stopAdvancedStream();
      advancedServiceId = null;
      advancedPanel.classList.add("hidden");
    }
    await Promise.all([loadServices(), refreshAllStatuses(), refreshAllMetrics(), refreshAllAlerts(), refreshAllLogs(currentRecentRowsLimit())]);
    renderSettingsPanel();
    renderCards();
  } catch (error) {
    window.alert(`Errore salvataggio impostazioni: ${error.message}`);
  } finally {
    saveSettingsBtn.disabled = false;
  }
}

function toggleSettingsPanel(forceOpen = null) {
  const shouldOpen = forceOpen === null ? settingsPanel.classList.contains("hidden") : Boolean(forceOpen);
  settingsPanel.classList.toggle("hidden", !shouldOpen);
  if (shouldOpen) {
    renderSettingsPanel();
  }
}

function scheduleAutoRefresh() {
  if (refreshTimer) {
    window.clearInterval(refreshTimer);
    refreshTimer = null;
  }
  const interval = currentRefreshIntervalMs();
  if (!interval) {
    return;
  }
  refreshTimer = window.setInterval(() => {
    Promise.all([refreshAllStatuses(), refreshAllMetrics(), refreshAllAlerts(), loadDashboardStatus()]).then(() => {
      services = [...services].sort(compareServices);
      renderCards();
      if (advancedServiceId) {
        const service = services.find(s => s.id === advancedServiceId);
        if (service && isServiceVisible(service)) {
          renderAdvancedMeta(service);
          if (supportsAlerts(service)) {
            renderAlertsForAdvanced(service.id);
          }
        } else {
          stopAdvancedStream();
          advancedServiceId = null;
          advancedPanel.classList.add("hidden");
        }
      }
    });
  }, interval);
}

async function killEmAll() {
  if (!window.confirm("Questo fermerà tutti gli MCP e la dashboard. Continuare?")) {
    return;
  }
  killAllBtn.disabled = true;
  refreshAllBtn.disabled = true;
  stopAdvancedStream();
  try {
    await apiJson("/api/control/kill-all", { method: "POST" });
    dashboardPidText.textContent = `PID: ${dashboardStatus.pid || "n/d"} | arresto in corso`;
    widgetGrid.innerHTML = `<article class="widget-card"><div class="widget-title">Shutdown</div><div class="widget-meta">Kill 'em All eseguito. La dashboard si sta arrestando.</div></article>`;
    advancedPanel.classList.add("hidden");
  } catch (error) {
    killAllBtn.disabled = false;
    refreshAllBtn.disabled = false;
    window.alert(`Kill 'em All fallito: ${error.message}`);
  }
}

function renderCards() {
  widgetGrid.innerHTML = "";
  const visibleServices = [...services].sort(compareServices).filter(service => shouldRenderServiceCard(service));

  if (!visibleServices.length) {
    widgetGrid.innerHTML = `<article class="widget-card"><div class="widget-title">Nessun servizio visibile</div><div class="widget-meta">Usa l'icona impostazioni per mostrare servizi o riattivare quelli nascosti.</div></article>`;
    return;
  }

  for (const service of visibleServices) {
    const state = getServiceState(service.id);
    const runtime = getRuntimeStatus(service.id);
    const entries = state.entries || [];
    const last = entries.length > 0 ? entries[0] : null;

    const card = document.createElement("article");
    card.className = "widget-card";

    const head = document.createElement("div");
    head.className = "widget-head";
    const alertPayload = getServiceAlerts(service.id);
    const alertStatus = String(alertPayload.status || "ok").toLowerCase();
    const hasVisibleAlert =
      Boolean(preferenceValue("show_alerts_in_home", true)) &&
      supportsAlerts(service) &&
      Number(alertPayload.triggered_count || 0) > 0;
    head.innerHTML = `
      <div>
        <div class="widget-eyebrow">${serviceGroupLabel(service)}</div>
        <div class="widget-title">${service.name}</div>
      </div>
      <div class="status">
        <span class="dot ${runtimeDotClass(runtime, state)}"></span><span>${runtimeLabel(runtime, state)}</span>
        ${hasVisibleAlert ? `<span class="alert-chip ${alertClass(alertStatus)}">${alertLabel(alertStatus)} ${alertPayload.triggered_count || 0}</span>` : ""}
      </div>
    `;

    const meta = document.createElement("div");
    meta.className = "widget-meta widget-meta-stack";
    const endpoint = runtime.port ? `${runtime.host || "127.0.0.1"}:${runtime.port}` : "n/d";
    const pidLabel = runtime.pid ? `PID ${runtime.pid}` : "PID n/d";
    const lastEvent = serviceLatestEventSummary(last);
    const optsCount = service.control?.options_count || 0;
    const lineOne = document.createElement("div");
    lineOne.textContent = `${endpoint} | ${pidLabel}`;
    const lineTwo = document.createElement("div");
    lineTwo.textContent = `Health: ${healthLabel(runtime)} | Opzioni: ${optsCount}`;
    meta.appendChild(lineOne);
    meta.appendChild(lineTwo);

    const metrics = getServiceMetrics(service.id);
    const kpi = document.createElement("div");
    kpi.className = "widget-kpi";
    kpi.textContent = serviceSummaryLine(service, metrics, runtime);

    const trend = document.createElement("div");
    trend.className = "widget-trend";
    let trendData = metrics.activity_series || [];
    let trendColor = "#73c2ff";
    if (serviceKind(service) === "db") {
      trendData = metrics.db_row_count_series || [];
      trendColor = "#f2b84b";
    } else if (serviceKind(service) === "rag") {
      trendData = metrics.context_retrieval_series || [];
      trendColor = "#7fdc8d";
    }
    trend.innerHTML = sparklineSvg(trendData, trendColor);

    const lastLog = document.createElement("div");
    lastLog.className = "widget-last-log";
    lastLog.textContent = lastEvent;

    const controls = document.createElement("div");
    controls.className = "widget-actions";

    const reloadBtn = document.createElement("button");
    reloadBtn.textContent = "Aggiorna";
    reloadBtn.disabled = state.actionBusy;
    reloadBtn.addEventListener("click", async () => {
      await Promise.all([
        loadServiceTail(service.id, currentRecentRowsLimit()),
        refreshServiceStatus(service.id),
        refreshServiceMetrics(service.id),
        refreshServiceAlerts(service.id)
      ]);
      renderCards();
    });

    const startBtn = document.createElement("button");
    startBtn.textContent = "Start";
    startBtn.className = "btn-ok";
    startBtn.disabled = state.actionBusy || !runtime.control_available || runtime.running;
    startBtn.addEventListener("click", () => controlAction(service.id, "start"));

    const stopActionBtn = document.createElement("button");
    stopActionBtn.textContent = "Stop";
    stopActionBtn.className = "btn-warn";
    stopActionBtn.disabled = state.actionBusy || !runtime.control_available || !runtime.running;
    stopActionBtn.addEventListener("click", () => controlAction(service.id, "stop"));

    const restartBtn = document.createElement("button");
    restartBtn.textContent = "Restart";
    restartBtn.disabled = state.actionBusy || !runtime.control_available || !runtime.running;
    restartBtn.addEventListener("click", () => controlAction(service.id, "restart"));

    const clearBtn = document.createElement("button");
    clearBtn.textContent = "Pulisci Log";
    clearBtn.disabled = state.actionBusy;
    clearBtn.addEventListener("click", () => clearServiceLogs(service.id));

    const advancedBtn = document.createElement("button");
    advancedBtn.textContent = "Avanzate";
    advancedBtn.addEventListener("click", () => openAdvanced(service.id));

    controls.appendChild(reloadBtn);
    controls.appendChild(startBtn);
    controls.appendChild(stopActionBtn);
    controls.appendChild(restartBtn);
    controls.appendChild(clearBtn);
    controls.appendChild(advancedBtn);

    card.appendChild(head);
    card.appendChild(meta);
    card.appendChild(kpi);
    card.appendChild(trend);
    card.appendChild(lastLog);
    card.appendChild(controls);
    widgetGrid.appendChild(card);
  }
}

function renderOptionsForm(serviceId) {
  const options = optionsByService.get(serviceId) || [];
  optionsForm.innerHTML = "";

  optionsPanel.classList.remove("hidden");

  if (!options.length) {
    const empty = document.createElement("div");
    empty.className = "option-empty muted";
    empty.textContent = "Nessuna opzione configurabile per questo servizio.";
    optionsForm.appendChild(empty);
    return;
  }

  for (const opt of options) {
    const row = document.createElement("div");
    row.className = "option-row";

    const label = document.createElement("label");
    label.className = "option-label";
    label.textContent = opt.label || opt.id;
    label.htmlFor = `opt-${opt.id}`;

    const hint = document.createElement("div");
    hint.className = "option-hint";

    let input;
    if (opt.type === "boolean") {
      input = document.createElement("input");
      input.type = "checkbox";
      input.checked = Boolean(opt.value);
      hint.textContent = opt.description || "";
    } else if (opt.type === "integer") {
      input = document.createElement("input");
      input.type = "number";
      input.value = opt.value ?? "";
      hint.textContent = opt.description || "";
    } else if (opt.type === "select") {
      input = document.createElement("select");
      const allowed = opt.allowed_values || [];
      for (const val of allowed) {
        const option = document.createElement("option");
        option.value = val;
        option.textContent = val;
        if (String(opt.value ?? "") === val) {
          option.selected = true;
        }
        input.appendChild(option);
      }
      hint.textContent = opt.description || "";
    } else {
      input = document.createElement("input");
      input.type = opt.secret ? "password" : "text";
      input.value = opt.secret ? "" : (opt.value ?? "");
      if (opt.secret) {
        input.autocomplete = "new-password";
        input.spellcheck = false;
        input.placeholder = opt.is_set ? "******** (già impostata)" : "inserisci valore";
        hint.textContent = `${opt.description || ""} ${opt.is_set ? "Valore presente solo in memoria della dashboard corrente." : "Valore non impostato."} Non verra' salvato su disco.`.trim();
      } else {
        hint.textContent = opt.description || "";
      }
    }

    input.id = `opt-${opt.id}`;
    input.dataset.optionId = opt.id;
    input.dataset.optionType = opt.type;
    input.dataset.secret = opt.secret ? "true" : "false";

    row.appendChild(label);
    row.appendChild(input);
    if (hint.textContent) {
      row.appendChild(hint);
    }
    optionsForm.appendChild(row);
  }
}

function collectOptionsFromForm() {
  const values = {};
  const inputs = optionsForm.querySelectorAll("[data-option-id]");
  for (const el of inputs) {
    const optionId = el.dataset.optionId;
    const type = el.dataset.optionType;
    const isSecret = el.dataset.secret === "true";
    if (!optionId || !type) {
      continue;
    }

    if (type === "boolean") {
      values[optionId] = Boolean(el.checked);
      continue;
    }

    if (type === "integer") {
      if (el.value === "") {
        continue;
      }
      values[optionId] = Number(el.value);
      continue;
    }

    const text = el.value ?? "";

    // Secret string/select: empty means keep current value.
    if (isSecret && !String(text).trim()) {
      continue;
    }

    values[optionId] = text;
  }
  return values;
}

async function loadServices() {
  services = (await apiJson("/api/services"))
    .map((service, index) => ({
      ...normalizeServiceDefinition(service),
      registryIndex: index
    }))
    .sort(compareServices);
  for (const service of services) {
    getServiceState(service.id);
    const runtime = getRuntimeStatus(service.id);
    if (service.control && service.control.enabled) {
      runtime.control_available = true;
      runtime.host = service.control.host || "127.0.0.1";
      runtime.port = service.control.port || null;
    }
  }
}

async function loadServiceTail(serviceId, tail = currentRecentRowsLimit()) {
  const state = getServiceState(serviceId);
  state.loading = true;
  try {
    const payload = await apiJson(`/api/services/${serviceId}/logs?tail=${tail}`);
    state.entries = payload.entries || [];
  } catch {
    state.entries = state.entries || [];
  } finally {
    state.loading = false;
  }
}

async function loadServiceQueries(serviceId, tail = 2000) {
  if (!supportsQueryInspector(serviceId)) {
    queriesByService.set(serviceId, []);
    return;
  }
  try {
    const textParam = advancedFilters.text ? `&text=${encodeURIComponent(advancedFilters.text)}` : "";
    const payload = await apiJson(`/api/services/${serviceId}/queries?tail=${tail}${textParam}`);
    queriesByService.set(serviceId, payload.queries || []);
  } catch {
    queriesByService.set(serviceId, queriesByService.get(serviceId) || []);
  }
}

async function refreshServiceMetrics(serviceId) {
  try {
    const payload = await apiJson(`/api/services/${serviceId}/metrics?tail=2000`);
    metricsByService.set(serviceId, payload);
  } catch {
    metricsByService.set(serviceId, getServiceMetrics(serviceId));
  }
}

async function refreshServiceAlerts(serviceId) {
  try {
    const payload = await apiJson(`/api/services/${serviceId}/alerts?tail=2000`);
    alertsByService.set(serviceId, payload);
  } catch {
    alertsByService.set(serviceId, getServiceAlerts(serviceId));
  }
}

async function loadServiceOptions(serviceId) {
  try {
    const payload = await apiJson(`/api/services/${serviceId}/options`);
    optionsByService.set(serviceId, payload.options || []);
  } catch {
    optionsByService.set(serviceId, []);
  }
}

async function saveServiceOptions(serviceId) {
  const state = getServiceState(serviceId);
  state.optionsBusy = true;
  saveOptionsBtn.disabled = true;

  try {
    const values = collectOptionsFromForm();
    const payload = await apiJson(`/api/services/${serviceId}/options`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ values })
    });
    optionsByService.set(serviceId, payload.options || []);
    renderOptionsForm(serviceId);
  } catch (error) {
    console.error("Save options failed", error);
    alert(`Errore salvataggio opzioni: ${error.message}`);
  } finally {
    state.optionsBusy = false;
    saveOptionsBtn.disabled = false;
  }
}

async function refreshServiceStatus(serviceId) {
  try {
    const status = await apiJson(`/api/services/${serviceId}/status`);
    statusByService.set(serviceId, status);
  } catch (error) {
    const runtime = getRuntimeStatus(serviceId);
    runtime.last_error = error.message;
    statusByService.set(serviceId, runtime);
  }
}

async function refreshAllStatuses() {
  await Promise.all(services.map(service => refreshServiceStatus(service.id)));
}

async function refreshAllMetrics() {
  await Promise.all(services.map(service => refreshServiceMetrics(service.id)));
}

async function refreshAllAlerts() {
  await Promise.all(services.map(service => refreshServiceAlerts(service.id)));
}

async function refreshAllLogs(tail = currentRecentRowsLimit()) {
  await Promise.all(services.map(service => loadServiceTail(service.id, tail)));
}

async function refreshAll(tail = currentRecentRowsLimit()) {
  await Promise.all([refreshAllStatuses(), refreshAllLogs(tail), refreshAllMetrics(), refreshAllAlerts()]);
  services = [...services].sort(compareServices);
  renderCards();
}

async function controlAction(serviceId, action) {
  const state = getServiceState(serviceId);
  state.actionBusy = true;
  state.pendingAction = action;
  renderCards();
  try {
    await apiJson(`/api/services/${serviceId}/${action}`, { method: "POST" });
  } catch (error) {
    console.error(`Control action failed (${serviceId}:${action})`, error);
  } finally {
    state.actionBusy = false;
    state.pendingAction = "";
    await Promise.all([
      refreshServiceStatus(serviceId),
      loadServiceTail(serviceId, currentRecentRowsLimit()),
      refreshServiceMetrics(serviceId),
      refreshServiceAlerts(serviceId)
    ]);
    renderCards();

    if (advancedServiceId === serviceId) {
      await reloadAdvanced();
    }
  }
}

async function loadServiceActivity(serviceId, tail = 2000) {
  if (!supportsActivity(serviceId)) {
    activityByService.set(serviceId, []);
    return;
  }
  try {
    const textParam = advancedFilters.text ? `&text=${encodeURIComponent(advancedFilters.text)}` : "";
    const payload = await apiJson(`/api/services/${serviceId}/activity?tail=${tail}${textParam}`);
    activityByService.set(serviceId, payload.activity || []);
  } catch {
    activityByService.set(serviceId, activityByService.get(serviceId) || []);
  }
}

async function clearServiceLogs(serviceId) {
  await apiJson(`/api/services/${serviceId}/logs/clear`, { method: "POST" });
  const state = getServiceState(serviceId);
  state.entries = [];
  queriesByService.set(serviceId, []);
  renderCards();

  if (advancedServiceId === serviceId) {
    clearAdvancedLogs();
    clearQueryRows();
    await reloadAdvanced();
  }
}

function stopAdvancedStream() {
  if (advancedEventSource) {
    advancedEventSource.close();
    advancedEventSource = null;
  }
  if (advancedServiceId) {
    const service = services.find(item => item.id === advancedServiceId);
    if (service) {
      renderAdvancedMeta(service);
    }
  }
}

function renderAdvancedMeta(service) {
  const runtime = getRuntimeStatus(service.id);
  const uiState = getServiceState(service.id);
  const alertPayload = getServiceAlerts(service.id);
  const runtimeText = runtime.control_available
    ? `${runtimeLabel(runtime, uiState)} @ ${runtime.host || "127.0.0.1"}:${runtime.port || "n/d"}`
    : "control not configured";
  const streamState = advancedEventSource ? "active" : "stopped";
  const sourceSummary = (service.log_sources || []).map(source => sourceSummaryLabel(source)).join("; ") || "n/d";
  const contextMode = serviceKind(service) === "rag" ? llmContextModeLabel(runtime) : "";
  const alertText = supportsAlerts(service)
    ? ` | Alert: ${String(alertPayload.status || "ok").toUpperCase()} (${alertPayload.triggered_count || 0})`
    : "";
  advancedMeta.textContent = `Status: ${runtimeText} | Health: ${healthLabel(runtime)}${contextMode ? ` | ${contextMode}` : ""} | Stream: ${streamState}${alertText} | Sources: ${sourceSummary}`;
}

async function openAdvanced(serviceId) {
  advancedServiceId = serviceId;
  stopAdvancedStream();

  const service = services.find(s => s.id === serviceId);
  if (!service) {
    return;
  }

  await Promise.all([
    refreshServiceStatus(serviceId),
    loadServiceOptions(serviceId),
    refreshServiceMetrics(serviceId),
    refreshServiceAlerts(serviceId)
  ]);

  advancedTitle.textContent = `Dettaglio: ${service.name}`;
  renderAdvancedMeta(service);
  renderOptionsForm(serviceId);
  advancedPanel.classList.remove("hidden");
  setAdvancedTab(pickDefaultAdvancedTab(service, getRuntimeStatus(serviceId)));

  filterLevel.value = advancedFilters.level || "";
  filterChannel.value = advancedFilters.channel || "";
  filterText.value = advancedFilters.text || "";
  rebuildSourceFilterOptions(service);
  if (advancedFilters.source) {
    filterSource.value = advancedFilters.source;
  }
  syncAdvancedFiltersFromInputs();

  const tail = Number(tailInput.value || 200);
  await Promise.all([
    loadServiceTail(serviceId, tail),
    loadServiceQueries(serviceId, Math.max(tail * 8, 500)),
    loadServiceActivity(serviceId, Math.max(tail * 8, 500))
  ]);

  const state = getServiceState(serviceId);
  rebuildEventFilterOptions(state.entries || []);
  if (advancedFilters.event) {
    filterEvent.value = advancedFilters.event;
  }
  syncAdvancedFiltersFromInputs();
  renderAdvancedEntriesForService(serviceId);

  if (supportsQueryInspector(service)) {
    queryPanel.classList.remove("hidden");
    renderQueriesForAdvanced(serviceId);
  } else {
    queryPanel.classList.add("hidden");
    clearQueryRows();
  }
  if (supportsActivity(service)) {
    activityPanel.classList.remove("hidden");
    renderActivityForAdvanced(serviceId);
  } else {
    activityPanel.classList.add("hidden");
    clearActivityRows();
  }
  if (supportsAlerts(service)) {
    alertPanel.classList.remove("hidden");
    renderAlertsForAdvanced(serviceId);
  } else {
    alertPanel.classList.add("hidden");
  }
  if (!supportsInspector(service) && advancedActiveTab === "inspector") {
    setAdvancedTab("logs");
  }
  renderCards();
}

async function reloadAdvanced() {
  if (!advancedServiceId) {
    return;
  }
  syncAdvancedFiltersFromInputs();
  const tail = Number(tailInput.value || 200);
  await Promise.all([
    loadServiceTail(advancedServiceId, tail),
    refreshServiceStatus(advancedServiceId),
    refreshServiceMetrics(advancedServiceId),
    refreshServiceAlerts(advancedServiceId),
    loadServiceQueries(advancedServiceId, Math.max(tail * 8, 500)),
    loadServiceActivity(advancedServiceId, Math.max(tail * 8, 500))
  ]);

  const service = services.find(s => s.id === advancedServiceId);
  if (service) {
    rebuildSourceFilterOptions(service);
    if (advancedFilters.source) {
      filterSource.value = advancedFilters.source;
    }
    renderAdvancedMeta(service);
  }

  const state = getServiceState(advancedServiceId);
  rebuildEventFilterOptions(state.entries || []);
  syncAdvancedFiltersFromInputs();
  renderAdvancedEntriesForService(advancedServiceId);
  if (supportsQueryInspector(advancedServiceId)) {
    renderQueriesForAdvanced(advancedServiceId);
  }
  if (supportsActivity(advancedServiceId)) {
    renderActivityForAdvanced(advancedServiceId);
  }
  if (supportsAlerts(advancedServiceId)) {
    renderAlertsForAdvanced(advancedServiceId);
  }
  renderCards();
}

function startAdvancedStream() {
  if (!advancedServiceId) {
    return;
  }
  stopAdvancedStream();

  advancedEventSource = new EventSource(`/api/services/${advancedServiceId}/logs/stream`);
  const service = services.find(s => s.id === advancedServiceId);
  if (service) {
    renderAdvancedMeta(service);
  }
  advancedEventSource.onmessage = evt => {
    try {
      const entry = JSON.parse(evt.data);
      const state = getServiceState(advancedServiceId);
      state.entries.unshift(entry);
      if (state.entries.length > currentRecentRowsLimit()) {
        state.entries = state.entries.slice(0, currentRecentRowsLimit());
      }
      rebuildEventFilterOptions(state.entries || []);
      if (entryMatchesAdvancedFilters(entry)) {
        appendAdvancedEntries([entry], { prepend: true });
      }
      if (supportsQueryInspector(advancedServiceId) && isDbQueryEvent(entry)) {
        loadServiceQueries(advancedServiceId, 2000).then(() => renderQueriesForAdvanced(advancedServiceId));
      }
      if (supportsActivity(advancedServiceId)) {
        loadServiceActivity(advancedServiceId, 2000).then(() => renderActivityForAdvanced(advancedServiceId));
      }
      Promise.all([
        refreshServiceMetrics(advancedServiceId),
        refreshServiceAlerts(advancedServiceId)
      ]).then(() => {
        renderAlertsForAdvanced(advancedServiceId);
        renderCards();
      });
      renderCards();
    } catch {
      // ignore malformed chunk
    }
  };
  advancedEventSource.onerror = () => {
    const currentService = services.find(s => s.id === advancedServiceId);
    if (currentService) {
      renderAdvancedMeta(currentService);
    }
  };
}

loadBtn.addEventListener("click", reloadAdvanced);
streamBtn.addEventListener("click", startAdvancedStream);
stopBtn.addEventListener("click", stopAdvancedStream);
tabOptionsBtn.addEventListener("click", () => setAdvancedTab("options"));
tabLogsBtn.addEventListener("click", () => setAdvancedTab("logs"));
tabInspectorBtn.addEventListener("click", () => {
  if (supportsInspector(advancedServiceId)) {
    setAdvancedTab("inspector");
  }
});
applyFilterBtn.addEventListener("click", async () => {
  syncAdvancedFiltersFromInputs();
  if (!advancedServiceId) {
    return;
  }
  renderAdvancedEntriesForService(advancedServiceId);
  if (supportsQueryInspector(advancedServiceId)) {
    await loadServiceQueries(advancedServiceId, Math.max(Number(tailInput.value || 200) * 8, 500));
    renderQueriesForAdvanced(advancedServiceId);
  }
  if (supportsActivity(advancedServiceId)) {
    await loadServiceActivity(advancedServiceId, Math.max(Number(tailInput.value || 200) * 8, 500));
    renderActivityForAdvanced(advancedServiceId);
  }
});
clearFilterBtn.addEventListener("click", async () => {
  advancedFilters.level = "";
  advancedFilters.event = "";
  advancedFilters.channel = "";
  advancedFilters.source = "";
  advancedFilters.text = "";
  filterLevel.value = "";
  filterEvent.value = "";
  filterChannel.value = "";
  filterSource.value = "";
  filterText.value = "";
  if (!advancedServiceId) {
    return;
  }
  const state = getServiceState(advancedServiceId);
  rebuildEventFilterOptions(state.entries || []);
  renderAdvancedEntriesForService(advancedServiceId);
  if (supportsQueryInspector(advancedServiceId)) {
    await loadServiceQueries(advancedServiceId, Math.max(Number(tailInput.value || 200) * 8, 500));
    renderQueriesForAdvanced(advancedServiceId);
  }
  if (supportsActivity(advancedServiceId)) {
    await loadServiceActivity(advancedServiceId, Math.max(Number(tailInput.value || 200) * 8, 500));
    renderActivityForAdvanced(advancedServiceId);
  }
});
clearLogsBtn.addEventListener("click", async () => {
  if (!advancedServiceId) {
    return;
  }
  await clearServiceLogs(advancedServiceId);
});
refreshAllBtn.addEventListener("click", () => refreshAll(currentRecentRowsLimit()));
killAllBtn.addEventListener("click", killEmAll);
settingsFab.addEventListener("click", () => toggleSettingsPanel());
closeSettingsBtn.addEventListener("click", () => toggleSettingsPanel(false));
saveSettingsBtn.addEventListener("click", saveDashboardSettings);
reloadAlertsBtn.addEventListener("click", async () => {
  if (!advancedServiceId || !supportsAlerts(advancedServiceId)) {
    return;
  }
  await refreshServiceAlerts(advancedServiceId);
  renderAlertsForAdvanced(advancedServiceId);
  renderCards();
});
reloadQueriesBtn.addEventListener("click", async () => {
  if (!advancedServiceId || !supportsQueryInspector(advancedServiceId)) {
    return;
  }
  await loadServiceQueries(advancedServiceId, Math.max(Number(tailInput.value || 200) * 8, 500));
  renderQueriesForAdvanced(advancedServiceId);
});
reloadActivityBtn.addEventListener("click", async () => {
  if (!advancedServiceId || !supportsActivity(advancedServiceId)) {
    return;
  }
  await loadServiceActivity(advancedServiceId, Math.max(Number(tailInput.value || 200) * 8, 500));
  renderActivityForAdvanced(advancedServiceId);
});
saveOptionsBtn.addEventListener("click", async () => {
  if (!advancedServiceId) {
    return;
  }
  await saveServiceOptions(advancedServiceId);
});

async function boot() {
  await loadServices();
  await loadDashboardSettings();
  await loadDashboardStatus();
  renderSettingsPanel();
  await refreshAll(currentRecentRowsLimit());
  scheduleAutoRefresh();
}

boot().catch(err => {
  widgetGrid.innerHTML = `<article class="widget-card"><div class="widget-title">Errore</div><div class="widget-meta">${err.message}</div></article>`;
});
