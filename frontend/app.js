const widgetGrid = document.getElementById("widgetGrid");
const dashboardPidText = document.getElementById("dashboardPidText");
const killAllBtn = document.getElementById("killAllBtn");
const refreshAllBtn = document.getElementById("refreshAllBtn");
const settingsFab = document.getElementById("settingsFab");
const settingsPanel = document.getElementById("settingsPanel");
const saveSettingsBtn = document.getElementById("saveSettingsBtn");
const closeSettingsBtn = document.getElementById("closeSettingsBtn");
const settingsFlash = document.getElementById("settingsFlash");
const settingsServicesTabBtn = document.getElementById("settingsServicesTabBtn");
const settingsDbTargetsTabBtn = document.getElementById("settingsDbTargetsTabBtn");
const settingsDashboardTabBtn = document.getElementById("settingsDashboardTabBtn");
const settingsVaultTabBtn = document.getElementById("settingsVaultTabBtn");
const settingsServicesView = document.getElementById("settingsServicesView");
const settingsDbTargetsView = document.getElementById("settingsDbTargetsView");
const settingsDashboardView = document.getElementById("settingsDashboardView");
const settingsVaultView = document.getElementById("settingsVaultView");
const settingsServicesList = document.getElementById("settingsServicesList");
const settingsDbTargetsSummary = document.getElementById("settingsDbTargetsSummary");
const dbTargetsList = document.getElementById("dbTargetsList");
const dbTargetEditorMeta = document.getElementById("dbTargetEditorMeta");
const dbTargetEditorForm = document.getElementById("dbTargetEditorForm");
const dbTargetsReloadBtn = document.getElementById("dbTargetsReloadBtn");
const dbTargetNewBtn = document.getElementById("dbTargetNewBtn");
const settingsPreferencesForm = document.getElementById("settingsPreferencesForm");
const vaultStatusCard = document.getElementById("vaultStatusCard");
const vaultControls = document.getElementById("vaultControls");
const vaultEntries = document.getElementById("vaultEntries");

const advancedPanel = document.getElementById("advancedPanel");
const advancedTitle = document.getElementById("advancedTitle");
const advancedMeta = document.getElementById("advancedMeta");
const tabOptionsBtn = document.getElementById("tabOptionsBtn");
const tabLogsBtn = document.getElementById("tabLogsBtn");
const tabInspectorBtn = document.getElementById("tabInspectorBtn");
const tabMemoryBtn = document.getElementById("tabMemoryBtn");
const advancedOptionsView = document.getElementById("advancedOptionsView");
const advancedLogsView = document.getElementById("advancedLogsView");
const advancedInspectorView = document.getElementById("advancedInspectorView");
const advancedMemoryView = document.getElementById("advancedMemoryView");
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
const queryPanelTitle = document.getElementById("queryPanelTitle");
const queryBody = document.getElementById("queryBody");
const reloadQueriesBtn = document.getElementById("reloadQueriesBtn");
const activityPanel = document.getElementById("activityPanel");
const activityPanelTitle = document.getElementById("activityPanelTitle");
const activityBody = document.getElementById("activityBody");
const reloadActivityBtn = document.getElementById("reloadActivityBtn");
const alertPanel = document.getElementById("alertPanel");
const alertSummary = document.getElementById("alertSummary");
const alertList = document.getElementById("alertList");
const reloadAlertsBtn = document.getElementById("reloadAlertsBtn");
const memoryAdminStatus = document.getElementById("memoryAdminStatus");
const memoryAdminSummaryGrid = document.getElementById("memoryAdminSummaryGrid");
const reloadMemoryAdminBtn = document.getElementById("reloadMemoryAdminBtn");
const memoryCandidatesSummary = document.getElementById("memoryCandidatesSummary");
const memoryCandidatesLimitInput = document.getElementById("memoryCandidatesLimitInput");
const memoryCandidatesWorkspaceInput = document.getElementById("memoryCandidatesWorkspaceInput");
const memoryCandidatesProjectInput = document.getElementById("memoryCandidatesProjectInput");
const memoryCandidatesStatusInput = document.getElementById("memoryCandidatesStatusInput");
const memoryCandidatesIncludeResolvedInput = document.getElementById("memoryCandidatesIncludeResolvedInput");
const applyMemoryCandidatesBtn = document.getElementById("applyMemoryCandidatesBtn");
const resetMemoryCandidatesBtn = document.getElementById("resetMemoryCandidatesBtn");
const memoryCandidatesBody = document.getElementById("memoryCandidatesBody");
const memoryDistillationSummary = document.getElementById("memoryDistillationSummary");
const memoryDistillationAgentInput = document.getElementById("memoryDistillationAgentInput");
const memoryDistillationUserInput = document.getElementById("memoryDistillationUserInput");
const memoryDistillationWorkspaceInput = document.getElementById("memoryDistillationWorkspaceInput");
const memoryDistillationProjectInput = document.getElementById("memoryDistillationProjectInput");
const memoryDistillationReasonInput = document.getElementById("memoryDistillationReasonInput");
const memoryDistillationPreparedPre = document.getElementById("memoryDistillationPreparedPre");
const memoryDistillationOutputInput = document.getElementById("memoryDistillationOutputInput");
const memoryDistillationDryRunInput = document.getElementById("memoryDistillationDryRunInput");
const previewMemoryDistillationApplyBtn = document.getElementById("previewMemoryDistillationApplyBtn");
const applyMemoryDistillationBtn = document.getElementById("applyMemoryDistillationBtn");
const resetMemoryDistillationBtn = document.getElementById("resetMemoryDistillationBtn");
const memoryDistillationRunsSummary = document.getElementById("memoryDistillationRunsSummary");
const memoryDistillationRunsLimitInput = document.getElementById("memoryDistillationRunsLimitInput");
const memoryDistillationRunsStatusInput = document.getElementById("memoryDistillationRunsStatusInput");
const reloadMemoryDistillationRunsBtn = document.getElementById("reloadMemoryDistillationRunsBtn");
const resetMemoryDistillationRunsBtn = document.getElementById("resetMemoryDistillationRunsBtn");
const memoryDistillationRunsBody = document.getElementById("memoryDistillationRunsBody");
const memoryDistillationRunDetailPre = document.getElementById("memoryDistillationRunDetailPre");
const memoryAuditSummary = document.getElementById("memoryAuditSummary");
const memoryAuditLimitInput = document.getElementById("memoryAuditLimitInput");
const memoryAuditActionInput = document.getElementById("memoryAuditActionInput");
const memoryAuditActorInput = document.getElementById("memoryAuditActorInput");
const memoryAuditReasonInput = document.getElementById("memoryAuditReasonInput");
const memoryAuditSinceInput = document.getElementById("memoryAuditSinceInput");
const applyMemoryAuditBtn = document.getElementById("applyMemoryAuditBtn");
const resetMemoryAuditBtn = document.getElementById("resetMemoryAuditBtn");
const memoryAuditBody = document.getElementById("memoryAuditBody");
const memoryProjectsSummary = document.getElementById("memoryProjectsSummary");
const memoryProjectsLimitInput = document.getElementById("memoryProjectsLimitInput");
const memoryProjectsWorkspaceInput = document.getElementById("memoryProjectsWorkspaceInput");
const reloadMemoryProjectsBtn = document.getElementById("reloadMemoryProjectsBtn");
const resetMemoryProjectsBtn = document.getElementById("resetMemoryProjectsBtn");
const memoryProjectsBody = document.getElementById("memoryProjectsBody");

const optionsPanel = document.getElementById("optionsPanel");
const optionsForm = document.getElementById("optionsForm");
const saveOptionsBtn = document.getElementById("saveOptionsBtn");

let services = [];
let advancedServiceId = null;
let advancedEventSource = null;
let advancedActiveTab = "options";
let dashboardStatus = { pid: null };
let settingsActiveTab = "services";
let settingsFlashState = null;
let dbTargetsState = {
  loading: false,
  error: "",
  items: [],
  selectedId: "",
  draft: null,
  runtimeExportPath: ""
};
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
let vaultState = {
  initialized: false,
  unlocked: false,
  entry_count: 0,
  entries: []
};
let refreshTimer = null;
let cardRenderTimer = null;
let advancedQueryRefreshTimer = null;
let advancedActivityRefreshTimer = null;
let advancedMetricsAlertsTimer = null;
const LOCAL_VAULT_REF_NAME_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$/;
const stateByService = new Map();
const statusByService = new Map();
const optionsByService = new Map();
const metricsByService = new Map();
const queriesByService = new Map();
const activityByService = new Map();
const alertsByService = new Map();
const memoryAdminByService = new Map();
const advancedFilters = { level: "", event: "", channel: "", source: "", text: "" };

function clearTimer(timerId) {
  if (timerId) {
    window.clearTimeout(timerId);
  }
  return null;
}

function scheduleCardRender(delay = 120) {
  cardRenderTimer = clearTimer(cardRenderTimer);
  cardRenderTimer = window.setTimeout(() => {
    cardRenderTimer = null;
    renderCards();
  }, delay);
}

function scheduleAdvancedQueryRefresh(serviceId, tail = 2000, delay = 180) {
  advancedQueryRefreshTimer = clearTimer(advancedQueryRefreshTimer);
  advancedQueryRefreshTimer = window.setTimeout(async () => {
    advancedQueryRefreshTimer = null;
    if (!advancedServiceId || advancedServiceId !== serviceId || !supportsQueryInspector(serviceId)) {
      return;
    }
    await loadServiceQueries(serviceId, tail);
    if (advancedServiceId === serviceId) {
      renderQueriesForAdvanced(serviceId);
    }
  }, delay);
}

function scheduleAdvancedActivityRefresh(serviceId, tail = 2000, delay = 220) {
  advancedActivityRefreshTimer = clearTimer(advancedActivityRefreshTimer);
  advancedActivityRefreshTimer = window.setTimeout(async () => {
    advancedActivityRefreshTimer = null;
    if (!advancedServiceId || advancedServiceId !== serviceId || !supportsActivity(serviceId)) {
      return;
    }
    await loadServiceActivity(serviceId, tail);
    if (advancedServiceId === serviceId) {
      renderActivityForAdvanced(serviceId);
    }
  }, delay);
}

function scheduleAdvancedMetricsAlertsRefresh(serviceId, delay = 260) {
  advancedMetricsAlertsTimer = clearTimer(advancedMetricsAlertsTimer);
  advancedMetricsAlertsTimer = window.setTimeout(async () => {
    advancedMetricsAlertsTimer = null;
    if (!advancedServiceId || advancedServiceId !== serviceId) {
      return;
    }
    await Promise.all([refreshServiceMetrics(serviceId), refreshServiceAlerts(serviceId)]);
    if (advancedServiceId !== serviceId) {
      return;
    }
    const service = services.find(item => item.id === serviceId);
    if (service) {
      renderAdvancedMeta(service);
    }
    if (supportsAlerts(serviceId)) {
      renderAlertsForAdvanced(serviceId);
    }
    scheduleCardRender(80);
  }, delay);
}

function clearAdvancedRefreshTimers() {
  advancedQueryRefreshTimer = clearTimer(advancedQueryRefreshTimer);
  advancedActivityRefreshTimer = clearTimer(advancedActivityRefreshTimer);
  advancedMetricsAlertsTimer = clearTimer(advancedMetricsAlertsTimer);
}

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

