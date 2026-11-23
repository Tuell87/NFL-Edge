const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const html=fs.readFileSync('workbench.html','utf8');
const index=fs.readFileSync('index.html','utf8');
const workflow=fs.readFileSync('.github/workflows/pages.yml','utf8');
test('mobile viewport',()=>assert.match(html,/name="viewport"/));
test('manual probability distinguished from prediction',()=>assert.match(html,/does not predict games/));
test('empty probability blocks EV',()=>assert.ok(html.includes("if(raw==='')")));
test('workbench includes EV and edge outputs',()=>{assert.match(html,/id="ev"/);assert.match(html,/id="edge"/);});
test('rejects invalid odds',()=>assert.ok(html.includes('Math.abs(odds)<100')));
test('rejects invalid probability',()=>assert.ok(html.includes('probability<0||probability>100')));
test('no third-party scripts or credentials',()=>{assert.doesNotMatch(html,/<script[^>]+src=/);assert.doesNotMatch(html,/localStorage|api\.the-odds-api\.com/);});
test('home navigation links to workbench',()=>assert.match(index,/href="\.\/workbench\.html"/));
test('deploy includes workbench',()=>assert.match(workflow,/cp workbench\.html _site\/workbench\.html/));

test('payout includes stake and distinguishes combined and separate selections', () => {
 const vm = require('node:vm');
 const helpers = html.slice(html.indexOf('const slipPriceValid'), html.indexOf('function renderSlipTotals'));
 vm.runInNewContext(helpers + `
  const legs = [{price: 150, game: 'a'}, {price: 200, game: 'b'}, {price: -150, game: 'c'}];
  assert.equal(slipTotals(legs.slice(0, 1), 10, false, 0).total, 25);
  assert.equal(slipTotals(legs, 10, false, 0).total, 125);
  assert.equal(slipTotals(legs, 10, true, 0).risk, 30);
  assert.equal(slipTotals(legs, 10, true, 0).total, 71.67);
  legs[1].game = 'a';
  assert.equal(slipTotals(legs, 10, false, 0).total, null);
  assert.equal(slipTotals(legs, 10, false, 650).total, 75);
  assert.equal(slipTotals(legs, 10, false, 650).risk, 10);
  legs[1].game = '';
  assert.equal(slipTotals(legs, 10, false, 0).needsQuote, true);
 `, {assert});
});
