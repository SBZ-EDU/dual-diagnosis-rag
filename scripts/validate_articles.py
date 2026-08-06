"""Quality checks for the exported academic-paper catalog before HF publication."""
import json, re, sys
from pathlib import Path
KEYWORDS = {'psychosis','schizophrenia','substance','addiction','dual diagnosis','comorbidity','alcohol','cannabis','treatment'}
def main(path='data/articles/cloudflare_articles.json'):
    raw=json.loads(Path(path).read_text(encoding='utf-8')); rows=raw.get('articles',raw)
    seen=set(); valid=[]; rejected=[]
    for r in rows:
        title=(r.get('title') or '').strip(); url=r.get('url') or ''; year=str(r.get('published') or '')[:4]
        reasons=[]
        if not title: reasons.append('missing_title')
        if url in seen: reasons.append('duplicate_url')
        if year and (not year.isdigit() or not 2023 <= int(year) <= 2026): reasons.append('year_out_of_range')
        text=(title+' '+(r.get('abstract') or '')).lower()
        if not any(k in text for k in KEYWORDS): reasons.append('low_topic_relevance')
        if reasons: rejected.append({**r,'reasons':reasons})
        else: valid.append(r); seen.add(url)
    report={'total':len(rows),'valid':len(valid),'rejected':len(rejected),'checks':['title','duplicate URL','publication year 2023-2026','topic keyword relevance']}
    out=Path('data/articles'); out.mkdir(parents=True,exist_ok=True)
    (out/'validated_articles.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in valid)+'\n',encoding='utf-8')
    (out/'article_validation_report.json').write_text(json.dumps({**report,'rejected_items':rejected},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False)); return 0 if valid else 1
if __name__=='__main__': raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else 'data/articles/cloudflare_articles.json'))
