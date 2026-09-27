/* Browser-only acceptance smoke; file:// matters. Never touches GitHub. */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require('playwright');
const app = pathToFileURL(path.resolve(__dirname,'../app/index.html')).toString();
const consoleUrl = pathToFileURL(path.resolve(__dirname,'../console/index.html')).toString();
let browser;
test.before(async () => { browser = await chromium.launch({headless:true}); });
test.after(async () => { if(browser) await browser.close(); });

test('file-mode Setup shows accessible required errors and preserves legacy draft until confirmation',async () => {
  const page = await browser.newPage();
  await page.goto(app);
  assert.equal(await page.locator('#modeSelect').inputValue(),'basic');
  await page.keyboard.press('Tab');
  assert.ok(await page.evaluate(()=>['BUTTON','SELECT','INPUT'].includes(document.activeElement.tagName)));
  await page.getByRole('button',{name:'Continue'}).click();
  assert.equal(await page.locator('#field-project_name').getAttribute('aria-invalid'),'true');
  assert.match(await page.locator('#errorSummary').innerText(),/required/);
  assert.equal(await page.evaluate(()=>document.activeElement.id),'errorSummary');
  await page.locator('#field-project_name').fill('Example');
  assert.equal(await page.locator('#field-project_name').getAttribute('aria-invalid'),null);
  await page.locator('#modeSelect').selectOption('detailed');
  assert.equal(await page.locator('#field-project_name').inputValue(),'Example');
  await page.locator('#modeSelect').selectOption('basic');
  assert.equal(await page.locator('#field-project_name').inputValue(),'Example');
  await page.locator('#langBtn').click();
  assert.equal(await page.locator('html').getAttribute('lang'),'pt-BR');
  await page.locator('#langBtn').click();
  await page.getByRole('button',{name:'AI workflow'}).click();
  assert.equal(await page.locator('#field-execution_profile').inputValue(),'protected_manual');
  assert.equal(await page.locator('.optionDetails li').count(),3);
  assert.match(await page.locator('.optionDetails').innerText(),/filesystem/i);
  assert.match(await page.locator('.optionDetails').innerText(),/network/i);
  await page.locator('#field-execution_profile').selectOption('full_access');
  assert.equal(await page.locator('#field-full_access_acknowledgement').isVisible(),true);
  assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('bootcrate-project-intake-v2')).answers.project_name),'Example');
  await page.reload();
  await page.getByRole('button',{name:'AI workflow'}).click();
  assert.equal(await page.locator('#field-execution_profile').inputValue(),'full_access');
  assert.equal(await page.locator('#field-full_access_acknowledgement').inputValue(),'');
  await page.getByRole('button',{name:'Project'}).click();
  assert.equal(await page.locator('#field-project_name').inputValue(),'Example');
  await page.getByRole('button',{name:'AI workflow'}).click();
  await page.locator('#field-full_access_acknowledgement').selectOption('acknowledged');
  await page.locator('#field-execution_profile').selectOption('protected_manual');
  assert.equal(await page.locator('#field-full_access_acknowledgement').count(),0);
  assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('bootcrate-project-intake-v2')).answers.full_access_acknowledgement),undefined);
  await page.locator('#field-execution_profile').selectOption('full_access');
  assert.equal(await page.locator('#field-full_access_acknowledgement').inputValue(),'');
  await page.locator('#field-execution_profile').selectOption('protected_manual');
  await page.locator('#importInput').setInputFiles({name:'unsafe-intake.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify({schema:'bootcrate-project-intake/v2',answers:{project_name:'Unsafe',execution_profile:'full_access'}}))});
  await page.waitForFunction(()=>document.querySelector('#inlineMessage').textContent.includes('current draft was preserved'));
  assert.equal(await page.locator('#field-execution_profile').inputValue(),'protected_manual');
  await page.locator('#inlineMessage').evaluate(element => { element.textContent=''; });
  await page.locator('#importInput').setInputFiles({name:'hidden-opt-in.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify({schema:'bootcrate-project-intake/v2',answers:{project_name:'Unsafe',execution_profile:'protected_auto',full_access_acknowledgement:'acknowledged'}}))});
  await page.waitForFunction(()=>document.querySelector('#importInput').value==='' &&
    document.querySelector('#inlineMessage').textContent.includes('current draft was preserved'));
  assert.equal(await page.locator('#field-execution_profile').inputValue(),'protected_manual');
  const old = {schema:'bootcrate-project-intake/v1',answers:{project_name:'Legacy',issues_tracking:'no',primary_orchestration:'local_planner'}};
  await page.locator('#importInput').setInputFiles({name:'legacy.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(old))});
  assert.equal(await page.locator('#legacyDialog').evaluate(e=>e.open),true);
  await page.locator('#cancelLegacyBtn').click();
  await page.getByRole('button',{name:'Project'}).click();
  assert.equal(await page.locator('#field-project_name').inputValue(),'Example');
  await page.locator('#importInput').setInputFiles({name:'legacy.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(old))});
  await page.locator('#confirmLegacyBtn').click();
  assert.equal(await page.locator('#field-project_name').inputValue(),'Legacy');
  assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('bootcrate-project-intake-v2')).answers.execution_profile),'protected_manual');
  await page.getByRole('button',{name:'Next steps'}).click();
  await page.locator('#repoInput').fill('https://github.com/owner/example.git');
  assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('bootcrate-project-intake-v2')).repository),'owner/example');
  const displayedRepository=await page.locator('#repoInput').inputValue();
  for(const repository of ['owner/.','owner/..']){
    await page.locator('#inlineMessage').evaluate(element => { element.textContent=''; });
    await page.locator('#importInput').setInputFiles({name:'invalid-repository.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify({
      schema:'bootcrate-project-intake/v2',repository,answers:{project_name:'Replaced'}
    }))});
    await page.waitForFunction(()=>document.querySelector('#importInput').value==='' &&
      document.querySelector('#inlineMessage').textContent.includes('current draft was preserved'));
    const draft=await page.evaluate(()=>JSON.parse(localStorage.getItem('bootcrate-project-intake-v2')));
    assert.equal(draft.repository,'owner/example');
    assert.equal(draft.answers.project_name,'Legacy');
    assert.equal(await page.locator('#repoInput').inputValue(),displayedRepository);
  }
  await page.reload();
  await page.getByRole('button',{name:'Next steps'}).click();
  assert.equal(await page.locator('#repoInput').inputValue(),'owner/example');
  assert.match(await page.locator('#instructionsOutput').inputValue(),/BootCrate v0\.9/);
  await page.close();
});

