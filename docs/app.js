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
};

const FAMILY_LABEL = {
  "Structuring": "Structuring",
  "Pricing / Quant": "Pricing / Quant",
  "Risk": "Risque",
  "Quant dev": "Quant dev / Strats",
  "Trading": "Trading",
  "Product control": "Product control",
  "Markets (other)": "Autres métiers marchés",
  "Other": "Autre",
};

const state = {
  tab: "new",
  jobs: [],
  newIds: new Set(),
  runDate: "",
  tracking: loadTracking(),
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

function saveTracking() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state.tracking));
  } catch {
    alert("Impossible d'enregistrer dans ce navigateur (navigation privée ?). Exportez un CSV pour ne rien perdre.");
  }
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
    const [jobs, fresh, errors] = await Promise.all([
      fetchJson("data/jobs.json"),
      fetchJson("data/new_today.json").catch(() => ({ jobs: [] })),
      fetchJson("data/errors.json").catch(() => null),
    ]);
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
  const known = new Set(state.jobs.map((j) => j.id));
  for (const [id, t] of Object.entries(state.tracking)) {
    if (!known.has(id) && t.job) {
      state.jobs.push({ id, ...t.job, employer_type: "", countries: [], country_names: [],
        family: "Other", score: 0, active: false, first_seen: "", archived: true });
    }
  }
  fillFilters();
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

const FILTER_IDS = ["f-search", "f-employer", "f-type", "f-country", "f-family", "f-date", "f-status", "f-score", "f-inactive"];

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
  fillSelect("f-status", [["__any", "Suivie (tout statut)"], ...STATUSES.slice(1)]);
}

function currentFilters() {
  return {
    search: $("f-search").value.trim().toLowerCase(),
    employer: $("f-employer").value,
    type: $("f-type").value,
    country: $("f-country").value,
    family: $("f-family").value,
    days: Number($("f-date").value) || 0,
    status: $("f-status").value,
    minScore: Number($("f-score").value) || 0,
    inactive: $("f-inactive").checked,
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
  if (state.tab === "mine" && !t) return false;
  if (!f.inactive && !job.active && state.tab !== "mine") return false;
  if (f.employer && job.employer !== f.employer) return false;
  if (f.type && job.employer_type !== f.type) return false;
  if (f.country === "__none" && (job.countries || []).length) return false;
  if (f.country && f.country !== "__none" && !(job.countries || []).includes(f.country)) return false;
  if (f.family && job.family !== f.family) return false;
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
  score.textContent = job.score;
  score.classList.add(scoreClass(job.score));
  if (job.score_breakdown) {
    const b = job.score_breakdown;
    score.title = `Score ${job.score} = métier ${b.role} + zone ${b.geo} + ville ${b.city} + calendrier ${b.timing}`;
  }

  const link = node.querySelector(".title a");
  link.href = job.url;
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
  if (!job.active) addTag(job.archived ? "Archivée" : "Fermée", "closed");
  if (job.family) addTag(FAMILY_LABEL[job.family] || job.family);
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
  let timer;
  notes.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(() => updateTracking(job, { notes: notes.value }), 400);
  });
  return node;
}

function render() {
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

function updateCounts() {
  $("count-new").textContent = state.jobs.filter((j) => state.newIds.has(j.id)).length;
  $("count-all").textContent = state.jobs.filter((j) => j.active).length;
  $("count-mine").textContent = Object.keys(state.tracking).length;
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

// ---------------------------------------------------------------- CSV

const CSV_COLUMNS = ["id", "employer", "title", "location", "url", "score", "family", "first_seen", "status", "applied_on", "notes"];

function csvEscape(value) {
  const s = String(value ?? "");
  return /[",\n\r;]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

function exportCsv() {
  const byId = new Map(state.jobs.map((j) => [j.id, j]));
  const lines = [CSV_COLUMNS.join(",")];
  for (const [id, t] of Object.entries(state.tracking)) {
    const j = byId.get(id) || { id, ...(t.job || {}) };
    const row = { ...j, id, status: STATUS_LABEL[t.status] || "", applied_on: t.applied_on || "", notes: t.notes || "" };
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
      const job = state.jobs.find((j) => j.id === id) || {
        id, title: r[col("title")] || "", employer: r[col("employer")] || "", url: r[col("url")] || "", location: r[col("location")] || "",
      };
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
$("import").addEventListener("change", (e) => e.target.files[0] && importCsv(e.target.files[0]));

load();
