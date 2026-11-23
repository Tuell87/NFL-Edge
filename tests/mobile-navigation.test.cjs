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
 const html = (home+matchups).replace('<script src="./search-choices.js"></script>', '');
 assert.doesNotMatch(html,/api\.the-odds-api\.com|localStorage|<script[^>]+src=/);
});

test('matchup pagination can reach records beyond the old 60-row cap', async () => {
 const vm = require('node:vm');
 function element() {
  return {
   value: '', children: [], handlers: {},
   append(...children) { this.children.push(...children); },
   replaceChildren(...children) { this.children = children; },
   addEventListener(type, handler) { this.handlers[type] = handler; },
   setAttribute() {},
   focus() { this.focused = true; },
  };
 }
 const elements = Object.fromEntries(['list', 'search', 'market', 'quality', 'status', 'pagination', 'previous', 'next']
  .map(id => [id, element()]));
 elements['search-choice'] = Object.assign(element(), {dataset: {defaultLabel: 'All players and teams'}});
 Object.defineProperty(elements['search-choice'], 'options', {get() { return this.children; }});
 elements.search.select = () => {};
 elements.search.dispatchEvent = event => elements.search.handlers[event.type]();
 const records = Array.from({length: 65}, (_, i) => ({player: 'Player ' + i, market: 'Receiving'}));
 await vm.runInNewContext(fs.readFileSync('search-choices.js', 'utf8') + '\n' + matchups.match(/<script>([\s\S]+)<\/script>/)[1], {
  Option: function(text, value) { Object.assign(this, {text, value}); },
  Event: function(type) { this.type = type; },
  document: {createElement: element, getElementById: id => elements[id]},
  fetch: async () => ({ok: true, json: async () => ({status: 'ok', matchups: records})}),
 });
 assert.equal(elements.list.children.length, 20);
 for (let i = 0; i < 3; i++) elements.next.handlers.click();
 assert.equal(elements.status.textContent, 'Showing 61–65 of 65 matching records');
 assert.equal(elements.status.focused, true);
 assert.equal(elements.next.disabled, true);
 elements['search-choice'].value = 'name:Player 0';
 elements['search-choice'].onchange();
 assert.equal(elements.search.hidden, true);
 assert.equal(elements.status.textContent, 'Showing 1–1 of 1 matching records');
 elements['search-choice'].value = 'custom';
 elements['search-choice'].onchange();
 assert.equal(elements.search.hidden, false);
 assert.equal(elements.search.focused, true);
 elements.search.value = 'Player 0';
 elements.search.handlers.input();
 assert.equal(elements.status.textContent, 'Showing 1–1 of 1 matching records');
 assert.equal(elements.pagination.hidden, true);
});
