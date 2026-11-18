"""Generate and score a daily-candidate batch or a calibrated 20-item form, offline."""
import argparse, json, random, sys
from collections import Counter
from pathlib import Path
import benchmark

DATA=Path(__file__).resolve().parent/'data'

def load_form(bank, tag):
    doc=json.loads(bank.read_bytes())
    if tag is None:
        items=doc['items']; benchmark.validate_news(items)
        return items
    items=[r for r in doc['items'] if r['date'][:7]==tag]
    if not items or len(items)>99 or len({r['date'] for r in items})!=len(items):
        raise ValueError('provide a valid monthly tag for the daily bank')
    random.Random(tag).shuffle(items)
    return [dict(i,id=f'N{j:02}') for j,i in enumerate(items,1)]

def score(text,items):
    answers=benchmark.parse(text,[i['id'] for i in items])
    by_uid={i['uid']:benchmark.grade_answer(i,answers[i['id']]) for i in items}
    result={'total':len(items),'correct':sum(i['mark']=='match' for i in by_uid.values()),'items':by_uid}
    if len(items)==20 and Counter(i['date'][:7] for i in items)==Counter({m:2 for m in benchmark.NEWS_MONTHS}):
        result.update(benchmark.news_metrics({'status':'graded','graded':{i['id']:by_uid[i['uid']] for i in items}},items))
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('prompt','grade')); p.add_argument('--bank',type=Path,default=DATA/'daily-202511-202608-v1.json'); p.add_argument('--month'); p.add_argument('--answers',type=Path); a=p.parse_args()
    if hasattr(sys.stdout,'reconfigure'): getattr(sys.stdout,'reconfigure')(encoding='utf-8')
    items=load_form(a.bank,a.month)
    if a.action=='prompt': print(benchmark.make_prompt(items),end='')
    elif not a.answers: p.error('--answers is required in grade mode')
    else: print(json.dumps(score(a.answers.read_text(encoding='utf-8-sig'),items),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
