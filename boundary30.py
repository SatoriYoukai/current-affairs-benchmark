"""June–July boundary benchmark CLI. No network access."""
import argparse,json,sys
from datetime import date,timedelta
from pathlib import Path
import benchmark as b

BANK=Path(__file__).resolve().parent/'data'/'boundary30-v2.json'

def group(doc):
    return [((start,end),[i for i in doc['items'] if start<=i['date']<=end]) for start,end in doc['bins']]

def batches(doc):
    items=doc['items']; start=0; result=[]
    for size in doc.get('batch_sizes',[len(items)]):
        if not isinstance(size,int) or size<1: raise ValueError('invalid batch size')
        result.append(items[start:start+size]); start+=size
    if start!=len(items):raise ValueError('batch coverage mismatch')
    if 'batch_hashes' in doc and [b.digest(b.make_prompt(x)) for x in result]!=doc['batch_hashes']:raise ValueError('batch fingerprint mismatch')
    return result

def load(path=BANK):
    doc=json.loads(path.read_bytes()); items=doc['items']; bins=doc['bins']
    if len(items)!=30 or len({i['id'] for i in items})!=30 or len({i['uid'] for i in items})!=30: raise ValueError('expected 30 unique items')
    if any(date.fromisoformat(a)>date.fromisoformat(z) for a,z in bins) or any(date.fromisoformat(x)+timedelta(days=1)!=date.fromisoformat(y) for (_,x),(y,_) in zip(bins,bins[1:])):
        raise ValueError('bins must be sorted and consecutive')
    if sum(len(x) for _,x in group(doc))!=30 or any(not x for _,x in group(doc)): raise ValueError('every span needs a question; no unmatched questions')
    if any(i.get('axis')!='recall' or not i.get('source','').startswith('https://') or not i.get('quote') for i in items): raise ValueError('item evidence missing')
    if b.digest(b.make_prompt(items))!=doc['prompt_hash']:raise ValueError('frozen prompt mismatch')
    batches(doc)
    return doc

def metrics(doc,row):
    marks=row.get('graded',{})
    result={'score':None,'out_of':len(doc['items']),'all_correct_through':None,'any_correct_through':None,'spans':[]}
    if row.get('status')!='graded' or set(marks)!={i['id'] for i in doc['items']}:return result
    for (start,end),items in group(doc):
        got=[marks[i['id']] for i in items]
        result['spans'].append(dict(start=start,end=end,correct=sum(x['mark']=='match' for x in got),total=len(got),guesses=sum(x['mark']=='match' and x['guess'] for x in got)))
    result['score']=sum(x['correct'] for x in result['spans'])
    for field in ('all_correct_through','any_correct_through'):
        for s in result['spans']:
            n=s['total'] if field=='all_correct_through' else 1
            if not s['total'] or s['correct']<n:break
            result[field]=s['end']
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('action',choices=('prompt','grade')); parser.add_argument('answers',type=Path,nargs='?'); parser.add_argument('--batch',type=int); args=parser.parse_args()
    bank=load(); items=bank['items']; getattr(sys.stdout,'reconfigure',lambda **kw:None)(encoding='utf-8')
    if args.batch is not None:
        parts=batches(bank)
        if args.action!='prompt' or not 1<=args.batch<=len(parts):parser.error('--batch is only for prompt and must select an existing batch')
        items=parts[args.batch-1]
    if args.action=='prompt':print(b.make_prompt(items),end='');return
    if not args.answers:parser.error('grade requires an answer file')
    values=b.parse(args.answers.read_text(encoding='utf-8-sig'),[i['id'] for i in items]); scored={i['id']:b.grade_answer(i,values[i['id']]) for i in items}
    print(json.dumps(dict(**metrics(bank,dict(status='graded',graded=scored)),items=scored),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
