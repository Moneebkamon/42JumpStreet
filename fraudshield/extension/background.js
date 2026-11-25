/**
 * Manee — MV3 service worker.
 * Coordinates rules scoring, RDAP age lookup, tab result storage and the
 * optional team LLM hook. No remote code and no API keys.
 */

import { analyzeDomain } from "./scoring.js";
import { getDomainAgeDays, getRegistrableDomain } from "./rdap.js";
import { getIpOwner } from "./ip-intel.js";
import { initBlocker, getSettings, tintedIcon } from "./blocker.js";
import { initDownloadGuard } from "./downloads.js";
import { TOKEN_KEY, ENABLED_KEY, isEnabled } from "./account-state.js";
import { initReports } from "./reports.js";
import "./i18n.js";
import "./phone-claims.js";

const I18N = globalThis.FE_I18N;

// Redirect high-risk navigations to warning.html (see blocker.js).
initBlocker();
// Pause and check dangerous downloads (see downloads.js).
initDownloadGuard();
initReports();

const MAX_CONCURRENT_DOMAINS = 5;
const MAX_TAB_RESULTS = 250;
const TAB_STORAGE_PREFIX = "fe:tab-results:";
const LLM_TIMEOUT_MS = 6000;
// Known body + personal mobile number in a search result (fake customer service).
const BRAND_PHONE_POINTS = 60;

// Last known results per tab. Storage is the crash/restart-safe backup.
const tabResultsMemory = new Map();
const tabMergeQueues = new Map();

// ---------------------------------------------------------------------------
// Message handling
// ---------------------------------------------------------------------------

if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onMessage) {
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (!message || typeof message.type !== "string") return false;

    try {
      if (message.type === "GET_ACCOUNT") {
        getAccountState().then((p) => safeRespond(sendResponse, p)).catch(() => safeRespond(sendResponse, { linked: false }));
        return true;
      }
      if (message.type === "LINK_ACCOUNT") {
        linkAccount(message.token).then((p) => safeRespond(sendResponse, p)).catch(() => safeRespond(sendResponse, { linked: false }));
        return true;
      }
      if (message.type === "UNLINK_ACCOUNT") {
        unlinkAccount().then((p) => safeRespond(sendResponse, p)).catch(() => safeRespond(sendResponse, { linked: false }));
        return true;
      }
      if (message.type === "REPORT_URL" && typeof message.url === "string") {
        reportToManee(message.url, message.note)
          .then((payload) => safeRespond(sendResponse, payload))
          .catch(() => safeRespond(sendResponse, { ok: false, status: 0 }));
        return true;
      }
      if (message.type === "ANALYZE") {
        handleAnalyzeMessage(message, sender)
          .then((results) => safeRespond(sendResponse, results))
          .catch((error) => {
            console.warn("[Manee] Analyze failed:", error);
            safeRespond(sendResponse, []);
          });
        return true;
      }

      if (message.type === "GET_TAB_RESULTS") {
        getTabResults(message, sender)
          .then((payload) => safeRespond(sendResponse, payload))
          .catch(() => safeRespond(sendResponse, emptyTabPayload(null)));
        return true;
      }
    } catch (error) {
      console.warn("[Manee] Message handler failed:", error);
      safeRespond(sendResponse, message.type === "ANALYZE" ? [] : emptyTabPayload(null));
      return false;
    }

    return false;
  });

  if (chrome.tabs && chrome.tabs.onRemoved) {
    chrome.tabs.onRemoved.addListener((tabId) => {
      void clearTabResults(tabId);
    });
  }

  // A real navigation starts a new page; drop the previous page's results.
  if (chrome.tabs && chrome.tabs.onUpdated) {
    chrome.tabs.onUpdated.addListener((tabId, changeInfo) => {
      if (changeInfo && changeInfo.status === "loading" && changeInfo.url) {
        void clearTabResults(tabId);
      }
    });
  }
}

async function handleAnalyzeMessage(message, sender) {
  // Switched off from the website: do nothing, so no badges appear.
  if (!(await isEnabled())) return [];
  const rawUrls = Array.isArray(message.urls) ? message.urls : [];
  const targets = prepareTargets(rawUrls, message.sponsoredUrls, message.meta);
  if (targets.length === 0) return [];

  // One RDAP lookup per registrable domain, shared by all of its URLs.
  const ageLookups = new Map();
  const getAge = (hostname) => {
    const domain = getRegistrableDomain(hostname);
    if (!domain) return Promise.resolve(null);

    if (!ageLookups.has(domain)) {
      ageLookups.set(
        domain,
        getDomainAgeDays(domain).catch(() => null)
      );
    }
    return ageLookups.get(domain);
  };

  const lang = I18N.resolve((await getSettings()).lang);
  const analyzed = await mapWithConcurrency(
    targets,
    MAX_CONCURRENT_DOMAINS,
    async (target) => analyzeTarget(target, getAge, lang)
  );

  const results = analyzed.filter(Boolean);
  const tabId = resolveAnalyzeTabId(message, sender);

  if (tabId !== null && results.length > 0) {
    await mergeTabResults(tabId, results);
  }
  // Visits from page content (not manual popup checks) are added to the signed-in user's history.
  if (sender && sender.tab && results.length > 0) {
    void uploadVisits(results);
  }

  return results;
}

