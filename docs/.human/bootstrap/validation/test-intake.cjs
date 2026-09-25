const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const app = path.join(__dirname, '../app');
const Core = require(path.join(app, 'intake-core.js'));
const Handoff = require(path.join(app, 'setup-handoff.js'));
const Guidance = require(path.join(app, 'guidance.js'));
const Preset = require(path.join(app, 'preset.js'));
const Execution = require(path.join(app, 'execution-profile.js'));
const scope = {window:{}};
vm.runInNewContext(fs.readFileSync(path.join(app,'questions.js'),'utf8'),scope);
const Q = JSON.parse(JSON.stringify(scope.window.BOOTCRATE_QUESTIONS));
const core = Core.create(Q);
const envelope = answers => ({schema:Core.SCHEMA,answers});

test('empty intake is a valid draft but cannot satisfy required fields',()=>{
  assert.equal(core.validate(envelope({})).length,0);
  assert.ok(core.missing({}).length>0);
});
test('whitespace does not satisfy a required answer',()=>{
  assert.ok(core.missing({project_name:'  '}).some(q=>q.id==='project_name'));
});
test('unknown id and wrong enum are rejected',()=>{
  assert.ok(core.validate(envelope({unknown_question:'x'})).length);
  assert.ok(core.validate(envelope({project_kind:'invented'})).length);
});
test('language/session must be typed before import can alter state',()=>{
  assert.ok(core.validate({...envelope({}),language:42}).length);
  assert.ok(core.validate({...envelope({}),session:'invalid'}).length);
  assert.throws(()=>core.normalize({...envelope({}),language:42}));
});
test('prototype-shaped answer keys are unknown data',()=>{
  const input=JSON.parse('{"schema":"'+Core.SCHEMA+'","answers":{"__proto__":{"polluted":true}}}');
  assert.ok(core.validate(input).length);
  assert.equal({}.polluted,undefined);
});
test('conditional answers disappear and do not leak through a child',()=>{
  const answers={existing_or_new:'new',external_integration:'no',external_product_name:'Synthetic game',community_tool_known:'yes',community_tool_value:'Loader'};
  const out=core.exportAnswers(answers);
  assert.equal(out.external_product_name,undefined);
  assert.equal(out.community_tool_value,undefined);
});
test('unknown and not applicable remain distinct from an empty optional text answer',()=>{
  const data={...envelope({project_name:'Example'}),answer_states:{known_risks:'unknown',must_avoid_tools:'not_applicable'}};
  assert.equal(core.validate(data).length,0);
  const normalized=core.normalize(data);
  assert.equal(normalized.states.known_risks,'unknown');
  assert.equal(normalized.states.must_avoid_tools,'not_applicable');
  assert.deepEqual(core.exportStates(normalized.states,normalized.answers),data.answer_states);
  assert.ok(core.validate({...data,answers:{known_risks:'Already known'}}).length);
  assert.ok(core.validate({...data,answer_states:{project_name:'unknown'}}).length);
  assert.ok(core.validate({...data,answer_states:{__proto__:'unknown',unrecognized:'unknown'}}).length);
});
test('visible known answers remain and normalization trims text',()=>{
  const source=envelope({project_name:'  Example  ',existing_or_new:'existing_code',external_integration:'yes',external_product_name:'Game'});
  assert.equal(core.normalize(source).answers.project_name,'Example');
  assert.equal(core.exportAnswers(source.answers).external_product_name,'Game');
});
test('duplicate multiselect items and wrong types are rejected',()=>{
  assert.ok(core.validate(envelope({target_platforms:['windows','windows']})).length);
  assert.ok(core.validate(envelope({project_name:['not a string']})).length);
});
test('oversized text is rejected, not silently omitted',()=>{
  assert.ok(core.validate(envelope({project_name:'a'.repeat(Core.MAX_TEXT+1)})).length);
  assert.throws(()=>core.exportAnswers({project_name:'a'.repeat(Core.MAX_TEXT+1)}));
});
test('HTML-like text stays text; validation never evaluates it',()=>{
  const data=envelope({one_sentence:'<img src=x onerror="globalThis.pwned=true">'});
  assert.equal(core.validate(data).length,0);
  assert.equal(core.normalize(data).answers.one_sentence,data.answers.one_sentence);
  assert.equal(globalThis.pwned,undefined);
});
test('question metadata cycles are rejected',()=>{
  assert.throws(()=>Core.create([{id:'a',condition:{id:'b',in:['yes']}},{id:'b',condition:{id:'a',in:['yes']}}]));
});
test('handoff parses only supported GitHub repository forms',()=>{
  assert.equal(Handoff.parseRepository('owner/project'),'owner/project');
  assert.equal(Handoff.parseRepository('owner/project.git'),'owner/project');
  assert.equal(Handoff.parseRepository('https://github.com/owner/project'),'owner/project');
  assert.equal(Handoff.parseRepository('javascript:alert(1)'),'');
  assert.equal(Handoff.parseRepository('https://example.com/owner/project'),'');
});
test('GitHub creation URL does not pretend this repository is configured as a template',()=>{
  const url=new URL(Handoff.githubCreateUrl({name:'My Project <x>',description:'Example',visibility:'private'}));
  assert.equal(url.origin,'https://github.com');
  assert.equal(url.pathname,'/new');
  assert.equal(url.searchParams.get('template_owner'),null);
  assert.equal(url.searchParams.get('template_name'),null);
  assert.equal(url.searchParams.get('name'),'my-project-x');
  assert.equal(url.searchParams.get('visibility'),'private');
  assert.equal(url.searchParams.get('token'),null);
});
test('Project instructions route through stable PROJECT_GUIDE only',()=>{
  const text=Handoff.projectInstructions('owner/project');
  assert.match(text,/PROJECT_GUIDE\.md/);
  assert.match(text,/BootCrate v0\.9/);
  assert.equal(Handoff.BOOTSTRAP_SOURCE.repository,'https://github.com/rabrunos/BootCrate');
  assert.match(Handoff.projectInstructions('owner/project','existing','protected_auto'),/requested by the intake: protected_auto/);
  assert.match(Handoff.projectInstructions('owner/project'),/Effective permissions: not observed/);
  assert.doesNotMatch(text,/docs\/.ai\/TASK_POLICY|AGENTS\.md|CLAUDE\.md/);
  assert.match(Handoff.projectInstructions('owner/project','empty'),/materialize/);
  assert.match(Handoff.projectInstructions('owner/project','existing'),/if it is absent/);
});
test('repository identity and bootstrap source are typed envelope fields',()=>{
  const data={...envelope({}),repository:'owner/project',bootstrap_source:Handoff.BOOTSTRAP_SOURCE};
  assert.equal(core.validate(data).length,0);
  assert.equal(core.normalize(data).repository,'owner/project');
  assert.ok(core.validate({...data,repository:'https://github.com/owner/project'}).length);
  assert.ok(core.validate({...data,repository:'owner/project.git'}).length);
  assert.ok(core.validate({...data,bootstrap_source:{product:'BootCrate'}}).length);
});
test('app includes pure helpers before execution and keeps questions data-driven',()=>{
  const html=fs.readFileSync(path.join(app,'index.html'),'utf8');
  assert.ok(html.indexOf('intake-core.js')<html.indexOf('src="app.js"'));
  assert.ok(html.indexOf('setup-handoff.js')<html.indexOf('src="app.js"'));
  assert.ok(html.indexOf('guidance.js')<html.indexOf('src="app.js"'));
  assert.ok(html.indexOf('preset.js')<html.indexOf('src="app.js"'));
  assert.ok(html.indexOf('execution-profile.js')<html.indexOf('src="app.js"'));
  const byId=new Map(Q.map(q=>[q.id,q]));
  for(const id of ['existing_or_new','external_integration','repository_state','distribution_mode','consumption_preset','execution_profile','project_console'])assert.ok(byId.has(id));
  for(const id of ['issues_tracking','primary_orchestration','agent_budget'])assert.ok(!byId.has(id));
  assert.deepEqual(byId.get('consumption_preset').options.map(o=>o[0]),['standard','economy']);
  assert.deepEqual(byId.get('execution_profile').options.map(o=>o[0]),Execution.ids);
  assert.ok(byId.get('execution_profile').option_details.full_access.en.includes('Highest risk'));
});
test('legacy intake requires visible confirmation of conflicts, not silent acceptance',()=>{
  const result=core.upgradeLegacy({schema:'bootcrate-project-intake/v1',answers:{
    project_name:'Example',existing_or_new:'external_target',issues_tracking:'no',
    primary_orchestration:'local_planner',agent_budget:'main_worker_scout'}});
  assert.ok(result.conflicts.includes('github_issues_required'));
  assert.ok(result.conflicts.includes('chatgpt_primary_required'));
  assert.equal(result.converted.answers.existing_or_new,'unknown');
  assert.equal(result.converted.answers.external_integration,'yes');
  assert.equal(result.converted.answers.consumption_preset,undefined);
  assert.equal(result.converted.answers.execution_profile,'protected_manual');
  assert.throws(()=>core.upgradeLegacy({schema:'bootcrate-project-intake/v1',answers:{unrecognized:'x'}}));
  assert.throws(()=>core.upgradeLegacy({schema:'bootcrate-project-intake/v1',answers:{issues_tracking:'skip'}}));
});
test('offline guidance cannot turn owner entry into observed access or checks',()=>{
  const result=Guidance.resolve({project_name:'Example',one_sentence:'A product',repository_state:'existing'});
  assert.equal(result.items.find(x=>x.id==='intent').status,'satisfied');
  assert.equal(result.items.find(x=>x.id==='remote_access').status,'unknown');
  assert.equal(result.items.find(x=>x.id==='checks').status,'unknown');
  const stale=Guidance.resolve({}, {checks:{status:'satisfied',source:'tool_observed',freshness:'current',basis:'old'}}, 'new');
  assert.equal(stale.items.find(x=>x.id==='checks').status,'unknown');
});
test('old v2 intake defaults safely without inferring permissions from autonomy',()=>{
  const normalized=core.normalize(envelope({autonomy:'high',consumption_preset:'economy'}));
  assert.equal(normalized.answers.execution_profile,'protected_manual');
});
test('execution profiles have task/local/default precedence and Full Access acknowledgement',()=>{
  assert.deepEqual(Execution.resolve({task:'protected_manual',local:'protected_auto'}),{requested:'protected_manual',source:'task'});
  assert.deepEqual(Execution.resolve({local:'protected_auto'}),{requested:'protected_auto',source:'local'});
  assert.deepEqual(Execution.resolve(),{requested:'protected_manual',source:'safe_default'});
  assert.throws(()=>Execution.parseOverride({schema:'bootcrate-execution-profile-override/v1',profile:'full_access'}));
  assert.throws(()=>Execution.parseOverride({schema:'bootcrate-execution-profile-override/v1',profile:'protected_manual',unexpected:true}));
  assert.equal(Execution.parseOverride({schema:'bootcrate-execution-profile-override/v1',profile:'full_access',risk_acknowledged:true}).profile,'full_access');
  assert.ok(core.missing({execution_profile:'full_access'}).some(q=>q.id==='full_access_acknowledgement'));
  assert.ok(!core.active({execution_profile:'protected_manual'}).some(q=>q.id==='full_access_acknowledgement'));
});
test('guidance enforces applicability, authority, basis and permissions',()=>{
  const basis={repository:'owner/project',commit:'a'.repeat(40),scope:'issue-12'};
  const evidence=Object.fromEntries(Guidance.requirements.map(req=>[req.id,{
    status:'satisfied',source:['intent','repository','decisions','scope','acceptance'].includes(req.id)?'owner_confirmed':'tool_observed',
    freshness:'current',basis,permissions:req.id==='remote_access'?'verified':undefined
  }]));
  assert.equal(Guidance.resolve({distribution_mode:'artifact'},evidence,basis).readiness,'accepted');

  const allNa=Object.fromEntries(Guidance.requirements.map(req=>[req.id,{
    status:'not_applicable',source:'agent_declared',freshness:'stale',basis
  }]));
  assert.equal(Guidance.resolve({distribution_mode:'none'},allNa,basis).readiness,'pending');

  const missingBasis=structuredClone(evidence);delete missingBasis.checks.basis;
  assert.equal(Guidance.resolve({distribution_mode:'artifact'},missingBasis,basis).items.find(x=>x.id==='checks').reason,'evidence_basis_missing_or_divergent');
  const changed={...basis,repository:'other/project'};
  assert.equal(Guidance.resolve({distribution_mode:'artifact'},evidence,changed).readiness,'pending');

  const unknownPermissions=structuredClone(evidence);unknownPermissions.remote_access.permissions='unknown';
  assert.equal(Guidance.resolve({distribution_mode:'artifact'},unknownPermissions,basis).items.find(x=>x.id==='remote_access').reason,'permissions_not_verified');
  const agentAcceptance=structuredClone(evidence);agentAcceptance.acceptance.source='agent_declared';
  assert.equal(Guidance.resolve({distribution_mode:'artifact'},agentAcceptance,basis).items.find(x=>x.id==='acceptance').reason,'evidence_source_insufficient');

  const legitimate=structuredClone(evidence);
  legitimate.distribution={status:'not_applicable',source:'owner_confirmed',freshness:'current',waiver:{reason:'no_distribution_selected'}};
  assert.equal(Guidance.resolve({distribution_mode:'none'},legitimate,basis).readiness,'accepted');
  legitimate.distribution.source='agent_declared';
  assert.equal(Guidance.resolve({distribution_mode:'none'},legitimate,basis).readiness,'pending');
  assert.equal(Guidance.resolve({distribution_mode:'none'},legitimate,basis).readiness_levels.behavior,'pending');
});
test('economy never lowers Main effort, and overrides have explicit precedence',()=>{
  assert.deepEqual(Preset.resolve({task:'economy',local:'standard',project:'standard'}),{preset:'economy',source:'task'});
  assert.deepEqual(Preset.resolve({local:'economy',project:'standard'}),{preset:'economy',source:'local'});
  assert.equal(Preset.effort('E3'), 'xhigh');
  assert.equal(Preset.effort('E1',false),'high');
  assert.throws(()=>Preset.resolve({local:'free'}));
});
