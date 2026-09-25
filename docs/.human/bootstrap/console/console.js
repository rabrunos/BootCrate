(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const Preset = window.BootCratePreset;
  let profile = null, override = null, version = null, preflight = null, history = null;
  function status(message) { $("status").textContent = message; }
  function add(name, value) {
    const label = document.createElement("dt"), content = document.createElement("dd");
    label.textContent = name; content.textContent = value; $("details").append(label, content);
  }
  function refresh() {
    $("details").replaceChildren();
    if (!profile) return;
    const preset = Preset.resolve({local:override?.preset, project:profile.workflow.consumption_preset || "standard"});
    add("Project", profile.project.name);
    add("Product type", profile.project.kind);
    add("Version source", profile.versioning.canonical_source);
    add("Imported version file", version || "Not imported — checkout version unknown");
    add("Consumption preset", preset.preset + " (" + preset.source + ")");
    add("Main effort", "Medium / High / XHigh by task; High default; preset does not lower required effort");
    add("Roles", "Main decides and verifies; optional Scout reads; bounded Worker implements delegated work");
    add("Executors", profile.workflow.implementation_harnesses.join(", "));
    add("Distribution", profile.distribution?.mode || "Unknown for old profile");
    add("Selected skills", profile.skills?.length ? profile.skills.join(", ") : "None declared; verify the actual checkout");
    add("Canonical checks", profile.validation?.canonical_capabilities?.length ? profile.validation.canonical_capabilities.join(", ") : "Not declared");
    add("Security controls", profile.security?.control_map || "Not imported");
    add("Remote publications", "Unknown until provider receipts are reconciled");
    add("Source", "Imported local files; current GitHub state has not been checked");
  }
  async function read(id, max = 1024*1024) {
    const file = $(id).files[0]; if (!file) return null;
    if (file.size > max) throw new Error("Selected file exceeds 1 MiB");
    return file.text();
  }
  function download(name, value) {
    const blob = new Blob([JSON.stringify(value, null, 2) + "\n"], {type:"application/json"});
    const anchor = document.createElement("a"); anchor.href = URL.createObjectURL(blob);
    anchor.download = name; anchor.click(); setTimeout(() => URL.revokeObjectURL(anchor.href), 1000);
  }
  $("profile").onchange = async () => {
    try {
      const value = JSON.parse(await read("profile"));
      if (!["project-profile/v2","project-profile/v3"].includes(value.schema) ||
          !value.project?.name || value.workflow?.tracking !== "github_issues" ||
          value.workflow?.primary_orchestrator !== "chatgpt" ||
          !Array.isArray(value.workflow?.implementation_harnesses) ||
          !value.versioning?.canonical_source) throw new Error("Unsupported or incomplete profile");
      const source = value.versioning.canonical_source;
      if (source.startsWith("/") || source.includes("\\") || source.split("/").some(x => ["..",".local",".git",".env"].includes(x)))
        throw new Error("Unsafe version source reference");
      if (value.schema === "project-profile/v3" && !["standard","economy"].includes(value.workflow.consumption_preset))
        throw new Error("Invalid project preset");
      profile = value; override = null; version = null; preflight = null; history = null;
      $("override").value = $("version").value = $("preflight").value = $("history").value = "";
      $("historyNotes").textContent = "No changelog imported; history unknown.";
      $("notes").textContent = "No preflight imported. Remote status unknown.";
      $("localCheck").textContent = "No local check run for this profile.";
      refresh(); status("Profile imported. This is a local structural preview, not full schema or behavior verification.");
    } catch (error) { status("Profile import failed: " + error.message + ". Previous profile was preserved."); }
  };
  $("override").onchange = async () => {
    try {
      const value = JSON.parse(await read("override"));
      if (value.schema !== "bootcrate-preset-override/v1" || !["standard","economy"].includes(value.preset))
        throw new Error("Invalid local preset override");
      override = value; refresh(); status("Local override imported; it applies only where the executor reads this file.");
    } catch (error) { status("Override import failed: " + error.message + ". Previous override was preserved."); }
  };
  $("version").onchange = async () => {
    try {
      if (!profile) throw new Error("Import a profile first");
      const expected = profile.versioning.canonical_source.split("/").at(-1);
      if ($("version").files[0]?.name !== expected) throw new Error("Selected file does not match the declared version source");
      const raw = (await read("version")).trim();
      let value = null;
      if (expected === "VERSION" && /^[0-9A-Za-z][0-9A-Za-z.+-]{0,63}$/.test(raw)) value = raw;
      if (expected.endsWith(".json")) {
        const parsed = JSON.parse(raw);
        if (typeof parsed.version === "string" && /^[0-9A-Za-z][0-9A-Za-z.+-]{0,63}$/.test(parsed.version)) value = parsed.version;
      }
      if (!value) throw new Error("Native format needs its own verified version reader; no raw file content is displayed");
      version = value; refresh(); status("Version source imported; this reflects the selected local file only.");
    } catch (error) { status("Version import failed: " + error.message); }
  };
  $("history").onchange = async () => {
    try {
      if ($("history").files[0]?.name !== "CHANGELOG.md") throw new Error("Select CHANGELOG.md");
      const source = await read("history"), entries = [...source.matchAll(/^## v([^\s]+) — ([^\r\n]+)$/gm)];
      if (!entries.length || new Set(entries.map(e => e[1])).size !== entries.length)
        throw new Error("No unique version headings found");
      history = entries.map(e => `v${e[1]} — ${e[2]}`);
      $("historyNotes").textContent = history.join("\n") + "\nLocal selected changelog only; no provider state checked.";
      status("Version headings imported; run the native changelog parser before delivery.");
    } catch (error) { status("History import failed: " + error.message + ". Previous history was preserved."); }
  };
  $("preflight").onchange = async () => {
    try { const value = JSON.parse(await read("preflight"));
      const items = Array.isArray(value) ? value : [value];
      if (!items.length || items.length > 50 || items.some(x => !x || !["READY","SKIP","BLOCK"].includes(x.status)))
        throw new Error("Unsupported preflight result");
      preflight = items;
      $("notes").textContent = items.map(x => `${String(x.destination || "Unidentified destination").slice(0,100)} / ${String(x.channel || "unknown channel").slice(0,100)}: ${x.status}\n${String(x.notes || x.reason || "No notes").slice(0,20000)}`).join("\n\n")
        + "\nPreview only; remote state not verified here.";
      status("Preflight imported; it does not authorize publication or prove remote state.");
    } catch (error) { status("Preflight import failed: " + error.message + ". Previous preview was preserved."); }
  };
  $("validateLocal").onclick = () => {
    const missing = [];
    if (!profile) missing.push("stable profile");
    else {
      if (!version) missing.push("canonical version source file");
      if (!history) missing.push("CHANGELOG.md version headings");
      if (profile.distribution?.mode !== "none" && !preflight) missing.push("per-destination preflight");
    }
    $("localCheck").textContent = missing.length
      ? "Local preview incomplete: " + missing.join(", ") + ". Full schema and product checks require native tools."
      : "Selected local inputs are present. Full schema, version consistency, product behavior and remote status still require native checks.";
  };
  $("exportPreset").onclick = () => {
    const value = $("presetSelect").value;
    if (!value) { status("Use the project default by removing an existing local override through the normal file tool."); return; }
    download("preset.json",{schema:"bootcrate-preset-override/v1",preset:value});
    status("Downloaded preset.json; place it in the ignored .local/config/ directory to activate it.");
  };
  $("exportSnapshot").onclick = () => {
    if (!profile) { status("Import a profile first."); return; }
    const effective = Preset.resolve({local:override?.preset,project:profile.workflow.consumption_preset || "standard"});
    download("project-snapshot.json", {schema:"bootcrate-console-snapshot/v1",
      project:{name:profile.project.name,kind:profile.project.kind},
      version_source:profile.versioning.canonical_source,imported_version:version,
      preset:effective,executors:profile.workflow.implementation_harnesses,
      distribution_mode:profile.distribution?.mode || null,
      remote_state:"not_observed",product_checks:"not_run"});
    status("Sanitized snapshot downloaded. It is a local observation, not shared project status.");
  };
})();
