const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');
const html=fs.readFileSync('home-next.html','utf8');const index=fs.readFileSync('index.html','utf8');const workflow=fs.readFileSync('.github/workflows/pages.yml','utf8');
test('mobile game day page',()=>assert.match(html,/name="viewport"/));
test('scoreboard snapshot fetch',()=>assert.match(html,/data\/games\.json/));
test('odds snapshot fetch',()=>assert.match(html,/data\/odds\.json/));
test('honest forecast status',()=>assert.match(html,/Independent player predictions are still in development/));
test('text-only safe rendering',()=>assert.doesNotMatch(html,/innerHTML/));
test('game day is default home',()=>assert.match(index,/NFL Games/));
test('scoreboard job',()=>assert.match(workflow,/python3 scripts\/fetch_games\.py/));
test('scoreboard published',()=>assert.match(workflow,/cp data\/games\.json _site\/data\/games\.json/));

test('game markets require a fresh book price and a future kickoff', () => {
  const vm = require('node:vm');
  const page = require('node:fs').readFileSync('game.html', 'utf8');
  const helpers = page.slice(page.indexOf('const normalize ='), page.indexOf('function impliedChance'));
  vm.runInNewContext(helpers + `
    const now = Date.parse('2026-11-23T18:00:00Z');
    const game = {start:'2026-11-23T19:00:00Z', away:{name:'Away'}, home:{name:'Home'}};
    const row = {odds:150, event:'Away @ Home', commence_time:game.start, bookmaker_updated:'2026-11-23T17:30:00Z'};
    const old = {...row, bookmaker_updated:'2026-11-21T18:00:00Z'};
    const premature = {...row, bookmaker_updated:'2026-11-23T18:30:00Z'};
    assert.equal(matchingMarkets(game, [row, old, premature], now).length, 1);
    assert.equal(matchingMarkets(game, [row], Date.parse(game.start)).length, 0);
  `, {assert});
});
