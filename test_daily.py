import json, unittest
from datetime import date,timedelta
from pathlib import Path
import daily

BANK=daily.DATA/'daily-202511-202608-v1.json'

class DailyTest(unittest.TestCase):
    def test_every_day_has_exactly_one_cited_event(self):
        rows=json.loads(BANK.read_bytes())['items']
        d=date(2025,11,1); last=date(2026,8,31)
        want=[(d+timedelta(days=j)).isoformat() for j in range((last-d).days+1)]
        self.assertEqual([r['date'] for r in rows],want)
        self.assertEqual(len(set(r['uid'] for r in rows)),len(want))
        self.assertEqual(len(set(r['source'] for r in rows)),len(want))
        for i in rows:
            self.assertTrue(i['source'].startswith('https://') and i['quote'] and i['answer'])
            if not i['uid'].startswith('V2-'):
                self.assertEqual(i['question'].split(': ',1)[1].count('[BLANK]'),1)
                self.assertTrue(i['index_url'].startswith('https://en.wikipedia.org/'))

    def test_one_month_can_render_and_score_without_gateway(self):
        rows=daily.load_form(BANK,'2026-07')
        expected='\n'.join(i['id']+'='+i['answer'] for i in rows)
        score=daily.score(expected,rows)
        self.assertEqual((score['correct'],score['total']),(31,31))
        self.assertEqual(len(set(i['id'] for i in rows)),31)
        self.assertEqual(len(daily.benchmark.make_prompt(rows).splitlines()),32)

    def test_confirmed_form_matches_prompt_digest_and_three_metrics(self):
        path=daily.DATA/'daily-calibrated-ea9741f67e9e.json'
        doc=json.loads(path.read_bytes())
        rows=daily.load_form(path,None)
        self.assertEqual(daily.benchmark.digest(daily.benchmark.make_prompt(rows)),doc['prompt_hash'])
        answer='\n'.join(i['id']+'='+i['answer'] for i in rows)
        score=daily.score(answer,rows)
        self.assertEqual((score['score'],score['all_correct_through'],score['any_correct_through']),(20,'2026-08','2026-08'))
