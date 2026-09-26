/* One small evidence resolver for the offline Setup and handoff. No remote claims. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.BootCrateGuidance = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const requirements = [
    {id:"intent", owner:"owner", action:"Review the project intent and unresolved decisions", sources:["owner_confirmed","tool_observed"]},
    {id:"repository", owner:"owner", action:"Identify the intended GitHub repository", sources:["owner_confirmed","tool_observed"], basis:["repository"]},
    {id:"remote_access", owner:"planner", action:"Verify the repository identity, contents and permissions", sources:["tool_observed"], basis:["repository"], permissions:true},
    {id:"issues", owner:"planner", action:"Verify Issues and the relevant work item", sources:["tool_observed"], basis:["repository"]},
    {id:"executor", owner:"executor", action:"Verify the checkout and available executor capabilities", sources:["tool_observed"], basis:["repository","commit"]},
    {id:"decisions", owner:"owner", action:"Resolve material product and security decisions", sources:["owner_confirmed"]},
    {id:"scope", owner:"owner", action:"Approve the concrete implementation or adoption scope", sources:["owner_confirmed"]},
    {id:"materialized", owner:"executor", action:"Materialize or adopt the complete selected method", sources:["tool_observed"], basis:["repository","commit"]},
    {id:"checks", owner:"executor", action:"Run the applicable structural and product checks", sources:["tool_observed"], basis:["repository","commit"]},
    {id:"distribution", owner:"executor", action:"Verify the selected delivery path, or confirm that distribution is not selected", sources:["tool_observed"], basis:["repository","commit"], waivable:true},
    {id:"acceptance", owner:"owner", action:"Review the evidence and accept the result", sources:["owner_confirmed"], basis:["repository","commit","scope"]}
  ];
  const states = new Set(["satisfied","unsatisfied","blocked","unknown","not_applicable"]);
  const sources = new Set(["tool_observed","owner_confirmed","agent_declared"]);
  const basisFields = new Set(["repository","commit","scope"]);

  function normalizedBasis(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;
    const result = {};
    for (const key of basisFields) if (typeof value[key] === "string" && value[key].trim()) result[key] = value[key].trim();
    return result;
  }
  function basisMatches(required, observed, current) {
    if (!required?.length) return true;
    const a = normalizedBasis(observed), b = normalizedBasis(current);
    return !!a && !!b && required.every(key => a[key] && b[key] && a[key] === b[key]);
  }
  function legitimateWaiver(req, item, answers) {
    return req.id === "distribution" && req.waivable && answers.distribution_mode === "none" &&
      item.source === "owner_confirmed" && item.waiver?.reason === "no_distribution_selected";
  }
  function level(items, ids) {
    return ids.every(id => items.find(item => item.id === id)?.status === "satisfied" ||
      items.find(item => item.id === id)?.status === "not_applicable") ? "ready" : "pending";
  }
  function resolve(answers = {}, evidence = {}, basis = null) {
    const items = requirements.map(req => {
      const item = evidence[req.id];
      let status = "unknown", freshness = "unknown", source = null, reason = "evidence_missing";
      if (item && states.has(item.status) && sources.has(item.source)) {
        status = item.status; source = item.source;
        freshness = item.freshness === "current" || item.freshness === "stale" ? item.freshness : "unknown";
        reason = null;
        if (status === "not_applicable") {
          if (!legitimateWaiver(req, item, answers)) {
            status = "unknown"; reason = "waiver_not_authorized_or_not_applicable";
          } else if (freshness !== "current") {
            status = "unknown"; reason = "evidence_not_current";
          } else if (!basisMatches(req.basis, item.basis, basis)) {
            status = "unknown"; reason = "evidence_basis_missing_or_divergent";
          }
        } else if (status === "satisfied") {
          if (freshness !== "current") {
            status = "unknown"; reason = "evidence_not_current";
          } else if (!req.sources.includes(source)) {
            status = "unknown"; reason = "evidence_source_insufficient";
          } else if (!basisMatches(req.basis, item.basis, basis)) {
            status = "unknown"; reason = "evidence_basis_missing_or_divergent";
          } else if (req.permissions && item.permissions !== "verified") {
            status = "unknown"; reason = "permissions_not_verified";
          }
        }
      }
      // Entered information is intent; it does not verify a GitHub session or a checkout.
      if (req.id === "intent" && answers.project_name && answers.one_sentence && !item) {
        status = "satisfied"; source = "owner_confirmed"; freshness = "current"; reason = null;
      }
      if (req.id === "repository" && answers.repository_state === "none" && !item) {
        status = "unsatisfied"; reason = "repository_not_identified";
      }
      if (req.id === "repository" && answers.repository_state === "unknown" && !item) {
        status = "unknown"; reason = "repository_unknown";
      }
      if (req.id === "distribution" && answers.distribution_mode === "none" && !item) {
        status = "unknown"; reason = "owner_confirmation_required_for_no_distribution";
      }
      return {id:req.id, owner:req.owner, action:req.action, status, source, freshness, reason};
    });
    const next = items.find(item => item.status !== "satisfied" && item.status !== "not_applicable") || null;
    const readiness = {
      planning: level(items,["intent","repository","decisions"]),
      execution: level(items,["intent","repository","remote_access","issues","executor","decisions","scope"]),
      structure: level(items,["materialized"]),
      behavior: level(items,["checks","distribution"]),
      acceptance: level(items,["acceptance"])
    };
    return {items, next, readiness: next ? "pending" : "accepted", readiness_levels:readiness,
      blocked_action: next ? next.action : null,
      observation: "Offline intake only; repository, permissions, checkout and product checks need independent observation"};
  }
  return {requirements, resolve};
});
