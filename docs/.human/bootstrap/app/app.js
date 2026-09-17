(() => {
  const Q = window.BOOTCRATE_QUESTIONS;
  const SECTIONS = window.BOOTCRATE_SECTIONS;
  const BY_ID = Object.fromEntries(Q.map(q => [q.id, q]));
  const KEY = "bootcrate-project-intake-v1";
  const SCHEMA = "bootcrate-project-intake/v1";

  let lang = localStorage.getItem(KEY + "-lang") || "en";
  let answers = {};
  let invalidIds = new Set();
  let sessionMeta = newSession();

  const t = (en, pt) => lang === "pt" ? pt : en;
  const root = document.getElementById("formRoot");
  const nav = document.getElementById("sectionNav");

  function newSession() {
    return { id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()), created_at: new Date().toISOString() };
  }

  function visible(q, source = answers, seen = new Set()) {
    if (!q.condition) return true;
    if (seen.has(q.id)) return false;
    seen.add(q.id);

    const parent = BY_ID[q.condition.id];
    if (parent && !visible(parent, source, seen)) return false;

    const value = source[q.condition.id];
    if (q.condition.in) return q.condition.in.includes(value);
    return true;
  }

  function visibleQuestions(source = answers) {
    return Q.filter(q => visible(q, source));
  }

  function valuePresent(v) {
    return Array.isArray(v) ? v.length > 0 : !(v === undefined || v === null || v === "");
  }

  function requiredMissing(source = answers) {
    return visibleQuestions(source).filter(q => q.required && !valuePresent(source[q.id]));
  }

  function currentExportAnswers(source = answers) {
    const out = {};
    for (const q of visibleQuestions(source)) {
      if (valuePresent(source[q.id])) out[q.id] = source[q.id];
    }
    return out;
  }

  function validateAnswerValue(q, value) {
    if (q.type === "text" || q.type === "textarea") return typeof value === "string";
    if (q.type === "select") {
      return typeof value === "string" && (q.options || []).some(o => o[0] === value);
    }
    if (q.type === "multiselect") {
      const allowed = new Set((q.options || []).map(o => o[0]));
      return Array.isArray(value) && new Set(value).size === value.length && value.every(v => typeof v === "string" && allowed.has(v));
    }
    return false;
  }

  function validateImport(data) {
    const errors = [];
    if (!data || typeof data !== "object" || Array.isArray(data)) return [t("Root must be a JSON object.", "A raiz deve ser um objeto JSON.")];
    if (data.schema !== SCHEMA) errors.push(t(`Expected schema ${SCHEMA}.`, `Schema esperado: ${SCHEMA}.`));
    if (!data.answers || typeof data.answers !== "object" || Array.isArray(data.answers)) {
      errors.push(t("answers must be an object.", "answers deve ser um objeto."));
      return errors;
    }
    for (const [id, value] of Object.entries(data.answers)) {
      const q = BY_ID[id];
      if (!q) { errors.push(t(`Unknown answer id: ${id}`, `ID de resposta desconhecido: ${id}`)); continue; }
      if (!validateAnswerValue(q, value)) errors.push(t(`Invalid value for: ${id}`, `Valor inválido para: ${id}`));
    }
    return errors;
  }

  function inputFor(q) {
    const wrap = document.createElement("div");
    wrap.className = "question" + (q.required ? " required" : "") + (invalidIds.has(q.id) ? " invalid" : "");
    wrap.dataset.qid = q.id;

    const label = document.createElement("label");
    label.className = "label";
    label.textContent = lang === "pt" ? q.pt : q.en;
    wrap.appendChild(label);

    const set = v => {
      answers[q.id] = v;
      invalidIds.delete(q.id);
      persist();
      render();
    };

    if (q.type === "text" || q.type === "textarea") {
      const el = document.createElement(q.type === "textarea" ? "textarea" : "input");
      if (q.type === "text") el.type = "text";
      el.value = answers[q.id] || "";
      el.addEventListener("change", () => set(el.value.trim()));
      wrap.appendChild(el);
    } else if (q.type === "select") {
      const el = document.createElement("select");
      const empty = document.createElement("option");
      empty.value = "";
      empty.textContent = t("Choose…", "Escolha…");
      el.appendChild(empty);
      (q.options || []).forEach(([value, en, pt]) => {
        const o = document.createElement("option");
        o.value = value;
        o.textContent = lang === "pt" ? pt : en;
        if (answers[q.id] === value) o.selected = true;
        el.appendChild(o);
      });
      el.addEventListener("change", () => set(el.value));
      wrap.appendChild(el);
    } else if (q.type === "multiselect") {
      const opts = document.createElement("div");
      opts.className = "options";
      const selected = new Set(answers[q.id] || []);
      (q.options || []).forEach(([value, en, pt]) => {
        const l = document.createElement("label");
        l.className = "opt";
        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.checked = selected.has(value);
        cb.addEventListener("change", () => {
          const cur = new Set(answers[q.id] || []);
          cb.checked ? cur.add(value) : cur.delete(value);
          set([...cur]);
        });
        const span = document.createElement("span");
        span.textContent = lang === "pt" ? pt : en;
        l.append(cb, span);
        opts.appendChild(l);
      });
      wrap.appendChild(opts);
    }

    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = q.id;
    wrap.appendChild(meta);
    return wrap;
  }

  function render() {
    document.documentElement.lang = lang === "pt" ? "pt-BR" : "en";
    document.getElementById("langBtn").textContent = lang === "pt" ? "EN" : "PT-BR";
    document.getElementById("newBtn").textContent = t("New", "Novo");
    document.getElementById("saveBtn").textContent = t("Save local", "Salvar local");
    document.getElementById("exportBtn").textContent = t("Export final JSON", "Exportar JSON final");
    document.querySelector(".fileBtn").childNodes[0].nodeValue = t("Import JSON", "Importar JSON");
    document.getElementById("subtitle").textContent = t(
      "Project discovery intake — architecture is decided later with ChatGPT and the owner.",
      "Intake de descoberta — a arquitetura é decidida depois com o ChatGPT e o owner."
    );
    document.getElementById("privacyHint").textContent = t(
      "Everything stays in your browser unless you export the JSON.",
      "Tudo fica no navegador até você exportar o JSON."
    );
    document.getElementById("footerText").textContent = t(
      "Unknown is a valid answer. ChatGPT researches what you should not need to research yourself.",
      "“Não sei” é uma resposta válida. O ChatGPT pesquisa o que você não deveria precisar pesquisar sozinho."
    );

    root.innerHTML = "";
    nav.innerHTML = "";
    Object.keys(SECTIONS).forEach(sectionId => {
      const qs = Q.filter(q => q.section === sectionId && visible(q));
      if (!qs.length) return;
      const section = document.createElement("section");
      section.className = "section";
      section.id = "section-" + sectionId;
      const h = document.createElement("h2");
      h.textContent = lang === "pt" ? SECTIONS[sectionId][1] : SECTIONS[sectionId][0];
      section.appendChild(h);
      qs.forEach(q => section.appendChild(inputFor(q)));
      root.appendChild(section);

      const b = document.createElement("button");
      b.textContent = h.textContent;
      b.onclick = () => section.scrollIntoView({behavior:"smooth"});
      nav.appendChild(b);
    });

    const visibleQs = visibleQuestions();
    const answered = visibleQs.filter(q => valuePresent(answers[q.id])).length;
    const missing = requiredMissing();
    document.getElementById("progressText").textContent = t(
      `${answered} / ${visibleQs.length} answered`,
      `${answered} / ${visibleQs.length} respondidas`
    );
    document.getElementById("barFill").style.width = `${visibleQs.length ? answered / visibleQs.length * 100 : 0}%`;
    const req = document.getElementById("requiredText");
    req.textContent = missing.length
      ? t(`${missing.length} required answer(s) missing`, `${missing.length} resposta(s) obrigatória(s) faltando`)
      : t("Required answers complete", "Respostas obrigatórias completas");
    req.className = "requiredStatus" + (missing.length ? " error" : "");
  }

  function payload() {
    return {
      schema: SCHEMA,
      exported_at: new Date().toISOString(),
      session: sessionMeta,
      language: lang === "pt" ? "pt-BR" : "en",
      answers: currentExportAnswers(),
      interpretation_rules: {
        owner_explicit_answers_are_not_to_be_overwritten: true,
        unknown_requires_research_when_material: true,
        preferences_are_not_hard_constraints_unless_owner_says_so: true,
        app_does_not_choose_architecture: true,
        hidden_conditional_answers_are_not_exported: true
      }
    };
  }

  function persist() {
    localStorage.setItem(KEY, JSON.stringify({sessionMeta, answers}));
  }

  document.getElementById("langBtn").onclick = () => {
    lang = lang === "pt" ? "en" : "pt";
    localStorage.setItem(KEY + "-lang", lang);
    render();
  };

  document.getElementById("saveBtn").onclick = () => {
    persist();
    alert(t("Draft saved locally in this browser.", "Rascunho salvo localmente neste navegador."));
  };

  document.getElementById("newBtn").onclick = () => {
    if (!confirm(t("Start a new intake? Current local answers will be cleared.", "Iniciar um novo intake? As respostas locais atuais serão apagadas."))) return;
    answers = {};
    invalidIds = new Set();
    sessionMeta = newSession();
    persist();
    render();
  };

  document.getElementById("exportBtn").onclick = () => {
    const missing = requiredMissing();
    if (missing.length) {
      invalidIds = new Set(missing.map(q => q.id));
      render();
      const first = document.querySelector(".question.invalid");
      if (first) first.scrollIntoView({behavior:"smooth", block:"center"});
      alert(t(
        `Complete the ${missing.length} required answer(s) before exporting.`,
        `Complete as ${missing.length} resposta(s) obrigatória(s) antes de exportar.`
      ));
      return;
    }
    invalidIds = new Set();
    const blob = new Blob([JSON.stringify(payload(), null, 2)], {type:"application/json"});
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    const safe = (answers.project_name || "project").replace(/[^a-z0-9_-]+/gi,"-").replace(/^-|-$/g,"");
    a.download = `${safe || "project"}-intake.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  document.getElementById("importInput").onchange = async ev => {
    const f = ev.target.files[0];
    if (!f) return;
    try {
      const data = JSON.parse(await f.text());
      const errors = validateImport(data);
      if (errors.length) {
        alert(t("Invalid intake:\n", "Intake inválido:\n") + errors.slice(0, 10).join("\n"));
        return;
      }
      answers = data.answers || {};
      sessionMeta = data.session || newSession();
      if (data.language) lang = data.language.toLowerCase().startsWith("pt") ? "pt" : "en";
      invalidIds = new Set();
      persist();
      render();
      const missing = requiredMissing();
      if (missing.length) {
        alert(t(
          `Imported as a draft. ${missing.length} required answer(s) are still missing.`,
          `Importado como rascunho. Ainda faltam ${missing.length} resposta(s) obrigatória(s).`
        ));
      }
    } catch (e) {
      alert(t("Invalid JSON file.", "Arquivo JSON inválido."));
    } finally {
      ev.target.value = "";
    }
  };

  try {
    const saved = JSON.parse(localStorage.getItem(KEY) || "null");
    if (saved) {
      answers = saved.answers || {};
      sessionMeta = saved.sessionMeta || sessionMeta;
    }
  } catch {}

  render();
})();