async function analyzeTarget(target, getAge, lang) {
  const { url, parsed } = target;
  const hostname = parsed.hostname;
  const scoringOptions = {
    protocol: parsed.protocol,
    path: `${parsed.pathname}${parsed.search}`,
    lang
  };

  try {
    // Immediate rules result (RDAP has not answered yet).
    let scored = analyzeDomain(hostname, scoringOptions);

    // The lookup is shared/cached; scoring is re-run with the real age.
    // For an IP address, also ask who owns it (Google itself vs a rented server).
    const [ageDays, ipOwner] = await Promise.all([
      getAge(hostname),
      getIpOwner(hostname).catch(() => null)
    ]);
    scored = analyzeDomain(hostname, { ...scoringOptions, ageDays, ipOwner });

    // A known bank / police / government name with a personal mobile number
    // in the result text (fake "customer service" ads and listings).
    if (scored.level !== "safe") {
      scored = applyBrandPhone(scored, `${target.title || ""} ${target.snippet || ""}`, lang);
    }

    // Only gray-zone results are eligible for the optional LLM hook.
    if (scored.level === "medium") {
      scored = await blendWithLlm(scored, {
        url,
        title: target.title || "",
        snippet: target.snippet || ""
      });
    }

    // Sponsored result on a non-official domain: +15 after rules and RDAP.
    if (target.sponsored && scored.level !== "safe") {
      scored = applySponsoredBoost(scored, lang);
    }

    return {
      url,
      hostname,
      score: scored.score,
      level: scored.level,
      reasons: scored.reasons,
      ageDays
    };
  } catch {
    return {
      url,
      hostname,
      score: 0,
      level: "low",
      reasons: [I18N.t("analyzeFailed", lang)],
      ageDays: null
    };
  }
}

/**
 * TEAM LLM HOOK: gray-zone (score 30-59) pages are sent here; if result is
 * non-null, blend it: final = max(rulesScore, llmScore).
 *
 * Replace the body with the team's local/remote implementation later. Keep the
 * return shape: { score: number, reasons: string[] } or null. The caller
 * enforces a 6-second timeout and never lets this hook break an analysis.
 *
 * Input comes from the page: Search sends the result title + visible snippet,
 * Maps sends the place name + "category | phone | source: Google Maps".
 *
 * @param {{url: string, title: string, snippet: string}} input
 * @returns {Promise<{score: number, reasons: string[]}|null>}
 */
