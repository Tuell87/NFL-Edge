const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');
const html=fs.readFileSync('evaluation.html','utf8');const home=fs.readFileSync('home-next.html','utf8');const workflow=fs.readFileSync('.github/workflows/pages.yml','utf8');
test('evaluation mobile viewport',()=>assert.match(html,/name="viewport"/));
test('uses published evaluation data',()=>assert.match(html,/data\/evaluation\.json/));
test('no claims of validated predictions',()=>assert.match(html,/not a validated prediction system/));
test('safe DOM rendering',()=>assert.doesNotMatch(html,/innerHTML/));
test('game day links evaluation',()=>assert.match(home,/href="\.\/evaluation\.html"/));
test('evaluation runs on deploy',()=>assert.match(workflow,/python3 scripts\/evaluate_baseline\.py/));
test('evaluation JSON published',()=>assert.match(workflow,/cp data\/evaluation\.json _site\/data\/evaluation\.json/));
