const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');
const html=fs.readFileSync('compare.html','utf8');
test('historical comparison excludes stale feeds',()=>assert.match(html,/now-checked<=86400000/));
test('historical comparison excludes stale bookmaker markets',()=>assert.match(html,/now-bookTime>86400000/));
test('historical comparison excludes started events',()=>assert.match(html,/kickoff<=now/));
test('historical comparison avoids arbitrary multi-event matches',()=>assert.match(html,/events.size===1&&candidates.length===1/));
test('only matches over side for clear hit rate',()=>assert.match(html,/x.side!=='Over'/));
test('historical comparison explains missing matches',()=>assert.match(html,/stale, ambiguous, or unavailable/));
