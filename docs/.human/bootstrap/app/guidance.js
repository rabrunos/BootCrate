/* One small evidence resolver for the offline Setup and handoff. No remote claims. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.BootCrateGuidance = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const requirements = [
    {id:"intent", owner:"owner", action:"Review the project intent and unresolved decisions"},
    {id:"repository", owner:"owner", action:"Identify the intended GitHub repository"},
    {id:"remote_access", owner:"planner", action:"Verify the repository identity, contents and permissions"},
    {id:"issues", owner:"planner", action:"Verify Issues and the relevant work item"},
    {id:"executor", owner:"executor", action:"Verify the checkout and available executor capabilities"},
    {id:"decisions", owner:"owner", action:"Resolve material product and security decisions"},
    {id:"scope", owner:"owner", action:"Approve the concrete implementation or adoption scope"},
    {id:"materialized", owner:"executor", action:"Materialize or adopt the complete selected method"},
    {id:"checks", owner:"executor", action:"Run the applicable structural and product checks"},
    {id:"acceptance", owner:"owner", action:"Review the evidence and accept the result"}
  ];
  const states = new Set(["satisfied","unsatisfied","blocked","unknown","not_applicable"]);
  const sources = new Set(["tool_observed","owner_confirmed","agent_declared"]);
  function resolve(answers, evidence = {}, basis = null) {
    const items = requirements.map(req => {
      const item = evidence[req.id];
      let status = "unknown", freshness = "unknown", source = null;
      if (item && states.has(item.status) && sources.has(item.source)) {
        status = item.status; source = item.source;
        freshness = item.freshness === "current" || item.freshness === "stale" ? item.freshness : "unknown";
        if (basis && item.basis && basis !== item.basis) freshness = "stale";
        if (status === "satisfied" && (freshness !== "current" ||
            (["remote_access","executor","materialized","checks"].includes(req.id) && source !== "tool_observed")))
          status = "unknown";
      }
      // Entered information is intent; it does not verify a GitHub session or a checkout.
      if (req.id === "intent" && answers.project_name && answers.one_sentence && !item) {
        status = "satisfied"; source = "owner_confirmed"; freshness = "current";
      }
      if (req.id === "repository" && answers.repository_state === "none" && !item) status = "unsatisfied";
      if (req.id === "repository" && answers.repository_state === "unknown" && !item) status = "unknown";
      return {...req, status, source, freshness};
    });
    const next = items.find(item => item.status !== "satisfied" && item.status !== "not_applicable") || null;
    return {items, next, readiness: next ? "pending" : "accepted",
      observation: "Offline intake only; repository, permissions, checkout and product checks need independent observation"};
  }
  return {requirements, resolve};
});
