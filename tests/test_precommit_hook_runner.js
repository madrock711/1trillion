const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const runner = fs.readFileSync(path.join(root, 'scripts', 'run_precommit_hook.ps1'), 'utf8');
const instructions = fs.readFileSync(path.join(root, 'AGENTS.md'), 'utf8');

assert.match(
    runner,
    /&\s+bash\s+['"]\.githooks\/pre-commit['"]/,
    'PowerShell 안전 실행기는 훅을 Bash로만 호출해야 합니다.'
);
assert.match(
    runner,
    /Get-Command bash -CommandType Application/,
    'Bash 부재는 명확한 검증 실패로 알려야 합니다.'
);
assert.match(
    instructions,
    /bash \.githooks\/pre-commit/,
    '저장소 운영 지침은 Bash 훅 실행 명령을 명시해야 합니다.'
);
assert.ok(
    instructions.includes('Windows PowerShell에서 확장자 없는 훅을 직접 실행하지 않는다.'),
    '저장소 운영 지침은 Windows 직접 실행을 금지해야 합니다.'
);

console.log('pre-commit hook runner contract: passed');
