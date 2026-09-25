(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const Preset = window.BootCratePreset, Execution = window.BootCrateExecutionProfile;
  const LIMIT = 1024 * 1024, EXECUTORS = new Set(["codex","claude_code"]);
  let state = {profile:null,presetOverride:null,executionOverride:null,version:null,preflight:null,history:null,importedAt:null};
  function status(message) { $("status").textContent = message; }
  function text(value, name, max = 20000) {
    if (typeof value !== "string" || !value.trim() || value.length > max) throw new Error("Invalid " + name);
    return value;
  }
  function stringArray(value, name, allowed = null) {
    if (!Array.isArray(value) || value.length > 100 || value.some(x => typeof x !== "string" || !x || x.length > 500) ||
        new Set(value).size !== value.length || (allowed && value.some(x => !allowed.has(x)))) throw new Error("Invalid " + name);
    return [...value];
  }
  function safePath(value, name) {
    const source = text(value,name,500);
    if (source.startsWith("/") || source.includes("\\") || source.split("/").some(x => ["..",".local",".git",".env"].includes(x)))
      throw new Error("Unsafe " + name);
    return source;
  }
  function validateProfile(value) {
    if (!value || !["project-profile/v2","project-profile/v3"].includes(value.schema)) throw new Error("Unsupported profile schema");
    text(value.project?.name,"project name",200); text(value.project?.kind,"project kind",200);
    if (value.workflow?.tracking !== "github_issues" || value.workflow?.primary_orchestrator !== "chatgpt") throw new Error("Unsupported workflow authority");
    stringArray(value.workflow?.implementation_harnesses,"implementation harnesses",EXECUTORS);
    if (!["standard","economy"].includes(value.workflow?.consumption_preset || "standard")) throw new Error("Invalid project preset");
    safePath(value.versioning?.canonical_source,"version source");
    if (value.schema === "project-profile/v3") {
      safePath(value.versioning?.history_source,"history source");
      if (value.execution_permissions?.safe_default !== "protected_manual") throw new Error("Unsafe execution default");
    }
    stringArray(value.skills || [],"skills"); stringArray(value.validation?.canonical_capabilities || [],"canonical capabilities");
    text(value.security?.exposure || "unknown","security exposure",200); stringArray(value.security?.modules || [],"security modules");
    const controlMap=text(value.security?.control_map || "Not imported","security control map",500);
    if (/^[A-Za-z]:[\\/]/.test(controlMap) || controlMap.startsWith("/") || controlMap.startsWith("\\")) throw new Error("Machine path in security control map");
    text(value.distribution?.mode || "unknown","distribution mode",100);
    return value;
  }
  function add(fragment,name,value) { const label=document.createElement("dt"),content=document.createElement("dd"); label.textContent=name;content.textContent=value;fragment.append(label,content); }
  function derive(next) {
    const fragment=document.createDocumentFragment();
    if (!next.profile) return {fragment,historyText:"No changelog imported; history unknown.",notesText:"No preflight imported. Remote status unknown.",localCheck:"No local check run for this profile."};
    const p=next.profile,preset=Preset.resolve({local:next.presetOverride?.preset,project:p.workflow.consumption_preset||"standard"}),execution=Execution.resolve({local:next.executionOverride?.profile});
    add(fragment,"Project",p.project.name);add(fragment,"Product type",p.project.kind);add(fragment,"Version source",p.versioning.canonical_source);
    add(fragment,"Imported version file",next.version||"Not imported - checkout version unknown");add(fragment,"Consumption preset",preset.preset+" ("+preset.source+")");
    add(fragment,"Execution permissions requested",execution.requested+" ("+execution.source+")");add(fragment,"Execution permissions effective","Not observed in this local file view");
    add(fragment,"Main effort","Medium / High / XHigh by task; High default; independent from consumption and permissions");
    add(fragment,"Implementation autonomy","Bounded by the approved task and repository rules; not a permission profile");
    add(fragment,"Executors",p.workflow.implementation_harnesses.join(", "));add(fragment,"Distribution",p.distribution?.mode||"Unknown for old profile");
    add(fragment,"Selected skills",p.skills?.length?p.skills.join(", "):"None declared; verify the actual checkout");
    add(fragment,"Canonical checks",p.validation?.canonical_capabilities?.length?p.validation.canonical_capabilities.join(", "):"Not declared");
    add(fragment,"Security controls",p.security?.control_map||"Not imported");add(fragment,"Remote publications","Unknown until provider receipts are reconciled");
    add(fragment,"Source","Imported local files; current GitHub and executor state have not been checked");
    const historyText=next.history?next.history.join("\n")+"\nLocal selected changelog only; no provider state checked.":"No changelog imported; history unknown.";
    const notesText=next.preflight?next.preflight.map(x=>`${x.destination} / ${x.channel}: ${x.status}\n${x.notes}`).join("\n\n")+"\nPreview only; remote state not verified here.":"No preflight imported. Remote status unknown.";
    return {fragment,historyText,notesText,localCheck:"No local check run for this profile."};
  }
  function commit(next) { const view=derive(next);$("details").replaceChildren(view.fragment);$("historyNotes").textContent=view.historyText;$("notes").textContent=view.notesText;$("localCheck").textContent=view.localCheck;state=next; }
  async function read(id,max=LIMIT) { const file=$(id).files[0];if(!file)return null;if(file.size>max)throw new Error("Selected file exceeds 1 MiB");return file.text(); }
  function download(name,value) { const blob=new Blob([JSON.stringify(value,null,2)+"\n"],{type:"application/json"}),anchor=document.createElement("a");anchor.href=URL.createObjectURL(blob);anchor.download=name;anchor.click();setTimeout(()=>URL.revokeObjectURL(anchor.href),1000); }
  $("profile").onchange=async()=>{try{const raw=await read("profile");if(raw===null)return;const value=validateProfile(JSON.parse(raw));commit({profile:value,presetOverride:null,executionOverride:null,version:null,preflight:null,history:null,importedAt:new Date().toISOString()});for(const id of["presetOverride","executionOverride","version","preflight","history"])$(id).value="";status("Profile imported. This local structural preview is not full schema or behavior verification.");}catch(error){status("Profile import failed: "+error.message+". Previous state was preserved.");}};
  $("presetOverride").onchange=async()=>{try{const raw=await read("presetOverride");if(raw===null)return;const value=JSON.parse(raw);if(value?.schema!=="bootcrate-preset-override/v1"||!["standard","economy"].includes(value.preset)||Object.keys(value).some(k=>!["schema","preset"].includes(k)))throw new Error("Invalid local preset override");commit({...state,presetOverride:value});status("Consumption override imported; it applies only where an executor reads the ignored local file.");}catch(error){status("Consumption override import failed: "+error.message+". Previous state was preserved.");}};
  $("executionOverride").onchange=async()=>{try{const raw=await read("executionOverride");if(raw===null)return;const value=JSON.parse(raw);Execution.parseOverride(value);commit({...state,executionOverride:value});status("Execution override imported as a request. Effective executor permissions remain unobserved.");}catch(error){status("Execution override import failed: "+error.message+". Previous state was preserved.");}};
  $("version").onchange=async()=>{try{if(!state.profile)throw new Error("Import a profile first");const rawFile=await read("version");if(rawFile===null)return;const expected=state.profile.versioning.canonical_source.split("/").at(-1);if($("version").files[0]?.name!==expected)throw new Error("Selected file does not match the declared version source");const raw=rawFile.trim();let value=null;if(expected==="VERSION"&&/^[0-9A-Za-z][0-9A-Za-z.+-]{0,63}$/.test(raw))value=raw;if(expected.endsWith(".json")){const parsed=JSON.parse(raw);if(typeof parsed.version==="string"&&/^[0-9A-Za-z][0-9A-Za-z.+-]{0,63}$/.test(parsed.version))value=parsed.version;}if(!value)throw new Error("Native format needs its verified reader; raw content is not displayed");commit({...state,version:value});status("Version source imported; this reflects the selected local file only.");}catch(error){status("Version import failed: "+error.message+". Previous state was preserved.");}};
  $("history").onchange=async()=>{try{if($("history").files[0]?.name!=="CHANGELOG.md")throw new Error("Select CHANGELOG.md");const source=await read("history");if(source===null)return;const entries=[...source.matchAll(/^## v([^\s]+) \u2014 ([^\r\n]+)$/gm)];if(!entries.length||new Set(entries.map(e=>e[1])).size!==entries.length)throw new Error("No unique version headings found");commit({...state,history:entries.map(e=>`v${e[1]} \u2014 ${e[2]}`)});status("Version headings imported; run the native changelog parser before delivery.");}catch(error){status("History import failed: "+error.message+". Previous state was preserved.");}};
  $("preflight").onchange=async()=>{try{const raw=await read("preflight");if(raw===null)return;const value=JSON.parse(raw),items=Array.isArray(value)?value:[value];if(!items.length||items.length>50)throw new Error("Unsupported preflight result");const clean=items.map(item=>{if(!item||!["READY","SKIP","BLOCK"].includes(item.status))throw new Error("Unsupported preflight result");return{destination:text(String(item.destination||"Unidentified destination"),"destination",100),channel:text(String(item.channel||"unknown channel"),"channel",100),status:item.status,notes:String(item.notes||item.reason||"No notes").slice(0,20000)};});commit({...state,preflight:clean});status("Preflight imported; it does not authorize publication or prove remote state.");}catch(error){status("Preflight import failed: "+error.message+". Previous state was preserved.");}};
  $("validateLocal").onclick=()=>{const missing=[];if(!state.profile)missing.push("stable profile");else{if(!state.version)missing.push("canonical version source file");if(!state.history)missing.push("CHANGELOG.md version headings");if(state.profile.distribution?.mode!=="none"&&!state.preflight)missing.push("per-destination preflight");}$("localCheck").textContent=missing.length?"Local preview incomplete: "+missing.join(", ")+". Full schema and product checks require native tools.":"Selected local inputs are present. Full schema, version consistency, product behavior and remote status still require native checks.";};
  $("exportPreset").onclick=()=>{const value=$("presetSelect").value;if(!value){status("Remove .local/config/preset.json with the normal file tool to use the project default.");return;}download("preset.json",{schema:"bootcrate-preset-override/v1",preset:value});status("Downloaded preset.json for ignored .local/config/preset.json.");};
  $("clearPreset").onclick=()=>{commit({...state,presetOverride:null});$("presetOverride").value="";$("presetSelect").value="";status("Imported consumption override cleared from this view. Remove .local/config/preset.json with the normal file tool (or resolver --clear-local-preset) to restore the project/default precedence.");};
  $("exportExecution").onclick=()=>{try{const profile=$("executionSelect").value,risk=$("fullRisk").checked,value={schema:"bootcrate-execution-profile-override/v1",profile};if(profile==="full_access")value.risk_acknowledged=risk;Execution.parseOverride(value);download("execution-profile.json",value);status("Downloaded an execution request for ignored .local/config/execution-profile.json; native application still needs verification.");}catch(error){status("Execution override not exported: "+error.message+".");}};
  $("clearExecution").onclick=()=>{commit({...state,executionOverride:null});$("executionOverride").value="";$("executionSelect").value="protected_manual";$("fullRisk").checked=false;$("fullRiskRow").hidden=true;status("Imported override cleared from this view. Remove .local/config/execution-profile.json with the normal file tool (or the adapter resolver --clear-local option) to restore the protected/manual safe default.");};
  $("executionSelect").onchange=()=>{$("fullRiskRow").hidden=$("executionSelect").value!=="full_access";};
  $("exportSnapshot").onclick=()=>{if(!state.profile){status("Import a profile first.");return;}const p=state.profile,preset=Preset.resolve({local:state.presetOverride?.preset,project:p.workflow.consumption_preset||"standard"}),execution=Execution.resolve({local:state.executionOverride?.profile});const observations=p.workflow.implementation_harnesses.map(executor=>Execution.observation(execution,{executor,surface:"not_observed",status:"unknown",effective:null,reason:"Import-only Console cannot observe the executor."}));download("project-snapshot.json",{schema:"bootcrate-console-snapshot/v2",project:{name:p.project.name,kind:p.project.kind},version:{source:p.versioning.canonical_source,imported:state.version},consumption:preset,execution:observations,executors:[...p.workflow.implementation_harnesses],skills:[...(p.skills||[])],canonical_capabilities:[...(p.validation?.canonical_capabilities||[])],control_summary:{exposure:p.security?.exposure||"unknown",modules:[...(p.security?.modules||[])],control_map:p.security?.control_map||null},distribution:{mode:p.distribution?.mode||null,targets_count:Array.isArray(p.distribution?.targets)?p.distribution.targets.length:null},observation:{source:"local_imports",timestamp:new Date().toISOString()},remote_state:"not_observed",product_checks:"not_run"});status("Sanitized allowlisted snapshot downloaded. It is a local observation, not shared project status.");};
})();