test('invalid repository edit clears the stored identity and exported intake',async () => {
  const page = await browser.newPage();
  await page.addInitScript(() => localStorage.setItem('bootcrate-project-intake-v2',JSON.stringify({answers:{
    project_name:'Example',one_sentence:'Synthetic project',project_kind:'cli_tool',existing_or_new:'new',
    success:'A working example',report_language:'pt-BR',repo_language:'en',distribution_mode:'none',
    single_or_team:'single',repository_state:'none',consumption_preset:'standard',
    execution_profile:'protected_manual',project_console:'no'
  }})));
  await page.goto(app);
  await page.getByRole('button',{name:'Next steps'}).click();
  await page.locator('#repoInput').fill('owner/valid');
  assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('bootcrate-project-intake-v2')).repository),'owner/valid');
  await page.locator('#repoInput').fill('owner/..');
  assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('bootcrate-project-intake-v2')).repository),'');
  assert.equal(await page.locator('#instructionsOutput').inputValue(),'');
  assert.match(await page.locator('#inlineMessage').innerText(),/valid GitHub repository/);
  const downloadPromise=page.waitForEvent('download');
  await page.getByRole('button',{name:'Download intake JSON'}).click();
  const download=await downloadPromise;
  let exported='';
  for await(const chunk of await download.createReadStream()) exported+=chunk;
  assert.equal(JSON.parse(exported).repository,undefined);
  await page.close();
});

test('Console local check handles a partial v3 distribution preview',async () => {
  const page = await browser.newPage(), errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto(consoleUrl);
  const partial={schema:'project-profile/v3',project:{name:'Example',kind:'static'},
    workflow:{tracking:'github_issues',primary_orchestrator:'chatgpt',implementation_harnesses:['codex']},
    versioning:{canonical_source:'VERSION',history_source:'CHANGELOG.md'},
    execution_permissions:{safe_default:'protected_manual'},skills:[]};
  await page.locator('#profile').setInputFiles({name:'partial.json',mimeType:'application/json',
    buffer:Buffer.from(JSON.stringify(partial))});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Profile imported'));
  await page.locator('#validateLocal').click();
  assert.match(await page.locator('#localCheck').innerText(),/Local preview incomplete/);
  assert.deepEqual(errors,[]);
  await page.close();
});

