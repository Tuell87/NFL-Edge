const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');
const html=fs.readFileSync('dashboard.html','utf8');const workflow=fs.readFileSync('.github/workflows/pages.yml','utf8');
test('dashboard is mobile responsive',()=>assert.match(html,/name="viewport"/));
test('dashboard reads GitHub API',()=>assert.match(html,/api\.github\.com\/repos\/Tuell87\/NFL-Edge/));
test('dashboard shows clear data limitations',()=>assert.match(html,/Roadmap percentage is a planning estimate/));
test('dashboard does not store browser secrets',()=>{assert.doesNotMatch(html,/localStorage|sessionStorage|api[_-]?key\s*[:=]/i);});
test('dashboard safely renders external API text',()=>{assert.match(html,/a\.textContent=label/);assert.doesNotMatch(html,/innerHTML\s*=/);});
test('change requests use GitHub issue form',()=>assert.match(html,/github\.com\/Tuell87\/NFL-Edge\/issues\/new/));
test('deploy workflow includes dashboard',()=>assert.match(workflow,/cp dashboard\.html _site\/dashboard\.html/));
