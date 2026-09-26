(() => {
  "use strict";
  const Q = window.BOOTCRATE_QUESTIONS, S = window.BOOTCRATE_SECTIONS;
  const C = window.BootCrateIntakeCore, H = window.BootCrateHandoff;
  const G = window.BootCrateGuidance, Preset = window.BootCratePreset, Execution = window.BootCrateExecutionProfile;
  const core = C.create(Q), KEY = "bootcrate-project-intake-v2";
  const $ = id => document.getElementById(id);
  let storage = true, lang = "en", mode = "basic", answers = {}, states = {}, invalid = new Set(), step = 0, repository = "";
  let session = {id: crypto?.randomUUID?.() || String(Date.now()), created_at: new Date().toISOString()};
  let pendingLegacy = null;
  const t = (en, pt) => lang === "pt" ? pt : en;
  const present = v => typeof v === "string" ? !!v.trim() : Array.isArray(v) && v.length > 0;
  const get = key => { try { return localStorage.getItem(key); } catch { storage = false; return null; } };
  const set = (key, value) => { try { localStorage.setItem(key, value); return true; } catch { storage = false; return false; } };
  lang = get(KEY + "-lang") === "pt" ? "pt" : "en";
  mode = get(KEY + "-mode") === "detailed" ? "detailed" : "basic";
  const BASIC = new Set([
    "project_name","one_sentence","project_kind","existing_or_new","external_integration","external_product_name","success",
    "report_language","repo_language","target_platforms","distribution_mode","distribution_targets",
    "language_known","language_value","framework_known","framework_value",
    "sensitive_data","secrets_needed","automated_tests","manual_smoke","ci",
    "single_or_team","repository_state","claude_code","codex_local","codex_cloud","consumption_preset","execution_profile","full_access_acknowledgement",
    "must_have_tools","must_avoid_tools","known_risks","project_console","anything_else"
  ]);
  try {
    const draft = JSON.parse(get(KEY) || "null");
    const envelope = {schema:C.SCHEMA, answers:draft?.answers, answer_states:draft?.answer_states, session:draft?.sessionMeta,
      repository:draft?.repository, bootstrap_source:draft?.bootstrap_source};
    if (draft && !core.validate(envelope).length) {
      const normalized = core.normalize(envelope);
      answers = normalized.answers;
      states = normalized.states;
      repository = normalized.repository;
      session = {...session, ...(normalized.session || {})};
    } else {
      const old = JSON.parse(get("bootcrate-project-intake-v1") || "null");
      if (old?.answers) pendingLegacy = core.upgradeLegacy({schema:"bootcrate-project-intake/v1", answers:old.answers, session:old.sessionMeta});
    }
  } catch { /* Invalid local data never overwrites a valid draft. */ }
  if (!answers.execution_profile) answers.execution_profile = "protected_manual";

  const shown = q => core.visible(q, answers) && (mode === "detailed" || q.required || BASIC.has(q.id) || present(answers[q.id]) || states[q.id]);
  const requestedExecution = () => answers.execution_profile === "full_access" && answers.full_access_acknowledgement !== "acknowledged"
    ? "protected_manual" : (answers.execution_profile || "protected_manual");
  const sections = () => Object.keys(S).filter(id => Q.some(q => q.section === id && shown(q)));
  const steps = () => [...sections(), "__review", "__finish"];
  function title(id) {
    if (id === "__review") return t("Review", "Revisão");
    if (id === "__finish") return t("Next steps", "Próximos passos");
    return lang === "pt" ? S[id][1] : S[id][0];
  }
  function desc(id) {
    if (id === "__review") return t("Review what you know. Unanswered decisions stay open.", "Revise o que você sabe. Decisões sem resposta continuam abertas.");
    if (id === "__finish") return t("The intake records intent; repository access and product checks still need verification.", "O intake registra intenção; acesso ao repositório e testes do produto ainda precisam ser verificados.");
    return mode === "basic"
      ? t("Answer what you know. Switch to Detailed to add technical context; your answers stay saved.", "Responda o que sabe. Use Detalhado para adicionar contexto técnico; suas respostas são preservadas.")
      : t("Add precise constraints and context where useful. Unanswered optional questions stay open.", "Adicione restrições e contexto técnico quando úteis. Perguntas opcionais sem resposta permanecem abertas.");
  }
  function save() {
    const ok = set(KEY, JSON.stringify({sessionMeta:session, repository, bootstrap_source:H.BOOTSTRAP_SOURCE, answers, answer_states:states}));
    $("saveStatus").textContent = ok ? t("Saved locally", "Salvo neste navegador") : t("Local save unavailable: export before leaving", "Não foi possível salvar: exporte antes de sair");
  }
  function payload() {
    const value = {schema:C.SCHEMA, exported_at:new Date().toISOString(), session,
      language:lang === "pt" ? "pt-BR" : "en", answers:core.exportAnswers(answers),
      bootstrap_source:H.BOOTSTRAP_SOURCE,
      answer_states:core.exportStates(states, answers),
      interpretation_rules:{owner_explicit_answers_are_not_to_be_overwritten:true,
        unknown_requires_research_when_material:true, preferences_are_not_hard_constraints_unless_owner_says_so:true,
        app_does_not_choose_architecture:true, hidden_conditional_answers_are_not_exported:true}};
    if (repository) value.repository = repository;
    return value;
  }
  function progress() {
    const qs = Q.filter(shown), n = qs.filter(q => present(answers[q.id]) || states[q.id]).length;
    const p = qs.length ? Math.round(n / qs.length * 100) : 0, remaining = core.missing(answers).length;
    $("progressText").textContent = t(`${n} / ${qs.length} answered`, `${n} / ${qs.length} respondidas`);
    $("progressPercent").textContent = p + "%";
    $("barFill").style.width = p + "%";
    document.querySelector(".progressTrack").setAttribute("aria-valuenow", p);
    $("requiredText").textContent = remaining ? t(`${remaining} required remaining`, `${remaining} obrigatórias faltando`)
      : t("Required intake answers complete; environment not verified", "Intake obrigatório respondido; ambiente não verificado");
  }
  function complete(id) {
    return !id.startsWith("__") && !Q.some(q => q.section === id && core.visible(q, answers) && q.required && !present(answers[q.id]));
  }
  function nav() {
    const nav = $("sectionNav"); nav.replaceChildren();
    steps().forEach((id, index) => {
      const b = document.createElement("button"); b.type = "button";
      if (index === step) b.setAttribute("aria-current", "step");
      if (complete(id)) b.classList.add("complete");
      const dot = document.createElement("span"); dot.className = "navDot"; dot.setAttribute("aria-hidden", "true");
      const label = document.createElement("span"); label.textContent = title(id);
      b.append(dot, label); b.onclick = () => { step = index; render(true); }; nav.appendChild(b);
    });
  }
  function qnode(q) {
    const group = q.type === "multiselect";
    const wrapper = document.createElement(group ? "fieldset" : "div");
    wrapper.className = "question" + (q.type === "textarea" ? " wide" : "") + (invalid.has(q.id) ? " invalid" : "");
    const id = "field-" + q.id, label = document.createElement(group ? "legend" : "label");
    label.className = "label"; if (!group) label.htmlFor = id;
    label.textContent = lang === "pt" ? q.pt : q.en;
    if (q.required) {
      const mark = document.createElement("span"); mark.className = "requiredMark";
      mark.textContent = t(" (required)", " (obrigatório)"); label.appendChild(mark);
    }
    wrapper.appendChild(label);
    let control;
    const clear = () => {
      invalid.delete(q.id); wrapper.classList.remove("invalid");
      control?.removeAttribute("aria-invalid"); control?.removeAttribute("aria-describedby");
      wrapper.querySelector(".fieldError")?.remove(); save(); progress();
      if (!Q.some(item => item.section === steps()[step] && invalid.has(item.id))) {
        $("errorSummary").hidden = true; $("errorSummary").textContent = "";
      }
    };
    if (["text", "textarea"].includes(q.type)) {
      control = document.createElement(q.type === "textarea" ? "textarea" : "input");
      if (q.type === "text") control.type = "text";
      control.id = id; control.maxLength = C.MAX_TEXT; control.required = Boolean(q.required);
      control.value = answers[q.id] || "";
      control.oninput = () => { answers[q.id] = control.value; clear(); };
      wrapper.appendChild(control);
    } else if (q.type === "select") {
      if (q.option_details) {
        const details = document.createElement("ul"); details.className = "optionDetails";
        (q.options || []).forEach(([value,en,pt]) => {
          const item = document.createElement("li"), name = document.createElement("strong");
          name.textContent = (lang === "pt" ? pt : en) + ": ";
          item.append(name, lang === "pt" ? q.option_details[value].pt : q.option_details[value].en);
          details.appendChild(item);
        });
        wrapper.appendChild(details);
      }
      control = document.createElement("select"); control.id = id; control.required = Boolean(q.required);
      const blank = document.createElement("option"); blank.value = ""; blank.textContent = t("Choose…", "Escolha…");
      control.appendChild(blank);
      (q.options || []).forEach(([value, en, pt]) => {
        const option = document.createElement("option"); option.value = value;
        option.textContent = lang === "pt" ? pt : en; option.selected = answers[q.id] === value;
        control.appendChild(option);
      });
      control.onchange = () => { answers[q.id] = control.value; clear(); render(false); $(id)?.focus(); };
      wrapper.appendChild(control);
    } else {
      control = wrapper;
      const box = document.createElement("div"); box.className = "options";
      const selected = new Set(answers[q.id] || []);
      (q.options || []).forEach(([value, en, pt]) => {
        const option = document.createElement("label"); option.className = "opt";
        const input = document.createElement("input"); input.type = "checkbox"; input.checked = selected.has(value);
        const text = document.createElement("span"); text.textContent = lang === "pt" ? pt : en;
        input.onchange = () => {
          const next = new Set(answers[q.id] || []);
          input.checked ? next.add(value) : next.delete(value);
          answers[q.id] = [...next]; clear();
        };
        option.append(input, text); box.appendChild(option);
      });
      wrapper.appendChild(box);
    }
    if (!q.required && ["text", "textarea"].includes(q.type)) {
      const stateLabel = document.createElement("label"); stateLabel.className = "stateLabel";
      const stateSelect = document.createElement("select"); stateSelect.setAttribute("aria-label", t("Answer status: ", "Estado da resposta: ") + (lang === "pt" ? q.pt : q.en));
      [["", t("Answer or leave open", "Responder ou deixar em aberto")],
        ["unknown", t("I don't know yet", "Ainda não sei")],
        ["not_applicable", t("Does not apply", "Não se aplica")]].forEach(([value, caption]) => {
        const option = document.createElement("option"); option.value = value; option.textContent = caption; stateSelect.appendChild(option);
      });
      stateSelect.value = states[q.id] || "";
      control.disabled = Boolean(states[q.id]);
      stateSelect.onchange = () => {
        if (stateSelect.value) { answers[q.id] = ""; control.value = ""; control.disabled = true; }
        else control.disabled = false;
        if (stateSelect.value) states[q.id] = stateSelect.value; else delete states[q.id];
        save(); progress(); nav();
      };
      stateLabel.appendChild(stateSelect); wrapper.appendChild(stateLabel);
    }
    if (invalid.has(q.id)) {
      const error = document.createElement("p"); error.className = "fieldError"; error.id = id + "-error";
      error.textContent = t("Answer this required question.", "Responda a esta pergunta obrigatória.");
      wrapper.appendChild(error); control.setAttribute("aria-invalid", "true");
      control.setAttribute("aria-describedby", error.id);
    }
    return wrapper;
  }
  function questions(id) {
    const grid = document.createElement("div"); grid.className = "questionGrid";
    if (mode === "basic") {
      const hint = document.createElement("p"); hint.className = "modeHint";
      hint.textContent = t("Detailed view adds optional questions without replacing these answers.", "A visão detalhada acrescenta perguntas opcionais sem substituir estas respostas.");
      grid.appendChild(hint);
    }
    Q.filter(q => q.section === id && shown(q)).forEach(q => grid.appendChild(qnode(q)));
    $("formRoot").replaceChildren(grid);
  }
  function display(q, value) {
    if (Array.isArray(value)) return value.map(x => (q.options || []).find(o => o[0] === x)).filter(Boolean)
      .map(o => lang === "pt" ? o[2] : o[1]).join(", ");
    const option = (q.options || []).find(o => o[0] === value);
    return option ? (lang === "pt" ? option[2] : option[1]) : String(value || "");
  }
  function review() {
    const root = $("formRoot"); root.replaceChildren();
    const inactive = Q.filter(q => !core.visible(q, answers) && (present(answers[q.id]) || states[q.id])).length;
    if (inactive) {
      const note = document.createElement("p"); note.className = "statusNote";
      note.textContent = t(`${inactive} earlier conditional answer(s) are kept in this browser for editing, but excluded from export.`, `${inactive} resposta(s) condicionais anteriores estão guardadas neste navegador para edição, mas não entram na exportação.`);
      root.appendChild(note);
    }
    sections().forEach(id => {
      const section = document.createElement("section"); section.className = "reviewGroup";
      const heading = document.createElement("h2"); heading.textContent = title(id);
      const edit = document.createElement("button"); edit.type = "button"; edit.className = "editLink";
      edit.textContent = t("Edit section", "Editar seção"); edit.onclick = () => { step = steps().indexOf(id); render(true); };
      section.append(heading, edit);
      Q.filter(q => q.section === id && core.visible(q, answers) && (present(answers[q.id]) || states[q.id])).forEach(q => {
        const row = document.createElement("div"); row.className = "reviewItem";
        const label = document.createElement("div"); label.className = "reviewLabel";
        label.textContent = lang === "pt" ? q.pt : q.en;
        const value = document.createElement("div"); value.className = "reviewValue";
        value.textContent = states[q.id] ? (states[q.id] === "unknown" ? t("Not known yet", "Ainda não sei") : t("Not applicable", "Não se aplica")) : display(q, answers[q.id]);
        row.append(label, value); section.appendChild(row);
      }); root.appendChild(section);
    });
  }
  async function copy(value, message) {
    if (!value) { $("inlineMessage").textContent = t("Enter a valid GitHub repository first.", "Informe primeiro um repositório GitHub válido."); return; }
    try {
      if (!navigator.clipboard?.writeText) throw new Error("Clipboard unavailable");
      await navigator.clipboard.writeText(value); $("inlineMessage").textContent = message;
    } catch {
      $("inlineMessage").textContent = t("Copy unavailable. Select the visible text manually.", "Cópia indisponível. Selecione o texto visível manualmente.");
    }
  }
  function download() {
    const missing = core.missing(answers);
    if (missing.length) {
      invalid = new Set(missing.map(q => q.id)); step = Math.max(0, steps().indexOf(missing[0].section));
      render(true); focusErrors(missing); return;
    }
    const blob = new Blob([JSON.stringify(payload(), null, 2)], {type:"application/json"});
    if (blob.size > C.MAX_FILE_BYTES) { $("inlineMessage").textContent = t("Intake too large to export.", "Intake grande demais para exportar."); return; }
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
    a.download = (H.slugify(answers.project_name) || "project") + "-intake.json";
    a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }
  function finish() {
    const root = $("formRoot"), card = document.createElement("section"); card.className = "completionCard";
    const existing = answers.existing_or_new === "existing_code" || ["existing","local_only"].includes(answers.repository_state);
    const heading = document.createElement("h2"); heading.textContent = existing ? t("Prepare an Adoption Sandbox", "Prepare uma Adoption Sandbox") : t("Prepare the new project", "Prepare o projeto novo");
    const info = document.createElement("p"); info.textContent = existing
      ? t("Keep the original intact. Verify its baseline, then make a separate clone for the adoption and review the delta before applying it.", "Mantenha o original intacto. Verifique a base, crie um clone separado para a adoção e revise o delta antes de aplicá-lo.")
      : t("Identify or create the GitHub repository. An empty repository does not yet contain BootCrate; materialization follows the approved plan.", "Identifique ou crie o repositório GitHub. Um repositório vazio ainda não contém o BootCrate; a materialização segue o plano aprovado.");
    const issues = document.createElement("p"); issues.className = "statusNote";
    issues.textContent = t("GitHub Issues, version identity, checks and acceptance are part of the method. Setup cannot verify repository access or grant publication permission.", "GitHub Issues, versão, verificações e aceite fazem parte do método. O Setup não verifica acesso ao repositório nem concede permissão para publicar.");
    const guide = G.resolve(answers); const next = document.createElement("p"); next.className = "statusNote";
    next.textContent = guide.next ? t("Next check: ", "Próxima verificação: ") + guide.next.action + " (" + guide.next.owner + ")."
      : t("No actionable next check was derived; preserve open decisions for the orchestrator.", "Nenhuma próxima verificação acionável foi derivada; preserve as decisões abertas para o orquestrador.");
    card.append(heading, info, issues, next);
    if (answers.execution_profile === "full_access" && answers.full_access_acknowledgement !== "acknowledged") {
      const warning=document.createElement("p");warning.className="statusNote";
      warning.textContent=t("Full Access was not explicitly confirmed, so the handoff remains protected/manual.","Acesso Total não foi confirmado explicitamente; o handoff permanece protegido/manual.");
      card.appendChild(warning);
    }
    const label = document.createElement("label"); label.htmlFor = "repoInput";
    label.textContent = t("GitHub repository URL or owner/name", "URL do repositório GitHub ou owner/name");
    const row = document.createElement("div"); row.className = "repoRow";
    const input = document.createElement("input"); input.id = "repoInput"; input.type = "text";
    input.value = repository; input.placeholder = "owner/project";
    row.appendChild(input);
    if (answers.repository_state === "none") {
      const button = document.createElement("button"); button.type = "button"; button.className = "secondaryButton";
      button.textContent = t("Open GitHub to create", "Abrir GitHub para criar");
      button.onclick = () => {
        window.open(H.githubCreateUrl({name:answers.project_name, description:answers.one_sentence, visibility:"private"}), "_blank", "noopener");
        $("inlineMessage").textContent = t("If no tab opened, visit github.com/new. The proposed name and description are sent to GitHub when opened. Return with the repository address.", "Se nenhuma aba abriu, acesse github.com/new. O nome e a descrição propostos são enviados ao GitHub ao abrir. Volte com o endereço do repositório.");
      };
      row.appendChild(button);
    }
    card.append(label, row);
    const addOutput = (id, caption, buttonText) => {
      const l = document.createElement("label"); l.htmlFor = id; l.textContent = caption;
      const area = document.createElement("textarea"); area.id = id; area.readOnly = true;
      const button = document.createElement("button"); button.type = "button"; button.className = "secondaryButton";
      button.textContent = buttonText; button.onclick = () => copy(area.value, t("Copied.", "Copiado."));
      card.append(l, area, button); return area;
    };
    const instructions = addOutput("instructionsOutput", t("ChatGPT Project instructions", "Instruções do Projeto do ChatGPT"), t("Copy instructions", "Copiar instruções"));
    const message = addOutput("messageOutput", t("First message", "Primeira mensagem"), t("Copy message", "Copiar mensagem"));
    const button = document.createElement("button"); button.type = "button"; button.className = "primaryButton";
    button.textContent = t("Download intake JSON", "Baixar intake JSON"); button.onclick = download; card.appendChild(button);
    root.replaceChildren(card);
    const refresh = () => {
      const raw = input.value.trim(), parsed = H.parseRepository(raw);
      if (!raw || parsed) {
        if (repository !== parsed) { repository = parsed; save(); }
        instructions.value = H.projectInstructions(repository, answers.repository_state, requestedExecution());
        $("inlineMessage").textContent = "";
      } else {
        instructions.value = "";
        $("inlineMessage").textContent = t("Enter a valid GitHub repository as owner/name or an https://github.com/owner/name URL.", "Informe um repositório GitHub válido como owner/name ou URL https://github.com/owner/name.");
      }
      message.value = H.initialMessage(lang === "pt" ? "pt-BR" : "en");
    };
    input.oninput = refresh; refresh();
  }
  function render(focus) {
    const list = steps(); step = Math.min(step, list.length - 1); const id = list[Math.max(0, step)];
    document.documentElement.lang = lang === "pt" ? "pt-BR" : "en";
    $("langBtn").textContent = lang === "pt" ? "EN" : "PT-BR";
    $("modeLabel").textContent = t("View", "Visão");
    $("modeSelect").setAttribute("aria-label", t("Presentation mode", "Modo de apresentação"));
    $("modeSelect").options[0].textContent = t("Basic", "Básico");
    $("modeSelect").options[1].textContent = t("Detailed", "Detalhado");
    $("modeSelect").value = mode;
    $("newBtn").textContent = t("New", "Novo");
    document.querySelector(".fileButton .fileLabel").textContent = t("Import JSON", "Importar JSON");
    $("privacyHint").textContent = t("Draft answers stay in this browser. Export sends nothing automatically.", "O rascunho fica neste navegador. Exportar não envia dados automaticamente.");
    const header = $("stepHeader"); header.replaceChildren();
    const heading = document.createElement("h1"); heading.tabIndex = -1; heading.textContent = title(id);
    const subtitle = document.createElement("p"); subtitle.textContent = desc(id); header.append(heading, subtitle);
    $("errorSummary").replaceChildren(); $("errorSummary").hidden = true; $("inlineMessage").textContent = "";
    $("resetTitle").textContent = t("Start over?", "Começar de novo?");
    $("resetText").textContent = t("This clears the local draft in this browser.", "Isso apaga o rascunho local neste navegador.");
    $("cancelResetBtn").textContent = $("cancelLegacyBtn").textContent = t("Cancel", "Cancelar");
    $("confirmResetBtn").textContent = t("Start new", "Iniciar novo");
    $("legacyTitle").textContent = t("Review older intake", "Revise o intake antigo");
    $("confirmLegacyBtn").textContent = t("Adopt current method", "Adotar o método atual");
    $("importInput").setAttribute("aria-label", t("Import JSON", "Importar JSON"));
    id === "__review" ? review() : id === "__finish" ? finish() : questions(id);
    $("backBtn").textContent = t("Back", "Voltar"); $("backBtn").disabled = step === 0;
    $("nextBtn").textContent = id === "__review" ? t("Prepare handoff", "Preparar handoff") : id === "__finish"
      ? t("Download intake", "Baixar intake") : t("Continue", "Continuar");
    nav(); progress(); if (focus) heading.focus();
    if (!storage) $("saveStatus").textContent = t("Local save unavailable: export before leaving", "Não foi possível salvar: exporte antes de sair");
  }
  function focusErrors(missing) {
    const summary = $("errorSummary"); summary.textContent = t("Answer the required questions in this section: ", "Responda às perguntas obrigatórias desta seção: ")
      + missing.filter(q => q.section === steps()[step]).map(q => lang === "pt" ? q.pt : q.en).join("; ");
    summary.hidden = false; summary.focus();
    $("field-" + missing[0].id)?.scrollIntoView({block:"center"});
  }
  $("backBtn").onclick = () => { if (step > 0) { step--; render(true); } };
  $("modeSelect").onchange = event => {
    const id = steps()[step]; mode = event.target.value === "detailed" ? "detailed" : "basic";
    set(KEY + "-mode", mode); step = Math.max(0, steps().indexOf(id)); render(true);
  };
  $("nextBtn").onclick = () => {
    const id = steps()[step]; if (id === "__finish") return download();
    if (!id.startsWith("__")) {
      const missing = Q.filter(q => q.section === id && core.visible(q, answers) && q.required && !present(answers[q.id]));
      if (missing.length) { invalid = new Set(missing.map(q => q.id)); render(false); focusErrors(missing); return; }
    }
    step++; render(true);
  };
  $("langBtn").onclick = () => { lang = lang === "pt" ? "en" : "pt"; set(KEY + "-lang", lang); render(false); };
  $("newBtn").onclick = () => $("resetDialog").showModal();
  $("confirmResetBtn").onclick = () => { answers = {execution_profile:"protected_manual"}; states = {}; repository = ""; invalid = new Set();
    session = {id:crypto?.randomUUID?.() || String(Date.now()), created_at:new Date().toISOString()}; step = 0; save(); render(true); };
  function importData(data) {
    let imported = data;
    if (data?.schema === "bootcrate-project-intake/v1") {
      pendingLegacy = core.upgradeLegacy(data);
      $("legacyText").textContent = t("This old intake may contain choices that conflict with the mandatory method. Review it and explicitly adopt GitHub Issues and ChatGPT as normal orchestration. Original file remains unchanged.", "Este intake antigo pode conter opções contrárias ao método obrigatório. Revise e confirme a adoção de GitHub Issues e ChatGPT como orquestração normal. O arquivo original permanece intacto.")
        + (pendingLegacy.conflicts.length ? " [" + pendingLegacy.conflicts.join(", ") + "]" : "");
      $("legacyDialog").showModal(); return;
    }
    if (core.validate(imported).length) throw new Error("Invalid intake");
    const normalized = core.normalize(imported);
    const nextAnswers = normalized.answers, nextStates = normalized.states;
    const nextSession = {...session, ...(normalized.session || {})}, nextRepository = normalized.repository;
    answers = nextAnswers; states = nextStates; session = nextSession; repository = nextRepository;
    lang = normalized.language === "pt-BR" ? "pt" : "en";
    invalid = new Set(); step = 0; save(); render(true);
  }
  $("confirmLegacyBtn").onclick = () => { if (pendingLegacy) { const data = pendingLegacy.converted;
    pendingLegacy = null; importData(data); } };
  $("cancelLegacyBtn").onclick = () => { pendingLegacy = null; };
  $("importInput").onchange = async event => {
    const file = event.target.files[0]; if (!file) return;
    try { if (file.size > C.MAX_FILE_BYTES) throw new Error("too large"); importData(JSON.parse(await file.text())); }
    catch { $("inlineMessage").textContent = t("Invalid intake. The current draft was preserved.", "Intake inválido. O rascunho atual foi preservado."); }
    finally { event.target.value = ""; }
  };
  render(false);
  if (pendingLegacy) {
    $("legacyText").textContent = t("An older local draft is available. Confirm the current mandatory method before importing it; your current draft is preserved until then.", "Há um rascunho local antigo. Confirme o método obrigatório atual antes de importar; seu rascunho atual fica preservado até lá.");
    $("legacyDialog").showModal();
  }
  // A selected preset is an intention, never an authorization or a reduction of Main effort.
  void Preset.resolve({project:answers.consumption_preset});
  // Execution permissions are independent from autonomy, effort and consumption; absent data stays protected/manual.
  void Execution.resolve({task:requestedExecution()});
})();
