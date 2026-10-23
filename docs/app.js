"use strict";

// Personal tracking (status, application date, notes) lives ONLY in this
// browser's localStorage. It is never sent anywhere nor written to the repo.
const STORAGE_KEY = "internship-tracker.v1";

const STATUSES = [
  ["", "—"],
  ["watch", "À regarder"],
  ["apply", "À postuler"],
  ["applied", "Postulé"],
  ["interview", "Entretien"],
  ["rejected", "Refus"],
  ["offer", "Offre"],
  ["hidden", "Masquée (pas intéressée)"],
];
const STATUS_LABEL = Object.fromEntries(STATUSES);

const TYPE_LABEL = {
  french_bank: "Banque française",
  intl_bank: "Banque internationale",
  european_bank: "Banque européenne",
  broker: "Broker / structuration",
  asset_manager: "Asset manager",
  hedge_fund: "Hedge fund / trading",
  software: "Éditeur",
  insurance: "Assurance",
  institution: "Institution",
  consulting: "Conseil risque",
  commodities: "Trading matières premières",
  infrastructure: "Bourse / infrastructure",
  corporate: "Grand groupe (trésorerie / marchés)",
};

const FAMILY_LABEL = {
  "Structuring": "Structuring",
  "Pricing / Quant": "Pricing / Quant",
  "Risk": "Risque",
  "Quant dev": "Quant dev / Strats",
  "Trading": "Trading",
  "Product control": "Product control",
  "Treasury": "Trésorerie / financement",
  "Markets (other)": "Autres métiers marchés",
  "Other": "Autre",
};

const TIMING_LABEL = {
  june: "Début en juin",
  summer: "Summer",
  "off-cycle": "Off-cycle",
  unknown: "Calendrier inconnu",
};
const MONTHS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
  "septembre", "octobre", "novembre", "décembre"];

// "june" is a sub-case of summer: offers starting in June are shown first.
function timingKey(job) {
  if ((job.start || "").endsWith("-06")) return "june";
  return job.timing || "unknown";
}

function startLabel(job) {
  if (!job.start) return "";
  const [y, m] = job.start.split("-");
  if (m) return `Démarre en ${MONTHS_FR[Number(m) - 1]} ${y}`;
  if (job.timing === "summer") return `Summer ${y} · été`;
  if (job.timing === "off-cycle") return `Off-cycle ${y} · mois à vérifier`;
  return `Démarrage ${y} · mois à vérifier`;
}

// ---------------------------------------------------------------- recruiting calendar

// Keep in sync with EARLIEST_START and GRADUATION_YEAR in tracker/config.py.
const EARLIEST_START = [2027, 6];
const GRADUATION_YEAR = 2029;
const MONTHS_SHORT = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];

// Usual application windows, relative to the start year Y of the internship:
// [year offset, month]. "start" is when the internship begins. Indicative only.
const CYCLES = {
  anglo: [
    { name: "Summer", start: [0, 6], open: [-1, 7], close: [-1, 11] },
    { name: "Off-cycle juil.", start: [0, 7], open: [0, 1], close: [0, 4] },
    { name: "Off-cycle janv.", start: [0, 1], open: [-1, 9], close: [-1, 11] },
  ],
  trading: [
    { name: "Summer", start: [0, 6], open: [-1, 6], close: [-1, 10] },
    { name: "Off-cycle juil.", start: [0, 7], open: [0, 1], close: [0, 4] },
    { name: "Off-cycle janv.", start: [0, 1], open: [-1, 8], close: [-1, 12] },
  ],
  fr: [
    { name: "Stage dès juin", start: [0, 6], open: [0, 1], close: [0, 4] },
    { name: "Stage dès sept.", start: [0, 9], open: [0, 4], close: [0, 7] },
    { name: "Stage dès janv.", start: [0, 1], open: [-1, 9], close: [-1, 11] },
  ],
  consulting: [
    { name: "Stage dès juin", start: [0, 6], open: [-1, 10], close: [0, 3] },
    { name: "Stage dès janv.", start: [0, 1], open: [-1, 7], close: [-1, 10] },
  ],
};
const TYPE_CYCLE = {
  intl_bank: "anglo", infrastructure: "anglo", hedge_fund: "trading",
  french_bank: "fr", european_bank: "fr", broker: "fr", asset_manager: "fr",
  insurance: "fr", commodities: "fr", software: "fr", corporate: "fr", consulting: "consulting",
  institution: null,
};

const monthIndex = (y, m) => y * 12 + (m - 1);

