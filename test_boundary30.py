import unittest
import boundary30 as b

class BoundaryTest(unittest.TestCase):
    def test_prefix_stops_at_first_failed_span(self):
        items=[{'id':'N01','date':'2026-05-31'},{'id':'N02','date':'2026-06-06'},{'id':'N03','date':'2026-06-07'},{'id':'N04','date':'2026-06-21'}]
        doc={'items':items,'bins':[['2026-05-31','2026-05-31'],['2026-06-01','2026-06-10'],['2026-06-11','2026-06-20'],['2026-06-21','2026-06-30']]}
        g={x:{'mark':y,'guess':False} for x,y in zip(('N01','N02','N03','N04'),('match','match','miss','match'))}
        x=b.metrics(doc,{'status':'graded','graded':g})
        self.assertEqual((x['score'],x['all_correct_through'],x['any_correct_through']),(3,'2026-05-31','2026-06-10'))
        self.assertEqual(b.metrics(doc,{'status':'route_unverified'})['score'],None)

    def test_bank_has_30_questions_in_finer_windows(self):
        x=b.load(); self.assertEqual(len(x['items']),30)
        self.assertEqual([len(part) for part in b.batches(x)],[15,15])
        spans=b.group(x)
        self.assertGreaterEqual(sum(1 for (_,end),items in spans if end.startswith(('2026-06','2026-07')) and items),5)
        self.assertTrue(all(items for _,items in spans))
