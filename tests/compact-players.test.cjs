const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const html=fs.readFileSync('players.html','utf8');
test('player list is capped at 25 visible records per page',()=>{assert.match(html,/PAGE_SIZE=25/);assert.match(html,/filtered\.slice\(page\*PAGE_SIZE,\(page\+1\)\*PAGE_SIZE\)/);});
test('search and category changes reset to page one',()=>{assert.match(html,/page=0;render\(\)/);assert.match(html,/id="search"/);assert.match(html,/id="category"/);});
test('pagination is bounded and disabled appropriately',()=>{assert.match(html,/id="previous"/);assert.match(html,/id="next"/);assert.match(html,/page=Math\.min\(page,pages-1\)/);assert.match(html,/page>=pages-1/);});
test('stats expand on demand with accessible state',()=>{assert.match(html,/aria-expanded/);assert.match(html,/details.hidden=!details.hidden/);assert.doesNotMatch(html,/innerHTML/);});
test('player browser links to homepage tabs',()=>{assert.match(html,/href="\.\/#players"/);});