// For each usual window, the next one that is not over yet, for an internship
// starting between EARLIEST_START and graduation.
function nextWindows(type) {
  const cycle = CYCLES[TYPE_CYCLE[type]];
  if (!cycle) return [];
  const now = new Date();
  const today = monthIndex(now.getFullYear(), now.getMonth() + 1);
  const earliest = monthIndex(...EARLIEST_START);
  const out = [];
  for (const w of cycle) {
    for (let y = now.getFullYear(); y <= GRADUATION_YEAR; y++) {
      const start = monthIndex(y + w.start[0], w.start[1]);
      const open = monthIndex(y + w.open[0], w.open[1]);
      const close = monthIndex(y + w.close[0], w.close[1]);
      if (start < earliest || close < today) continue;
      const state = open <= today ? "open" : open - today <= 3 ? "soon" : "later";
      const fmt = (i) => `${MONTHS_SHORT[i % 12]} ${Math.floor(i / 12)}`;
      out.push({ label: `${w.name} ${y} : ${fmt(open)} → ${fmt(close)}`, state, open });
      break;
    }
  }
  return out.sort((a, b) => a.open - b.open);
}

const CONTACT_STATUSES = [
  ["", "—"],
  ["todo", "À contacter"],
  ["contacted", "Contacté"],
  ["followup", "Relancé"],
  ["positive", "Réponse positive"],
  ["negative", "Refus"],
];

const state = {
  tab: "new",
  jobs: [],
  newIds: new Set(),
  runDate: "",
  tracking: loadTracking(),
  manual: loadManual(),
  companies: [],
  contacts: loadContacts(),
};

const $ = (id) => document.getElementById(id);

// ---------------------------------------------------------------- storage

function loadTracking() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
  } catch {
    return {};
  }
}

// Offers added by hand: same privacy rule as tracking (this browser only).
function loadManual() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY + ".manual")) || [];
  } catch {
    return [];
  }
}

function saveManual() {
  try {
    localStorage.setItem(STORAGE_KEY + ".manual", JSON.stringify(state.manual));
  } catch {
    alert("Impossible d'enregistrer dans ce navigateur (navigation privée ?). Exportez un CSV pour ne rien perdre.");
  }
}

function loadContacts() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY + ".contacts")) || {};
  } catch {
    return {};
  }
}

function updateContact(name, patch) {
  const next = { ...(state.contacts[name] || {}), ...patch };
  if (!next.status && !next.date && !next.notes) delete state.contacts[name];
  else state.contacts[name] = next;
  try { localStorage.setItem(STORAGE_KEY + ".contacts", JSON.stringify(state.contacts)); } catch { /* ignore */ }
}

function saveTracking() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state.tracking));
  } catch {
    alert("Impossible d'enregistrer dans ce navigateur (navigation privée ?). Exportez un CSV pour ne rien perdre.");
  }
}

// Statuses meaning "I applied": these offers stay in Mon suivi even once closed.
const APPLIED = new Set(["applied", "interview", "rejected", "offer"]);
const todayIso = () => new Date().toISOString().slice(0, 10);

function applied(job) {
  return APPLIED.has((state.tracking[job.id] || {}).status);
}

// Closed: removed by the employer, or past a deadline stated in the ad.
function isClosed(job) {
  if (job.manual) return false;
  return !job.active || (job.deadline_source === "annonce" && job.deadline && job.deadline < todayIso());
}

function daysLeft(job) {
  if (!job.deadline) return Infinity;
  return Math.round((new Date(job.deadline + "T23:59:59") - new Date()) / 86400000);
}

function deadlineLabel(job) {
  const [y, m, d] = job.deadline.split("-");
  if (job.deadline_source === "annonce") return `Clôture le ${d}/${m}/${y}`;
  return `Clôture estimée fin ${MONTHS_SHORT[Number(m) - 1]} ${y}`;
}

function isHidden(job) {
  return (state.tracking[job.id] || {}).status === "hidden";
}

let toastTimer;
function showToast(text, undo) {
  $("toast-text").textContent = text;
  $("toast").hidden = false;
  $("toast-undo").onclick = () => { undo(); $("toast").hidden = true; };
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { $("toast").hidden = true; }, 6000);
}

function updateTracking(job, patch) {
  const current = state.tracking[job.id] || {};
  const next = { ...current, ...patch, updated: new Date().toISOString() };
  // Keep a snapshot so the offer stays in "Mon suivi" even after it closes.
  next.job = { title: job.title, employer: job.employer, url: job.url, location: job.location };
  if (!next.status && !next.applied_on && !next.notes) {
    delete state.tracking[job.id];
  } else {
    state.tracking[job.id] = next;
  }
  saveTracking();
  updateCounts();
}

// ---------------------------------------------------------------- data

async function fetchJson(path) {
  const resp = await fetch(path, { cache: "no-cache" });
  if (!resp.ok) throw new Error(`${path}: ${resp.status}`);
  return resp.json();
}

