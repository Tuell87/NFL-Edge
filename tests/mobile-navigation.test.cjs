const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const home=fs.readFileSync('index.html','utf8');
const matchups=fs.readFileSync('matchups.html','utf8');
const players=fs.readFileSync('players.html','utf8');
const history=fs.readFileSync('history.html','utf8');
test('five mobile sections use accessible tab and panel semantics',()=>{
 for(const id of ['games','players','odds','research','project']){
  assert.match(home,new RegExp('role="tab" id="tab-'+id+'" aria-controls="panel-'+id+'"'));
  assert.match(home,new RegExp('role="tabpanel" id="panel-'+id+'" aria-labelledby="tab-'+id+'"'));
 }
 assert.equal((home.match(/role="tab" id=/g)||[]).length,5);
 assert.match(home,/overflow-x:auto/);
});
test('tab selection supports direct links, keyboard and hidden panels',()=>{
 assert.match(home,/location.hash.slice\(1\)/);
 assert.match(home,/ArrowRight/);
 assert.match(home,/ArrowLeft/);
 assert.match(home,/aria-selected/);
 assert.match(home,/panel.hidden=!active/);
});
test('homepage keeps all research and calculator destinations',()=>{
 for(const name of ['dashboard','odds','players','history','matchups','workbench','market','opponent-seasons','opponent-rolling','roster-quality','feed-integrity'])
  assert.ok(home.includes('href="./'+name+'.html"'),name);
});
test('game filters are interactive and do not create extra cards',()=>{
 for(const id of ['all','scheduled','live','final'])assert.match(home,new RegExp('data-filter="'+id+'"'));
 assert.match(home,/function renderGames\(/);
 assert.match(home,/aria-pressed/);
});
test('matchups are searchable, filtered, and expandable without injected HTML',()=>{
 assert.match(matchups,/id="search"/);
 assert.match(matchups,/id="market"/);
 assert.match(matchups,/id="quality"/);
 assert.match(matchups,/aria-expanded/);
 assert.match(matchups,/rows\.filter/);
 assert.doesNotMatch(matchups,/innerHTML\s*=/);
});
test('player and historical pages return to main navigation tabs',()=>{
 assert.match(players,/href="\.\/#players"/);
 assert.match(history,/href="\.\/#players"/);
});
test('no browser-side API key or external scripts added',()=>{
 assert.doesNotMatch(home+matchups,/api\.the-odds-api\.com|localStorage|<script[^>]+src=/);
});
