const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const skillRoot = path.join(root, '.agents', 'skills', 'humanize-korean');
const skill = fs.readFileSync(path.join(skillRoot, 'SKILL.md'), 'utf8');
const rules = fs.readFileSync(path.join(skillRoot, 'references', 'quick-rules.md'), 'utf8');
const chatgpt = fs.readFileSync(path.join(skillRoot, 'references', 'chatgpt-project-instructions.md'), 'utf8');
const license = fs.readFileSync(path.join(skillRoot, 'references', 'upstream-license.txt'), 'utf8');
const agents = fs.readFileSync(path.join(root, 'AGENTS.md'), 'utf8');
const finished = fs.readFileSync(path.join(root, '.agents', 'skills', 'write-finished-manuscript', 'SKILL.md'), 'utf8');

assert(skill.includes('name: humanize-korean'));
assert(skill.includes('사실, 주장, 논리 관계와 결론'));
assert(skill.includes('공개 페이지에는 AI 패턴명, 변경률, 자체검증, 작업 과정 같은 내부 메모를 노출하지 않는다.'));
assert(rules.includes('## A. 번역투와 피동'));
assert(rules.includes('## J. 장식'));
assert(rules.includes('수치·날짜·단위·고유명사·URL·직접 인용이 그대로인가'));
assert(chatgpt.includes('[한글 윤문 모드]'));
assert(chatgpt.includes('윤문된 최종문만 출력한다.'));
assert(license.includes('Copyright (c) 2026 epoko77-ai'));
assert(agents.includes('.agents/skills/humanize-korean/SKILL.md'));
assert(finished.includes('`humanize-korean`을 마지막 단계로 적용한다.'));

console.log('Humanize Korean skill integration tests passed.');
