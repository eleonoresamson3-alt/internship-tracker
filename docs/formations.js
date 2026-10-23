"use strict";

// "Formations" tab: trainings and certifications from config/formations.yaml
// (built into formations.json), personal tracking in localStorage only.

const FO_KEY = STORAGE_KEY + ".formations";
const FO_STATUSES = [
  ["todo", "À faire"],
  ["doing", "En cours"],
  ["done", "Terminé"],
  ["certified", "Certifié"],
];
const FO_STATUS_LABEL = Object.fromEntries(FO_STATUSES);
const FO_DUE_ALERT_DAYS = 30;

const fo = {
  categories: {},
  base: [],        // from formations.json
  store: loadFoStore(),
  editing: null,   // id of the custom formation being edited
};

function loadFoStore() {
  try {
    const s = JSON.parse(localStorage.getItem(FO_KEY)) || {};
    return { tracking: s.tracking || {}, custom: s.custom || [] };
  } catch {
    return { tracking: {}, custom: [] };
  }
}

function saveFoStore() {
  try {
    localStorage.setItem(FO_KEY, JSON.stringify(fo.store));
  } catch { /* private browsing: kept until the page closes */ }
}

async function loadFormations() {
  try {
    const data = await fetchJson("formations.json");
    fo.categories = data.categories || {};
    fo.base = data.formations || [];
  } catch {
    fo.base = [];
  }
  fillFoFilters();
}

function allFormations() {
  return [...fo.base, ...fo.store.custom.map((c) => ({ ...c, custom: true }))];
}

function foTrack(id) {
  return fo.store.tracking[id] || {};
}

function updateFoTrack(id, patch) {
  const t = { status: "todo", progress: 0, log: [], ...foTrack(id), ...patch };
  fo.store.tracking[id] = t;
  saveFoStore();
}

function foHours(t) {
  return (t.log || []).reduce((sum, e) => sum + (Number(e.h) || 0), 0);
}

function weekStart() {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7));   // Monday
  return d.toISOString().slice(0, 10);
}

function formationsCount() {
  return allFormations().filter((f) => foTrack(f.id).status === "doing").length;
}

function daysUntil(iso) {
  return Math.round((new Date(iso + "T00:00:00") - new Date(todayIso() + "T00:00:00")) / 86400000);
}

function monthYear(iso) {
  return new Date(iso + "T12:00:00").toLocaleDateString("fr-FR", { month: "long", year: "numeric" });
}

function cvSentence(f, t) {
  const when = t.obtained ? monthYear(t.obtained) : "";
  if (f.cv) return f.cv.replace("{date}", when);
  const skills = (f.competences || []).slice(0, 4).join(", ");
  const head = t.status === "certified" ? `${f.nom} – certification obtenue` : `${f.nom} – formation suivie`;
  const org = f.organisme ? ` (${f.organisme.replace(/\s*\(.*\)\s*$/, "")}${when ? ", " + when : ""})` : (when ? ` (${when})` : "");
  return `${head}${org}${skills ? " : " + skills.toLowerCase() : ""}.`;
}

function fillFoFilters() {
  const cat = $("fo-cat");
  if (cat.options.length === 1) for (const [k, v] of Object.entries(fo.categories)) cat.append(new Option(v, k));
  const st = $("fo-status");
  if (st.options.length === 1) for (const [k, v] of FO_STATUSES) st.append(new Option(v, k));
  const dlg = $("fo-form").elements.categorie;
  if (!dlg.options.length) for (const [k, v] of Object.entries(fo.categories)) dlg.append(new Option(v, k));
}

// ---------------------------------------------------------------- overview