async function load() {
  try {
    const [jobs, fresh, errors, companies] = await Promise.all([
      fetchJson("data/jobs.json"),
      fetchJson("data/new_today.json").catch(() => ({ jobs: [] })),
      fetchJson("data/errors.json").catch(() => null),
      fetchJson("employers.json").catch(() => []),
    ]);
    state.companies = companies;
    state.jobs = jobs.jobs || [];
    state.newIds = new Set((fresh.jobs || []).map((j) => j.id));
    state.runDate = fresh.date || "";
    renderStatus(jobs.generated_at, errors);
  } catch (err) {
    $("status").textContent = "Données indisponibles";
    $("empty").hidden = false;
    $("empty").textContent = "Les données n'ont pas encore été générées : lancez le workflow « Daily scrape ».";
    return;
  }
  // Tracked offers that disappeared from the history are kept from their snapshot.
  const known = new Set([...state.jobs, ...state.manual].map((j) => j.id));
  for (const [id, t] of Object.entries(state.tracking)) {
    if (!known.has(id) && t.job) {
      state.jobs.push({ id, ...t.job, employer_type: "", countries: [], country_names: [],
        family: "Other", score: 0, active: false, first_seen: "", archived: true });
    }
  }
  state.jobs.push(...state.manual);
  fillFilters();
  fillDialog();
  restoreFilters();
  render();
}

function renderStatus(generatedAt, errors) {
  const when = generatedAt ? new Date(generatedAt) : null;
  const fmt = when ? when.toLocaleString("fr-FR", { dateStyle: "medium", timeStyle: "short" }) : "inconnue";
  const failed = errors ? errors.employers_failed : 0;
  const total = errors ? errors.employers_total : 0;
  $("status").innerHTML = `Dernière mise à jour : <strong>${fmt}</strong><br>` +
    (errors ? `${total - failed}/${total} employeurs OK` : "");
  if (errors && errors.errors && errors.errors.length) {
    $("errors").hidden = false;
    $("errors-summary").textContent = `${errors.errors.length} employeur(s) en erreur lors du dernier passage`;
    const list = $("errors-list");
    list.innerHTML = "";
    for (const e of errors.errors) {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = e.careers_url;
      a.target = "_blank";
      a.rel = "noopener";
      a.textContent = e.employer;
      const code = document.createElement("code");
      code.textContent = ` ${e.platform} — ${e.error}`;
      li.append(a, code);
      list.append(li);
    }
  }
}

// ---------------------------------------------------------------- filters

const FILTER_IDS = ["f-search", "f-employer", "f-type", "f-country", "f-family", "f-timing", "f-year", "f-date", "f-status", "f-score", "f-inactive", "f-hidden"];

function fillSelect(id, entries) {
  const select = $(id);
  for (const [value, label] of entries) {
    const opt = document.createElement("option");
    opt.value = value;
    opt.textContent = label;
    select.append(opt);
  }
}

function fillFilters() {
  const uniq = (arr) => [...new Set(arr.filter(Boolean))];
  const employers = uniq(state.jobs.map((j) => j.employer)).sort((a, b) => a.localeCompare(b, "fr"));
  fillSelect("f-employer", employers.map((e) => [e, e]));
  const types = uniq(state.jobs.map((j) => j.employer_type));
  fillSelect("f-type", types.map((t) => [t, TYPE_LABEL[t] || t]).sort((a, b) => a[1].localeCompare(b[1], "fr")));
  const countries = new Map();
  for (const j of state.jobs) {
    (j.countries || []).forEach((c, i) => countries.set(c, (j.country_names || [])[i] || c));
  }
  const countryEntries = [...countries.entries()].sort((a, b) => a[1].localeCompare(b[1], "fr"));
  fillSelect("f-country", [["__none", "Non précisé"], ...countryEntries]);
  const families = uniq(state.jobs.map((j) => j.family));
  fillSelect("f-family", Object.keys(FAMILY_LABEL).filter((f) => families.includes(f)).map((f) => [f, FAMILY_LABEL[f]]));
  fillSelect("f-timing", [
    ["june", "Début en juin"],
    ["summer", "Summer (dont juin)"],
    ["off-cycle", "Off-cycle"],
    ["unknown", "Calendrier inconnu"],
  ]);
  // Years come from the data, so new years (2029...) appear by themselves.
  const years = uniq(state.jobs.map((j) => (j.start || "").slice(0, 4))).sort();
  fillSelect("f-year", [...years.map((y) => [y, y]), ["__none", "Non précisée"]]);
  fillSelect("f-status", [["__any", "Suivie (tout statut)"], ...STATUSES.slice(1)]);
  const ctypes = [...new Set(state.companies.map((c) => c.type))];
  fillSelect("c-type", ctypes.map((t) => [t, TYPE_LABEL[t] || t]).sort((a, b) => a[1].localeCompare(b[1], "fr")));
  fillSelect("c-contact", [["__any", "Suivi (tout statut)"], ...CONTACT_STATUSES.slice(1)]);
}

function currentFilters() {
  return {
    search: $("f-search").value.trim().toLowerCase(),
    employer: $("f-employer").value,
    type: $("f-type").value,
    country: $("f-country").value,
    family: $("f-family").value,
    timing: $("f-timing").value,
    year: $("f-year").value,
    days: Number($("f-date").value) || 0,
    status: $("f-status").value,
    minScore: Number($("f-score").value) || 0,
    inactive: $("f-inactive").checked,
    hidden: $("f-hidden").checked,
  };
}

