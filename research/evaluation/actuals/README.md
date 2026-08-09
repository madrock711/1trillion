# 거래일 확정값

KRX 장 마감 뒤 한 거래일에 한 파일만 저장한다. `bizdate`, `fetchedAt`, `marketStatus: CLOSE`, KOSPI 최종 OHLC를 고정한다. `closeSnapshot`에는 KODEX 최종 OHLCV, 외국인·기관·개인 현물, 프로그램 차익·비차익·전체, 시장 폭을 `kodex`, `cashFlow`, `program`, `breadth`로 나누고 각 묶음의 원천 시각·출처·원문 해시·단위를 기록한다. 하나라도 확인하지 못하면 임의의 0을 채우지 않고 스냅샷 전체를 `null`로 두며 누락 사유를 쓴다. 대시보드의 장중 고가·저가나 다음 보고서의 반올림 문장을 실제값으로 대체하지 않는다.

`flowTrajectory`는 `flow_trajectory_v1`로 09:30 `open30`, 10:00 `open60`, 14:00 `at1400`, 15:30 `close` 앵커를 모두 보존한다. 각 앵커에는 외국인 현물, 프로그램 비차익·전체 누적값과 출처·원문 해시를 둔다. 누락 앵커도 예정 시각·확인 시각·원천 상태·누락 사유·해시로 남긴다. 종가 스냅샷이 있으면 close 앵커 세 값은 정확히 일치해야 하고, 종가 스냅샷이 없으면 close 앵커도 누락으로 남겨야 한다. 궤적 전체가 없으면 `flowTrajectoryMissingEvidence`를 기록하며 임의 보간하지 않는다.

여러 전망 판본은 모두 같은 `YYYY-MM-DD.json`을 참조하므로 판본마다 서로 다른 종가를 갖지 않는다.