function renderFoOverview(items) {
  const monday = weekStart();
  let week = 0;
  const perFormation = [];
  for (const f of items) {
    const h = (foTrack(f.id).log || []).filter((e) => e.date >= monday).reduce((s, e) => s + (Number(e.h) || 0), 0);
    if (h) perFormation.push(`${f.nom} ${fmtH(h)} h`);
    week += h;
  }
  $("f-week-hours").textContent = fmtH(week);
  const total = items.reduce((s, f) => s + foHours(foTrack(f.id)), 0);
  $("f-week-detail").textContent = (perFormation.length ? perFormation.join(" · ") + " — " : "depuis lundi — ")
    + `${fmtH(total)} h au total`;

  const doing = items.filter((f) => foTrack(f.id).status === "doing");
  $("f-current-empty").hidden = doing.length > 0;
  $("f-current").replaceChildren(...doing.map((f) => {
    const t = foTrack(f.id);
    const li = el("li");
    const name = el("div", "f-current-name", f.nom);
    const pct = Number(t.progress) || 0;
    const bar = el("div", "f-bar");
    bar.setAttribute("role", "progressbar");
    bar.setAttribute("aria-valuenow", pct);
    bar.setAttribute("aria-valuemin", 0);
    bar.setAttribute("aria-valuemax", 100);
    bar.setAttribute("aria-label", `Avancement ${f.nom}`);
    const fill = el("span");
    fill.style.width = `${pct}%`;
    bar.append(fill);
    const meta = el("div", "meta", `${pct} % · ${fmtH(foHours(t))} h${f.heures ? " / " + f.heures + " h estimées" : ""}`
      + (t.target ? ` · objectif ${frDate(t.target)}` : ""));
    li.append(name, bar, meta);
    return li;
  }));

  const today = todayIso();
  const due = [];
  for (const f of items) {
    const t = foTrack(f.id);
    if (["done", "certified"].includes(t.status)) continue;
    if (f.echeance && f.echeance >= today) due.push({ date: f.echeance, f, what: f.echeance_libelle || "Échéance officielle" });
    if (t.target && t.target >= today) due.push({ date: t.target, f, what: "Ma date cible" });
  }
  due.sort((a, b) => a.date.localeCompare(b.date));
  $("f-due-empty").hidden = due.length > 0;
  $("f-due").replaceChildren(...due.slice(0, 8).map((d) => {
    const n = daysUntil(d.date);
    const li = el("li", n <= FO_DUE_ALERT_DAYS ? "soon-alert" : "");
    const when = el("span", "f-due-date", `${frDate(d.date)} · ${n === 0 ? "aujourd'hui" : `J-${n}`}`);
    li.append(when, el("strong", "", ` ${d.f.nom}`), el("span", "meta", ` — ${d.what}`));
    return li;
  }));
}

function fmtH(h) {
  return (Math.round(h * 10) / 10).toLocaleString("fr-FR");
}

// ---------------------------------------------------------------- cards

function renderFoCard(f) {
  const t = foTrack(f.id);
  const status = t.status || "todo";
  const card = el("article", `card formation status-${status}`);

  const head = el("div", "fo-head");
  const prio = el("span", `prio prio-${f.priorite}`, `P${f.priorite}`);
  prio.title = ["", "Priorité 1 – indispensable", "Priorité 2 – importante", "Priorité 3 – bonus"][f.priorite] || "";
  const title = el("h3", "title");
  if (f.lien) {
    const a = el("a", "", f.nom);
    setLink(a, f.lien);
    title.append(a);
  } else {
    title.textContent = f.nom;
  }
  head.append(prio, title);
  card.append(head);

  const facts = [f.organisme, f.heures ? `≈ ${f.heures} h` : "durée non renseignée", f.cout || "coût non renseigné"]
    .filter(Boolean).join(" · ");
  card.append(el("p", "meta", facts));
  const tags = el("p", "tags");
  tags.append(el("span", "tag theme", fo.categories[f.categorie] || f.categorie));
  if (f.custom) tags.append(el("span", "tag", "ajoutée par moi"));
  if (f.echeance) {
    const n = daysUntil(f.echeance);
    const tag = el("span", `tag ${n >= 0 && n <= FO_DUE_ALERT_DAYS ? "alert" : ""}`, `Échéance ${frDate(f.echeance)}`);
    tag.title = f.echeance_libelle || "";
    tags.append(tag);
  }
  card.append(tags);
  if (f.utilite) card.append(el("p", "fo-why", f.utilite));
  if ((f.competences || []).length) card.append(el("p", "meta", "Compétences : " + f.competences.join(", ")));
  if ((f.a_verifier || []).length) {
    const box = el("details", "fo-missing");
    box.append(el("summary", "", `ⓘ ${f.a_verifier.length} information(s) non trouvée(s) sur le site officiel`));
    const ul = el("ul");
    ul.append(...f.a_verifier.map((x) => el("li", "", x)));
    box.append(ul);
    card.append(box);
  }
  if (f.verifie_le) card.append(el("p", "meta small", `Informations vérifiées le ${frDate(f.verifie_le)}`));

  // CV sentence for finished trainings
  if (status === "done" || status === "certified") {
    const cv = el("div", "fo-cv");
    const text = el("p", "", cvSentence(f, t));
    const copy = el("button", "ghost small", "Copier");
    copy.type = "button";
    copy.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(text.textContent); showToast("Phrase copiée"); } catch { /* ignore */ }
    });
    cv.append(el("strong", "", "Pour ton CV : "), text, copy);
    card.append(cv);
  }

  card.append(renderFoTracking(f, t));
  return card;
}

