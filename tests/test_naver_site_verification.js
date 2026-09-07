const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const home = fs.readFileSync(path.resolve(__dirname, '..', 'index.html'), 'utf8');
const head = home.match(/<head>[\s\S]*?<\/head>/)?.[0] || '';

assert.match(
    head,
    /<meta name="naver-site-verification" content="4a526c8ff87b82cd056d3d97108526a0a9bdbd6c">/
);
assert.equal((head.match(/name="naver-site-verification"/g) || []).length, 1);

console.log('naver site verification: ok');