function restoreFilters() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY + ".filters")) || {};
    for (const id of FILTER_IDS) {
      if (!(id in saved)) continue;
      const el = $(id);
      if (el.type === "checkbox") el.checked = saved[id];
      else if ([...(el.options || [])].length === 0 || [...el.options].some((o) => o.value === saved[id])) el.value = saved[id];
    }
    if (saved.tab) setTab(saved.tab, false);
  } catch { /* ignore */ }
  $("f-score-out").textContent = $("f-score").value;
}

function saveFilters() {
  const saved = { tab: state.tab };
  for (const id of FILTER_IDS) {
    const el = $(id);
    saved[id] = el.type === "checkbox" ? el.checked : el.value;
  }
  try { localStorage.setItem(STORAGE_KEY + ".filters", JSON.stringify(saved)); } catch { /* ignore */ }
}

function daysAgo(isoDate) {
  if (!isoDate) return Infinity;
  const ms = Date.now() - new Date(isoDate + "T00:00:00Z").getTime();
  return Math.floor(ms / 86400000);
}

function matches(job, f) {
  const t = state.tracking[job.id];
  if (state.tab === "new" && !state.newIds.has(job.id)) return false;
  if (state.tab === "mine" && !t && !job.manual) return false;
  // An offer that is gone disappears unless I applied to it (then it stays in Mon suivi).
  if (isClosed(job) && !f.inactive && !(state.tab === "mine" && applied(job))) return false;
  // Offers marked "not interested" disappear everywhere unless asked for.
  if (isHidden(job) && !f.hidden && f.status !== "hidden") return false;
  if (f.employer && job.employer !== f.employer) return false;
  if (f.type && job.employer_type !== f.type) return false;
  if (f.country === "__none" && (job.countries || []).length) return false;
  if (f.country && f.country !== "__none" && !(job.countries || []).includes(f.country)) return false;
  if (f.family && job.family !== f.family) return false;
  if (f.timing) {
    const key = timingKey(job);
    const ok = f.timing === "summer" ? key === "summer" || key === "june" : key === f.timing;
    if (!ok) return false;
  }
  if (f.year === "__none" && job.start) return false;
  if (f.year && f.year !== "__none" && !(job.start || "").startsWith(f.year)) return false;
  if (f.days && daysAgo(job.first_seen) >= f.days) return false;
  if (f.status === "__any" && !(t && t.status)) return false;
  if (f.status && f.status !== "__any" && (!t || t.status !== f.status)) return false;
  if (job.score < f.minScore) return false;
  if (f.search) {
    const hay = `${job.title} ${job.employer} ${job.location} ${(job.country_names || []).join(" ")} ${t && t.notes || ""}`.toLowerCase();
    if (!f.search.split(/\s+/).every((w) => hay.includes(w))) return false;
  }
  return true;
}

// ---------------------------------------------------------------- render

function scoreClass(score) {
  return score >= 60 ? "high" : score >= 35 ? "mid" : "low";
}