function renderFoTracking(f, t) {
  const box = el("details", "fo-track");
  box.append(el("summary", "", `Mon suivi : ${FO_STATUS_LABEL[t.status || "todo"]} · ${Number(t.progress) || 0} % · ${fmtH(foHours(t))} h`));
  const grid = el("div", "form-grid");

  const field = (label, input, wide = false) => {
    const l = el("label", wide ? "wide" : "");
    l.append(label, input);
    grid.append(l);
    return input;
  };
  const status = field("Statut", el("select"));
  for (const [k, v] of FO_STATUSES) status.append(new Option(v, k));
  status.value = t.status || "todo";
  status.addEventListener("change", () => {
    const patch = { status: status.value };
    if (status.value === "doing" && !t.start) patch.start = todayIso();
    if (["done", "certified"].includes(status.value)) {
      patch.progress = 100;
      if (!t.obtained) patch.obtained = todayIso();
    }
    updateFoTrack(f.id, patch);
    render();
  });

  const progress = field("Avancement (%)", el("input"));
  Object.assign(progress, { type: "number", min: 0, max: 100, step: 5, value: Number(t.progress) || 0 });
  progress.addEventListener("change", () => {
    updateFoTrack(f.id, { progress: Math.max(0, Math.min(100, Number(progress.value) || 0)) });
    render();
  });

  const add = el("div", "fo-hours");
  const hours = el("input");
  Object.assign(hours, { type: "number", min: 0, step: 0.5, placeholder: "ex. 1,5" });
  hours.setAttribute("aria-label", "Heures à ajouter");
  const addBtn = el("button", "small", "Ajouter");
  addBtn.type = "button";
  addBtn.addEventListener("click", () => {
    const h = Number(hours.value);
    if (!h) return;
    updateFoTrack(f.id, { log: [...(foTrack(f.id).log || []), { date: todayIso(), h }], status: t.status === "todo" || !t.status ? "doing" : t.status,
      start: t.start || todayIso() });
    render();
  });
  add.append(hours, addBtn);
  field(`Heures passées : ${fmtH(foHours(t))} h — en ajouter aujourd'hui`, add);

  for (const [key, label] of [["start", "Date de début"], ["target", "Date cible"], ["obtained", "Date d'obtention"]]) {
    const input = field(label, el("input"));
    Object.assign(input, { type: "date", value: t[key] || "" });
    input.addEventListener("change", () => { updateFoTrack(f.id, { [key]: input.value }); render(); });
  }
  const notes = field("Notes", el("textarea"), true);
  notes.rows = 2;
  notes.value = t.notes || "";
  notes.addEventListener("change", () => updateFoTrack(f.id, { notes: notes.value }));

  box.append(grid);
  if ((t.log || []).length) {
    const log = el("p", "meta small", "Historique : " + t.log.slice(-6).map((e) => `${frDate(e.date)} ${fmtH(e.h)} h`).join(" · "));
    const undo = el("button", "ghost small", "Annuler le dernier ajout");
    undo.type = "button";
    undo.addEventListener("click", () => { updateFoTrack(f.id, { log: t.log.slice(0, -1) }); render(); });
    box.append(log, undo);
  }
  if (f.custom) {
    const edit = el("button", "ghost small", "Modifier la formation");
    edit.type = "button";
    edit.addEventListener("click", () => openFoDialog(f));
    box.append(edit);
  }
  return box;
}

