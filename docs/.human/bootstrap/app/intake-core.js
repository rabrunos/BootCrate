/* Pure intake validation shared by the offline app and deterministic tests. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.BootCrateIntakeCore = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const SCHEMA = "bootcrate-project-intake/v1";
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
      const allowed = new Set(["schema", "exported_at", "session", "language", "answers", "interpretation_rules"]);
      for (const key of Object.keys(data)) if (!allowed.has(key)) add("unknown", key);
      if (data.schema !== SCHEMA) add("schema", "schema");
      if (data.language !== undefined && !["en", "pt-BR"].includes(data.language)) add("value", "language");
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
      return errors;
    }
    function exportAnswers(answers) {
      const out = {};
      for (const q of active(answers)) {
        const value = answers[q.id];
        if (present(value) && !validValue(q, value)) throw new Error("Invalid active answer: " + q.id);
        if (present(value)) out[q.id] = typeof value === "string" ? value.trim() : [...value];
      }
      return out;
    }
    function normalize(data) {
      const errors = validate(data);
      if (errors.length) throw new Error("Invalid intake envelope");
      const answers = {};
      for (const [id, value] of Object.entries(data.answers)) answers[id] = typeof value === "string" ? value.trim() : [...value];
      return {answers, language: data.language || "en", session: data.session ? {...data.session} : null};
    }
    return {visible, active, missing, validValue, validate, exportAnswers, normalize};
  }
  return {SCHEMA, MAX_FILE_BYTES, MAX_TEXT, create};
});
