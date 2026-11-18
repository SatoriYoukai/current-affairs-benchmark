"""Offline prompt generation and scorer: no account credentials or network required."""
import argparse, hashlib, json, re, sys, unicodedata
from collections import Counter
from datetime import date
from fractions import Fraction
from pathlib import Path

BANK = Path(__file__).resolve().parent/'data'/'news-202511-202608-v2.json'

class legacy:
    @staticmethod
    def correct(item, text):
        if item!='B08': raise ValueError('unexpected legacy item')
        parts=re.split(r'[、,，/;；]|\s+and\s+|\s+和\s+|和|与',unicodedata.normalize('NFKC',text).strip().strip('`*').strip().rstrip('。.;；').casefold())
        parts=[re.sub(r'^gpt[\-‐‑–]?5\.6[\s\-‐‑–]*','',p.strip()) for p in parts]
        return len(parts)==3 and set(parts)=={'sol','terra','luna'}

NEWS_MONTHS = ('2025-11','2025-12',*(f'2026-{m:02d}' for m in range(1,9)))


GRADE_ALIASES = {'Elena Rybakina': ('叶连娜·莱巴金娜',)}


def make_prompt(items):
    return '无工具，仅用内置知识和题给信息。每题只交一行：题号=短答案。不确定可猜一个，猜测在答案前加?；无头绪填-。不解释、不列候选。\n' + '\n'.join(f"{x['id']}. {x['question']}" for x in items) + '\n'


def digest(s):
    return hashlib.sha256(s.encode()).hexdigest()


def parse(text, ids):
    lines = text.strip().splitlines()
    if lines and re.fullmatch(r'```(?:text)?', lines[0].strip(), re.I) and lines[-1].strip()=='```': lines=lines[1:-1]
    out = {}
    for line in lines:
        m = re.fullmatch(r'([NR][0-9]{2})(?:\s*[=：:.．、]\s*|\s+)(\S.*)', line.strip())
        if not m or m[1] not in ids or m[1] in out: raise ValueError('bad_line_or_id')
        out[m[1]]=m[2]
    if len(out)!=len(ids): raise ValueError('missing_id')
    return out


def norm(s):
    s=unicodedata.normalize('NFKC',s).strip().strip('*`').strip().rstrip('。.;；').casefold()
    return re.sub(r'\s+','',s.translate(str.maketrans({'・':'·','–':'-','‐':'-','‑':'-','—':'-'})))


def grade_answer(item, raw):
    text=unicodedata.normalize('NFKC',raw).strip(); guess=text.startswith('?'); text=text[1:].strip() if guess else text
    if text in ('','-','?','—','不知道','不确定','无头绪','unknown'): return {'mark':'unknown','guess':False}
    kind=item['kind']; clean=norm(text)
    match=clean in {norm(x) for x in [item['answer'],*item.get('aliases',[]),*GRADE_ALIASES.get(item['answer'],())]}
    if kind=='legacy': match=match or legacy.correct(item['legacy'], text)
    if not match and kind in ('number','percent','fraction'):
        p=clean.removesuffix('%') if kind=='percent' else clean
        pat=r'[+-]?\d+(?:/\d+)?' if kind=='fraction' else r'[+-]?\d+(?:\.\d+)?'
        if re.fullmatch(pat,p):
            try: match=Fraction(p)==Fraction(item['answer'])
            except ZeroDivisionError: pass
    return {'mark':'match' if match else 'miss','guess':guess}


def validate_news(items):
    if Counter(date.fromisoformat(i['date']).isoformat()[:7] for i in items) != Counter({m:2 for m in NEWS_MONTHS}):
        raise ValueError('news_months_require_two_each')
    if any(i.get('axis')!='recall' or not i.get('source','').startswith('https://') or not i.get('quote') for i in items):
        raise ValueError('news_item_evidence_missing')


def news_profile(row, items):
    result={}
    grading=row.get('graded',{})
    for i in items:
        totals=result.setdefault(i['date'][:7],dict(correct=0,correct_guess=0,wrong=0,unknown=0,missing=0))
        item=grading.get(i['id'])
        if item is None: totals['missing']+=1
        elif item['mark']=='match':
            totals['correct']+=1
            totals['correct_guess']+=int(item['guess'])
        else: totals['unknown' if item['mark']=='unknown' else 'wrong']+=1
    return result


def news_metrics(row, items):
    metrics=dict(score=None,out_of=len(items),all_correct_through=None,any_correct_through=None)
    if row.get('status')!='graded': return metrics
    profile=news_profile(row,items)
    if any(m not in profile or profile[m]['missing'] for m in NEWS_MONTHS): return metrics
    metrics['score']=sum(profile[m]['correct'] for m in NEWS_MONTHS)
    for field,threshold in (('all_correct_through',2),('any_correct_through',1)):
        for month in NEWS_MONTHS:
            if profile[month]['correct']<threshold: break
            metrics[field]=month
    return metrics


def load():
    bank=json.loads(BANK.read_bytes())
    validate_news(bank['items'])
    if len({x['id'] for x in bank['items']})!=20 or digest(make_prompt(bank['items']))!=bank['prompt_hash']:
        raise ValueError('frozen bank mismatch')
    return bank


def grade(text, bank):
    answers=parse(text,[i['id'] for i in bank['items']])
    row={'status':'graded','graded':{i['id']:grade_answer(i,answers[i['id']]) for i in bank['items']}}
    return {**news_metrics(row,bank['items']),'months':news_profile(row,bank['items']),'items':row['graded']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_subparsers(dest='action',required=True)
    group.add_parser('prompt')
    group.add_parser('grade').add_argument('answer_file',type=Path)
    a=parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    bank=load()
    if a.action=='prompt': print(make_prompt(bank['items']),end='')
    else: print(json.dumps(grade(a.answer_file.read_text(encoding='utf-8-sig'),bank),ensure_ascii=False,indent=2))

if __name__=='__main__': main()