export async function llmAnalyze({ url, title, snippet }) {
  void title;
  void snippet;
  // Manee backend: URL-only scan (never deep). Any failure -> null, so the local rules result stands.
  const base = await getApiBase();
  const response = await fetch(`${base}/api/v1/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, deep: false })
  });
  if (!response.ok) return null;

  const data = await response.json();
  if (!data || !Number.isFinite(Number(data.score))) return null;

  const reasons = Array.isArray(data.reasons)
    ? data.reasons.slice(0, 3).map((r) => `Manee: ${r.reason}`)
    : [];
  return { score: Number(data.score), reasons };
}

// ---------------------------------------------------------------------------
// Manee account link (optional). Unlinked = the extension works fully locally, as before.
// ---------------------------------------------------------------------------

const SYNC_ALARM = "fe:sync";
const uploadedUrls = new Set();

async function getToken() {
  try {
    const data = await chrome.storage.local.get(TOKEN_KEY);
    return typeof data[TOKEN_KEY] === "string" ? data[TOKEN_KEY] : "";
  } catch {
    return "";
  }
}

/** Ask the website whether the extension should be active. Offline/unlinked -> keep the last known value. */
async function syncConfig() {
  const token = await getToken();
  if (!token) return { linked: false, enabled: true };
  try {
    const base = await getApiBase();
    const response = await withTimeout(
      fetch(`${base}/api/v1/ext/config`, { headers: { Authorization: `Bearer ${token}` } }),
      LLM_TIMEOUT_MS
    );
    if (response.status === 401) {
      await chrome.storage.local.remove([TOKEN_KEY, ENABLED_KEY]); // device was removed on the website
      return { linked: false, enabled: true, revoked: true };
    }
    if (response.ok) {
      const data = await response.json();
      await chrome.storage.local.set({ [ENABLED_KEY]: data.enabled !== false });
      return { linked: true, enabled: data.enabled !== false };
    }
  } catch {
    // Offline: fall through to the stored value.
  }
  return { linked: true, enabled: await isEnabled(), offline: true };
}

async function getAccountState() {
  return syncConfig();
}

async function linkAccount(token) {
  if (typeof token !== "string" || !/^fsd_[A-Za-z0-9_-]{20,80}$/.test(token.trim())) {
    return { linked: false, error: "invalid" };
  }
  await chrome.storage.local.set({ [TOKEN_KEY]: token.trim() });
  const state = await syncConfig();
  if (!state.linked) return { linked: false, error: "rejected" };
  return state;
}

async function unlinkAccount() {
  await chrome.storage.local.remove([TOKEN_KEY, ENABLED_KEY]);
  return { linked: false, enabled: true };
}

async function uploadVisits(results) {
  const token = await getToken();
  if (!token) return;
  const fresh = results.filter((r) => r && r.url && !uploadedUrls.has(r.url)).slice(0, 100);
  if (fresh.length === 0) return;
  fresh.forEach((r) => uploadedUrls.add(r.url));
  try {
    const base = await getApiBase();
    await withTimeout(
      fetch(`${base}/api/v1/ext/visits`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          visits: fresh.map((r) => ({
            url: String(r.url).slice(0, 2048),
            score: clamp(Math.round(Number(r.score) || 0), 0, 100),
            level: r.level === "high" || r.level === "medium" ? r.level : "low"
          }))
        })
      }),
      LLM_TIMEOUT_MS
    );
  } catch {
    fresh.forEach((r) => uploadedUrls.delete(r.url)); // try again with the next batch
  }
}

const PLAIN_ICON = { 16: "icons/icon16.png", 48: "icons/icon48.png", 128: "icons/icon128.png" };

/**
 * Toolbar icon: grey with an OFF badge while the website's switch is Inactive, plain Manee icon when Active.
 * Chrome does not let an extension remove its own icon, so this is the clearest "off" it can show.
 */
async function applyToolbarState(on) {
  if (typeof chrome === "undefined" || !chrome.action) return;
  const grey = on ? null : await tintedIcon("#6B7280").catch(() => null);
  const apply = async (target) => {
    try {
      await chrome.action.setBadgeText({ ...target, text: on ? "" : "OFF" });
      if (!on) {
        await chrome.action.setBadgeBackgroundColor({ ...target, color: "#6B7280" });
        if (chrome.action.setBadgeTextColor) await chrome.action.setBadgeTextColor({ ...target, color: "#FFFFFF" });
      }
      await chrome.action.setTitle({ ...target, title: on ? "Manee" : "Manee — switched off from the website" });
      await chrome.action.setIcon(grey ? { ...target, imageData: grey } : { ...target, path: PLAIN_ICON });
    } catch {
      // Tab closed meanwhile: the indicator is cosmetic.
    }
  };
  await apply({}); // new tabs and new pages
  try {
    for (const tab of await chrome.tabs.query({})) {
      if (Number.isInteger(tab.id)) await apply({ tabId: tab.id }); // tabs that already have their own indicator
    }
  } catch {
    // Ignore.
  }
}

if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.onChanged) {
  // Fires as soon as the website's switch reaches the extension (or the account is linked / unlinked).
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== "local" || !(ENABLED_KEY in changes || TOKEN_KEY in changes)) return;
    void isEnabled().then(applyToolbarState);
  });
}
// Whenever the background worker wakes up, make the icon match the saved state.
void isEnabled().then(applyToolbarState);

if (typeof chrome !== "undefined" && chrome.alarms && chrome.runtime) {
  chrome.alarms.create(SYNC_ALARM, { periodInMinutes: 1 });
  chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === SYNC_ALARM) void syncConfig();
  });
  chrome.runtime.onStartup.addListener(() => void syncConfig());
  chrome.runtime.onInstalled.addListener(() => void syncConfig());
}

// ---------------------------------------------------------------------------
// Manee connection
// ---------------------------------------------------------------------------

// Default: the web app on :3000, which proxies /api/v1/* to the backend (works for `yarn frontend` and Docker).
const DEFAULT_API_BASE = "http://127.0.0.1:3000";
const API_BASE_KEY = "fe:api-base";

async function getApiBase() {
  try {
    const data = await chrome.storage.local.get(API_BASE_KEY);
    const value = data && data[API_BASE_KEY];
    if (typeof value === "string" && /^https?:\/\//.test(value)) return value.replace(/\/+$/, "");
  } catch {
    // Fall through to the default.
  }
  return DEFAULT_API_BASE;
}

/** Send a link the user reports to Manee's public citizen-report endpoint (the page is never opened there). */
async function reportToManee(url, note) {
  try {
    const base = await getApiBase();
    const response = await withTimeout(
      fetch(`${base}/api/v1/citizen-reports`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, note: note || "Reported from the Manee", contact: "", website: "" })
      }),
      LLM_TIMEOUT_MS
    );
    return { ok: response.ok, status: response.status };
  } catch {
    return { ok: false, status: 0 };
  }
}

async function blendWithLlm(scored, input) {
  let llmResult = null;

  try {
    llmResult = await withTimeout(
      llmAnalyze(input),
      LLM_TIMEOUT_MS
    );
  } catch {
    return scored;
  }

  if (!llmResult || typeof llmResult !== "object") return scored;

  const llmScore = Number(llmResult.score);
  if (!Number.isFinite(llmScore)) return scored;

  const finalScore = Math.max(
    scored.score,
    clamp(Math.round(llmScore), 0, 100)
  );

  const reasons = scored.reasons.slice();
  if (Array.isArray(llmResult.reasons)) {
    for (const reason of llmResult.reasons) {
      if (
        typeof reason === "string" &&
        reason.trim() &&
        !reasons.includes(reason)
      ) {
        reasons.push(reason);
      }
    }
  }

  return {
    score: finalScore,
    level: levelForScore(finalScore),
    reasons
  };
}

function withTimeout(promise, timeoutMs) {
  let timer = null;

  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error("LLM timeout")), timeoutMs);
  });

  return Promise.race([promise, timeout]).finally(() => {
    if (timer !== null) clearTimeout(timer);
  });
}

export function applyBrandPhone(scored, text, lang) {
  const hit = globalThis.FE_PHONE.findBrandMobile(text);
  if (!hit) return scored;
  const score = Math.min(100, scored.score + BRAND_PHONE_POINTS);
  const reason = I18N.t("searchPhone", lang, {
    brand: I18N.brandLabel(hit.brand, lang),
    phone: hit.phone
  });
  return { ...scored, score, level: levelForScore(score), reasons: [...scored.reasons, reason] };
}

function applySponsoredBoost(scored, lang) {
  const score = Math.min(100, scored.score + 15);
  const reason = I18N.t("sponsored", lang);
  const reasons = scored.reasons.includes(reason)
    ? scored.reasons
    : [...scored.reasons, reason];

  return {
    score,
    level: levelForScore(score),
    reasons
  };
}

// ---------------------------------------------------------------------------
// Input preparation and bounded concurrency
// ---------------------------------------------------------------------------

function prepareTargets(rawUrls, sponsoredUrls, meta) {
  const metaByUrl = meta && typeof meta === "object" ? meta : {};
  const seen = new Set();
  const targets = [];
  const sponsoredKeys = new Set();

  if (Array.isArray(sponsoredUrls)) {
    for (const sponsoredUrl of sponsoredUrls) {
      if (typeof sponsoredUrl !== "string") continue;
      try {
        const parsed = new URL(sponsoredUrl.trim());
        parsed.hash = "";
        sponsoredKeys.add(parsed.href);
      } catch {
        // Ignore malformed sponsored URLs.
      }
    }
  }

  for (const rawUrl of rawUrls) {
    if (typeof rawUrl !== "string") continue;

    let parsed;
    try {
      parsed = new URL(rawUrl.trim());
    } catch {
      continue;
    }

    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") continue;

    // Fragments are irrelevant for a domain analysis.
    parsed.hash = "";
    const key = parsed.href;
    if (seen.has(key)) continue;

    seen.add(key);
    const info = metaByUrl[rawUrl] || metaByUrl[rawUrl.trim()] || metaByUrl[key] || {};
    targets.push({
      url: rawUrl.trim(),
      parsed,
      sponsored: sponsoredKeys.has(key),
      title: typeof info.title === "string" ? info.title.slice(0, 200) : "",
      snippet: typeof info.snippet === "string" ? info.snippet.slice(0, 400) : ""
    });
  }

  return targets;
}

async function mapWithConcurrency(items, limit, worker) {
  const results = new Array(items.length).fill(null);
  let nextIndex = 0;

  async function runWorker() {
    while (true) {
      const index = nextIndex;
      nextIndex += 1;
      if (index >= items.length) return;

      try {
        results[index] = await worker(items[index], index);
      } catch {
        results[index] = null;
      }
    }
  }

  const workerCount = Math.min(limit, items.length);
  await Promise.all(Array.from({ length: workerCount }, () => runWorker()));
  return results;
}

// ---------------------------------------------------------------------------
// Per-tab result store (memory + chrome.storage.local)
// ---------------------------------------------------------------------------

function resolveAnalyzeTabId(message, sender) {
  if (sender && sender.tab && Number.isInteger(sender.tab.id)) {
    return sender.tab.id;
  }
  if (Number.isInteger(message.tabId)) return message.tabId;
  return null;
}

/**
 * Serialize reads/merges/writes per tab so two quick MutationObserver batches
 * cannot overwrite each other.
 */
function mergeTabResults(tabId, freshResults) {
  const previous = tabMergeQueues.get(tabId) || Promise.resolve();

  const queued = previous
    .catch(() => {})
    .then(() => performMergeTabResults(tabId, freshResults))
    .catch((error) => {
      console.warn("[Manee] Saving tab results failed:", error);
    });

  tabMergeQueues.set(tabId, queued);
  queued.finally(() => {
    if (tabMergeQueues.get(tabId) === queued) tabMergeQueues.delete(tabId);
  });

  return queued;
}

async function performMergeTabResults(tabId, freshResults) {
  const state = await loadTabState(tabId);
  const byUrl = new Map();

  for (const result of state.results) {
    if (result && typeof result.url === "string") {
      byUrl.set(resultKey(result.url), result);
    }
  }

  for (const result of freshResults) {
    if (result && typeof result.url === "string") {
      byUrl.set(resultKey(result.url), result);
    }
  }

  const merged = Array.from(byUrl.values())
    .sort((a, b) => Number(b.score) - Number(a.score))
    .slice(0, MAX_TAB_RESULTS);

  const nextState = {
    updatedAt: Date.now(),
    results: merged
  };

  tabResultsMemory.set(tabId, nextState);

  try {
    await chrome.storage.local.set({
      [`${TAB_STORAGE_PREFIX}${tabId}`]: nextState
    });
  } catch {
    // Memory still serves the popup while this worker is alive.
  }
}

async function loadTabState(tabId) {
  const cached = tabResultsMemory.get(tabId);
  if (cached) return cached;

  try {
    const key = `${TAB_STORAGE_PREFIX}${tabId}`;
    const data = await chrome.storage.local.get(key);
    const state = data && data[key];

    if (state && Array.isArray(state.results)) {
      const normalized = {
        updatedAt: Number.isFinite(state.updatedAt) ? state.updatedAt : null,
        results: state.results
      };
      tabResultsMemory.set(tabId, normalized);
      return normalized;
    }
  } catch {
    // Ignore storage failures and return an empty state.
  }

  return { updatedAt: null, results: [] };
}

async function getTabResults(message, sender) {
  const tabId = await resolveReadTabId(message, sender);
  if (tabId === null) return emptyTabPayload(null);

  const state = await loadTabState(tabId);
  return {
    ok: true,
    tabId,
    results: state.results,
    updatedAt: state.updatedAt
  };
}

async function resolveReadTabId(message, sender) {
  if (Number.isInteger(message.tabId)) return message.tabId;
  if (sender && sender.tab && Number.isInteger(sender.tab.id)) {
    return sender.tab.id;
  }

  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tabs && tabs[0] && Number.isInteger(tabs[0].id)) return tabs[0].id;
  } catch {
    // No active tab available.
  }

  return null;
}

async function clearTabResults(tabId) {
  tabResultsMemory.delete(tabId);

  try {
    await chrome.storage.local.remove(`${TAB_STORAGE_PREFIX}${tabId}`);
  } catch {
    // Ignore cleanup failures.
  }
}

function emptyTabPayload(tabId) {
  return {
    ok: false,
    tabId,
    results: [],
    updatedAt: null
  };
}

function resultKey(url) {
  try {
    const parsed = new URL(url);
    parsed.hash = "";
    return parsed.href;
  } catch {
    return String(url);
  }
}

// ---------------------------------------------------------------------------
// Small utilities
// ---------------------------------------------------------------------------

function levelForScore(score) {
  if (score >= 60) return "high";
  if (score >= 30) return "medium";
  return "low";
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function safeRespond(sendResponse, payload) {
  try {
    sendResponse(payload);
  } catch {
    // The message port may already be closed (for example after navigation).
  }
}