function supportsMemoryAdmin(serviceOrId) {
  return hasCapability(serviceOrId, "memory_admin");
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

function defaultMemoryAdminState() {
  return {
    summary: null,
    summaryError: "",
    candidates: {
      count: 0,
      limit: 20,
      source_count: 0,
      cluster_count: 0,
      filters: {
        workspace_id: "",
        project_id: "",
        include_resolved: false,
        distillation_status: "pending"
      },
      items: []
    },
    candidatesError: "",
    distillation: {
      operator: {
        agent_id: "dashboard-operator",
        user_id: "",
        workspace_id: "",
        project_id: "",
        reason: ""
      },
      prepared: null,
      preparedClusterId: "",
      preparedError: "",
      applyDraft: "",
      applyResult: null,
      applyError: "",
      dryRun: true,
      currentRunId: ""
    },
    runs: {
      count: 0,
      limit: 20,
      filters: {
        status: "",
        workspace_id: "",
        project_id: "",
        agent_id: ""
      },
      items: [],
      selectedRunId: "",
      selectedRun: null
    },
    runsError: "",
    audit: {
      count: 0,
      limit: 50,
      filters: {
        action: "",
        actor: "",
        reason: "",
        since: ""
      },
      items: []
    },
    auditError: "",
    projects: {
      count: 0,
      limit: 50,
      workspace_id: "",
      items: []
    },
    projectsError: ""
  };
}

function getMemoryAdminState(serviceId) {
  if (!memoryAdminByService.has(serviceId)) {
    memoryAdminByService.set(serviceId, defaultMemoryAdminState());
  }
  return memoryAdminByService.get(serviceId);
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
    return "RUNTIME: log letti dall'ambiente di deploy deploy-runtime";
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
    if (preference === "memory" && !supportsMemoryAdmin(service)) {
      return runtime?.running ? "logs" : "options";
    }
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
  if (supportsMemoryAdmin(service)) {
    return "memory";
  }
  return "logs";
}

function inspectorTabLabel(serviceOrId) {
  const hasQuery = supportsQueryInspector(serviceOrId);
  const hasAct = supportsActivity(serviceOrId);
  if (hasQuery && hasAct) {
    return "Inspector";
  }
  if (hasQuery) {
    return "Query";
  }
  if (hasAct) {
    return "Activity";
  }
  return "Inspector";
}

function activityPanelHeading(serviceOrId) {
  const kind = serviceKind(serviceOrId);
  if (kind === "ops" && String(serviceOrId?.id || serviceOrId) === "llm-bitbucket-mcp") {
    return "Bitbucket API Activity";
  }
  if (kind === "memory") {
    return "Memory Activity";
  }
  if (kind === "rag") {
    return "Tool Activity";
  }
  return "Activity";
}

function createSummaryCard(label, value) {
  const card = document.createElement("div");
  card.className = "advanced-summary-card";

  const cardLabel = document.createElement("div");
  cardLabel.className = "advanced-summary-label";
  cardLabel.textContent = label;

  const cardValue = document.createElement("div");
  cardValue.className = "advanced-summary-value";
  cardValue.textContent = value || "n/d";

  card.append(cardLabel, cardValue);
  return card;
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
    },
    {
      name: "memory",
      button: tabMemoryBtn,
      view: advancedMemoryView,
      enabled: supportsMemoryAdmin(advancedServiceId)
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

function clearMemoryAuditRows() {
  while (memoryAuditBody.firstChild) {
    memoryAuditBody.removeChild(memoryAuditBody.firstChild);
  }
}

function clearMemoryCandidateRows() {
  while (memoryCandidatesBody.firstChild) {
    memoryCandidatesBody.removeChild(memoryCandidatesBody.firstChild);
  }
}

function clearMemoryProjectRows() {
  while (memoryProjectsBody.firstChild) {
    memoryProjectsBody.removeChild(memoryProjectsBody.firstChild);
  }
}

function appendEmptyTableRow(tbody, colSpan, text) {
  const tr = document.createElement("tr");
  const td = document.createElement("td");
  td.colSpan = colSpan;
  td.className = "memory-admin-empty";
  td.textContent = text;
  tr.appendChild(td);
  tbody.appendChild(tr);
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

function clampLimitValue(value, fallback = 50) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return fallback;
  }
  return Math.max(1, Math.min(500, Math.trunc(parsed)));
}

function renderMemoryAdminSummaryCards(serviceId) {
  const state = getMemoryAdminState(serviceId);
  memoryAdminSummaryGrid.innerHTML = "";

  if (state.summaryError) {
    memoryAdminSummaryGrid.appendChild(createSummaryCard("Errore", state.summaryError));
    return;
  }

  const summary = state.summary;
  if (!summary) {
    memoryAdminSummaryGrid.appendChild(createSummaryCard("Summary", "n/d"));
    return;
  }

  const counts = summary.counts || {};
  const scopes = summary.scopes || {};
  const settings = summary.settings || {};
  const embedding = summary.embedding?.active_version || null;

  const cards = [
    ["Entries attive", String(counts.active_entries ?? "n/d")],
    ["Entries invalidated", String(counts.invalidated_entries ?? "n/d")],
    ["Projects", String(counts.projects_total ?? "n/d")],
    ["Audit events", String(counts.audit_events_total ?? "n/d")],
    ["Scope attivi", `Project ${scopes.project ?? "n/d"} | Workspace ${scopes.workspace ?? "n/d"} | Global ${scopes.global ?? "n/d"}`],
    ["Settings", `Encryption ${settings.encryption_enabled ? "ON" : "OFF"} | Multi-project ${settings.multi_project_enabled ? "ON" : "OFF"}`],
    [
      "Embedding",
      embedding
        ? `${embedding.provider_id || "provider"} | ${embedding.model_id || "model"} | dim ${embedding.dimension ?? "n/d"}`
        : "Nessuna versione attiva"
    ],
    ["Latest audit", summary.latest_audit_at ? formatTimestamp(summary.latest_audit_at) : "n/d"]
  ];

  for (const [label, value] of cards) {
    memoryAdminSummaryGrid.appendChild(createSummaryCard(label, value));
  }
}

function renderMemoryCandidatesTable(serviceId) {
  const state = getMemoryAdminState(serviceId);
  clearMemoryCandidateRows();

  if (state.candidatesError) {
    memoryCandidatesSummary.textContent = `Errore candidates: ${state.candidatesError}`;
    appendEmptyTableRow(memoryCandidatesBody, 7, "Impossibile caricare la candidate queue.");
    return;
  }

  const candidates = state.candidates || {
    count: 0,
    limit: 20,
    source_count: 0,
    cluster_count: 0,
    filters: {},
    items: []
  };
  const filters = candidates.filters || {};
  memoryCandidatesSummary.textContent =
    `Candidati: ${candidates.count || 0} | Pool ${candidates.source_count || 0} | Cluster ${candidates.cluster_count || 0}` +
    `${filters.workspace_id ? ` | Workspace ${filters.workspace_id}` : ""}` +
    `${filters.project_id ? ` | Project ${filters.project_id}` : ""}` +
    `${filters.include_resolved ? " | Include resolved" : ""}` +
    `${filters.distillation_status ? ` | Status ${filters.distillation_status}` : ""}`;

  if (!Array.isArray(candidates.items) || candidates.items.length === 0) {
    appendEmptyTableRow(memoryCandidatesBody, 7, "Nessun candidato disponibile per i filtri correnti.");
    return;
  }

  const frag = document.createDocumentFragment();
  for (const item of candidates.items) {
    const tr = document.createElement("tr");

    const scoreTd = document.createElement("td");
    scoreTd.textContent = typeof item.candidate_score === "number" ? item.candidate_score.toFixed(3) : "n/d";

    const clusterTd = document.createElement("td");
    const clusterWrap = document.createElement("div");
    clusterWrap.className = "memory-admin-stack";
    const clusterId = document.createElement("div");
    clusterId.textContent = item.cluster_id || "n/d";
    applyTooltip(clusterId, item.cluster_key || item.cluster_id || "Cluster non disponibile");
    const clusterKind = document.createElement("div");
    clusterKind.className = "muted";
    clusterKind.textContent = item.representative_kind || item.representative_event_type || "n/d";
    clusterWrap.append(clusterId, clusterKind);
    clusterTd.appendChild(clusterWrap);

    const scopeTd = document.createElement("td");
    const scopeWrap = document.createElement("div");
    scopeWrap.className = "memory-admin-stack";
    for (const value of [item.product_area, item.component, item.feature].filter(Boolean)) {
      const chip = document.createElement("span");
      chip.className = "memory-admin-chip";
      chip.textContent = value;
      scopeWrap.appendChild(chip);
    }
    if (!scopeWrap.childNodes.length) {
      scopeWrap.textContent = "n/d";
    }
    scopeTd.appendChild(scopeWrap);

    const signalsTd = document.createElement("td");
    const signalsWrap = document.createElement("div");
    signalsWrap.className = "memory-admin-stack";
    const signalMeta = document.createElement("div");
    signalMeta.textContent =
      `members ${item.member_count ?? "n/d"} | recurrence ${item.recurrence_total ?? "n/d"} | sessions ${item.distinct_session_count ?? "n/d"}`;
    signalsWrap.appendChild(signalMeta);
    const reasonsWrap = document.createElement("div");
    reasonsWrap.className = "memory-admin-chip-list";
    for (const reason of Array.isArray(item.reasons) ? item.reasons : []) {
      const chip = document.createElement("span");
      chip.className = "memory-admin-chip";
      chip.textContent = reason;
      reasonsWrap.appendChild(chip);
    }
    if (reasonsWrap.childNodes.length) {
      signalsWrap.appendChild(reasonsWrap);
    }
    signalsTd.appendChild(signalsWrap);

    const entriesTd = document.createElement("td");
    const entriesWrap = document.createElement("div");
    entriesWrap.className = "memory-admin-stack";
    const entryMeta = document.createElement("div");
    entryMeta.textContent = `anchor ${item.representative_entry_id || "n/d"} | unresolved ${item.unresolved_count ?? "n/d"}`;
    entriesWrap.appendChild(entryMeta);
    const entryIds = document.createElement("div");
    entryIds.className = "muted";
    entryIds.textContent = Array.isArray(item.member_entry_ids) ? item.member_entry_ids.join(", ") : "n/d";
    entriesWrap.appendChild(entryIds);
    entriesTd.appendChild(entriesWrap);

    const previewTd = document.createElement("td");
    const previewPre = document.createElement("pre");
    previewPre.className = "message-preview";
    previewPre.textContent = item.content_preview || "";
    previewTd.appendChild(previewPre);

    const actionTd = document.createElement("td");
    const prepareBtn = document.createElement("button");
    prepareBtn.type = "button";
    prepareBtn.textContent = "Prepare";
    prepareBtn.addEventListener("click", () => prepareDistillationForCluster(serviceId, item.cluster_id));
    actionTd.appendChild(prepareBtn);

    tr.append(scoreTd, clusterTd, scopeTd, signalsTd, entriesTd, previewTd, actionTd);
    frag.appendChild(tr);
  }

  memoryCandidatesBody.appendChild(frag);
}

function renderMemoryDistillationPanel(serviceId) {
  const state = getMemoryAdminState(serviceId);
  const distillation = state.distillation || {};
  const prepared = distillation.prepared;
  const applyResult = distillation.applyResult;

  let statusText = distillation.currentRunId
    ? `Run attiva ${distillation.currentRunId}.`
    : "Nessun pack preparato.";
  if (distillation.preparedError) {
    statusText = `Errore prepare: ${distillation.preparedError}`;
  } else if (distillation.applyError) {
    statusText = `Errore apply: ${distillation.applyError}`;
  } else if (applyResult && applyResult.success) {
    statusText = applyResult.dry_run
      ? `Preview apply completata su ${applyResult.count || 0} decisioni${distillation.currentRunId ? ` | run ${distillation.currentRunId}` : ""}.`
      : `Apply completato su ${applyResult.count || 0} decisioni${distillation.currentRunId ? ` | run ${distillation.currentRunId}` : ""}.`;
  } else if (prepared) {
    statusText = `Prepared ${prepared.prepared_count || 0} candidati` +
      `${distillation.preparedClusterId ? ` | cluster ${distillation.preparedClusterId}` : ""}` +
      `${distillation.currentRunId ? ` | run ${distillation.currentRunId}` : ""}`;
  }

  memoryDistillationSummary.textContent = statusText;
  memoryDistillationPreparedPre.textContent = prepared
    ? JSON.stringify(
        {
          run_id: prepared.run_id || distillation.currentRunId || null,
          prepared_count: prepared.prepared_count,
          reason: prepared.reason,
          protection: prepared.protection,
          candidates: prepared.candidates,
          contract: prepared.contract,
          prompt: prepared.prompt
        },
        null,
        2
      )
    : "";
  if (document.activeElement !== memoryDistillationOutputInput) {
    memoryDistillationOutputInput.value = distillation.applyDraft || "";
  }
  memoryDistillationDryRunInput.checked = distillation.dryRun !== false;
}

function clearMemoryDistillationRunsRows() {
  memoryDistillationRunsBody.innerHTML = "";
}

async function selectMemoryDistillationRun(serviceId, runId) {
  if (!runId) {
    return;
  }
  await loadMemoryDistillationRunDetail(serviceId, runId);
  const state = getMemoryAdminState(serviceId);
  const selectedRun = state.runs?.selectedRun || null;
  state.distillation = {
    ...(state.distillation || {}),
    currentRunId: runId,
    prepared: selectedRun?.prepared_payload || state.distillation?.prepared || null,
    preparedClusterId: Array.isArray(selectedRun?.cluster_ids) && selectedRun.cluster_ids.length === 1
      ? selectedRun.cluster_ids[0]
      : (state.distillation?.preparedClusterId || "")
  };
  syncMemoryDistillationInputsFromState(serviceId);
  renderMemoryAdminForAdvanced(serviceId);
}

function renderMemoryDistillationRunsPanel(serviceId) {
  const state = getMemoryAdminState(serviceId);
  clearMemoryDistillationRunsRows();

  if (state.runsError) {
    memoryDistillationRunsSummary.textContent = `Errore runs: ${state.runsError}`;
    memoryDistillationRunDetailPre.textContent = "";
    appendEmptyTableRow(memoryDistillationRunsBody, 6, "Impossibile caricare la run history.");
    return;
  }

  const runs = state.runs || { count: 0, limit: 20, filters: {}, items: [], selectedRunId: "", selectedRun: null };
  const filters = runs.filters || {};
  memoryDistillationRunsSummary.textContent = `Runs: ${runs.count || 0} | Limit ${runs.limit || 20}` +
    `${filters.status ? ` | Status ${filters.status}` : ""}`;
  memoryDistillationRunDetailPre.textContent = runs.selectedRun ? JSON.stringify(runs.selectedRun, null, 2) : "";

  if (!Array.isArray(runs.items) || runs.items.length === 0) {
    appendEmptyTableRow(memoryDistillationRunsBody, 6, "Nessuna run per i filtri correnti.");
    return;
  }

  const frag = document.createDocumentFragment();
  for (const item of runs.items) {
    const tr = document.createElement("tr");
    if (runs.selectedRunId && item.id === runs.selectedRunId) {
      tr.className = "memory-admin-row-selected";
    }

    const runTd = document.createElement("td");
    runTd.textContent = item.id || "n/d";

    const statusTd = document.createElement("td");
    statusTd.textContent = item.status || "n/d";

    const scopeTd = document.createElement("td");
    scopeTd.textContent = `${item.workspace_id || "n/d"} / ${item.project_id || "n/d"}`;

    const countsTd = document.createElement("td");
    countsTd.textContent = `clusters ${(item.cluster_ids || []).length} | entries ${(item.source_entry_ids || []).length} | prepared ${item.prepared_count ?? 0}`;

    const updatedTd = document.createElement("td");
    updatedTd.textContent = formatTimestamp(item.updated_at);
    applyTooltip(updatedTd, item.updated_at || "Timestamp non disponibile");

    const actionTd = document.createElement("td");
    const openBtn = document.createElement("button");
    openBtn.type = "button";
    openBtn.textContent = "Bind";
    openBtn.addEventListener("click", () => selectMemoryDistillationRun(serviceId, item.id));
    actionTd.appendChild(openBtn);

    tr.append(runTd, statusTd, scopeTd, countsTd, updatedTd, actionTd);
    frag.appendChild(tr);
  }

  memoryDistillationRunsBody.appendChild(frag);
}

function renderMemoryAuditTable(serviceId) {
  const state = getMemoryAdminState(serviceId);
  clearMemoryAuditRows();

  if (state.auditError) {
    memoryAuditSummary.textContent = `Errore audit: ${state.auditError}`;
    appendEmptyTableRow(memoryAuditBody, 6, "Impossibile caricare l'audit trail.");
    return;
  }

  const audit = state.audit || { count: 0, limit: 50, filters: {}, items: [] };
  const filters = audit.filters || {};
  const activeFilters = [filters.action, filters.actor, filters.reason, filters.since].filter(Boolean).length;
  memoryAuditSummary.textContent = `Eventi: ${audit.count || 0} | Limit ${audit.limit || 50} | Filtri attivi ${activeFilters}`;

  if (!Array.isArray(audit.items) || audit.items.length === 0) {
    appendEmptyTableRow(memoryAuditBody, 6, "Nessun evento audit per i filtri correnti.");
    return;
  }

  const frag = document.createDocumentFragment();
  for (const item of audit.items) {
    const tr = document.createElement("tr");

    const timeTd = document.createElement("td");
    timeTd.textContent = formatTimestamp(item.created_at || item.timestamp);
    applyTooltip(timeTd, item.created_at || item.timestamp || "Timestamp non disponibile");

    const actionTd = document.createElement("td");
    actionTd.textContent = item.action || "n/d";

    const actorTd = document.createElement("td");
    actorTd.textContent = item.actor || "n/d";

    const entryTd = document.createElement("td");
    entryTd.textContent = item.entry_id || "n/d";

    const reasonTd = document.createElement("td");
    reasonTd.textContent = item.reason || "n/d";

    const previewTd = document.createElement("td");
    const previewPre = document.createElement("pre");
    previewPre.className = "message-preview";
    previewPre.textContent = item.payload_preview || "";
    previewTd.appendChild(previewPre);

    tr.append(timeTd, actionTd, actorTd, entryTd, reasonTd, previewTd);
    frag.appendChild(tr);
  }

  memoryAuditBody.appendChild(frag);
}

function renderMemoryProjectsTable(serviceId) {
  const state = getMemoryAdminState(serviceId);
  clearMemoryProjectRows();

  if (state.projectsError) {
    memoryProjectsSummary.textContent = `Errore progetti: ${state.projectsError}`;
    appendEmptyTableRow(memoryProjectsBody, 6, "Impossibile caricare i progetti.");
    return;
  }

  const projects = state.projects || { count: 0, limit: 50, workspace_id: "", items: [] };
  memoryProjectsSummary.textContent = `Progetti: ${projects.count || 0} | Limit ${projects.limit || 50}${projects.workspace_id ? ` | Workspace ${projects.workspace_id}` : ""}`;

  if (!Array.isArray(projects.items) || projects.items.length === 0) {
    appendEmptyTableRow(memoryProjectsBody, 6, "Nessun progetto disponibile per i filtri correnti.");
    return;
  }

  const frag = document.createDocumentFragment();
  for (const item of projects.items) {
    const tr = document.createElement("tr");

    const projectTd = document.createElement("td");
    projectTd.textContent = item.project_id || "n/d";

    const workspaceTd = document.createElement("td");
    workspaceTd.textContent = item.workspace_id || "n/d";

    const nameTd = document.createElement("td");
    nameTd.textContent = item.display_name || "n/d";

    const activeTd = document.createElement("td");
    activeTd.textContent = String(item.active_entry_count ?? "n/d");

    const totalTd = document.createElement("td");
    totalTd.textContent = String(item.entry_count ?? "n/d");

    const updatedTd = document.createElement("td");
    updatedTd.textContent = formatTimestamp(item.updated_at);
    applyTooltip(updatedTd, item.updated_at || "Timestamp non disponibile");

    tr.append(projectTd, workspaceTd, nameTd, activeTd, totalTd, updatedTd);
    frag.appendChild(tr);
  }

  memoryProjectsBody.appendChild(frag);
}

function renderMemoryAdminForAdvanced(serviceId) {
  if (!supportsMemoryAdmin(serviceId)) {
    return;
  }

  const state = getMemoryAdminState(serviceId);
  const errors = [state.summaryError, state.candidatesError, state.runsError, state.auditError, state.projectsError].filter(Boolean);
  memoryAdminStatus.textContent = errors.length
    ? `Surface admin locale con errori: ${errors.join(" | ")}`
    : "Surface admin locale raggiungibile.";

  renderMemoryAdminSummaryCards(serviceId);
  renderMemoryCandidatesTable(serviceId);
  renderMemoryDistillationPanel(serviceId);
  renderMemoryDistillationRunsPanel(serviceId);
  renderMemoryAuditTable(serviceId);
  renderMemoryProjectsTable(serviceId);
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

    const targetTd = document.createElement("td");
    targetTd.textContent = query.target_id || "n/d";

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
    tr.appendChild(targetTd);
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

function optionGroupDefinitions(serviceId) {
  return [
    {
      id: "credentials",
      title: "Credenziali e Secret",
      description: "Valori sensibili o token richiesti al bootstrap del servizio.",
      match: opt => Boolean(opt.secret) || /(connection|secret|token|vault|password)/i.test(opt.id)
    },
    {
      id: "policy",
      title: "Policy e limiti",
      description: "Flag operativi, limiti e regole che modellano il comportamento del target.",
      match: opt => /(read|write|status|max_|limit|policy|anonym|mode|allowed_tools)/i.test(opt.id)
    },
    {
      id: "provider-runtime",
      title: "Provider Runtime",
      description: "Endpoint locali dei provider AI usati dai target che richiedono classificazione.",
      match: opt => /(provider|model|base_url|endpoint)/i.test(opt.id)
    },
    {
      id: "global-anon",
      title: "Global Anonymization",
      description: "Impostazioni globali del core di anonimizzazione condiviso.",
      match: opt => ["anon_hash_salt", "anon_field_identification", "anon_fail_open"].includes(opt.id)
    }
  ];
}

function createOptionRow(opt) {
  const row = document.createElement("div");
  row.className = "option-row";

  const header = document.createElement("div");
  header.className = "option-header";

  const label = document.createElement("label");
  label.className = "option-label";
  label.textContent = opt.label || opt.id;
  label.htmlFor = `opt-${opt.id}`;

  const badges = document.createElement("div");
  badges.className = "option-badges";

  const persistenceBadge = document.createElement("span");
  const isVaultSource = opt.secret && opt.secret_source === "vault";
  persistenceBadge.className = `option-badge ${opt.secret && !isVaultSource ? "option-badge-runtime" : "option-badge-persisted"}`;
  persistenceBadge.textContent = opt.secret ? (isVaultSource ? "Ref persisted" : "Runtime only") : "Persisted";
  badges.appendChild(persistenceBadge);

  if (opt.secret) {
    const secretBadge = document.createElement("span");
    secretBadge.className = "option-badge option-badge-secret";
    secretBadge.textContent = "Secret";
    badges.appendChild(secretBadge);
  }

  const hint = document.createElement("div");
  hint.className = "option-hint";

  if (opt.secret) {
    row.dataset.secretOption = "true";
    row.dataset.secretOptionId = opt.id;

    const sourceSelect = document.createElement("select");
    sourceSelect.dataset.optionSource = opt.id;
    sourceSelect.className = "secret-source-select";
    sourceSelect.innerHTML = `
      <option value="session">Sessione corrente</option>
      <option value="vault">Riferimento Local Vault</option>
    `;
    sourceSelect.value = opt.secret_source === "vault" ? "vault" : "session";

    const secretBody = document.createElement("div");
    secretBody.className = "secret-option-body";

    const sessionInput = document.createElement("input");
    sessionInput.type = "password";
    sessionInput.autocomplete = "new-password";
    sessionInput.spellcheck = false;
    sessionInput.dataset.optionSessionValue = opt.id;
    sessionInput.placeholder = opt.is_set && opt.secret_source === "session" ? "******** (già impostata)" : "inserisci valore";

    const vaultSelect = document.createElement("select");
    vaultSelect.dataset.optionVaultRef = opt.id;
    const currentRef = opt.vault_ref || "";
    const refs = [...new Set((vaultState.entries || []).map(entry => entry.ref).concat(currentRef ? [currentRef] : []))].sort();
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = refs.length ? "seleziona riferimento Local Vault" : "nessun ref nel Local Vault";
    vaultSelect.appendChild(placeholder);
    for (const ref of refs) {
      const option = document.createElement("option");
      option.value = ref;
      option.textContent = ref;
      if (currentRef === ref) {
        option.selected = true;
      }
      vaultSelect.appendChild(option);
    }

    const updateSecretMode = () => {
      const useVault = sourceSelect.value === "vault";
      sessionInput.classList.toggle("hidden", useVault);
      vaultSelect.classList.toggle("hidden", !useVault);
    };
    sourceSelect.addEventListener("change", updateSecretMode);
    updateSecretMode();

    const sourceHint = document.createElement("div");
    sourceHint.className = "option-hint";
    sourceHint.textContent = opt.status_message || opt.description || "";

    hint.textContent = opt.description || "";
    header.append(label, badges);
    row.appendChild(header);
    row.appendChild(sourceSelect);
    secretBody.appendChild(sessionInput);
    secretBody.appendChild(vaultSelect);
    row.appendChild(secretBody);
    if (sourceHint.textContent) {
      row.appendChild(sourceHint);
    }
    if (hint.textContent && hint.textContent !== sourceHint.textContent) {
      row.appendChild(hint);
    }
    return row;
  }

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

  header.append(label, badges);
  row.appendChild(header);
  row.appendChild(input);
  if (hint.textContent) {
    row.appendChild(hint);
  }
  return row;
}

function renderOptionGroup(container, title, description, options) {
  if (!options.length) {
    return;
  }

  const section = document.createElement("section");
  section.className = "option-group";

  const heading = document.createElement("h4");
  heading.className = "option-group-title";
  heading.textContent = title;
  section.appendChild(heading);

  if (description) {
    const descriptionNode = document.createElement("p");
    descriptionNode.className = "option-group-description muted";
    descriptionNode.textContent = description;
    section.appendChild(descriptionNode);
  }

  const body = document.createElement("div");
  body.className = "option-group-body";
  for (const opt of options) {
    body.appendChild(createOptionRow(opt));
  }

  section.appendChild(body);
  container.appendChild(section);
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

async function loadMemoryAdminSummary(serviceId) {
  if (!supportsMemoryAdmin(serviceId)) {
    return;
  }
  const state = getMemoryAdminState(serviceId);
  try {
    const payload = await apiJson(`/api/services/${serviceId}/memory-admin/summary`);
    state.summary = payload.summary || null;
    state.summaryError = "";
  } catch (error) {
    state.summary = null;
    state.summaryError = error.message;
  }
}

async function loadMemoryAdminCandidates(serviceId) {
  if (!supportsMemoryAdmin(serviceId)) {
    return;
  }
  const state = getMemoryAdminState(serviceId);
  const filters = state.candidates?.filters || {};
  const params = new URLSearchParams();
  params.set("limit", String(Math.max(1, Math.min(200, clampLimitValue(state.candidates?.limit, 20)))));
  if (filters.workspace_id) params.set("workspace_id", filters.workspace_id);
  if (filters.project_id) params.set("project_id", filters.project_id);
  if (filters.include_resolved) params.set("include_resolved", "true");
  if (filters.distillation_status) params.set("distillation_status", filters.distillation_status);

  try {
    const payload = await apiJson(`/api/services/${serviceId}/memory-admin/candidates?${params.toString()}`);
    state.candidates = payload.candidates || {
      count: 0,
      limit: 20,
      source_count: 0,
      cluster_count: 0,
      filters: {},
      items: []
    };
    state.candidatesError = "";
  } catch (error) {
    state.candidates = {
      ...(state.candidates || {}),
      count: 0,
      source_count: 0,
      cluster_count: 0,
      items: []
    };
    state.candidatesError = error.message;
  }
}

async function loadMemoryDistillationRunDetail(serviceId, runId) {
  if (!supportsMemoryAdmin(serviceId) || !runId) {
    return;
  }
  const state = getMemoryAdminState(serviceId);
  try {
    const payload = await apiJson(`/api/services/${serviceId}/memory-admin/distillation/runs/${encodeURIComponent(runId)}`);
    state.runs = {
      ...(state.runs || {}),
      selectedRunId: runId,
      selectedRun: payload.run || null
    };
    state.runsError = "";
  } catch (error) {
    state.runs = {
      ...(state.runs || {}),
      selectedRunId: runId,
      selectedRun: null
    };
    state.runsError = error.message;
  }
}

async function loadMemoryDistillationRuns(serviceId, options = {}) {
  if (!supportsMemoryAdmin(serviceId)) {
    return;
  }
  const state = getMemoryAdminState(serviceId);
  const filters = state.runs?.filters || {};
  const params = new URLSearchParams();
  params.set("limit", String(Math.max(1, Math.min(200, clampLimitValue(state.runs?.limit, 20)))));
  if (filters.workspace_id) params.set("workspace_id", filters.workspace_id);
  if (filters.project_id) params.set("project_id", filters.project_id);
  if (filters.agent_id) params.set("agent_id", filters.agent_id);
  if (filters.status) params.set("status", filters.status);

  try {
    const payload = await apiJson(`/api/services/${serviceId}/memory-admin/distillation/runs?${params.toString()}`);
    const runsPayload = payload.runs || { count: 0, limit: 20, filters: {}, items: [] };
    const items = Array.isArray(runsPayload.items) ? runsPayload.items : [];
    const preferredRunId = String(options?.preferredRunId || "").trim();
    const previousSelectedRunId = preferredRunId || String(state.runs?.selectedRunId || "").trim();
    const selectedRunId = items.some(item => item.id === previousSelectedRunId)
      ? previousSelectedRunId
      : (items[0]?.id || "");

    state.runs = {
      ...runsPayload,
      items,
      selectedRunId,
      selectedRun: state.runs?.selectedRun && state.runs.selectedRun.id === selectedRunId
        ? state.runs.selectedRun
        : null
    };
    state.runsError = "";

    if (selectedRunId) {
      await loadMemoryDistillationRunDetail(serviceId, selectedRunId);
    } else {
      state.runs = {
        ...(state.runs || {}),
        selectedRunId: "",
        selectedRun: null
      };
    }
  } catch (error) {
    state.runs = {
      ...(state.runs || {}),
      count: 0,
      items: [],
      selectedRunId: "",
      selectedRun: null
    };
    state.runsError = error.message;
  }
}

async function loadMemoryAdminAudit(serviceId) {
  if (!supportsMemoryAdmin(serviceId)) {
    return;
  }
  const state = getMemoryAdminState(serviceId);
  const filters = state.audit?.filters || {};
  const params = new URLSearchParams();
  params.set("limit", String(clampLimitValue(state.audit?.limit, 50)));
  if (filters.action) params.set("action", filters.action);
  if (filters.actor) params.set("actor", filters.actor);
  if (filters.reason) params.set("reason", filters.reason);
  if (filters.since) params.set("since", filters.since);

  try {
    const payload = await apiJson(`/api/services/${serviceId}/memory-admin/audit?${params.toString()}`);
    state.audit = payload.audit || { count: 0, limit: 50, filters: {}, items: [] };
    state.auditError = "";
  } catch (error) {
    state.audit = {
      ...(state.audit || {}),
      count: 0,
      items: []
    };
    state.auditError = error.message;
  }
}

async function loadMemoryAdminProjects(serviceId) {
  if (!supportsMemoryAdmin(serviceId)) {
    return;
  }
  const state = getMemoryAdminState(serviceId);
  const params = new URLSearchParams();
  params.set("limit", String(clampLimitValue(state.projects?.limit, 50)));
  if (state.projects?.workspace_id) {
    params.set("workspace_id", state.projects.workspace_id);
  }

  try {
    const payload = await apiJson(`/api/services/${serviceId}/memory-admin/projects?${params.toString()}`);
    state.projects = payload.projects || { count: 0, limit: 50, workspace_id: "", items: [] };
    state.projectsError = "";
  } catch (error) {
    state.projects = {
      ...(state.projects || {}),
      count: 0,
      items: []
    };
    state.projectsError = error.message;
  }
}

async function loadMemoryAdminAll(serviceId) {
  if (!supportsMemoryAdmin(serviceId)) {
    return;
  }
  await Promise.all([
    loadMemoryAdminSummary(serviceId),
    loadMemoryAdminCandidates(serviceId),
    loadMemoryDistillationRuns(serviceId),
    loadMemoryAdminAudit(serviceId),
    loadMemoryAdminProjects(serviceId)
  ]);
}

function syncMemoryDistillationStateFromInputs(serviceId) {
  const state = getMemoryAdminState(serviceId);
  state.distillation = {
    ...(state.distillation || {}),
    operator: {
      agent_id: String(memoryDistillationAgentInput.value || "").trim(),
      user_id: String(memoryDistillationUserInput.value || "").trim(),
      workspace_id: String(memoryDistillationWorkspaceInput.value || "").trim(),
      project_id: String(memoryDistillationProjectInput.value || "").trim(),
      reason: String(memoryDistillationReasonInput.value || "").trim()
    },
    applyDraft: String(memoryDistillationOutputInput.value || ""),
    dryRun: Boolean(memoryDistillationDryRunInput.checked)
  };
}

function syncMemoryDistillationInputsFromState(serviceId) {
  const state = getMemoryAdminState(serviceId);
  const operator = state.distillation?.operator || {};
  memoryDistillationAgentInput.value = operator.agent_id || "dashboard-operator";
  memoryDistillationUserInput.value = operator.user_id || "";
  memoryDistillationWorkspaceInput.value = operator.workspace_id || "";
  memoryDistillationProjectInput.value = operator.project_id || "";
  memoryDistillationReasonInput.value = operator.reason || "";
  memoryDistillationDryRunInput.checked = state.distillation?.dryRun !== false;
  if (document.activeElement !== memoryDistillationOutputInput) {
    memoryDistillationOutputInput.value = state.distillation?.applyDraft || "";
  }
}

async function prepareDistillationForCluster(serviceId, clusterId) {
  if (!supportsMemoryAdmin(serviceId)) {
    return;
  }
  const state = getMemoryAdminState(serviceId);
  syncMemoryDistillationStateFromInputs(serviceId);
  const operator = state.distillation?.operator || {};
  const candidateFilters = state.candidates?.filters || {};
  const payload = {
    agent_id: operator.agent_id || "dashboard-operator",
    user_id: operator.user_id || null,
    workspace_id: operator.workspace_id || candidateFilters.workspace_id || null,
    project_id: operator.project_id || candidateFilters.project_id || null,
    reason: operator.reason || `prepare cluster ${clusterId} from dashboard`,
    cluster_id: clusterId,
    top_k: 1,
    include_resolved: Boolean(candidateFilters.include_resolved),
    distillation_status: candidateFilters.distillation_status || "pending"
  };

  try {
    const response = await apiJson(`/api/services/${serviceId}/memory-admin/distillation/prepare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    state.distillation = {
      ...(state.distillation || {}),
      operator: {
        ...operator,
        agent_id: payload.agent_id,
        user_id: payload.user_id || "",
        workspace_id: payload.workspace_id || "",
        project_id: payload.project_id || "",
        reason: payload.reason
      },
      prepared: response.distillation_prepare || null,
      preparedClusterId: clusterId,
      preparedError: "",
      applyError: "",
      applyResult: null,
      currentRunId: response.distillation_prepare?.run_id || ""
    };
  } catch (error) {
    state.distillation = {
      ...(state.distillation || {}),
      prepared: null,
      preparedClusterId: clusterId,
      preparedError: error.message
    };
  }

  await loadMemoryDistillationRuns(serviceId, {
    preferredRunId: state.distillation?.currentRunId || state.distillation?.prepared?.run_id || ""
  });
  syncMemoryDistillationInputsFromState(serviceId);
  renderMemoryAdminForAdvanced(serviceId);
}

async function applyMemoryDistillation(serviceId, dryRun) {
  if (!supportsMemoryAdmin(serviceId)) {
    return;
  }
  const state = getMemoryAdminState(serviceId);
  syncMemoryDistillationStateFromInputs(serviceId);
  const operator = state.distillation?.operator || {};
  const activeRunId = String(state.distillation?.currentRunId || state.distillation?.prepared?.run_id || "").trim();
  if (!activeRunId) {
    state.distillation = {
      ...(state.distillation || {}),
      dryRun,
      applyError: "Prepare o seleziona una distillation run prima di eseguire preview/apply.",
      applyResult: null
    };
    renderMemoryAdminForAdvanced(serviceId);
    return;
  }

  let parsed;
  try {
    parsed = JSON.parse(state.distillation?.applyDraft || "{}");
  } catch (error) {
    state.distillation = {
      ...(state.distillation || {}),
      applyError: `JSON non valido: ${error.message}`,
      applyResult: null,
      dryRun
    };
    renderMemoryAdminForAdvanced(serviceId);
    return;
  }

  const payload = {
    agent_id: operator.agent_id || "dashboard-operator",
    user_id: operator.user_id || null,
    workspace_id: operator.workspace_id || null,
    project_id: operator.project_id || null,
    reason: operator.reason || "apply distillation from dashboard",
    run_id: activeRunId,
    dry_run: Boolean(dryRun),
    payload: parsed
  };

  try {
    const response = await apiJson(`/api/services/${serviceId}/memory-admin/distillation/apply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    state.distillation = {
      ...(state.distillation || {}),
      operator: {
        ...operator,
        agent_id: payload.agent_id,
        user_id: payload.user_id || "",
        workspace_id: payload.workspace_id || "",
        project_id: payload.project_id || "",
        reason: payload.reason
      },
      dryRun,
      applyError: "",
      applyResult: response.distillation_apply || null,
      currentRunId: response.distillation_apply?.run_id || activeRunId || state.distillation?.currentRunId || ""
    };
    if (!dryRun) {
      await Promise.all([
        loadMemoryAdminCandidates(serviceId),
        loadMemoryAdminAudit(serviceId),
        loadMemoryAdminProjects(serviceId),
        loadMemoryAdminSummary(serviceId)
      ]);
    }
    await loadMemoryDistillationRuns(serviceId, {
      preferredRunId: state.distillation?.currentRunId || response.distillation_apply?.run_id || ""
    });
  } catch (error) {
    state.distillation = {
      ...(state.distillation || {}),
      dryRun,
      applyError: error.message,
      applyResult: null,
      currentRunId: activeRunId
    };
  }

  syncMemoryDistillationInputsFromState(serviceId);
  renderMemoryAdminForAdvanced(serviceId);
}

async function loadDashboardStatus() {
  const payload = await apiJson("/api/dashboard/status");
  dashboardStatus = payload || { pid: null };
  dashboardPidText.textContent = `PID: ${dashboardStatus.pid || "n/d"}`;
}

function applyDashboardOverview(payload) {
  dashboardStatus = {
    pid: payload?.pid || null,
    service_count: payload?.service_count || services.length,
    evaluated_at: payload?.evaluated_at || null
  };
  dashboardPidText.textContent = `PID: ${dashboardStatus.pid || "n/d"}`;
  if (payload?.service_visibility) {
    dashboardSettings = {
      ...dashboardSettings,
      service_visibility: { ...dashboardSettings.service_visibility, ...payload.service_visibility }
    };
  }

  const overviewById = new Map((payload?.services || []).map(item => [item.service_id, item]));
  services = services
    .map(service => {
      const overview = overviewById.get(service.id);
      if (!overview) {
        return {
          ...service,
          visible: dashboardSettings.service_visibility[service.id] ?? service.visible ?? true
        };
      }
      statusByService.set(service.id, overview.runtime || getRuntimeStatus(service.id));
      metricsByService.set(service.id, overview.metrics || getServiceMetrics(service.id));
      alertsByService.set(service.id, overview.alerts || getServiceAlerts(service.id));
      const state = getServiceState(service.id);
      state.entries = Array.isArray(overview.entries) ? overview.entries : [];
      return {
        ...service,
        visible: dashboardSettings.service_visibility[service.id] ?? service.visible ?? true
      };
    })
    .sort(compareServices);
}

async function refreshDashboardOverview({ tail = 2000, recentCount = 1 } = {}) {
  const payload = await apiJson(`/api/dashboard/overview?tail=${tail}&recent_count=${recentCount}`);
  applyDashboardOverview(payload);
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

async function loadVaultState() {
  const payload = await apiJson("/api/vault");
  vaultState = {
    initialized: Boolean(payload.initialized),
    unlocked: Boolean(payload.unlocked),
    entry_count: Number(payload.entry_count || 0),
    entries: Array.isArray(payload.entries) ? payload.entries : [],
    ref_usage: payload.ref_usage && typeof payload.ref_usage === "object" ? payload.ref_usage : {}
  };
  renderDbTargetsPanel();
}

function setSettingsFlash(message, kind = "info", ref = "") {
  settingsFlashState = {
    message: String(message || ""),
    kind: String(kind || "info"),
    ref: String(ref || "")
  };
  renderSettingsFlash();
}

function clearSettingsFlash() {
  settingsFlashState = null;
  renderSettingsFlash();
}

function renderSettingsFlash() {
  if (!settingsFlash) {
    return;
  }
  if (!settingsFlashState || !settingsFlashState.message) {
    settingsFlash.className = "settings-flash hidden";
    settingsFlash.innerHTML = "";
    return;
  }
  const tone = settingsFlashState.kind || "info";
  settingsFlash.className = `settings-flash settings-flash-${tone}`;
  const refBlock = settingsFlashState.ref
    ? `<div class="settings-flash-ref"><code>${settingsFlashState.ref}</code><button type="button" data-settings-copy-ref="${settingsFlashState.ref}">Copia ref</button></div>`
    : "";
  settingsFlash.innerHTML = `
    <div class="settings-flash-message">${settingsFlashState.message}</div>
    ${refBlock}
  `;
  const copyBtn = settingsFlash.querySelector("[data-settings-copy-ref]");
  if (copyBtn) {
    copyBtn.addEventListener("click", async () => {
      await copyToClipboard(settingsFlashState.ref);
      setSettingsFlash("Ref copiato negli appunti.", "success", settingsFlashState.ref);
    });
  }
}

function setSettingsTab(tabId) {
  settingsActiveTab = ["services", "db-targets", "dashboard", "vault"].includes(tabId) ? tabId : "services";
  const isServices = settingsActiveTab === "services";
  const isDbTargets = settingsActiveTab === "db-targets";
  const isDashboard = settingsActiveTab === "dashboard";
  const isVault = settingsActiveTab === "vault";

  settingsServicesTabBtn.classList.toggle("active", isServices);
  settingsServicesTabBtn.setAttribute("aria-selected", String(isServices));
  settingsDbTargetsTabBtn.classList.toggle("active", isDbTargets);
  settingsDbTargetsTabBtn.setAttribute("aria-selected", String(isDbTargets));
  settingsDashboardTabBtn.classList.toggle("active", isDashboard);
  settingsDashboardTabBtn.setAttribute("aria-selected", String(isDashboard));
  settingsVaultTabBtn.classList.toggle("active", isVault);
  settingsVaultTabBtn.setAttribute("aria-selected", String(isVault));

  settingsServicesView.classList.toggle("hidden", !isServices);
  settingsDbTargetsView.classList.toggle("hidden", !isDbTargets);
  settingsDashboardView.classList.toggle("hidden", !isDashboard);
  settingsVaultView.classList.toggle("hidden", !isVault);
}

async function copyToClipboard(text) {
  const value = String(text || "");
  if (!value) {
    return;
  }
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(value);
    return;
  }
  const input = document.createElement("textarea");
  input.value = value;
  document.body.appendChild(input);
  input.select();
  document.execCommand("copy");
  document.body.removeChild(input);
}

function renderVaultPanel() {
  vaultStatusCard.innerHTML = "";
  vaultControls.innerHTML = "";
  vaultEntries.innerHTML = "";

  const statusBits = [
    `Stato: ${vaultState.initialized ? (vaultState.unlocked ? "Unlocked" : "Locked") : "Non inizializzato"}`,
    `Secret salvati: ${vaultState.entry_count || 0}`
  ];
  vaultStatusCard.innerHTML = `
    <div class="vault-status-title">Local Vault</div>
    <div class="vault-status-meta">${statusBits.join(" | ")}</div>
    <div class="vault-status-hint">I secret restano cifrati su disco. Dopo un restart dashboard non devi reinserirli: basta sbloccare il vault e i riferimenti ${"`vault://...`"} tornano utilizzabili nelle opzioni MCP.</div>
  `;

  if (!vaultState.initialized) {
    const row = document.createElement("div");
    row.className = "vault-inline-form";
    row.innerHTML = `
      <input id="vaultInitPassphrase" type="password" placeholder="passphrase Local Vault (min 12 caratteri)" autocomplete="new-password">
      <button id="vaultInitBtn" class="btn-ok">Inizializza Local Vault</button>
    `;
    vaultControls.appendChild(row);
    row.querySelector("#vaultInitBtn").addEventListener("click", initializeVault);
    return;
  }

  if (!vaultState.unlocked) {
    const row = document.createElement("div");
    row.className = "vault-inline-form";
    row.innerHTML = `
      <input id="vaultUnlockPassphrase" type="password" placeholder="passphrase Local Vault" autocomplete="current-password">
      <button id="vaultUnlockBtn" class="btn-ok">Unlock Local Vault</button>
    `;
    vaultControls.appendChild(row);
    row.querySelector("#vaultUnlockBtn").addEventListener("click", unlockVault);
  } else {
    const tools = document.createElement("div");
    tools.className = "vault-tool-stack";
    tools.innerHTML = `
      <div class="vault-inline-form vault-inline-form-wide">
        <input id="vaultEntryRef" type="text" placeholder="es. db.prod.connection_string">
        <input id="vaultEntryValue" type="password" placeholder="valore secret" autocomplete="new-password">
        <button id="vaultSaveEntryBtn" class="btn-ok">Salva nel Local Vault</button>
        <button id="vaultLockBtn">Lock Local Vault</button>
      </div>
      <div class="option-hint">Stai salvando nel Local Vault della dashboard. Inserisci un nome logico, salva la chiave e usa poi il ref mostrato sotto o nella lista. Il valore non verra' mai mostrato di nuovo in chiaro.</div>
    `;
    vaultControls.appendChild(tools);
    tools.querySelector("#vaultSaveEntryBtn").addEventListener("click", saveVaultEntry);
    tools.querySelector("#vaultLockBtn").addEventListener("click", lockVault);
  }

  const list = document.createElement("div");
  list.className = "vault-entry-list";

  if (!vaultState.entries.length) {
    const empty = document.createElement("div");
    empty.className = "muted vault-empty-state";
    empty.textContent = vaultState.unlocked ? "Nessun secret salvato nel Local Vault." : "Sblocca il Local Vault per gestire e usare i riferimenti salvati.";
    list.appendChild(empty);
  } else {
    for (const entry of vaultState.entries) {
      const usage = Array.isArray(vaultState.ref_usage?.[entry.ref]) ? vaultState.ref_usage[entry.ref] : [];
      const usageText = usage.length
        ? `Usato da ${usage.length} opzione${usage.length === 1 ? "" : "i"}: ${usage.map(item => `${item.service_id}.${item.option_id}`).join(", ")}`
        : "Non ancora referenziato da nessun servizio.";
      const row = document.createElement("div");
      row.className = "vault-entry-row";
      row.innerHTML = `
        <div class="vault-entry-main">
          <div class="vault-entry-ref">${entry.ref}</div>
          <div class="vault-entry-meta">Aggiornato ${formatTimestamp(entry.updated_at) || "n/d"}</div>
          <div class="vault-entry-usage">${usageText}</div>
        </div>
        <div class="vault-entry-actions">
          <button type="button" data-vault-copy="${entry.ref}">Copia ref</button>
          <button type="button" class="btn-warn" data-vault-delete="${entry.ref}">Elimina</button>
        </div>
      `;
      row.querySelector("[data-vault-copy]").addEventListener("click", async () => {
        await copyToClipboard(entry.ref);
        setSettingsFlash("Ref copiato negli appunti.", "success", entry.ref);
      });
      row.querySelector("[data-vault-delete]").addEventListener("click", () => deleteVaultEntry(entry.ref));
      list.appendChild(row);
    }
  }

  vaultEntries.appendChild(list);
}

async function initializeVault() {
  const input = document.getElementById("vaultInitPassphrase");
  const passphrase = String(input?.value || "");
  if (passphrase.length < 12) {
    window.alert("La passphrase del vault deve avere almeno 12 caratteri.");
    return;
  }
  try {
    await apiJson("/api/vault/init", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ passphrase })
    });
    await loadVaultState();
    renderVaultPanel();
    renderDbTargetsPanel();
    setSettingsFlash("Local Vault inizializzato e sbloccato.", "success");
    if (advancedServiceId) {
      await loadServiceOptions(advancedServiceId);
      renderOptionsForm(advancedServiceId);
    }
  } catch (error) {
    setSettingsFlash(`Errore inizializzazione Local Vault: ${error.message}`, "error");
  }
}

async function unlockVault() {
  const input = document.getElementById("vaultUnlockPassphrase");
  const passphrase = String(input?.value || "");
  if (!passphrase) {
    window.alert("Inserisci la passphrase del vault.");
    return;
  }
  try {
    await apiJson("/api/vault/unlock", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ passphrase })
    });
    await loadVaultState();
    renderVaultPanel();
    renderDbTargetsPanel();
    setSettingsFlash("Local Vault sbloccato. I riferimenti salvati sono di nuovo utilizzabili.", "success");
    if (advancedServiceId) {
      await loadServiceOptions(advancedServiceId);
      renderOptionsForm(advancedServiceId);
    }
  } catch (error) {
    setSettingsFlash(`Errore sblocco Local Vault: ${error.message}`, "error");
  }
}

async function lockVault() {
  try {
    await apiJson("/api/vault/lock", { method: "POST" });
    await loadVaultState();
    renderVaultPanel();
    renderDbTargetsPanel();
    setSettingsFlash("Local Vault bloccato.", "info");
    if (advancedServiceId) {
      await loadServiceOptions(advancedServiceId);
      renderOptionsForm(advancedServiceId);
    }
  } catch (error) {
    setSettingsFlash(`Errore lock Local Vault: ${error.message}`, "error");
  }
}

async function saveVaultEntry() {
  const refInput = document.getElementById("vaultEntryRef");
  const valueInput = document.getElementById("vaultEntryValue");
  const ref = String(refInput?.value || "");
  const value = String(valueInput?.value || "");
  if (!ref.trim() || !value) {
    window.alert("Inserisci sia il riferimento sia il valore del secret.");
    return;
  }
  const normalizedCandidate = ref.trim().startsWith("vault://") ? ref.trim().slice("vault://".length).trim() : ref.trim();
  if (!LOCAL_VAULT_REF_NAME_PATTERN.test(normalizedCandidate)) {
    setSettingsFlash(
      "Nome ref non valido. Usa solo lettere, numeri, punto, underscore, slash, due punti o trattino; niente spazi. Esempio: db.prod.connection_string",
      "error"
    );
    return;
  }
  try {
    const payload = await apiJson("/api/vault/entries", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ref, value })
    });
    vaultState = {
      initialized: Boolean(payload.vault?.initialized),
      unlocked: Boolean(payload.vault?.unlocked),
      entry_count: Number(payload.vault?.entry_count || 0),
      entries: Array.isArray(payload.vault?.entries) ? payload.vault.entries : vaultState.entries,
      ref_usage: payload.vault?.ref_usage && typeof payload.vault.ref_usage === "object" ? payload.vault.ref_usage : {}
    };
    const normalizedRef = String(payload.entry?.ref || ref).trim();
    if (refInput) {
      refInput.value = normalizedRef;
    }
    if (valueInput) {
      valueInput.value = "";
    }
    renderVaultPanel();
    renderDbTargetsPanel();
    setSettingsFlash("Secret salvato nel Local Vault.", "success", normalizedRef);
    if (advancedServiceId) {
      await loadServiceOptions(advancedServiceId);
      renderOptionsForm(advancedServiceId);
    }
  } catch (error) {
    setSettingsFlash(`Errore salvataggio Local Vault: ${error.message}`, "error");
  }
}

async function deleteVaultEntry(ref) {
  const usage = Array.isArray(vaultState.ref_usage?.[ref]) ? vaultState.ref_usage[ref] : [];
  const suffix = usage.length ? `\n\nAttenzione: il ref e' usato da ${usage.map(item => `${item.service_id}.${item.option_id}`).join(", ")}` : "";
  if (!window.confirm(`Eliminare ${ref} dal Local Vault?${suffix}`)) {
    return;
  }
  try {
    const payload = await apiJson(`/api/vault/entries?ref=${encodeURIComponent(ref)}`, { method: "DELETE" });
    vaultState = {
      initialized: Boolean(payload.vault?.initialized),
      unlocked: Boolean(payload.vault?.unlocked),
      entry_count: Number(payload.vault?.entry_count || 0),
      entries: Array.isArray(payload.vault?.entries) ? payload.vault.entries : [],
      ref_usage: payload.vault?.ref_usage && typeof payload.vault.ref_usage === "object" ? payload.vault.ref_usage : {}
    };
    renderVaultPanel();
    renderDbTargetsPanel();
    setSettingsFlash("Secret eliminato dal Local Vault.", "success");
    if (advancedServiceId) {
      await loadServiceOptions(advancedServiceId);
      renderOptionsForm(advancedServiceId);
    }
  } catch (error) {
    setSettingsFlash(`Errore eliminazione Local Vault: ${error.message}`, "error");
  }
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

  renderSettingsFlash();
  renderDbTargetsPanel();
  renderVaultPanel();
  setSettingsTab(settingsActiveTab);
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
    await loadServices();
    await refreshDashboardOverview({ tail: 2000, recentCount: 1 });
    renderSettingsPanel();
    setSettingsFlash("Impostazioni dashboard salvate.", "success");
    renderCards();
  } catch (error) {
    window.alert(`Errore salvataggio impostazioni: ${error.message}`);
  } finally {
    saveSettingsBtn.disabled = false;
  }
}

async function toggleSettingsPanel(forceOpen = null) {
  const shouldOpen = forceOpen === null ? settingsPanel.classList.contains("hidden") : Boolean(forceOpen);
  settingsPanel.classList.toggle("hidden", !shouldOpen);
  if (shouldOpen) {
    try {
      await Promise.all([loadVaultState(), loadDbTargets()]);
    } catch (error) {
      console.error("Settings bootstrap failed", error);
    }
    renderSettingsPanel();
  } else {
    clearSettingsFlash();
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
    refreshDashboardOverview({ tail: 2000, recentCount: 1 }).then(() => {
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
  const groups = optionGroupDefinitions(serviceId);
  if (!groups) {
    for (const opt of options) {
      optionsForm.appendChild(createOptionRow(opt));
    }
    return;
  }

  const matched = new Set();
  for (const group of groups) {
    const groupOptions = options.filter(opt => group.match(opt));
    for (const opt of groupOptions) {
      matched.add(opt.id);
    }
    renderOptionGroup(optionsForm, group.title, group.description, groupOptions);
  }

  const remaining = options.filter(opt => !matched.has(opt.id));
  renderOptionGroup(
    optionsForm,
    "Altre opzioni",
    "Impostazioni non classificate nei gruppi principali del gateway SQL.",
    remaining
  );
}

function collectOptionsFromForm() {
  const values = {};
  for (const row of optionsForm.querySelectorAll("[data-secret-option='true']")) {
    const optionId = row.dataset.secretOptionId;
    if (!optionId) {
      continue;
    }
    const source = row.querySelector(`[data-option-source="${optionId}"]`)?.value || "session";
    if (source === "vault") {
      const ref = row.querySelector(`[data-option-vault-ref="${optionId}"]`)?.value || "";
      if (String(ref).trim()) {
        values[optionId] = { source: "vault", ref };
      }
      continue;
    }
    const value = row.querySelector(`[data-option-session-value="${optionId}"]`)?.value ?? "";
    if (String(value).trim()) {
      values[optionId] = { source: "session", value };
    }
  }

  const inputs = optionsForm.querySelectorAll("input[data-option-id], select[data-option-id], textarea[data-option-id]");
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

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => {
    switch (char) {
      case "&":
        return "&amp;";
      case "<":
        return "&lt;";
      case ">":
        return "&gt;";
      case '"':
        return "&quot;";
      case "'":
        return "&#39;";
      default:
        return char;
    }
  });
}

function cloneValue(value) {
  return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
}

function normalizeDbTargetText(value, fallback = "") {
  const text = value === undefined || value === null ? fallback : String(value);
  return text.trim();
}

function normalizeDbTargetEnvironment(value) {
  return normalizeDbTargetText(value, "dev").toLowerCase() || "dev";
}

function normalizeDbTargetStatus(value) {
  const status = normalizeDbTargetText(value, "active").toLowerCase();
  return status === "disabled" ? "disabled" : "active";
}

function buildDbTargetConnectionEnvVar(targetId) {
  const normalized = normalizeDbTargetText(targetId)
    .replace(/[^A-Za-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .toUpperCase();
  return normalized ? `DB_${normalized}_CONNECTION_STRING` : "";
}

function normalizeDbTargetAllowedTools(value) {
  if (Array.isArray(value)) {
    return [...new Set(value.map(item => normalizeDbTargetText(item)).filter(Boolean))];
  }
  if (typeof value === "string") {
    return [...new Set(value.split(",").map(item => normalizeDbTargetText(item)).filter(Boolean))];
  }
  return [];
}

function normalizeDbTargetBinding(binding = {}, connectionVaultRef = "") {
  const vaultRef = normalizeDbTargetText(
    binding.vault_ref ?? binding.connection_vault_ref ?? binding.ref ?? connectionVaultRef
  );
  const status = normalizeDbTargetText(binding.status ?? binding.state ?? "");
  const message = normalizeDbTargetText(binding.status_message ?? binding.message ?? "");
  const ready = binding.is_ready ?? binding.ready ?? binding.env_ready ?? binding.vault_ready;
  return {
    source: normalizeDbTargetText(binding.source ?? "", "none").toLowerCase() || "none",
    vault_ref: vaultRef,
    env_var: normalizeDbTargetText(binding.env_var ?? binding.connection_env_var ?? ""),
    is_ready: typeof ready === "boolean" ? ready : Boolean(vaultRef && status !== "blocked"),
    env_ready: Boolean(binding.env_ready ?? binding.runtime_ready ?? false),
    vault_ready: Boolean(binding.vault_ready ?? Boolean(vaultRef)),
    status,
    status_message: message
  };
}

function normalizeDbTargetRecord(raw = {}) {
  const targetId = normalizeDbTargetText(raw.target_id ?? raw.id ?? raw.targetId);
  const environment = normalizeDbTargetEnvironment(raw.environment);
  const policy = raw.policy && typeof raw.policy === "object" ? raw.policy : {};
  const anonymization = raw.anonymization && typeof raw.anonymization === "object" ? raw.anonymization : {};
  const limits = raw.limits && typeof raw.limits === "object" ? raw.limits : {};
  const binding = normalizeDbTargetBinding(
    raw.binding ?? raw.connection_binding ?? raw.connection ?? raw.secret_binding ?? {},
    raw.connection_vault_ref ?? raw.vault_ref ?? raw.connection_ref ?? ""
  );

  return {
    target_id: targetId,
    display_name: normalizeDbTargetText(raw.display_name ?? raw.name ?? targetId),
    environment,
    db_kind: normalizeDbTargetText(raw.db_kind ?? raw.kind ?? "sqlserver", "sqlserver").toLowerCase(),
    status: normalizeDbTargetStatus(raw.status ?? (raw.enabled === false ? "disabled" : "active")),
    connection_vault_ref: normalizeDbTargetText(
      raw.connection_vault_ref ?? raw.vault_ref ?? raw.connection_ref ?? binding.vault_ref
    ),
    connection_env_var: normalizeDbTargetText(
      raw.connection_env_var ?? raw.connection_env ?? binding.env_var ?? buildDbTargetConnectionEnvVar(targetId)
    ),
    read_enabled: Boolean(raw.read_enabled ?? policy.read_enabled ?? raw.readAllowed ?? true),
    write_enabled: Boolean(
      raw.write_enabled ?? policy.effective_write_enabled ?? policy.write_enabled ?? raw.writeAllowed ?? false
    ),
    anonymization_enabled: Boolean(
      raw.anonymization_enabled ?? anonymization.enabled ?? raw.anonymizationEnabled ?? environment === "prod"
    ),
    anonymization_mode: normalizeDbTargetText(
      raw.anonymization_mode ?? anonymization.mode ?? raw.anonymizationMode ?? "off"
    ).toLowerCase(),
    llm_provider: normalizeDbTargetText(
      raw.llm_provider ?? anonymization.provider ?? raw.llmProvider ?? "none"
    ).toLowerCase() || "none",
    llm_model: normalizeDbTargetText(raw.llm_model ?? anonymization.model ?? raw.llmModel ?? ""),
    max_rows: Number.isFinite(Number(raw.max_rows ?? limits.max_rows)) ? Number(raw.max_rows ?? limits.max_rows) : 100,
    max_result_bytes: Number.isFinite(Number(raw.max_result_bytes ?? limits.max_result_bytes))
      ? Number(raw.max_result_bytes ?? limits.max_result_bytes)
      : 131072,
    allowed_tools: normalizeDbTargetAllowedTools(raw.allowed_tools ?? raw.allowedTools ?? []),
    binding,
    raw
  };
}

function defaultDbTargetDraft() {
  return normalizeDbTargetRecord({
    target_id: "",
    display_name: "",
    environment: "dev",
    db_kind: "sqlserver",
    status: "active",
    connection_vault_ref: "",
    read_enabled: true,
    write_enabled: true,
    anonymization_enabled: false,
    anonymization_mode: "off",
    llm_provider: "none",
    llm_model: "",
    max_rows: 100,
    max_result_bytes: 131072,
    allowed_tools: ["db_target_info", "db_policy_info", "db_read", "db_write"]
  });
}

function isDbTargetProd(target) {
  return normalizeDbTargetEnvironment(target?.environment) === "prod";
}

function isDbTargetHardFencedField(fieldId, target) {
  if (!isDbTargetProd(target)) {
    return false;
  }
  return ["write_enabled", "anonymization_enabled", "anonymization_mode"].includes(fieldId);
}

function normalizeDbTargetDraft(target) {
  const draft = normalizeDbTargetRecord(target ?? defaultDbTargetDraft());
  if (!draft.target_id) {
    draft.target_id = "";
  }
  draft.display_name = normalizeDbTargetText(draft.display_name, draft.target_id);
  draft.connection_env_var = normalizeDbTargetText(
    draft.connection_env_var || buildDbTargetConnectionEnvVar(draft.target_id)
  );
  draft.allowed_tools = normalizeDbTargetAllowedTools(draft.allowed_tools);
  if (!draft.allowed_tools.length) {
    draft.allowed_tools = ["db_target_info", "db_policy_info", "db_read", "db_write"];
  }
  if (isDbTargetProd(draft)) {
    draft.read_enabled = true;
    draft.write_enabled = false;
    draft.anonymization_enabled = true;
    if (!["deterministic", "hybrid", "llm-strict"].includes(draft.anonymization_mode)) {
      draft.anonymization_mode = "hybrid";
    }
  }
  if (!draft.anonymization_enabled) {
    draft.anonymization_mode = "off";
    draft.llm_provider = "none";
    draft.llm_model = "";
  }
  return draft;
}

function summarizeDbTargetBinding(target) {
  const vaultReady =
    Boolean(
      target.connection_vault_ref &&
        vaultState.unlocked &&
        Array.isArray(vaultState.entries) &&
        vaultState.entries.some(entry => entry.ref === target.connection_vault_ref)
    ) || Boolean(target.binding?.vault_ready);
  const envReady = Boolean(target.binding?.env_ready ?? target.binding?.runtime_ready ?? target.connection_env_var);
  const statusMessage =
    target.binding?.status_message ||
    (target.connection_vault_ref
      ? vaultReady
        ? "Riferimento Local Vault pronto."
        : "Riferimento Local Vault presente ma non ancora pronto."
      : "Nessun ref Local Vault configurato.");
  return { vaultReady, envReady, statusMessage };
}

function summarizeDbTargetPolicy(target) {
  return [
    target.read_enabled ? "read ON" : "read OFF",
    target.write_enabled ? "write ON" : "write OFF",
    target.anonymization_enabled ? `anon ${target.anonymization_mode || "on"}` : "anon OFF"
  ].join(" | ");
}

function summarizeDbTargetLimits(target) {
  return `max_rows ${formatNumber(target.max_rows, 0)} | max_bytes ${formatNumber(target.max_result_bytes, 0)}`;
}

function getDbTargetDraft() {
  if (dbTargetsState.draft) {
    return dbTargetsState.draft;
  }
  dbTargetsState.draft = defaultDbTargetDraft();
  dbTargetsState.selectedId = "__new__";
  return dbTargetsState.draft;
}

function setDbTargetDraft(draft, selectedId = null) {
  dbTargetsState.draft = normalizeDbTargetDraft(draft);
  if (selectedId !== null) {
    dbTargetsState.selectedId = selectedId;
  }
}

function selectDbTarget(targetId) {
  const target = dbTargetsState.items.find(item => item.target_id === targetId);
  if (!target) {
    return;
  }
  dbTargetsState.selectedId = target.target_id;
  dbTargetsState.draft = normalizeDbTargetDraft(cloneValue(target));
  renderDbTargetsPanel();
}

function startNewDbTarget() {
  dbTargetsState.selectedId = "__new__";
  dbTargetsState.draft = defaultDbTargetDraft();
  renderDbTargetsPanel();
}

function collectDbTargetPayload() {
  const draft = normalizeDbTargetDraft(cloneValue(getDbTargetDraft()));
  draft.target_id = normalizeDbTargetText(draft.target_id);
  draft.display_name = normalizeDbTargetText(draft.display_name, draft.target_id);
  draft.environment = normalizeDbTargetEnvironment(draft.environment);
  draft.status = normalizeDbTargetStatus(draft.status);
  draft.connection_vault_ref = normalizeDbTargetText(draft.connection_vault_ref);
  draft.connection_env_var = normalizeDbTargetText(
    draft.connection_env_var || buildDbTargetConnectionEnvVar(draft.target_id)
  );
  draft.allowed_tools = normalizeDbTargetAllowedTools(draft.allowed_tools);
  draft.max_rows = Number.isFinite(Number(draft.max_rows)) ? Number(draft.max_rows) : 100;
  draft.max_result_bytes = Number.isFinite(Number(draft.max_result_bytes))
    ? Number(draft.max_result_bytes)
    : 131072;
  return normalizeDbTargetDraft(draft);
}

async function loadDbTargets() {
  dbTargetsState.loading = true;
  dbTargetsState.error = "";
  try {
    const payload = await apiJson("/api/db-targets");
    dbTargetsState.items = Array.isArray(payload.targets)
      ? payload.targets.map(item => normalizeDbTargetRecord(item))
      : [];
    dbTargetsState.runtimeExportPath = String(payload.runtime_export_path || "");

    if (dbTargetsState.selectedId && dbTargetsState.selectedId !== "__new__") {
      const selected = dbTargetsState.items.find(item => item.target_id === dbTargetsState.selectedId);
      if (selected) {
        dbTargetsState.draft = normalizeDbTargetDraft(cloneValue(selected));
      } else {
        startNewDbTarget();
      }
    } else if (!dbTargetsState.draft) {
      if (dbTargetsState.items.length) {
        selectDbTarget(dbTargetsState.items[0].target_id);
      } else {
        startNewDbTarget();
      }
    }
  } catch (error) {
    dbTargetsState.error = error.message;
    dbTargetsState.items = [];
    dbTargetsState.runtimeExportPath = "";
  } finally {
    dbTargetsState.loading = false;
    renderDbTargetsPanel();
  }
}

function renderDbTargetsPanel() {
  if (!settingsDbTargetsSummary || !dbTargetsList || !dbTargetEditorForm || !dbTargetEditorMeta) {
    return;
  }

  const count = dbTargetsState.items.length;
  const exportText = dbTargetsState.runtimeExportPath
    ? ` | export runtime: ${dbTargetsState.runtimeExportPath}`
    : "";
  settingsDbTargetsSummary.textContent = dbTargetsState.error
    ? `Errore registry: ${dbTargetsState.error}`
    : `${count} target registrati${exportText}`;

  dbTargetsList.innerHTML = "";
  if (dbTargetsState.loading) {
    dbTargetsList.innerHTML = `<div class="vault-empty-state">Caricamento registry DB in corso...</div>`;
  } else if (!count) {
    dbTargetsList.innerHTML = `<div class="vault-empty-state">Nessun target DB registrato.</div>`;
  } else {
    for (const target of dbTargetsState.items) {
      const selected = dbTargetsState.selectedId === target.target_id;
      const binding = summarizeDbTargetBinding(target);
      const row = document.createElement("button");
      row.type = "button";
      row.className = `db-target-card ${selected ? "active-card" : ""}`;
      row.innerHTML = `
        <div class="db-target-card-header">
          <div>
            <div class="db-target-card-title">${escapeHtml(target.display_name || target.target_id)}</div>
            <div class="db-target-card-meta">${escapeHtml(target.target_id)}</div>
          </div>
          <div class="db-target-badge-row">
            <span class="db-target-badge ${isDbTargetProd(target) ? "env-prod" : "env-nonprod"}">${escapeHtml(target.environment)}</span>
            <span class="db-target-badge ${target.status === "active" ? "status-active" : "status-disabled"}">${escapeHtml(target.status)}</span>
          </div>
        </div>
        <div class="db-target-card-meta">${escapeHtml(summarizeDbTargetPolicy(target))}</div>
        <div class="db-target-card-meta">${escapeHtml(summarizeDbTargetLimits(target))}</div>
        <div class="db-target-card-hint">${escapeHtml(binding.statusMessage)}</div>
      `;
      row.addEventListener("click", () => selectDbTarget(target.target_id));
      dbTargetsList.appendChild(row);
    }
  }

  const draft = getDbTargetDraft();
  const selected = dbTargetsState.selectedId && dbTargetsState.selectedId !== "__new__";
  const binding = summarizeDbTargetBinding(draft);
  const prod = isDbTargetProd(draft);
  dbTargetEditorMeta.textContent = selected
    ? `${draft.target_id} | ${binding.statusMessage}`
    : "Nuovo target DB. I target prod applicano hard fences non aggirabili lato backend/MCP.";

  dbTargetEditorForm.innerHTML = `
    <div class="db-target-editor-section">
      <h4>Identità</h4>
      <div class="db-target-field-grid">
        <div class="db-target-field">
          <label for="dbTargetIdInput">Target ID</label>
          <input id="dbTargetIdInput" data-db-target-field="target_id" type="text" value="${escapeHtml(draft.target_id)}" ${selected ? "disabled" : ""}>
        </div>
        <div class="db-target-field">
          <label for="dbTargetNameInput">Display Name</label>
          <input id="dbTargetNameInput" data-db-target-field="display_name" type="text" value="${escapeHtml(draft.display_name)}">
        </div>
        <div class="db-target-field">
          <label for="dbTargetEnvironmentInput">Environment</label>
          <input id="dbTargetEnvironmentInput" data-db-target-field="environment" type="text" value="${escapeHtml(draft.environment)}">
        </div>
        <div class="db-target-field">
          <label for="dbTargetStatusInput">Status</label>
          <select id="dbTargetStatusInput" data-db-target-field="status">
            <option value="active" ${draft.status === "active" ? "selected" : ""}>active</option>
            <option value="disabled" ${draft.status === "disabled" ? "selected" : ""}>disabled</option>
          </select>
        </div>
      </div>
    </div>
    <div class="db-target-editor-section">
      <h4>Connessione</h4>
      <div class="db-target-field-grid">
        <div class="db-target-field">
          <label for="dbTargetVaultRefInput">Local Vault Ref</label>
          <input id="dbTargetVaultRefInput" data-db-target-field="connection_vault_ref" type="text" value="${escapeHtml(draft.connection_vault_ref)}" placeholder="vault://db.prod.connection">
          <div class="db-target-inline-hint">${escapeHtml(binding.statusMessage)}</div>
        </div>
        <div class="db-target-field">
          <label for="dbTargetEnvVarInput">Runtime Env Var</label>
          <input id="dbTargetEnvVarInput" data-db-target-field="connection_env_var" type="text" value="${escapeHtml(draft.connection_env_var)}">
        </div>
      </div>
    </div>
    <div class="db-target-editor-section">
      <h4>Policy</h4>
      <div class="db-target-field-grid">
        <label class="settings-toggle"><input data-db-target-field="read_enabled" type="checkbox" ${draft.read_enabled ? "checked" : ""}>Read enabled</label>
        <label class="settings-toggle"><input data-db-target-field="write_enabled" type="checkbox" ${draft.write_enabled ? "checked" : ""} ${prod ? "disabled" : ""}>Write enabled</label>
        <label class="settings-toggle"><input data-db-target-field="anonymization_enabled" type="checkbox" ${draft.anonymization_enabled ? "checked" : ""} ${prod ? "disabled" : ""}>Anonymization enabled</label>
      </div>
      <div class="db-target-field-grid">
        <div class="db-target-field">
          <label for="dbTargetAnonModeInput">Anonymization Mode</label>
          <select id="dbTargetAnonModeInput" data-db-target-field="anonymization_mode" ${prod ? "disabled" : ""}>
            ${["off", "deterministic", "hybrid", "llm-strict"].map(value => `<option value="${value}" ${draft.anonymization_mode === value ? "selected" : ""}>${value}</option>`).join("")}
          </select>
        </div>
        <div class="db-target-field">
          <label for="dbTargetProviderInput">Provider</label>
          <select id="dbTargetProviderInput" data-db-target-field="llm_provider">
            ${["none", "lmstudio", "ollama"].map(value => `<option value="${value}" ${draft.llm_provider === value ? "selected" : ""}>${value}</option>`).join("")}
          </select>
        </div>
        <div class="db-target-field">
          <label for="dbTargetModelInput">Model</label>
          <input id="dbTargetModelInput" data-db-target-field="llm_model" type="text" value="${escapeHtml(draft.llm_model)}">
        </div>
      </div>
      ${prod ? `<div class="db-target-inline-hint">Target prod: write OFF e anonymization ON sono hard-fenced lato backend/MCP.</div>` : ""}
    </div>
    <div class="db-target-editor-section">
      <h4>Limiti e Tool</h4>
      <div class="db-target-field-grid">
        <div class="db-target-field">
          <label for="dbTargetMaxRowsInput">Max Rows</label>
          <input id="dbTargetMaxRowsInput" data-db-target-field="max_rows" type="number" min="1" value="${escapeHtml(draft.max_rows)}">
        </div>
        <div class="db-target-field">
          <label for="dbTargetMaxBytesInput">Max Result Bytes</label>
          <input id="dbTargetMaxBytesInput" data-db-target-field="max_result_bytes" type="number" min="1" value="${escapeHtml(draft.max_result_bytes)}">
        </div>
        <div class="db-target-field">
          <label for="dbTargetAllowedToolsInput">Allowed Tools</label>
          <input id="dbTargetAllowedToolsInput" data-db-target-field="allowed_tools" type="text" value="${escapeHtml(draft.allowed_tools.join(", "))}">
        </div>
      </div>
    </div>
    <div class="db-target-editor-actions">
      <button type="submit" class="btn-ok">${selected ? "Salva Target" : "Crea Target"}</button>
      ${selected && draft.status === "active" ? '<button type="button" id="dbTargetDisableBtn" class="btn-warn">Disabilita</button>' : ""}
      ${selected && draft.status === "disabled" ? '<button type="button" id="dbTargetEnableBtn">Riattiva</button>' : ""}
    </div>
  `;

  dbTargetEditorForm.querySelectorAll("[data-db-target-field]").forEach(input => {
    input.addEventListener("input", handleDbTargetDraftChange);
    input.addEventListener("change", handleDbTargetDraftChange);
  });
  dbTargetEditorForm.addEventListener("submit", saveDbTargetFromEditor);
  dbTargetEditorForm.querySelector("#dbTargetDisableBtn")?.addEventListener("click", disableSelectedDbTarget);
  dbTargetEditorForm.querySelector("#dbTargetEnableBtn")?.addEventListener("click", enableSelectedDbTarget);
}

function handleDbTargetDraftChange(event) {
  const field = event.target?.dataset?.dbTargetField;
  if (!field) {
    return;
  }

  const draft = cloneValue(getDbTargetDraft());
  if (event.target.type === "checkbox") {
    draft[field] = Boolean(event.target.checked);
  } else {
    draft[field] = event.target.value;
  }

  if (field === "target_id" && !draft.connection_env_var) {
    draft.connection_env_var = buildDbTargetConnectionEnvVar(event.target.value);
  }

  setDbTargetDraft(draft);
  renderDbTargetsPanel();
}

async function saveDbTargetFromEditor(event) {
  event.preventDefault();
  const payload = collectDbTargetPayload();
  if (!payload.target_id) {
    window.alert("Il target_id è obbligatorio.");
    return;
  }

  const method = dbTargetsState.selectedId && dbTargetsState.selectedId !== "__new__" ? "PUT" : "POST";
  const url =
    method === "PUT"
      ? `/api/db-targets/${encodeURIComponent(dbTargetsState.selectedId)}`
      : "/api/db-targets";

  try {
    const response = await apiJson(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ values: payload })
    });
    setSettingsFlash(`Target ${payload.target_id} salvato.`, "success");
    if (response?.target) {
      setDbTargetDraft(response.target, response.target.target_id);
    }
    await loadDbTargets();
  } catch (error) {
    setSettingsFlash(`Errore salvataggio target: ${error.message}`, "error");
  }
}

async function disableSelectedDbTarget() {
  if (!dbTargetsState.selectedId || dbTargetsState.selectedId === "__new__") {
    return;
  }
  try {
    await apiJson(`/api/db-targets/${encodeURIComponent(dbTargetsState.selectedId)}/disable`, { method: "POST" });
    setSettingsFlash(`Target ${dbTargetsState.selectedId} disabilitato.`, "success");
    await loadDbTargets();
  } catch (error) {
    setSettingsFlash(`Errore disabilitazione target: ${error.message}`, "error");
  }
}

async function enableSelectedDbTarget() {
  if (!dbTargetsState.selectedId || dbTargetsState.selectedId === "__new__") {
    return;
  }
  try {
    await apiJson(`/api/db-targets/${encodeURIComponent(dbTargetsState.selectedId)}/enable`, { method: "POST" });
    setSettingsFlash(`Target ${dbTargetsState.selectedId} riattivato.`, "success");
    await loadDbTargets();
  } catch (error) {
    setSettingsFlash(`Errore riattivazione target: ${error.message}`, "error");
  }
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
  await refreshDashboardOverview({ tail: Math.max(tail * 8, 2000), recentCount: 1 });
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
  clearAdvancedRefreshTimers();
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
    ? `${String(alertPayload.status || "ok").toUpperCase()} (${alertPayload.triggered_count || 0})`
    : "n/d";

  advancedMeta.innerHTML = "";
  advancedMeta.appendChild(createSummaryCard("Status", runtimeText));
  advancedMeta.appendChild(createSummaryCard("Health", `${healthLabel(runtime)}${contextMode ? ` | ${contextMode}` : ""}`));
  advancedMeta.appendChild(createSummaryCard("Stream", streamState));
  if (supportsAlerts(service)) {
    advancedMeta.appendChild(createSummaryCard("Alert", alertText));
  }
  advancedMeta.appendChild(createSummaryCard("Sources", sourceSummary));
}

function renderAdvancedInspectorTitles(service) {
  tabInspectorBtn.textContent = inspectorTabLabel(service);
  if (queryPanelTitle) {
    queryPanelTitle.textContent = "Query Inspector";
  }
  if (activityPanelTitle) {
    activityPanelTitle.textContent = activityPanelHeading(service);
  }
}

function syncMemoryAdminInputsFromState(serviceId) {
  if (!supportsMemoryAdmin(serviceId)) {
    return;
  }
  const state = getMemoryAdminState(serviceId);
  const candidateFilters = state.candidates?.filters || {};
  const auditFilters = state.audit?.filters || {};

  memoryCandidatesLimitInput.value = String(Math.max(1, Math.min(200, clampLimitValue(state.candidates?.limit, 20))));
  memoryCandidatesWorkspaceInput.value = candidateFilters.workspace_id || "";
  memoryCandidatesProjectInput.value = candidateFilters.project_id || "";
  memoryCandidatesStatusInput.value = candidateFilters.distillation_status || "pending";
  memoryCandidatesIncludeResolvedInput.checked = Boolean(candidateFilters.include_resolved);
  memoryDistillationRunsLimitInput.value = String(Math.max(1, Math.min(200, clampLimitValue(state.runs?.limit, 20))));
  memoryDistillationRunsStatusInput.value = state.runs?.filters?.status || "";
  memoryAuditLimitInput.value = String(clampLimitValue(state.audit?.limit, 50));
  memoryAuditActionInput.value = auditFilters.action || "";
  memoryAuditActorInput.value = auditFilters.actor || "";
  memoryAuditReasonInput.value = auditFilters.reason || "";
  memoryAuditSinceInput.value = auditFilters.since || "";
  memoryProjectsLimitInput.value = String(clampLimitValue(state.projects?.limit, 50));
  memoryProjectsWorkspaceInput.value = state.projects?.workspace_id || "";
  syncMemoryDistillationInputsFromState(serviceId);
}

function syncMemoryCandidatesStateFromInputs(serviceId) {
  const state = getMemoryAdminState(serviceId);
  state.candidates = {
    ...(state.candidates || {}),
    limit: Math.max(1, Math.min(200, clampLimitValue(memoryCandidatesLimitInput.value, 20))),
    filters: {
      workspace_id: String(memoryCandidatesWorkspaceInput.value || "").trim(),
      project_id: String(memoryCandidatesProjectInput.value || "").trim(),
      include_resolved: Boolean(memoryCandidatesIncludeResolvedInput.checked),
      distillation_status: String(memoryCandidatesStatusInput.value || "pending").trim() || "pending"
    }
  };
}

function syncMemoryAuditStateFromInputs(serviceId) {
  const state = getMemoryAdminState(serviceId);
  state.audit = {
    ...(state.audit || {}),
    limit: clampLimitValue(memoryAuditLimitInput.value, 50),
    filters: {
      action: String(memoryAuditActionInput.value || "").trim(),
      actor: String(memoryAuditActorInput.value || "").trim(),
      reason: String(memoryAuditReasonInput.value || "").trim(),
      since: String(memoryAuditSinceInput.value || "").trim()
    }
  };
}

function syncMemoryProjectsStateFromInputs(serviceId) {
  const state = getMemoryAdminState(serviceId);
  state.projects = {
    ...(state.projects || {}),
    limit: clampLimitValue(memoryProjectsLimitInput.value, 50),
    workspace_id: String(memoryProjectsWorkspaceInput.value || "").trim()
  };
}

function syncMemoryDistillationRunsStateFromInputs(serviceId) {
  const state = getMemoryAdminState(serviceId);
  state.runs = {
    ...(state.runs || {}),
    limit: Math.max(1, Math.min(200, clampLimitValue(memoryDistillationRunsLimitInput.value, 20))),
    filters: {
      ...(state.runs?.filters || {}),
      status: String(memoryDistillationRunsStatusInput.value || "").trim()
    }
  };
}

async function reloadMemoryDistillationRuns() {
  if (!advancedServiceId || !supportsMemoryAdmin(advancedServiceId)) {
    return;
  }
  syncMemoryDistillationRunsStateFromInputs(advancedServiceId);
  await loadMemoryDistillationRuns(advancedServiceId);
  renderMemoryAdminForAdvanced(advancedServiceId);
}

async function resetMemoryDistillationRuns() {
  if (!advancedServiceId || !supportsMemoryAdmin(advancedServiceId)) {
    return;
  }
  const state = getMemoryAdminState(advancedServiceId);
  state.runs = {
    ...(state.runs || {}),
    limit: 20,
    filters: {
      ...(state.runs?.filters || {}),
      status: ""
    },
    selectedRunId: "",
    selectedRun: null
  };
  syncMemoryAdminInputsFromState(advancedServiceId);
  await loadMemoryDistillationRuns(advancedServiceId);
  renderMemoryAdminForAdvanced(advancedServiceId);
}

async function applyMemoryAuditFilters() {
  if (!advancedServiceId || !supportsMemoryAdmin(advancedServiceId)) {
    return;
  }
  syncMemoryAuditStateFromInputs(advancedServiceId);
  await loadMemoryAdminAudit(advancedServiceId);
  renderMemoryAdminForAdvanced(advancedServiceId);
}

async function applyMemoryCandidatesFilters() {
  if (!advancedServiceId || !supportsMemoryAdmin(advancedServiceId)) {
    return;
  }
  syncMemoryCandidatesStateFromInputs(advancedServiceId);
  await loadMemoryAdminCandidates(advancedServiceId);
  renderMemoryAdminForAdvanced(advancedServiceId);
}

async function resetMemoryCandidatesFilters() {
  if (!advancedServiceId || !supportsMemoryAdmin(advancedServiceId)) {
    return;
  }
  const state = getMemoryAdminState(advancedServiceId);
  state.candidates = {
    ...(state.candidates || {}),
    limit: 20,
    filters: {
      workspace_id: "",
      project_id: "",
      include_resolved: false,
      distillation_status: "pending"
    }
  };
  syncMemoryAdminInputsFromState(advancedServiceId);
  await loadMemoryAdminCandidates(advancedServiceId);
  renderMemoryAdminForAdvanced(advancedServiceId);
}

async function resetMemoryAuditFilters() {
  if (!advancedServiceId || !supportsMemoryAdmin(advancedServiceId)) {
    return;
  }
  const state = getMemoryAdminState(advancedServiceId);
  state.audit = {
    ...(state.audit || {}),
    limit: 50,
    filters: {
      action: "",
      actor: "",
      reason: "",
      since: ""
    }
  };
  syncMemoryAdminInputsFromState(advancedServiceId);
  await loadMemoryAdminAudit(advancedServiceId);
  renderMemoryAdminForAdvanced(advancedServiceId);
}

async function reloadMemoryProjects() {
  if (!advancedServiceId || !supportsMemoryAdmin(advancedServiceId)) {
    return;
  }
  syncMemoryProjectsStateFromInputs(advancedServiceId);
  await loadMemoryAdminProjects(advancedServiceId);
  renderMemoryAdminForAdvanced(advancedServiceId);
}

async function resetMemoryProjectsFilters() {
  if (!advancedServiceId || !supportsMemoryAdmin(advancedServiceId)) {
    return;
  }
  const state = getMemoryAdminState(advancedServiceId);
  state.projects = {
    ...(state.projects || {}),
    limit: 50,
    workspace_id: ""
  };
  syncMemoryAdminInputsFromState(advancedServiceId);
  await loadMemoryAdminProjects(advancedServiceId);
  renderMemoryAdminForAdvanced(advancedServiceId);
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
    refreshServiceAlerts(serviceId),
    loadMemoryAdminAll(serviceId)
  ]);

  advancedTitle.textContent = `Dettaglio: ${service.name}`;
  renderAdvancedMeta(service);
  renderAdvancedInspectorTitles(service);
  renderOptionsForm(serviceId);
  syncMemoryAdminInputsFromState(serviceId);
  renderMemoryAdminForAdvanced(serviceId);
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
  if (supportsMemoryAdmin(service)) {
    renderMemoryAdminForAdvanced(serviceId);
  }
  if (!supportsInspector(service) && advancedActiveTab === "inspector") {
    setAdvancedTab("logs");
  }
  if (!supportsMemoryAdmin(service) && advancedActiveTab === "memory") {
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
    loadServiceActivity(advancedServiceId, Math.max(tail * 8, 500)),
    loadMemoryAdminAll(advancedServiceId)
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
  if (supportsMemoryAdmin(advancedServiceId)) {
    syncMemoryAdminInputsFromState(advancedServiceId);
    renderMemoryAdminForAdvanced(advancedServiceId);
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
      const currentServiceId = advancedServiceId;
      if (!currentServiceId) {
        return;
      }
      const entry = JSON.parse(evt.data);
      const state = getServiceState(currentServiceId);
      state.entries.unshift(entry);
      if (state.entries.length > currentRecentRowsLimit()) {
        state.entries = state.entries.slice(0, currentRecentRowsLimit());
      }
      rebuildEventFilterOptions(state.entries || []);
      if (entryMatchesAdvancedFilters(entry)) {
        appendAdvancedEntries([entry], { prepend: true });
      }
      if (supportsQueryInspector(currentServiceId) && isDbQueryEvent(entry)) {
        scheduleAdvancedQueryRefresh(currentServiceId, 2000);
      }
      if (supportsActivity(currentServiceId)) {
        scheduleAdvancedActivityRefresh(currentServiceId, 2000);
      }
      scheduleAdvancedMetricsAlertsRefresh(currentServiceId);
      scheduleCardRender();
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
tabMemoryBtn.addEventListener("click", () => {
  if (supportsMemoryAdmin(advancedServiceId)) {
    setAdvancedTab("memory");
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
settingsServicesTabBtn.addEventListener("click", () => setSettingsTab("services"));
settingsDbTargetsTabBtn.addEventListener("click", () => setSettingsTab("db-targets"));
settingsDashboardTabBtn.addEventListener("click", () => setSettingsTab("dashboard"));
settingsVaultTabBtn.addEventListener("click", () => setSettingsTab("vault"));
dbTargetsReloadBtn?.addEventListener("click", () => loadDbTargets());
dbTargetNewBtn?.addEventListener("click", startNewDbTarget);
saveSettingsBtn.addEventListener("click", saveDashboardSettings);
reloadAlertsBtn.addEventListener("click", async () => {
  if (!advancedServiceId || !supportsAlerts(advancedServiceId)) {
    return;
  }
  await refreshServiceAlerts(advancedServiceId);
  renderAlertsForAdvanced(advancedServiceId);
  renderCards();
});
reloadMemoryAdminBtn?.addEventListener("click", async () => {
  if (!advancedServiceId || !supportsMemoryAdmin(advancedServiceId)) {
    return;
  }
  syncMemoryDistillationStateFromInputs(advancedServiceId);
  syncMemoryCandidatesStateFromInputs(advancedServiceId);
  syncMemoryDistillationRunsStateFromInputs(advancedServiceId);
  syncMemoryAuditStateFromInputs(advancedServiceId);
  syncMemoryProjectsStateFromInputs(advancedServiceId);
  await loadMemoryAdminAll(advancedServiceId);
  renderMemoryAdminForAdvanced(advancedServiceId);
});
applyMemoryCandidatesBtn?.addEventListener("click", applyMemoryCandidatesFilters);
resetMemoryCandidatesBtn?.addEventListener("click", resetMemoryCandidatesFilters);
previewMemoryDistillationApplyBtn?.addEventListener("click", async () => {
  if (!advancedServiceId || !supportsMemoryAdmin(advancedServiceId)) {
    return;
  }
  await applyMemoryDistillation(advancedServiceId, true);
});
applyMemoryDistillationBtn?.addEventListener("click", async () => {
  if (!advancedServiceId || !supportsMemoryAdmin(advancedServiceId)) {
    return;
  }
  await applyMemoryDistillation(advancedServiceId, false);
});
resetMemoryDistillationBtn?.addEventListener("click", () => {
  if (!advancedServiceId || !supportsMemoryAdmin(advancedServiceId)) {
    return;
  }
  const state = getMemoryAdminState(advancedServiceId);
  state.distillation = {
    operator: {
      agent_id: "dashboard-operator",
      user_id: "",
      workspace_id: "",
      project_id: "",
      reason: ""
    },
    prepared: null,
    preparedClusterId: "",
    preparedError: "",
    applyDraft: "",
    applyResult: null,
    applyError: "",
    dryRun: true,
    currentRunId: ""
  };
  syncMemoryDistillationInputsFromState(advancedServiceId);
  renderMemoryAdminForAdvanced(advancedServiceId);
});
reloadMemoryDistillationRunsBtn?.addEventListener("click", reloadMemoryDistillationRuns);
resetMemoryDistillationRunsBtn?.addEventListener("click", resetMemoryDistillationRuns);
applyMemoryAuditBtn?.addEventListener("click", applyMemoryAuditFilters);
resetMemoryAuditBtn?.addEventListener("click", resetMemoryAuditFilters);
reloadMemoryProjectsBtn?.addEventListener("click", reloadMemoryProjects);
resetMemoryProjectsBtn?.addEventListener("click", resetMemoryProjectsFilters);
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
  renderCards();

  const settingsResults = await Promise.allSettled([loadDashboardSettings(), loadVaultState(), loadDbTargets()]);
  for (const result of settingsResults) {
    if (result.status === "rejected") {
      console.warn("Dashboard bootstrap warning:", result.reason);
    }
  }

  renderSettingsPanel();

  try {
    await refreshDashboardOverview({ tail: Math.max(currentRecentRowsLimit() * 8, 2000), recentCount: 1 });
  } catch (err) {
    console.warn("Dashboard overview bootstrap failed:", err);
  }

  scheduleAutoRefresh();
}

boot().catch(err => {
  widgetGrid.innerHTML = `<article class="widget-card"><div class="widget-title">Errore</div><div class="widget-meta">${err.message}</div></article>`;
});












