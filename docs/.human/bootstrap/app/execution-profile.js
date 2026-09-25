/* Shared semantic execution-permission profiles; separate from effort and consumption. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.BootCrateExecutionProfile = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const ids = ["protected_manual","protected_auto","full_access"];
  const profiles = [
    {id:"protected_manual", recommended:true, name:"Protected — user approval", filesystem:"Workspace/sandbox only", network:"Sandbox policy", reviewer:"User", prompts:"Prompts when eligible elevation is needed", risk:"Recommended safe default. Managed policy and deny rules still apply."},
    {id:"protected_auto", recommended:false, name:"Protected — automatic review", filesystem:"Workspace/sandbox only", network:"Sandbox policy", reviewer:"Client reviewer/classifier", prompts:"Eligible elevations are reviewed automatically", risk:"The reviewer may allow or deny. Unsupported clients must block; this never becomes Full Access."},
    {id:"full_access", recommended:false, name:"Full access — no confirmations (advanced)", filesystem:"Broad host access where the client permits", network:"Broad network access where the client permits", reviewer:"No interactive reviewer", prompts:"No approval prompts", risk:"Highest risk. Explicit opt-in is required; managed policy, OS limits and deny rules still prevail."}
  ];
  function valid(value) { return ids.includes(value); }
  function resolve({task,local} = {}) {
    for (const [source,value] of [["task",task],["local",local],["safe_default","protected_manual"]]) {
      if (value !== undefined && value !== null && value !== "") {
        if (!valid(value)) throw new Error("Invalid execution profile from " + source);
        return {requested:value,source};
      }
    }
  }
  function parseOverride(value) {
    if (!value || Object.keys(value).some(key => !["schema","profile","risk_acknowledged"].includes(key)) ||
        (Object.hasOwn(value,"risk_acknowledged") && typeof value.risk_acknowledged !== "boolean") ||
        value.schema !== "bootcrate-execution-profile-override/v1" || !valid(value.profile))
      throw new Error("Invalid local execution-profile override");
    if (value.profile === "full_access" && value.risk_acknowledged !== true)
      throw new Error("Full Access requires explicit risk acknowledgement");
    return {profile:value.profile,risk_acknowledged:value.risk_acknowledged === true};
  }
  function observation(resolved,{executor,surface,status="unknown",effective=null,reason=null} = {}) {
    if (!ids.includes(effective) && effective !== null) throw new Error("Invalid observed effective profile");
    if (!["supported","unsupported","unknown"].includes(status)) throw new Error("Invalid support status");
    if (typeof executor !== "string" || !executor || typeof surface !== "string" || !surface)
      throw new Error("Executor and surface are required");
    return {requested:resolved.requested,effective,source:resolved.source,executor,surface,status,reason,
      applied:effective !== null};
  }
  return {ids,profiles,valid,resolve,parseOverride,observation};
});
