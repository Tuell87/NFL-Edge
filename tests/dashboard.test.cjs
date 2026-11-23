const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const html=fs.readFileSync('dashboard.html','utf8');
const index=fs.readFileSync('index.html','utf8');
const workflow=fs.readFileSync('.github/workflows/pages.yml','utf8');
test('command center is mobile responsive',()=>assert.match(html,/name="viewport"/));
test('reads public GitHub workflow and PR endpoints',()=>{
 assert.match(html,/api.github.com\/repos\/Tuell87\/NFL-Edge/);
 assert.match(html,/actions\/runs/);
 assert.match(html,/pulls\?state=open/);
});
test('renders external titles with textContent and rejects arbitrary external links',()=>{
 assert.match(html,/a.textContent=label/);
 assert.match(html,/url.startsWith\('https:\/\/github.com\/Tuell87\/NFL-Edge\/'\)/);
 assert.doesNotMatch(html,/innerHTML\s*=/);
});
test('does not invent roadmap completion percentages or expose tokens',()=>{
 assert.doesNotMatch(html,/45%|aria-valuenow|localStorage|sessionStorage|apiKey/i);
});
test('dashboard is published and linked from homepage',()=>{
 assert.match(workflow,/cp dashboard.html _site\/dashboard.html/);
 assert.match(index,/href="\.\/dashboard.html"/);
});
test('live Pages smoke checks command center',()=>{
 const smoke=fs.readFileSync('scripts/check_live_pages.py','utf8');
 assert.match(smoke,/dashboard.html/);
});