function frDate(iso) {
  if (!iso) return "";
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

function renderCard(job) {
  const node = $("card-tpl").content.firstElementChild.cloneNode(true);
  const t = state.tracking[job.id] || {};
  if (!job.active) node.classList.add("inactive");

  const score = node.querySelector(".score");
  score.textContent = job.manual ? "✎" : job.score;
  score.classList.add(job.manual ? "manual" : scoreClass(job.score));
  if (job.manual) score.title = "Offre ajoutée par moi";
  if (job.score_breakdown) {
    const b = job.score_breakdown;
    score.title = `Score ${job.score} = métier ${b.role} + zone ${b.geo} + ville ${b.city} + calendrier ${b.timing}`;
  }

  const link = node.querySelector(".title a");
  if (job.url) link.href = job.url;
  link.textContent = job.title;
  node.querySelector(".employer").textContent = job.employer;
  node.querySelector(".type").textContent = TYPE_LABEL[job.employer_type] || "";
  node.querySelector(".location").textContent = job.location || (job.country_names || []).join(", ");

  const tags = node.querySelector(".tags");
  const addTag = (text, cls) => {
    const span = document.createElement("span");
    span.className = "tag" + (cls ? " " + cls : "");
    span.textContent = text;
    tags.append(span);
  };
  if (state.newIds.has(job.id)) addTag("Nouveau", "new");
  if (job.manual) addTag("Ajoutée par moi", "manual");
  if (!job.active) addTag(job.archived ? "Archivée" : "Fermée", "closed");
  if (job.family) addTag(FAMILY_LABEL[job.family] || job.family);
  if (job.timing) addTag(startLabel(job) || TIMING_LABEL[timingKey(job)], timingKey(job) === "june" ? "june" : "");
  if (job.deadline && !isClosed(job)) addTag(deadlineLabel(job), daysLeft(job) <= 14 ? "deadline urgent" : "deadline");
  (job.country_names || []).slice(0, 3).forEach((c) => addTag(c));
  if (job.first_seen) addTag(`Vue le ${frDate(job.first_seen)}`);
  if (job.posted_at) addTag(`Publiée le ${frDate(job.posted_at)}`);

  const select = node.querySelector(".status-select");
  for (const [value, label] of STATUSES) {
    const opt = document.createElement("option");
    opt.value = value;
    opt.textContent = label;
    select.append(opt);
  }
  select.value = t.status || "";
  select.dataset.status = select.value;
  select.addEventListener("change", () => {
    select.dataset.status = select.value;
    const patch = { status: select.value };
    if (select.value === "applied" && !applied.value) {
      applied.value = new Date().toISOString().slice(0, 10);
      patch.applied_on = applied.value;
    }
    updateTracking(job, patch);
  });

  const applied = node.querySelector(".applied-input");
  applied.value = t.applied_on || "";
  applied.addEventListener("change", () => updateTracking(job, { applied_on: applied.value }));

  const notes = node.querySelector(".notes");
  const toggle = node.querySelector(".notes-toggle");
  notes.value = t.notes || "";
  notes.hidden = !t.notes;
  toggle.textContent = t.notes ? "Masquer les notes" : "Notes";
  toggle.addEventListener("click", () => {
    notes.hidden = !notes.hidden;
    toggle.textContent = notes.hidden ? "Notes" : "Masquer les notes";
    if (!notes.hidden) notes.focus();
  });
  const hide = node.querySelector(".hide-offer");
  if (isHidden(job)) {
    node.classList.add("is-hidden");
    hide.textContent = "↺ Réafficher";
  }
  hide.addEventListener("click", () => {
    const previous = { ...(state.tracking[job.id] || {}) };
    if (isHidden(job)) {
      updateTracking(job, { status: "" });
      render();
      return;
    }
    updateTracking(job, { status: "hidden" });
    render();
    showToast(`« ${job.title.slice(0, 60)} » masquée`, () => {
      updateTracking(job, { status: previous.status || "" });
      render();
    });
  });
  if (job.manual) {
    const edit = node.querySelector(".edit-offer");
    edit.hidden = false;
    edit.addEventListener("click", () => openDialog(job));
  }
  let timer;
  notes.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(() => updateTracking(job, { notes: notes.value }), 400);
  });
  return node;
}

// Static priority (employer type, specialists, location: docs/employers.json)
// plus what changes every day: open window, current offers, my contact status.
function companyScore(c) {
  const parts = { base: c.priority || 0, window: 0, offers: 0, contact: 0 };
  const states = c.windows.map((w) => w.state);
  parts.window = states.includes("open") ? 15 : states.includes("soon") ? 8 : 0;
  const good = state.jobs.filter((j) => j.employer === c.name && !isClosed(j) && j.score >= 60).length;
  parts.offers = Math.min(15, good * 5);
  if ((state.contacts[c.name] || {}).status === "negative") parts.contact = -30;
  const total = Math.max(0, Math.min(100, parts.base + parts.window + parts.offers + parts.contact));
  return { total, parts, good };
}

function renderCompany(c) {
  const node = $("company-tpl").content.firstElementChild.cloneNode(true);
  const link = node.querySelector(".title a");
  link.href = c.careers_url;
  link.textContent = c.name;
  const badge = node.querySelector(".score");
  badge.textContent = c.score.total;
  badge.classList.add(scoreClass(c.score.total));
  const p = c.score.parts;
  badge.title = `Priorité ${c.score.total} = type et profil ${p.base} + fenêtre ${p.window} + offres en cours ${p.offers}`
    + (p.contact ? ` + contact ${p.contact}` : "");
  node.querySelector(".type").textContent = TYPE_LABEL[c.type] || c.type;
  const cov = node.querySelector(".coverage");
  cov.textContent = c.covered ? "Suivi automatique" : "À regarder à la main";
  cov.classList.add(c.covered ? "auto" : "manual");
  if (!c.covered && c.notes) cov.title = c.notes;
  const meta = node.querySelector(".meta");
  const extra = [...(c.reasons || [])];
  if (c.score.good) extra.push(`${c.score.good} offre(s) pertinente(s) en cours`);
  for (const r of extra) {
    const span = document.createElement("span");
    span.className = "tag";
    span.textContent = r;
    meta.append(span);
  }
  const windows = node.querySelector(".windows");
  const list = c.windows.length ? c.windows : [{ label: "Campagnes ponctuelles : surveiller la page carrières", state: "later" }];
  for (const w of list) {
    const span = document.createElement("span");
    span.className = `window ${w.state}`;
    span.textContent = w.label + (w.state === "open" ? " · ouverte" : w.state === "soon" ? " · bientôt" : "");
    windows.append(span);
  }
  const contact = state.contacts[c.name] || {};
  const select = node.querySelector(".contact-select");
  select.replaceChildren(...CONTACT_STATUSES.map(([v, l]) => new Option(l, v)));
  select.value = contact.status || "";
  select.addEventListener("change", () => {
    const patch = { status: select.value };
    if (select.value && select.value !== "todo" && !date.value) {
      date.value = new Date().toISOString().slice(0, 10);
      patch.date = date.value;
    }
    updateContact(c.name, patch);
  });
  const date = node.querySelector(".contact-date");
  date.value = contact.date || "";
  date.addEventListener("change", () => updateContact(c.name, { date: date.value }));
  const notes = node.querySelector(".contact-notes");
  notes.value = contact.notes || "";
  notes.addEventListener("change", () => updateContact(c.name, { notes: notes.value }));
  return node;
}

