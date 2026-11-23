const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');
const html=fs.readFileSync('history.html','utf8');const home=fs.readFileSync('home-next.html','utf8');const workflow=fs.readFileSync('.github/workflows/pages.yml','utf8');
test('history mobile viewport',()=>assert.match(html,/name="viewport"/));
test('uses compact static history search JSON',()=>assert.match(html,/data\/history_search\.json/));
test('not represented as projections',()=>assert.match(html,/Not season totals, projections/));
test('safe text rendering',()=>assert.doesNotMatch(html,/innerHTML/));
test('home links to history',()=>assert.match(home,/href="\.\/history\.html"/));
test('collector runs',()=>assert.match(workflow,/python3 scripts\/fetch_history\.py/));
test('compact history snapshot deployed',()=>assert.match(workflow,/cp data\/history_search\.json _site\/data\/history_search\.json/));
