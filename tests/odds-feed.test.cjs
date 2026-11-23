const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');
const html=fs.readFileSync('odds.html','utf8');const index=fs.readFileSync('index.html','utf8');const workflow=fs.readFileSync('.github/workflows/pages.yml','utf8');
test('mobile odds board exists',()=>assert.match(html,/name="viewport"/));
test('connection status explicit',()=>assert.match(html,/not connected yet/));
test('safe text rendering',()=>assert.match(html,/textContent = x\.player/));
test('no credentials in browser',()=>assert.doesNotMatch(html,/apiKey=|ODDS_API_KEY.*value|localStorage/));
test('home links to feed',()=>assert.match(index,/href="\.\/odds\.html"/));
test('scheduled workflow',()=>assert.match(workflow,/schedule:/));
test('server-only secret',()=>assert.match(workflow,/secrets\.ODDS_API_KEY/));
test('static feed published',()=>assert.match(workflow,/cp data\/odds\.json _site\/data\/odds\.json/));

test('odds pagination reaches selections past the former 200-row limit and resets on search', () => {
  const vm = require('node:vm');
  const elements = new Map();
  const element = () => ({
    value: '',
    children: [],
    handlers: {},
    replaceChildren(...children) { this.children = children; },
    addEventListener(event, handler) { this.handlers[event] = handler; },
  });
  for (const id of ['status', 'updated', 'search', 'market', 'refresh', 'results', 'board', 'list', 'pagination', 'previous', 'next']) {
    elements.set(id, element());
  }
  const prices = Array.from({length: 205}, (_, i) => ({
    player: 'Player ' + i, event: 'Away @ Home', market: 'player_rush_yds',
    line: 0, side: 'Over', odds: -110, commence_time: '2020-01-01T00:00:00Z',
  }));
  const script = html.match(/<script>([\s\S]+)<\/script>/)[1];
  return vm.runInNewContext(script, {
    document: {
      getElementById: id => elements.get(id),
      createElement: tag => ({
        children: [],
        append(child) { this.children.push(child); },
        insertCell() { const cell = this.constructorCell(); this.append(cell); return cell; },
        constructorCell() { return {children: [], append(child) { this.children.push(child); }}; },
      }),
    },
    Option: function(text, value) { Object.assign(this, {text, value}); },
    fetch: async () => ({ok: true, json: async () => ({status: 'ok', markets: prices})}),
  }).then(() => {
    assert.equal(elements.get('list').children.length, 20);
    for (let i = 0; i < 10; i++) elements.get('next').handlers.click();
    assert.equal(elements.get('results').textContent, 'Showing 201–205 of 205 selections');
    assert.equal(elements.get('next').disabled, true);
    const [player, selection, price] = elements.get('list').children[0].children;
    assert.equal(player.children[1].textContent, 'Game started');
    assert.equal(selection.children[0].textContent, 'Over 0');
    assert.equal(price.children[0].textContent, 'Time unavailable');
    elements.get('search').value = 'Player 0';
    elements.get('search').handlers.input();
    assert.equal(elements.get('results').textContent, 'Showing 1–1 of 1 selections');
    assert.equal(elements.get('pagination').hidden, true);
  });
});