function renderCompanies() {
  const q = $("c-search").value.trim().toLowerCase();
  const type = $("c-type").value, covered = $("c-covered").value;
  const win = $("c-window").value, contact = $("c-contact").value;
  const rank = { open: 0, soon: 1, later: 2 };
  const rows = state.companies
    .map((c) => ({ ...c, windows: nextWindows(c.type) }))
    .map((c) => ({ ...c, score: companyScore(c) }))
    .filter((c) => {
      const states = c.windows.map((w) => w.state);
      const st = (state.contacts[c.name] || {}).status;
      if (q && !c.name.toLowerCase().includes(q)) return false;
      if (type && c.type !== type) return false;
      if (covered === "auto" && !c.covered) return false;
      if (covered === "manual" && c.covered) return false;
      if (win === "open" && !states.includes("open")) return false;
      if (win === "soon" && !states.includes("open") && !states.includes("soon")) return false;
      if (contact === "__any" && !st) return false;
      if (contact && contact !== "__any" && st !== contact) return false;
      return true;
    })
    .sort((a, b) => {
      const sort = $("c-sort").value;
      if (sort === "name") return a.name.localeCompare(b.name, "fr");
      const ra = Math.min(3, ...a.windows.map((w) => rank[w.state]));
      const rb = Math.min(3, ...b.windows.map((w) => rank[w.state]));
      if (sort === "window") return ra - rb || b.score.total - a.score.total;
      return b.score.total - a.score.total || ra - rb || a.name.localeCompare(b.name, "fr");
    });
  $("list").replaceChildren(...rows.map(renderCompany));
  $("result-line").textContent = `${rows.length} entreprise(s)`;
  $("empty").hidden = rows.length > 0;
  $("empty").textContent = "Aucune entreprise ne correspond aux filtres.";
}

function render() {
  const companiesTab = state.tab === "companies";
  $("filters").hidden = companiesTab;
  $("company-filters").hidden = !companiesTab;
  if (companiesTab) {
    $("pipeline").hidden = true;
    renderCompanies();
    updateCounts();
    saveFilters();
    return;
  }
  const f = currentFilters();
  const rows = state.jobs.filter((j) => matches(j, f));
  rows.sort((a, b) => b.score - a.score || (b.first_seen || "").localeCompare(a.first_seen || "") || a.employer.localeCompare(b.employer));
  const list = $("list");
  list.replaceChildren(...rows.slice(0, 500).map(renderCard));
  $("result-line").textContent = `${rows.length} offre(s)` + (rows.length > 500 ? " — 500 premières affichées, affinez les filtres" : "");
  const empty = $("empty");
  empty.hidden = rows.length > 0;
  empty.textContent = state.tab === "new"
    ? "Aucune nouvelle offre aujourd'hui avec ces filtres."
    : state.tab === "mine" ? "Aucune offre suivie : choisissez un statut sur une offre pour la retrouver ici." : "Aucune offre ne correspond aux filtres.";
  updateCounts();
  saveFilters();
}

const SOON_COLLAPSED = 8;

function renderSoon() {
  const box = $("soon");
  const rows = state.tab === "companies" ? [] : state.jobs
    .filter((j) => j.deadline && j.score >= 40 && !isClosed(j) && !isHidden(j) && !applied(j)
      && daysLeft(j) >= 0 && daysLeft(j) <= 14)
    // Deadlines stated in the ad first, then estimated ones; earliest first.
    .sort((a, b) => (a.deadline_source !== "annonce") - (b.deadline_source !== "annonce")
      || a.deadline.localeCompare(b.deadline) || b.score - a.score);
  box.hidden = rows.length === 0;
  const shown = state.soonExpanded ? rows : rows.slice(0, SOON_COLLAPSED);
  $("soon-list").replaceChildren(...shown.map((j) => {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = j.url; a.target = "_blank"; a.rel = "noopener"; a.textContent = j.title;
    const when = document.createElement("span");
    when.className = "when";
    const n = daysLeft(j);
    when.textContent = ` · ${deadlineLabel(j)} (${n === 0 ? "aujourd'hui" : `J-${n}`})`;
    li.append(a, ` — ${j.employer}`, when);
    return li;
  }));
  const more = $("soon-more");
  more.hidden = rows.length <= SOON_COLLAPSED;
  more.textContent = state.soonExpanded ? "Réduire la liste" : `Afficher les ${rows.length} échéances`;
}

