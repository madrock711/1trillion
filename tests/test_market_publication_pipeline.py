import datetime as dt
import importlib.util
import io
import json
from pathlib import Path
import random
import sys
import unittest
from unittest.mock import Mock, patch

from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('publication',ROOT/'scripts/publish_market_research.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
from market_research_indicators import MARKET_INDEXES, market_history_url
from market_news_sentiment_chart import CORRELATION_WEEKS, market_closes, rolling_weekly_correlations


class PublicationTests(unittest.TestCase):
    def test_indicator_evidence_explicitly_comes_from_the_day_collection(self):
        publisher = module.Publisher.__new__(module.Publisher)
        publisher.dir = Path('research/evidence/2026-11-22')
        cutoff = '2026-11-22T08:05:00+09:00'
        path = publisher.dir / 'collections/080000-000000/research-indicators.json'
        publisher.p = {'researchIndicatorsPath': path.as_posix()}
        evidence = {
            'schemaVersion': 1,
            'nsi': {
                'status': 'verified', 'sourceUrl': 'https://snapshot.bok.or.kr/dashboard/C8',
                'fetchedAt': '2026-11-22T08:00:00+09:00', 'period': '2026-11-15',
                'value': 99.09, 'change7d': 10.04, 'rawHash': 'f' * 64,
                'seriesId': 'NECOS-523U001-D-A001',
                'observations': [
                    {'period': '2026-07-01', 'value': 101.1},
                    {'period': '2026-11-14', 'value': 97.75},
                    {'period': '2026-11-15', 'value': 99.09},
                ],
            },
        }
        with patch.object(module, 'load', return_value=evidence):
            rows, files, comparison = publisher.research_indicators(cutoff)
        self.assertEqual(['99.09'], [row['value'] for row in rows])
        self.assertEqual([path.as_posix()], files)
        self.assertIsNone(comparison)
        publisher.p['researchIndicatorsPath'] = str(path).replace('2026-11-22', '2026-11-21')
        with self.assertRaisesRegex(ValueError, '당일 수집 경로'):
            publisher.research_indicators(cutoff)

    def test_news_market_plot_aligns_weekly_changes_and_correlations(self):
        initial = dt.date(2025, 10, 5)
        week = dt.timedelta(days=7)
        end = initial + 58 * week
        rng = random.Random(44)
        changes = [rng.uniform(-2, 2) for _ in range(58)]
        sentiment = [100]
        nasdaq = [10000]
        kospi = [3000]
        for i, change in enumerate(changes):
            sentiment.append(sentiment[-1] + change)
            nasdaq.append(nasdaq[-1] * (1 + (changes[i - 1] if i else 0) / 100))
            kospi.append(kospi[-1] * (1 + change / 100))

        def daily(levels):
            return [{'period': (initial + i * week - dt.timedelta(days=6 - day)).isoformat(), 'value': value}
                    for i, value in enumerate(levels) for day in range(7)]

        captured = (end + dt.timedelta(days=1)).isoformat() + 'T08:03:00+09:00'
        evidence = {
            'nsi': {'seriesId': 'NECOS-523U001-D-A001', 'period': end.isoformat(),
                    'value': sentiment[-1], 'observations': daily(sentiment)},
            'marketHistory': {
                key: {'status': 'verified', 'sourceUrl': market_history_url(key), 'symbol': MARKET_INDEXES[key][0],
                      'rawHash': 'b' * 64, 'fetchedAt': captured,
                      'observations': [row for row in daily(levels)
                                       if dt.date.fromisoformat(row['period']).weekday() < 5]}
                for key, levels in [('nasdaq', nasdaq), ('kospi', kospi)]
            }
        }
        rows = [{'source': 'https://snapshot.bok.or.kr/dashboard/C8'}]
        cutoff = dt.datetime.fromisoformat(captured)
        comparison = module.news_market_comparison(evidence, rows, cutoff)
        self.assertEqual(end, comparison['weeks'][-1])
        self.assertAlmostEqual(changes[-1], comparison['weekly_lines']['nsi'][end])
        self.assertAlmostEqual(changes[-2], comparison['weekly_lines']['nasdaq'][end])
        self.assertAlmostEqual(changes[-1], comparison['weekly_lines']['kospi'][end])
        self.assertAlmostEqual(1, comparison['weekly_correlations']['nsi', 'kospi'][end])
        self.assertEqual([100, 100, 100], [round(points[0][1], 2) for points in comparison['lines'].values()])
        self.assertIsNone(module.news_market_comparison(evidence, [], cutoff))
        with Image.open(io.BytesIO(module.render_news_sentiment_chart(comparison))) as chart:
            self.assertEqual('PNG', chart.format)
            chart.verify()
        chart_path = 'charts/korea_news_sentiment_markets_2026-11-22.png'
        figure = module.news_sentiment_figure(chart_path, comparison)
        panel = '<!-- market-news-sentiment:start -->\n<!-- market-news-sentiment:end -->'
        rendered = module.update_news_sentiment_panel(panel, figure)
        self.assertIn(f'src="../{chart_path}"', rendered)
        self.assertIn('최근 12주', rendered)
        self.assertIn('날짜별 주간 변화와 상관계수', rendered)
        self.assertIn(f'<th scope="row">{end:%Y.%m.%d}</th>', rendered)
        self.assertNotIn('시차', rendered)
        self.assertNotIn(chart_path, module.update_news_sentiment_panel(rendered, ''))

        session = end + dt.timedelta(days=1)
        next_morning = dt.datetime.fromisoformat(f'{session + dt.timedelta(days=1)}T08:05:00+09:00')
        for record in evidence['marketHistory'].values():
            record['fetchedAt'] = next_morning.isoformat()
        refreshed = module.news_market_comparison(
            evidence, rows, next_morning, verified_kospi_close=(session, 3100)
        )
        self.assertEqual((session, 3100), refreshed['latest']['kospi'])
        self.assertEqual(end, refreshed['weeks'][-1])
        self.assertTrue(refreshed['kospi_close_supplemented'])
        self.assertIn('코스피 전일 종가', module.news_sentiment_figure(chart_path, refreshed))

    def test_rolling_correlation_uses_only_trailing_consecutive_weeks(self):
        first = dt.date(2026, 8, 2)
        weeks = [first + dt.timedelta(weeks=i) for i in range(CORRELATION_WEEKS + 2)]
        levels = {
            'nsi': {week: float(i) for i, week in enumerate(weeks)},
            'nasdaq': {week: float(i) for i, week in enumerate(weeks)},
            'kospi': {week: -float(i) for i, week in enumerate(weeks)},
        }
        levels['nasdaq'][weeks[-1]] = -1000
        result = rolling_weekly_correlations(levels, weeks)
        self.assertNotIn(weeks[10], result['nsi', 'nasdaq'])
        self.assertAlmostEqual(1, result['nsi', 'nasdaq'][weeks[-2]])
        self.assertLess(result['nsi', 'nasdaq'][weeks[-1]], 0)
        self.assertAlmostEqual(-1, result['nsi', 'kospi'][weeks[-1]])
        del levels['kospi'][weeks[4]]
        self.assertEqual({}, rolling_weekly_correlations(levels, weeks)['nsi', 'nasdaq'])

    def test_today_daily_bar_requires_a_post_close_fetch(self):
        session = dt.date(2026, 11, 24)
        history = {
            'status': 'verified', 'symbol': '^KS11', 'sourceUrl': market_history_url('kospi'),
            'rawHash': 'b' * 64, 'fetchedAt': '2026-11-24T14:00:00+09:00',
            'observations': [{'period': session.isoformat(), 'value': 5006.03}],
        }
        evidence = {'marketHistory': {'kospi': history}}
        review = dt.datetime.fromisoformat('2026-11-24T20:16:00+09:00')
        self.assertEqual({}, market_closes(evidence, 'kospi', review))
        history['fetchedAt'] = '2026-11-24T20:15:00+09:00'
        self.assertEqual({session: 5006.03}, market_closes(evidence, 'kospi', review))

    def test_dashboard_copy_does_not_rewrite_historical_article(self):
        historical='<article>AMD yesterday</article>'
        page='<h1>시황분석 대시보드</h1><p>AMD yesterday</p><h2 id="market-checkpoint-title">AMD</h2><h2 id="strategy-title">전략</h2><p>old</p>'+historical
        result=module.update_dashboard_copy(page,'오늘 제목','오늘 설명')
        self.assertIn('<h2 id="market-checkpoint-title">오늘 제목</h2>',result)
        self.assertIn('<h1>시황분석 대시보드</h1><p>오늘 설명</p>',result)
        self.assertIn('<h2 id="strategy-title">전략</h2><p>오늘 설명</p>',result)
        self.assertTrue(result.endswith(historical))

    def test_card_insert_preserves_old_images_and_bodies(self):
        old='<article class="article-card"><a href="market-2026-11-04.html"><img src="old.png">old</a></article>'
        card='<article class="article-card"><a href="market-2026-11-05.html"><img src="new.png">new</a></article>'
        result=module.insert_card(old,card,'2026-11-05','article-card')
        self.assertEqual(card+'\n'+old,result)
        self.assertEqual(result,module.insert_card(result,card,'2026-11-05','article-card'))

    def test_ld_preserves_historical_image(self):
        old={'mainEntity':{'itemListElement':[{'url':'old','image':{'url':'old.png'}}]}}
        page='<script type="application/ld+json">'+json.dumps(old)+'</script>'
        result=module.update_ld(page,{'url':'new','image':{'url':'new.png'}})
        data=json.loads(result.split('>',1)[1].split('</script>')[0])
        self.assertEqual('old.png',data['mainEntity']['itemListElement'][1]['image']['url'])
        self.assertEqual(2,data['mainEntity']['numberOfItems'])

    def test_nxt_uses_response_completion_and_rejects_stale(self):
        row={'itemCode':'005930','marketStatus':'OPEN','localTradedAt':'2026-11-05T08:40:01+09:00','closePrice':'211,000','lowPrice':'210,000','highPrice':'212,000'}
        self.assertTrue(module.valid_nxt(row,'2026-11-05','2026-11-05T08:40:02+09:00'))
        self.assertFalse(module.valid_nxt(row,'2026-11-05','2026-11-05T08:46:02+09:00'))
        self.assertFalse(module.valid_nxt(row,'2026-11-05','2026-11-05T08:40:00+09:00'))
        row['closePrice']='213,000'
        self.assertFalse(module.valid_nxt(row,'2026-11-05','2026-11-05T08:40:02+09:00'))

    def test_committed_resume_never_reseals_or_retests(self):
        publisher=object.__new__(module.Publisher)
        publisher.s={'contentCommit':'a'*40,'contentPushed':'2026-11-05T08:00:00+09:00'}
        publisher.preflight=Mock(side_effect=AssertionError('must not restart'))
        publisher.final_query=Mock(side_effect=AssertionError('must not query/reseal'))
        publisher.publication=Mock(return_value='pushed.json')
        self.assertEqual(75,publisher.publish(stop_after='content_push'))
        publisher.preflight.assert_not_called();publisher.final_query.assert_not_called()
        publisher.publication.assert_called_once_with('pushed','a'*40)

    def test_failed_push_remains_resumable_and_not_complete(self):
        publisher=object.__new__(module.Publisher)
        publisher.s={'contentCommit':'a'*40}
        publisher.push=Mock(side_effect=RuntimeError('fixture network failure'))
        with self.assertRaises(RuntimeError): publisher.publish()
        self.assertNotIn('contentPushed',publisher.s)
        self.assertNotIn('finalCommit',publisher.s)


if __name__=='__main__': unittest.main()
