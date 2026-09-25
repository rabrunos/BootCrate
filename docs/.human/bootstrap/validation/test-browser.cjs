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
  await page.getByRole('button',{name:'Continue'}).click();
  assert.equal(await page.locator('#field-project_name').getAttribute('aria-invalid'),'true');
  assert.match(await page.locator('#errorSummary').innerText(),/required/);
  await page.locator('#field-project_name').fill('Example');
  assert.equal(await page.locator('#field-project_name').getAttribute('aria-invalid'),null);
  await page.locator('#modeSelect').selectOption('detailed');
  assert.equal(await page.locator('#field-project_name').inputValue(),'Example');
  await page.locator('#modeSelect').selectOption('basic');
  assert.equal(await page.locator('#field-project_name').inputValue(),'Example');
  const old = {schema:'bootcrate-project-intake/v1',answers:{project_name:'Legacy',issues_tracking:'no',primary_orchestration:'local_planner'}};
  await page.locator('#importInput').setInputFiles({name:'legacy.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(old))});
  assert.equal(await page.locator('#legacyDialog').evaluate(e=>e.open),true);
  await page.locator('#cancelLegacyBtn').click();
  assert.equal(await page.locator('#field-project_name').inputValue(),'Example');
  await page.locator('#importInput').setInputFiles({name:'legacy.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(old))});
  await page.locator('#confirmLegacyBtn').click();
  assert.equal(await page.locator('#field-project_name').inputValue(),'Legacy');
  await page.close();
});

test('file-mode optional Console imports a profile without claiming remote proof',async () => {
  const page = await browser.newPage();
  await page.goto(consoleUrl);
  const profile={schema:'project-profile/v3',project:{name:'Example',kind:'static'},
    workflow:{tracking:'github_issues',primary_orchestrator:'chatgpt',consumption_preset:'economy',implementation_harnesses:['codex']},
    versioning:{canonical_source:'VERSION'},distribution:{mode:'none'}};
  await page.locator('#profile').setInputFiles({name:'profile.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(profile))});
  assert.match(await page.locator('#details').innerText(),/Economy|economy/);
  assert.match(await page.locator('#details').innerText(),/Unknown until provider receipts/);
  assert.match(await page.locator('#status').innerText(),/local structural preview/);
  await page.locator('#history').setInputFiles({name:'CHANGELOG.md',mimeType:'text/markdown',buffer:Buffer.from('# Changelog\n## v1.2 — Search\n- Added search.\n')});
  assert.match(await page.locator('#historyNotes').innerText(),/v1.2 — Search/);
  await page.locator('#validateLocal').click();
  assert.match(await page.locator('#localCheck').innerText(),/canonical version source file/);
  await page.locator('#preflight').setInputFiles({name:'preflight.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify([{destination:'web',channel:'stable',status:'READY',notes:'New release'},{destination:'store',channel:'stable',status:'BLOCK',reason:'Unknown baseline'}]))});
  assert.match(await page.locator('#notes').innerText(),/web \/ stable: READY/);
  assert.match(await page.locator('#notes').innerText(),/store \/ stable: BLOCK/);
  await page.close();
});