function renderFormations() {
  const items = allFormations();
  renderFoOverview(items);
  const cat = $("fo-cat").value, prio = $("fo-prio").value, st = $("fo-status").value;
  const order = { doing: 0, todo: 1, done: 2, certified: 3 };
  const rows = items
    .filter((f) => (!cat || f.categorie === cat) && (!prio || String(f.priorite) === prio)
      && (!st || (foTrack(f.id).status || "todo") === st))
    .sort((a, b) => order[foTrack(a.id).status || "todo"] - order[foTrack(b.id).status || "todo"]
      || a.priorite - b.priorite || a.nom.localeCompare(b.nom));
  $("fo-count").textContent = `${rows.length} formation(s)`;
  $("fo-list").replaceChildren(...rows.map(renderFoCard));
}

// ---------------------------------------------------------------- add / edit, export / import

function openFoDialog(f = null) {
  fo.editing = f ? f.id : null;
  const form = $("fo-form");
  form.reset();
  $("fo-dialog-title").textContent = f ? "Modifier la formation" : "Ajouter une formation";
  $("fo-delete").hidden = !f;
  if (f) {
    for (const k of ["nom", "organisme", "categorie", "priorite", "heures", "cout", "lien", "echeance", "utilite"]) {
      if (form.elements[k]) form.elements[k].value = f[k] ?? "";
    }
    form.elements.competences.value = (f.competences || []).join(", ");
  }
  $("fo-dialog").showModal();
}

function saveFoDialog() {
  const e = $("fo-form").elements;
  const item = {
    id: fo.editing || `perso-${Date.now().toString(36)}`,
    nom: e.nom.value.trim(), organisme: e.organisme.value.trim(), categorie: e.categorie.value,
    priorite: Number(e.priorite.value), heures: e.heures.value ? Number(e.heures.value) : null,
    cout: e.cout.value.trim(), lien: e.lien.value.trim(), echeance: e.echeance.value || null, echeance_libelle: "",
    competences: e.competences.value.split(",").map((x) => x.trim()).filter(Boolean),
    utilite: e.utilite.value.trim(), a_verifier: [], verifie_le: null, cv: "",
  };
  const list = fo.store.custom.filter((c) => c.id !== item.id);
  fo.store.custom = [...list, item];
  saveFoStore();
  $("fo-dialog").close();
  render();
}

function deleteFoEditing() {
  if (!fo.editing || !confirm("Supprimer cette formation et son suivi ?")) return;
  fo.store.custom = fo.store.custom.filter((c) => c.id !== fo.editing);
  delete fo.store.tracking[fo.editing];
  saveFoStore();
  $("fo-dialog").close();
  render();
}

function exportFormations() {
  const blob = new Blob([JSON.stringify({ exported_at: new Date().toISOString(), ...fo.store }, null, 1)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `suivi-formations-${todayIso()}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
}

function importFormations(file) {
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const data = JSON.parse(reader.result);
      if (typeof data.tracking !== "object" || !Array.isArray(data.custom || [])) throw new Error("format");
      const ids = new Set(fo.store.custom.map((c) => c.id));
      fo.store.tracking = { ...fo.store.tracking, ...data.tracking };
      fo.store.custom = [...fo.store.custom, ...(data.custom || []).filter((c) => c && c.id && c.nom && !ids.has(c.id))];
      saveFoStore();
      showToast(`Suivi importé (${Object.keys(data.tracking).length} formation(s))`);
      render();
    } catch {
      showToast("Fichier non reconnu : exporte d'abord ton suivi depuis cet onglet pour voir le format.");
    }
  };
  reader.readAsText(file);
}

for (const id of ["fo-cat", "fo-prio", "fo-status"]) $(id).addEventListener("change", render);
$("fo-add").addEventListener("click", () => openFoDialog());
$("fo-cancel").addEventListener("click", () => $("fo-dialog").close());
$("fo-delete").addEventListener("click", deleteFoEditing);
$("fo-form").addEventListener("submit", (e) => {
  if (!e.target.checkValidity()) return;
  saveFoDialog();
});
$("fo-export").addEventListener("click", exportFormations);
$("fo-import-btn").addEventListener("click", () => $("fo-import").click());
$("fo-import").addEventListener("change", (e) => {
  if (e.target.files[0]) importFormations(e.target.files[0]);
  e.target.value = "";
});
