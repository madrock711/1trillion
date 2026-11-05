import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('publication',ROOT/'scripts/publish_market_research.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class PublicationTests(unittest.TestCase):
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
