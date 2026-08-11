const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const dashboard = fs.readFileSync(path.join(root, 'assets', 'market-dashboard.js'), 'utf8');
const html = fs.readFileSync(path.join(root, 'articles', 'market.html'), 'utf8');

assert(
    dashboard.includes("updateFlowCheckpoint(data, incomingKospi, '외국인', '외국인 현물')"),
    '외국인 현물 관찰 카드는 새로 받은 KOSPI 수급으로 갱신되어야 합니다.'
);
assert(
    dashboard.includes("item.label === '전체 프로그램' || item.label === '프로그램 전체'"),
    '프로그램 관찰 카드는 스냅샷의 프로그램 전체 라벨도 실시간 갱신 대상으로 찾아야 합니다.'
);
assert(
    dashboard.includes("updateExchangeCheckpoint(data, liveData.exchange)"),
    '달러/원 관찰 카드는 새로 받은 환율로 갱신되어야 합니다.'
);
assert(
    !dashboard.includes("updateFlowCheckpoint(data, incomingKospi, '외국인', 'KOSPI 기준선')"),
    'KOSPI 기준선은 작성 당시 분석값을 유지해야 합니다.'
);
assert(
    html.includes('market-dashboard.js?v=20260811-7'),
    '수정된 대시보드 스크립트가 캐시를 우회해야 합니다.'
);

console.log('market checkpoint live refresh tests passed');
