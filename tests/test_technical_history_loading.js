'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync(require.resolve('../assets/market-dashboard.js'),'utf8');
(async()=>{
 const data={technical:{instruments:[{id:'KODEX',liveSnapshot:{}}]}};
 const events=[],timeouts=[],cleared=[],calls=[];
 let resolveKodex,rejectTqqq;
 const context=vm.createContext({Promise,URL,AbortController,liveMarketSource:'/market-data/',latestLiveData:{},
  window:{location:{href:'https://example.com/articles/market.html'},fetch(){},setTimeout(fn,ms){timeouts.push(ms);return timeouts.length},clearTimeout(id){cleared.push(id)},MarketDashboardLive:{fetchTechnicalPriceHistory(symbol,fetch,base,options){calls.push({symbol,options});return new Promise((resolve,reject)=>{if(symbol==='KODEX')resolveKodex=resolve;else rejectTqqq=reject})}}},
  findById:(rows,id)=>rows.find(r=>r.id===id),publishTechnicalAnalysisData:(symbol,mode,bars)=>events.push({symbol,mode,bars}),renderKodex(){}});
 vm.runInContext(source.slice(source.indexOf('    var technicalPriceHistoryRequest = null;'),source.indexOf('    function loadKodexIntradayIndex(')),context);
 const pending=context.loadTechnicalPriceHistories(data,false);
 assert.equal(context.loadTechnicalPriceHistories(data,false),pending,'중복 로드 요청을 공유해야 한다');
 const rows=[{date:'2026-10-13',close:82180}];resolveKodex(rows);
 await new Promise(resolve=>setImmediate(resolve));
 assert.equal(events.length,1,'다른 종목의 지연을 기다리지 않고 먼저 완료된 종목을 전달해야 한다');
 assert.equal(data.technical.instruments[0].priceHistory,rows);
 assert.equal(data.technical.instruments[0].liveSnapshot.priceHistory,rows);
 rejectTqqq(new Error('시세 요청 지연'));assert.equal(await pending,true);
 assert.deepEqual(timeouts,[30000,30000]);assert.equal(cleared.length,2);
 assert.equal(context.technicalPriceHistoryRequest,null,'실패 이후 재시도가 가능해야 한다');
 assert(source.indexOf('loadTechnicalPriceHistories(data, false),')<source.indexOf('primeCurrentSession(data).then('),'전체 시세 요청보다 이력을 먼저 시작해야 한다');
 assert(source.includes("window.dispatchEvent(new window.CustomEvent('technical-dashboard-ready'))"));
 const workbench=fs.readFileSync(require.resolve('../assets/technical-workbench.js'),'utf8');
 assert(workbench.includes("window.addEventListener('technical-dashboard-ready', applyMode)"),'저장된 분봉 설정을 대시보드 준비 후 다시 적용해야 한다');
 console.log('차트 이력 독립 로딩·종목별 전달·타임아웃·실패 재시도 검증 통과');
})().catch(e=>{console.error(e);process.exitCode=1});
