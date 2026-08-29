"""دریافت رایگان مقالات تازه PubMed و تولید گزارش تغییر شواهد."""
import json, os, urllib.parse, urllib.request
from datetime import date, timedelta

# [tiab] = فقط عنوان و چکیده؛ بدون آن PubMed تطبیق‌های بسیار آزاد برمی‌گرداند
QUERY = '(psychosis[tiab] OR schizophreni*[tiab]) AND (substance use[tiab] OR substance-related[tiab] OR dual diagnosis[tiab] OR borderline[tiab]) AND (treatment[tiab] OR therapy[tiab] OR guideline*[tiab] OR trial[tiab])'

def _json(url):
    with urllib.request.urlopen(url, timeout=30) as r: return json.load(r)

def fetch(days=7, limit=20):
    since = (date.today()-timedelta(days=days)).isoformat()
    q = urllib.parse.quote(f'{QUERY} AND ("{since}"[Date - Publication] : "3000"[Date - Publication])')
    base='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
    ids=_json(f'{base}esearch.fcgi?db=pubmed&retmode=json&retmax={limit}&sort=relevance&term={q}')["esearchresult"]["idlist"]
    if not ids: return []
    s=_json(f'{base}esummary.fcgi?db=pubmed&retmode=json&id={",".join(ids)}')["result"]
    return [{"pmid":i,"title":s[i].get("title"),"date":s[i].get("pubdate"),
             "url":f"https://pubmed.ncbi.nlm.nih.gov/{i}/"} for i in ids]

def main():
    papers=fetch(int(os.getenv('ARTICLE_DAYS','7')))
    os.makedirs('data/articles',exist_ok=True)
    out=f'data/articles/pubmed-{date.today().isoformat()}.json'
    with open(out,'w',encoding='utf-8') as f: json.dump(papers,f,ensure_ascii=False,indent=2)
    print(f'{len(papers)} articles -> {out}')
if __name__=='__main__': main()
