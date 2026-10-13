/* Student progress: remembers each lesson's checkboxes in the browser (localStorage)
 * and shows a summary on the home page (#progresso). Nothing leaves the student's computer.
 * Texts follow the page language (<html lang>): en, es, pt.
 */
(function () {
  "use strict";
  const PREFIX = "cp:";
  const I18N = {
    en: { empty: "You have not checked anything yet. Open a lesson and tick the checklist at the end: your progress shows up here.",
          done: "items completed in the lessons you have opened.", of: "of", lesson: "Lesson", completed: "Completed" },
    es: { empty: "Todavía no marcaste nada. Abre una lección y marca la lista del final: tu progreso aparece aquí.",
          done: "ítems completados en las lecciones que ya abriste.", of: "de", lesson: "Lección", completed: "Completado" },
    pt: { empty: "Você ainda não marcou nada. Abra uma aula e marque a checklist do fim: o progresso aparece aqui.",
          done: "itens concluídos nas aulas que você já abriu.", of: "de", lesson: "Aula", completed: "Concluído" },
  };
  function S() {
    const lang = (document.documentElement.lang || "en").slice(0, 2);
    return I18N[lang] || I18N.en;
  }

  function store(key, value) {
    try {
      if (value === undefined) return localStorage.getItem(key);
      localStorage.setItem(key, value);
    } catch (e) {
      return null; // private browsing or blocked storage: the site works without progress
    }
    return null;
  }

  function pageKey() {
    return location.pathname.replace(/index\.html$/, "").replace(/\/$/, "") || "/";
  }

  function wireCheckboxes() {
    const boxes = document.querySelectorAll(".md-content .task-list-item input[type=checkbox]");
    if (!boxes.length) return;
    const key = PREFIX + pageKey();
    let saved = {};
    try { saved = JSON.parse(store(key) || "{}"); } catch (e) { saved = {}; }
    const title = (document.querySelector(".md-content h1") || {}).textContent || document.title;
    function save() {
      const state = {};
      let done = 0;
      boxes.forEach((b, i) => { state[i] = b.checked; if (b.checked) done++; });
      store(key, JSON.stringify(state));
      store(key + ":sum", JSON.stringify({ done: done, total: boxes.length, title: title.replace("¶", "").trim(), url: location.pathname }));
    }
    boxes.forEach((b, i) => {
      b.disabled = false;
      if (saved[i]) b.checked = true;
      b.addEventListener("change", save);
    });
    save();
  }

  function renderSummary() {
    const el = document.getElementById("progresso");
    if (!el) return;
    const items = [];
    try {
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        if (k && k.startsWith(PREFIX) && k.endsWith(":sum")) items.push(JSON.parse(localStorage.getItem(k)));
      }
    } catch (e) { /* no storage */ }
    if (!items.length) {
      el.innerHTML = "<p><em>" + S().empty + "</em></p>";
      return;
    }
    // Only lessons in this page's language (/es/..., /pt/..., or English at the root).
    const lang = (document.documentElement.lang || "en").slice(0, 2);
    const inLang = (u) => (lang === "en" ? !/^\/(es|pt)\//.test(u.replace(/^.*?(\/(es|pt)\/)/, "$1")) : u.includes("/" + lang + "/"));
    const mine = items.filter((x) => inLang(x.url));
    items.length = 0;
    items.push(...mine);
    if (!items.length) {
      el.innerHTML = "<p><em>" + S().empty + "</em></p>";
      return;
    }
    items.sort((a, b) => a.url.localeCompare(b.url));
    const done = items.reduce((s, x) => s + x.done, 0), total = items.reduce((s, x) => s + x.total, 0);
    el.innerHTML =
      "<p><strong>" + done + " " + S().of + " " + total + "</strong> " + S().done + "</p>" +
      "<table><thead><tr><th>" + S().lesson + "</th><th>" + S().completed + "</th></tr></thead><tbody>" +
      items.map((x) => '<tr><td><a href="' + x.url + '">' + x.title + "</a></td><td>" + x.done + "/" + x.total + "</td></tr>").join("") +
      "</tbody></table>";
  }

  function init() { wireCheckboxes(); renderSummary(); }
  if (typeof document$ !== "undefined") document$.subscribe(init);
  else document.addEventListener("DOMContentLoaded", init);
})();