test('file-mode optional Console imports a profile without claiming remote proof',async () => {
  const page = await browser.newPage();
  await page.goto(consoleUrl);
  const profile={schema:'project-profile/v3',project:{name:'Example',kind:'static'},
    workflow:{tracking:'github_issues',primary_orchestrator:'chatgpt',consumption_preset:'standard',implementation_harnesses:['codex']},
    execution_permissions:{safe_default:'protected_manual'},
    versioning:{canonical_source:'VERSION',reader:'plain',history_source:'CHANGELOG.md',history_format:'markdown-headings'},distribution:{mode:'none',targets:[]},
    security:{exposure:'local',modules:[],control_map:'baseline'},validation:{canonical_capabilities:['test']},skills:[]};
  await page.locator('#profile').setInputFiles({name:'profile.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(profile))});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Profile imported'));
  assert.match(await page.locator('#status').innerText(),/local structural preview/);
  assert.equal(await page.locator('#executionSelect').inputValue(),'protected_manual');
  assert.match(await page.locator('.profileComparison').innerText(),/filesystem|Workspace/i);
  assert.match(await page.locator('.profileComparison').innerText(),/network/i);
  assert.match(await page.locator('.profileComparison').innerText(),/approval prompts/i);
  await page.locator('#presetOverride').setInputFiles({name:'preset.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify({schema:'bootcrate-preset-override/v1',preset:'economy'}))});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Consumption override imported'));
  assert.match(await page.locator('#details').innerText(),/Economy|economy/);
  assert.match(await page.locator('#details').innerText(),/Unknown until provider receipts/);
  const before=await page.locator('#details').innerText();
  await page.locator('#profile').setInputFiles({name:'bad.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify({...profile,skills:'not-an-array'}))});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Profile import failed'));
  assert.equal(await page.locator('#details').innerText(),before);
  assert.match(await page.locator('#status').innerText(),/Previous state was preserved/);
  await page.locator('#profile').setInputFiles({name:'machine-path.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify({...profile,security:{...profile.security,control_map:'C:\\synthetic\\controls'}}))});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Machine path'));
  assert.equal(await page.locator('#details').innerText(),before);
  await page.locator('#profile').setInputFiles({name:'malformed.json',mimeType:'application/json',buffer:Buffer.from('{')});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Profile import failed'));
  assert.equal(await page.locator('#details').innerText(),before);
  const cancelStatus=await page.locator('#status').innerText();
  await page.locator('#profile').setInputFiles([]);
  assert.equal(await page.locator('#status').innerText(),cancelStatus);
  await page.locator('#presetOverride').setInputFiles({name:'large.json',mimeType:'application/json',buffer:Buffer.alloc(1024*1024+1,32)});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('exceeds 1 MiB'));
  assert.equal(await page.locator('#details').innerText(),before);
  await page.evaluate(()=>{document.querySelector('#details').replaceChildren=()=>{throw new Error('synthetic render failure');};});
  await page.locator('#presetOverride').setInputFiles({name:'preset.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify({schema:'bootcrate-preset-override/v1',preset:'standard'}))});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('synthetic render failure'));
  await page.evaluate(()=>{delete document.querySelector('#details').replaceChildren;});
  assert.equal(await page.locator('#details').innerText(),before);
  await page.locator('#executionOverride').setInputFiles({name:'execution-profile.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify({schema:'bootcrate-execution-profile-override/v1',profile:'full_access'}))});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Execution override import failed'));
  assert.match(await page.locator('#status').innerText(),/risk acknowledgement/);
  assert.equal(await page.locator('#details').innerText(),before);
  await page.locator('#executionOverride').setInputFiles({name:'execution-profile.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify({schema:'bootcrate-execution-profile-override/v1',profile:'protected_auto'}))});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Execution override imported'));
  assert.match(await page.locator('#details').innerText(),/protected_auto \(local\)/);
  await page.locator('#clearExecution').click();
  assert.match(await page.locator('#details').innerText(),/protected_manual \(safe_default\)/);
  assert.match(await page.locator('#details').innerText(),/economy \(local\)/i);
  await page.locator('#executionSelect').selectOption('full_access');
  await page.locator('#exportExecution').click();
  assert.match(await page.locator('#status').innerText(),/risk acknowledgement/);
  await page.locator('#fullRisk').check();
  const executionDownload=page.waitForEvent('download');
  await page.locator('#exportExecution').click();
  const execution=await executionDownload;
  assert.equal(execution.suggestedFilename(),'execution-profile.json');
  await page.locator('#history').setInputFiles({name:'CHANGELOG.md',mimeType:'text/markdown',buffer:Buffer.from('# Changelog\n    ## v1.2 — Code block\n')});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('History import failed'));
  assert.match(await page.locator('#status').innerText(),/No unique version headings found/);
  await page.locator('#history').setInputFiles({name:'CHANGELOG.md',mimeType:'text/markdown',buffer:Buffer.from('# Changelog\n  ## v1.2 — Search\n- Added search.\n')});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Version headings imported'));
  assert.match(await page.locator('#historyNotes').innerText(),/^v1.2 — Search/m);
  await page.locator('#history').setInputFiles({name:'CHANGELOG.md',mimeType:'text/markdown',buffer:Buffer.from('# Changelog\nv1.2 Setext release\n---\n')});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Version headings imported'));
  assert.match(await page.locator('#historyNotes').innerText(),/^v1.2 Setext release/m);
  for(const marker of ['```markdown','~~~markdown']){
    const close=marker.slice(0,3);
    await page.locator('#history').setInputFiles({name:'CHANGELOG.md',mimeType:'text/markdown',buffer:Buffer.from(`# Changelog\n${marker}\nv1.2 Fenced example\n---\n${close}\n`)});
    await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('History import failed'));
    assert.match(await page.locator('#status').innerText(),/No unique version headings found/);
    assert.match(await page.locator('#historyNotes').innerText(),/^v1.2 Setext release/m);
  }
  await page.locator('#history').setInputFiles({name:'CHANGELOG.md',mimeType:'text/markdown',buffer:Buffer.from('# Changelog\n## v1.2 ATX release\nv1.2 Setext release\n---\n')});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('History import failed'));
  assert.match(await page.locator('#status').innerText(),/No unique version headings found/);
  assert.match(await page.locator('#historyNotes').innerText(),/^v1.2 Setext release/m);
  await page.locator('#validateLocal').click();
  assert.match(await page.locator('#localCheck').innerText(),/canonical version source file/);
  await page.locator('#version').setInputFiles({name:'VERSION',mimeType:'text/plain',buffer:Buffer.from('1.2\n')});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Version source imported'));
  assert.match(await page.locator('#details').innerText(),/1\.2/);
  await page.locator('#preflight').setInputFiles({name:'preflight.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify([{destination:'web',channel:'stable',status:'READY',notes:'New release'},{destination:'store',channel:'stable',status:'BLOCK',reason:'Unknown baseline'}]))});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Preflight imported'));
  assert.match(await page.locator('#status').innerText(),/Preflight imported/);
  assert.match(await page.locator('#notes').innerText(),/web \/ stable: READY/);
  assert.match(await page.locator('#notes').innerText(),/store \/ stable: BLOCK/);
  const completeDetails=await page.locator('#details').innerText(),completeHistory=await page.locator('#historyNotes').innerText(),completeNotes=await page.locator('#notes').innerText();
  await page.locator('#profile').setInputFiles({name:'bad-again.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify({...profile,workflow:{...profile.workflow,implementation_harnesses:'codex'}}))});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Profile import failed'));
  assert.equal(await page.locator('#details').innerText(),completeDetails);
  assert.equal(await page.locator('#historyNotes').innerText(),completeHistory);
  assert.equal(await page.locator('#notes').innerText(),completeNotes);
  const snapshotDownload=page.waitForEvent('download');
  await page.locator('#exportSnapshot').click();
  const snapshot=await snapshotDownload;
  const snapshotText=await require('node:fs/promises').readFile(await snapshot.path(),'utf8');
  const parsed=JSON.parse(snapshotText);
  assert.equal(parsed.schema,'bootcrate-console-snapshot/v2');
  assert.equal(parsed.remote_state,'not_observed');
  assert.equal(parsed.execution[0].effective,null);
  assert.equal(parsed.execution[0].requested,'protected_manual');
  assert.deepEqual(parsed.skills,[]);
  assert.deepEqual(parsed.canonical_capabilities,['test']);
  assert.equal(parsed.control_summary.control_map,'baseline');
  assert.deepEqual(parsed.version,{source:'VERSION'});
  assert.equal(snapshotText.includes('"imported"'),false);
  assert.equal(parsed.profile,undefined);
  assert.equal(parsed.code,undefined);
  const jsonProfile={...profile,versioning:{canonical_source:'package.json',reader:'json',value_path:'/meta/release~1version',history_source:'HISTORY.md',history_format:'markdown-headings'}};
  await page.locator('#profile').setInputFiles({name:'json-profile.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(jsonProfile))});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Profile imported'));
  await page.locator('#version').setInputFiles({name:'package.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify({meta:{'release/version':'2.3'}}))});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Version source imported'));
  assert.match(await page.locator('#details').innerText(),/2\.3/);
  await page.locator('#history').setInputFiles({name:'HISTORY.md',mimeType:'text/markdown',buffer:Buffer.from('# History\n   ## [v2.3] Release\n')});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Version headings imported'));
  assert.match(await page.locator('#historyNotes').innerText(),/v2\.3/);
  const validJsonDetails=await page.locator('#details').innerText(),validJsonHistory=await page.locator('#historyNotes').innerText();
  for(const number of ['9007199254740993','1.0','2']) {
    await page.locator('#version').setInputFiles({name:'package.json',mimeType:'application/json',
      buffer:Buffer.from('{"meta":{"release/version":'+number+'}}')});
    await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Numeric JSON version requires native validation'));
    assert.match(await page.locator('#status').innerText(),/Previous state was preserved/);
    assert.equal(await page.locator('#details').innerText(),validJsonDetails);
  }
  await page.locator('#version').setInputFiles({name:'package.json',mimeType:'application/json',buffer:Buffer.from('{"meta":{"release/version":1e400}}')});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Version value must be a finite scalar'));
  assert.match(await page.locator('#status').innerText(),/Previous state was preserved/);
  assert.equal(await page.locator('#details').innerText(),validJsonDetails);
  assert.equal(await page.locator('#historyNotes').innerText(),validJsonHistory);
  await page.locator('#version').setInputFiles({name:'package.json',mimeType:'application/json',buffer:Buffer.from('{"meta":{}}')});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Version value path not found'));
  assert.equal(await page.locator('#details').innerText(),validJsonDetails);
  assert.equal(await page.locator('#historyNotes').innerText(),validJsonHistory);
  const tomlProfile={...profile,versioning:{canonical_source:'pyproject.toml',reader:'toml',history_source:'HISTORY.md',history_format:'markdown-headings'}};
  await page.locator('#profile').setInputFiles({name:'toml-profile.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(tomlProfile))});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Profile imported'));
  const beforeUnsupported=await page.locator('#details').innerText();
  await page.locator('#version').setInputFiles({name:'pyproject.toml',mimeType:'text/plain',buffer:Buffer.from('[project]\nversion="2.4"\n')});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes("Reader 'toml' is not supported"));
  assert.match(await page.locator('#status').innerText(),/Previous state was preserved/);
  assert.equal(await page.locator('#details').innerText(),beforeUnsupported);
  const legacyProfile={schema:'project-profile/v2',project:{name:'Legacy profile',kind:'cli'},workflow:{tracking:'github_issues',primary_orchestrator:'chatgpt',implementation_harnesses:['codex']},versioning:{canonical_source:'VERSION'}};
  await page.locator('#profile').setInputFiles({name:'legacy-profile.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(legacyProfile))});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Profile imported'));
  assert.match(await page.locator('#details').innerText(),/Legacy profile/);
  assert.match(await page.locator('#details').innerText(),/protected_manual \(safe_default\)/);
  await page.close();
});