function updateCounts() {
  renderSoon();
  $("count-new").textContent = state.jobs.filter((j) => state.newIds.has(j.id) && !isHidden(j) && !isClosed(j)).length;
  $("count-all").textContent = state.jobs.filter((j) => !isClosed(j) && !isHidden(j)).length;
  const mine = state.jobs.filter((j) => (state.tracking[j.id] || j.manual) && !isHidden(j)
    && !(isClosed(j) && !applied(j)));
  $("count-mine").textContent = mine.length;
  $("count-companies").textContent = state.companies.length;
  renderPipeline();
}

// Status summary shown on "Mon suivi"; a click filters on that status.
function renderPipeline() {
  const bar = $("pipeline");
  bar.hidden = state.tab !== "mine";
  if (bar.hidden) return;
  const counts = {};
  for (const t of Object.values(state.tracking)) if (t.status) counts[t.status] = (counts[t.status] || 0) + 1;
  const current = $("f-status").value;
  bar.replaceChildren(...STATUSES.slice(1).map(([value, label]) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = current === value ? "on" : "";
    b.innerHTML = `${label}<strong>${counts[value] || 0}</strong>`;
    b.addEventListener("click", () => {
      $("f-status").value = current === value ? "" : value;
      render();
    });
    return b;
  }));
}

function setTab(tab, rerender = true) {
  state.tab = tab;
  document.querySelectorAll(".tab").forEach((b) => {
    const on = b.dataset.tab === tab;
    b.classList.toggle("active", on);
    b.setAttribute("aria-selected", on);
  });
  if (rerender) render();
}

// ---------------------------------------------------------------- manual offers

let editing = null;

function fillDialog() {
  const form = $("offer-form");
  form.family.replaceChildren(...Object.entries(FAMILY_LABEL).map(([v, l]) => new Option(l, v)));
  form.family.value = "Structuring";
  form.status.replaceChildren(...STATUSES.map(([v, l]) => new Option(l, v)));
  const uniq = (arr) => [...new Set(arr.filter(Boolean))].sort((a, b) => a.localeCompare(b, "fr"));
  $("employer-list").replaceChildren(...uniq(state.jobs.map((j) => j.employer)).map((e) => new Option(e)));
  $("country-list").replaceChildren(...uniq(state.jobs.flatMap((j) => j.country_names || [])).map((c) => new Option(c)));
}

function openDialog(job = null) {
  editing = job;
  const form = $("offer-form");
  form.reset();
  $("offer-dialog-title").textContent = job ? "Modifier l'offre" : "Ajouter une offre";
  $("offer-delete").hidden = !job;
  if (job) {
    const t = state.tracking[job.id] || {};
    form.title.value = job.title;
    form.employer.value = job.employer;
    form.url.value = job.url || "";
    form.location.value = job.location || "";
    form.country.value = (job.country_names || [])[0] || "";
    form.family.value = job.family || "Other";
    form.timing.value = job.timing || "unknown";
    form.start.value = (job.start || "").length === 7 ? job.start : "";
    form.status.value = t.status || "";
    form.applied_on.value = t.applied_on || "";
    form.notes.value = t.notes || "";
  } else {
    form.family.value = "Structuring";
    form.timing.value = "summer";
  }
  $("offer-dialog").showModal();
}

// Map a typed country name to the code used by the filters, when known.
function countryCode(name) {
  for (const j of state.jobs) {
    const i = (j.country_names || []).findIndex((c) => c.toLowerCase() === name.toLowerCase());
    if (i >= 0) return j.countries[i];
  }
  return name;
}

function saveDialog() {
  const form = $("offer-form");
  const country = form.country.value.trim();
  const job = {
    ...(editing || {}),
    id: editing ? editing.id : `manual-${Date.now()}`,
    manual: true,
    active: true,
    title: form.title.value.trim(),
    employer: form.employer.value.trim(),
    url: form.url.value.trim(),
    location: form.location.value.trim(),
    countries: country ? [countryCode(country)] : [],
    country_names: country ? [country] : [],
    family: form.family.value,
    timing: form.start.value && form.start.value.endsWith("-06") ? "summer" : form.timing.value,
    start: form.start.value,
    employer_type: "",
    score: 0,
    first_seen: editing ? editing.first_seen : new Date().toISOString().slice(0, 10),
  };
  state.manual = state.manual.filter((j) => j.id !== job.id).concat(job);
  state.jobs = state.jobs.filter((j) => j.id !== job.id).concat(job);
  saveManual();
  const appliedOn = form.applied_on.value
    || (form.status.value === "applied" ? new Date().toISOString().slice(0, 10) : "");
  updateTracking(job, { status: form.status.value, applied_on: appliedOn, notes: form.notes.value });
  render();
}

function deleteEditing() {
  if (!editing || !confirm(`Supprimer « ${editing.title} » ?`)) return;
  state.manual = state.manual.filter((j) => j.id !== editing.id);
  state.jobs = state.jobs.filter((j) => j.id !== editing.id);
  delete state.tracking[editing.id];
  saveManual();
  saveTracking();
  $("offer-dialog").close();
  render();
}

// ---------------------------------------------------------------- CSV

