import json, unittest
from pathlib import Path
import benchmark as b

class BenchmarkTest(unittest.TestCase):
    def test_prompt_hash_and_perfect_score(self):
        bank=b.load()
        self.assertEqual(b.make_prompt(bank['items']),Path('data/questions.txt').read_text(encoding='utf-8'))
        answer='\n'.join(i['id']+'='+i['answer'] for i in bank['items'])
        x=b.grade(answer,bank)
        self.assertEqual((x['score'],x['all_correct_through'],x['any_correct_through']),(20,'2026-08','2026-08'))

    def test_baseline_is_consistent_with_published_scorer(self):
        bank=b.load()
        baseline=json.loads(Path('data/baseline.json').read_bytes())
        self.assertEqual(len(baseline['results']),8)
        for row in baseline['results']:
            stats=b.news_metrics({'status':'graded','graded':row['items']},bank['items'])
            self.assertEqual(stats,{k:row[k] for k in stats})
