// Fail locally before a push can create a failing Amplify deployment.
const { spawnSync } = require('node:child_process');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const checks = [
    'scripts/audit_public_site.js',
    'tests/test_home_article_feed.js',
    'tests/test_home_article_search.js'
];

for (const check of checks) {
    console.log(`preflight: node ${check}`);
    const result = spawnSync(process.execPath, [check], {
        cwd: root,
        stdio: 'inherit'
    });
    if (result.status !== 0) {
        console.error(`preflight failed: ${check}`);
        process.exit(result.status || 1);
    }
}

console.log('deployment preflight: passed');
