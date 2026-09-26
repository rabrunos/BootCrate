/* Pure intake validation shared by the offline app and deterministic tests. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.BootCrateIntakeCore = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const SCHEMA = "bootcrate-project-intake/v2";
  const MAX_FILE_BYTES = 1024 * 1024;
  const MAX_TEXT = 20000;
  const object = v => v !== null && typeof v === "object" && !Array.isArray(v);
  const present = v => typeof v === "string" ? v.trim().length > 0 : Array.isArray(v) && v.length > 0;

  function create(questions) {
    const byId = new Map(questions.map(q => [q.id, q]));
    if (byId.size !== questions.length) throw new Error("Duplicate question id");
    for (const q of questions) {
      if (!/^[a-z][a-z0-9_]*$/.test(q.id) || ["constructor", "prototype", "__proto__"].includes(q.id)) {
        throw new Error("Unsafe question id");
      }
      const seen = new Set([q.id]);
      let parent = q;
      while (parent.condition) {
        parent = byId.get(parent.condition.id);
        if (!parent || seen.has(parent.id)) throw new Error("Invalid condition graph");
        seen.add(parent.id);
      }
    }
    function visible(q, answers, seen = new Set()) {
      if (!q.condition) return true;
      if (seen.has(q.id)) return false;
      seen.add(q.id);
      const parent = byId.get(q.condition.id);
      return Boolean(parent && visible(parent, answers, seen) &&
        q.condition.in.includes(answers[parent.id]));
    }
    const active = answers => questions.filter(q => visible(q, answers));
    const missing = answers => active(answers).filter(q => q.required && !present(answers[q.id]));
    function validValue(q, value) {
      if (["text", "textarea"].includes(q.type)) return typeof value === "string" && value.length <= MAX_TEXT;
      const values = new Set((q.options || []).map(o => o[0]));
      if (q.type === "select") return typeof value === "string" && values.has(value);
      return q.type === "multiselect" && Array.isArray(value) && value.length <= values.size &&
        new Set(value).size === value.length && value.every(v => typeof v === "string" && values.has(v));
    }
    function validate(data) {
      const errors = [];
      const add = (code, path) => errors.push({code, path});
      if (!object(data)) return [{code: "object", path: "root"}];
      const allowed = new Set(["schema", "exported_at", "session", "language", "repository", "bootstrap_source", "answers", "answer_states", "interpretation_rules"]);
      for (const key of Object.keys(data)) if (!allowed.has(key)) add("unknown", key);
      if (data.schema !== SCHEMA) add("schema", "schema");
      if (data.language !== undefined && !["en", "pt-BR"].includes(data.language)) add("value", "language");
      if (data.repository !== undefined && (typeof data.repository !== "string" ||
          !/^[A-Za-z0-9][A-Za-z0-9-]{0,38}\/[A-Za-z0-9._-]{1,100}$/.test(data.repository) || data.repository.endsWith(".git"))) add("value", "repository");
      if (data.bootstrap_source !== undefined && (!object(data.bootstrap_source) ||
          Object.keys(data.bootstrap_source).some(key => !["product","version","repository","entrypoint"].includes(key)) ||
          ["product","version","repository","entrypoint"].some(key => typeof data.bootstrap_source[key] !== "string" || !data.bootstrap_source[key])))
        add("value", "bootstrap_source");
      if (data.exported_at !== undefined && (typeof data.exported_at !== "string" || data.exported_at.length > 64 || !Number.isFinite(Date.parse(data.exported_at)))) add("value", "exported_at");
      if (data.session !== undefined) {
        if (!object(data.session)) add("object", "session");
        else for (const [key, value] of Object.entries(data.session)) {
          if (!["id", "created_at"].includes(key)) add("unknown", "session." + key);
          else if (typeof value !== "string" || !value.trim() || value.length > 128 ||
            (key === "created_at" && !Number.isFinite(Date.parse(value)))) add("value", "session." + key);
        }
      }
      if (data.interpretation_rules !== undefined && (!object(data.interpretation_rules) ||
          Object.keys(data.interpretation_rules).length > 32 || Object.values(data.interpretation_rules).some(v => typeof v !== "boolean"))) add("value", "interpretation_rules");
      if (!object(data.answers)) add("object", "answers");
      else for (const [id, value] of Object.entries(data.answers)) {
        const q = byId.get(id);
        if (!q) add("unknown", "answers." + id);
        else if (!validValue(q, value)) add("value", "answers." + id);
      }
      if (data.answers?.execution_profile === "full_access" &&
          data.answers.full_access_acknowledgement !== "acknowledged")
        add("required", "answers.full_access_acknowledgement");
      if (data.answer_states !== undefined) {
        if (!object(data.answer_states)) add("object", "answer_states");
        else for (const [id, state] of Object.entries(data.answer_states)) {
          const q = byId.get(id);
          if (!q || q.required || !["text", "textarea"].includes(q.type) ||
              !["unknown", "not_applicable"].includes(state) || present(data.answers?.[id]))
            add("value", "answer_states." + id);
        }
      }
      return errors;
    }
    function exportAnswers(answers) {
      const out = {};
      for (const q of active(answers)) {
        const value = answers[q.id];
        if (present(value) && !validValue(q, value)) throw new Error("Invalid active answer: " + q.id);
        if (present(value)) out[q.id] = typeof value === "string" ? value.trim() : [...value];
      }
      if (out.execution_profile === "full_access" && out.full_access_acknowledgement !== "acknowledged")
        throw new Error("Full Access requires explicit acknowledgement");
      return out;
    }
    function exportStates(states, answers) {
      const out = {};
      for (const q of active(answers)) if (states[q.id]) out[q.id] = states[q.id];
      if (validate({schema:SCHEMA,answers:exportAnswers(answers),answer_states:out}).length)
        throw new Error("Invalid answer states");
      return out;
    }
    function normalize(data) {
      const errors = validate(data);
      if (errors.length) throw new Error("Invalid intake envelope");
      const answers = {};
      for (const [id, value] of Object.entries(data.answers)) answers[id] = typeof value === "string" ? value.trim() : [...value];
      if (!answers.execution_profile) answers.execution_profile = "protected_manual";
      return {answers, states:{...(data.answer_states || {})}, language: data.language || "en", session: data.session ? {...data.session} : null,
        repository:data.repository || "", bootstrap_source:data.bootstrap_source ? {...data.bootstrap_source} : null};
    }
    function upgradeLegacy(data) {
      if (!object(data) || data.schema !== "bootcrate-project-intake/v1" || !object(data.answers))
        throw new Error("Not a legacy intake");
      const old = data.answers;
      const conflicts = [];
      const retired = {
        issues_tracking: ["yes", "no", "custom"],
        primary_orchestration: ["chatgpt", "local_planner", "custom"],
        agent_budget: ["main_worker_scout", "main_worker", "recommend"]
      };
      for (const [id, value] of Object.entries(old)) {
        if (!byId.has(id) && (!Object.hasOwn(retired, id) || !retired[id].includes(value)))
          throw new Error("Unknown or invalid legacy answer: " + id);
      }
      if (old.issues_tracking && old.issues_tracking !== "yes") conflicts.push("github_issues_required");
      if (old.primary_orchestration && old.primary_orchestration !== "chatgpt") conflicts.push("chatgpt_primary_required");
      const answers = {};
      for (const [id, value] of Object.entries(old)) {
        const q = byId.get(id);
        if (q && validValue(q, value)) answers[id] = value;
        else if (q && id !== "existing_or_new") throw new Error("Invalid legacy answer: " + id);
      }
      if (old.existing_or_new === "external_target") {
        answers.existing_or_new = "unknown";
        answers.external_integration = "yes";
        conflicts.push("legacy_product_stage_unknown");
      } else if (old.existing_or_new && !validValue(byId.get("existing_or_new"), old.existing_or_new)) {
        throw new Error("Invalid legacy project stage");
      }
      // Topology is not a cost preset; the owner must select it separately.
      answers.execution_profile = "protected_manual";
      const converted = {schema: SCHEMA, answers, language: data.language, session: data.session};
      if (validate(converted).length) throw new Error("Invalid converted intake");
      return {converted, conflicts};
    }
    return {visible, active, missing, validValue, validate, exportAnswers, exportStates, normalize, upgradeLegacy};
  }
  return {SCHEMA, MAX_FILE_BYTES, MAX_TEXT, create};
});