const CSV_COLUMNS = ["id", "employer", "title", "location", "country", "url", "score", "family", "timing", "start", "first_seen", "manual", "status", "applied_on", "notes"];

function csvEscape(value) {
  const s = String(value ?? "");
  return /[",\n\r;]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

function exportCsv() {
  const byId = new Map(state.jobs.map((j) => [j.id, j]));
  const lines = [CSV_COLUMNS.join(",")];
  const ids = new Set([...Object.keys(state.tracking), ...state.manual.map((j) => j.id)]);
  for (const id of ids) {
    const t = state.tracking[id] || {};
    const j = byId.get(id) || { id, ...(t.job || {}) };
    const row = { ...j, id, country: (j.country_names || []).join(" / "), manual: j.manual ? "oui" : "",
      status: STATUS_LABEL[t.status] || "", applied_on: t.applied_on || "", notes: t.notes || "" };
    lines.push(CSV_COLUMNS.map((c) => csvEscape(row[c])).join(","));
  }
  const blob = new Blob(["﻿" + lines.join("\r\n")], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `suivi-stages-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
}

function parseCsv(text) {
  const rows = [];
  let row = [], field = "", quoted = false;
  text = text.replace(/^﻿/, "");
  const sep = text.split("\n")[0].includes(";") && !text.split("\n")[0].includes(",") ? ";" : ",";
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (ch === '"') quoted = false;
      else field += ch;
    } else if (ch === '"') quoted = true;
    else if (ch === sep) { row.push(field); field = ""; }
    else if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && text[i + 1] === "\n") i++;
      row.push(field); rows.push(row); row = []; field = "";
    } else field += ch;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  return rows.filter((r) => r.some((c) => c.trim()));
}

function importCsv(file) {
  const reader = new FileReader();
  reader.onload = () => {
    const rows = parseCsv(reader.result);
    if (!rows.length) return alert("Fichier vide.");
    const header = rows[0].map((h) => h.trim().toLowerCase());
    const col = (name) => header.indexOf(name);
    if (col("id") < 0) return alert("Colonne « id » introuvable : utilisez un fichier exporté depuis cette page.");
    const labelToStatus = Object.fromEntries(STATUSES.map(([v, l]) => [l.toLowerCase(), v]));
    let count = 0;
    for (const r of rows.slice(1)) {
      const id = r[col("id")];
      if (!id) continue;
      const rawStatus = (r[col("status")] || "").trim();
      const status = labelToStatus[rawStatus.toLowerCase()] ?? (STATUS_LABEL[rawStatus] !== undefined ? rawStatus : "");
      const get = (name) => (col(name) >= 0 ? r[col(name)] || "" : "").trim();
      let job = state.jobs.find((j) => j.id === id);
      if (!job && (get("manual") === "oui" || id.startsWith("manual-"))) {
        job = { id, manual: true, active: true, title: get("title"), employer: get("employer"), url: get("url"),
          location: get("location"), countries: get("country") ? [countryCode(get("country"))] : [],
          country_names: get("country") ? [get("country")] : [], family: get("family") || "Other",
          timing: get("timing") || "unknown", start: get("start"), employer_type: "", score: 0,
          first_seen: get("first_seen") };
        state.manual = state.manual.filter((j) => j.id !== id).concat(job);
        saveManual();
      }
      job = job || { id, title: get("title"), employer: get("employer"), url: get("url"), location: get("location") };
      updateTracking(job, { status, applied_on: (r[col("applied_on")] || "").trim(), notes: r[col("notes")] || "" });
      count++;
    }
    alert(`${count} offre(s) importée(s).`);
    location.reload();
  };
  reader.readAsText(file, "utf-8");
}

// ---------------------------------------------------------------- events

document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => setTab(b.dataset.tab)));
for (const id of FILTER_IDS) {
  $(id).addEventListener(id === "f-search" || id === "f-score" ? "input" : "change", () => {
    $("f-score-out").textContent = $("f-score").value;
    render();
  });
}
$("reset").addEventListener("click", () => {
  for (const id of FILTER_IDS) {
    const el = $(id);
    if (el.type === "checkbox") el.checked = false;
    else if (el.type === "range") el.value = 0;
    else el.value = "";
  }
  $("f-score-out").textContent = "0";
  render();
});
$("export").addEventListener("click", exportCsv);
$("soon-more").addEventListener("click", () => {
  state.soonExpanded = !state.soonExpanded;
  renderSoon();
});
for (const id of ["c-search", "c-type", "c-covered", "c-window", "c-contact", "c-sort"]) {
  $(id).addEventListener(id === "c-search" ? "input" : "change", render);
}
$("add-offer").addEventListener("click", () => openDialog());
$("offer-cancel").addEventListener("click", () => $("offer-dialog").close());
$("offer-delete").addEventListener("click", deleteEditing);
$("offer-form").addEventListener("submit", (e) => {
  if (!e.target.checkValidity()) return;
  saveDialog();
});
$("import").addEventListener("change", (e) => e.target.files[0] && importCsv(e.target.files[0]));

load();
