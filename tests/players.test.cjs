const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');
const html=fs.readFileSync('players.html','utf8');const home=fs.readFileSync('home-next.html','utf8');const workflow=fs.readFileSync('.github/workflows/pages.yml','utf8');
test('mobile player page',()=>assert.match(html,/name="viewport"/));
test('player page uses published JSON',()=>assert.match(html,/data\/players\.json/));
test('not falsely represented as forecasts',()=>assert.match(html,/not player forecasts/));
test('safe text rendering',()=>assert.doesNotMatch(html,/innerHTML/));
test('home links to player stats',()=>assert.match(home,/href="\.\/players\.html"/));
test('collector runs on deploy',()=>assert.match(workflow,/python3 scripts\/fetch_players\.py/));
test('player JSON published',()=>assert.match(workflow,/cp data\/players\.json _site\/data\/players\.json/));