test('file-mode Console rejects sensitive profile sources and preserves its previous view',async () => {
  const page=await browser.newPage();
  await page.goto(consoleUrl);
  const profile={schema:'project-profile/v3',project:{name:'Safe preview',kind:'static'},
    workflow:{tracking:'github_issues',primary_orchestrator:'chatgpt',implementation_harnesses:['codex']},
    execution_permissions:{safe_default:'protected_manual'},
    versioning:{canonical_source:'VERSION',reader:'plain',history_source:'CHANGELOG.md',history_format:'markdown-headings'}};
  const select=async value=>page.locator('#profile').setInputFiles({
    name:'profile.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(value))});
  await select(profile);
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Profile imported'));
  await page.locator('#version').setInputFiles({name:'VERSION',mimeType:'text/plain',buffer:Buffer.from('1.2\n')});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Version source imported'));
  const before=await page.locator('#details').innerText();
  for(const source of ['credentials.json','config/secrets.json','config/.env.production','config/PRIVATE.KEY',
    'config/id_ed25519','config/cert.p12','config/cert.pfx']) {
    await page.evaluate(()=>{document.querySelector('#status').textContent='pending';});
    await select({...profile,versioning:{...profile.versioning,canonical_source:source}});
    await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Profile import failed: Unsafe version source'));
    assert.match(await page.locator('#status').innerText(),/Previous state was preserved/);
    assert.equal(await page.locator('#details').innerText(),before);
  }
  for(const historySource of ['secrets.md','config/credentials.json','config/.env.production']) {
    await page.evaluate(()=>{document.querySelector('#status').textContent='pending';});
    await select({...profile,versioning:{...profile.versioning,history_source:historySource}});
    await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Profile import failed: Unsafe history source'));
    assert.equal(await page.locator('#details').innerText(),before);
  }
  for(const example of ['.env.example','config/secrets.example.json','config/credentials.example.json']) {
    await page.evaluate(()=>{document.querySelector('#status').textContent='pending';});
    await select({...profile,versioning:{...profile.versioning,canonical_source:example}});
    await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Profile imported'));
    assert.match(await page.locator('#details').innerText(),/Safe preview/);
  }
  await page.close();
});

test('file-mode Console keeps limited v2 version previews without inventing v3 metadata',async () => {
  const page=await browser.newPage();
  await page.goto(consoleUrl);
  const profile={schema:'project-profile/v2',project:{name:'Legacy profile',kind:'cli'},
    workflow:{tracking:'github_issues',primary_orchestrator:'chatgpt',implementation_harnesses:['codex']},
    versioning:{canonical_source:'VERSION'},security:{exposure:'local',control_map:'baseline'}};
  const selectProfile=async value=>{
    await page.locator('#profile').setInputFiles({name:'profile.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(value))});
    await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Profile imported'));
  };
  await selectProfile(profile);
  await page.locator('#version').setInputFiles({name:'VERSION',mimeType:'text/plain',buffer:Buffer.from('1.2\n')});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Version source imported'));
  assert.match(await page.locator('#details').innerText(),/1\.2/);
  await page.locator('#validateLocal').click();
  assert.match(await page.locator('#localCheck').innerText(),/v2 declares no reader or history source/);
  assert.doesNotMatch(await page.locator('#localCheck').innerText(),/incomplete|CHANGELOG\.md/);
  assert.match(await page.locator('#localCheck').innerText(),/native checks/);

  await selectProfile({...profile,versioning:{canonical_source:'package.json'}});
  await page.locator('#version').setInputFiles({name:'package.json',mimeType:'application/json',buffer:Buffer.from('{"name":"legacy","version":"2.3"}')});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('Version source imported'));
  assert.match(await page.locator('#details').innerText(),/2\.3/);

  await selectProfile({...profile,versioning:{canonical_source:'pyproject.toml'}});
  const before=await page.locator('#details').innerText();
  await page.locator('#version').setInputFiles({name:'pyproject.toml',mimeType:'text/plain',buffer:Buffer.from('[project]\nversion="3.2"\n')});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('cannot be interpreted'));
  assert.match(await page.locator('#status').innerText(),/use native validation.*Previous state was preserved/);
  assert.equal(await page.locator('#details').innerText(),before);
  await page.locator('#validateLocal').click();
  assert.match(await page.locator('#localCheck').innerText(),/readable canonical version source file/);
  assert.match(await page.locator('#localCheck').innerText(),/v2 declares no reader or history source/);
  assert.doesNotMatch(await page.locator('#localCheck').innerText(),/CHANGELOG\.md/);
  await page.close();
});
