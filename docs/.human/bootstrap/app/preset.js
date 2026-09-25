/* Shared deterministic precedence; a preset cannot change required effort or gates. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.BootCratePreset = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const valid = new Set(["standard", "economy"]);
  function resolve({task, local, project} = {}) {
    for (const [source, value] of [["task",task],["local",local],["project",project],["default","standard"]]) {
      if (value !== undefined && value !== null && value !== "") {
        if (!valid.has(value)) throw new Error("Invalid consumption preset from " + source);
        return {preset:value,source};
      }
    }
  }
  function effort(taskClass, mediumEligible = false) {
    if (taskClass === "E0") return "not_required";
    if (taskClass === "E1") return mediumEligible ? "medium" : "high";
    if (taskClass === "E2") return "high";
    if (taskClass === "E3") return "xhigh";
    throw new Error("Unknown task class");
  }
  return {resolve, effort};
});
