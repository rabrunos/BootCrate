const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const app = path.join(__dirname, '../app');
const Core = require(path.join(app, 'intake-core.js'));
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
  const answers={existing_or_new:'new',external_product_name:'Synthetic game',community_tool_known:'yes',community_tool_value:'Loader'};
  const out=core.exportAnswers(answers);
  assert.equal(out.external_product_name,undefined);
  assert.equal(out.community_tool_value,undefined);
});
test('visible known answers remain and normalization trims text',()=>{
  const source=envelope({project_name:'  Example  ',existing_or_new:'external_target',external_product_name:'Game'});
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
test('app includes core before execution and no question changes are required',()=>{
  const html=fs.readFileSync(path.join(app,'index.html'),'utf8');
  assert.ok(html.indexOf('intake-core.js')<html.indexOf('src="app.js"'));
  assert.ok(Q.length>50);
});
