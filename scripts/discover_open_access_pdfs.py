"""Discover legal Open Access PDF URLs and estimate sizes; does not bypass paywalls."""
import concurrent.futures, json, urllib.parse, urllib.request
from pathlib import Path
FILES=['data/articles/international_100.jsonl','data/articles/iran_affiliated_100.jsonl']
def api(ids):
 f='openalex_id:'+('|'.join(x.rsplit('/',1)[-1] for x in ids));u='https://api.openalex.org/works?filter='+urllib.parse.quote(f)+'&per-page=50&mailto=research@example.invalid'
 return json.load(urllib.request.urlopen(u,timeout=60))['results']
def size(url):
 if not url:return None
 try:
  req=urllib.request.Request(url,method='HEAD',headers={'User-Agent':'Mozilla/5.0 research metadata checker'})
  with urllib.request.urlopen(req,timeout=12) as r:
   n=r.headers.get('Content-Length');return int(n) if n and n.isdigit() else None
 except:return None
def main():
 rows=[]
 for f in FILES:rows += [json.loads(x) for x in open(f,encoding='utf-8') if x.strip()]
 byid={x['openalex_id'].rsplit('/',1)[-1]:x for x in rows}; works=[]
 ids=list(byid)
 for i in range(0,len(ids),50):works+=api(ids[i:i+50])
 manifest=[]
 for w in works:
  oid=w['id'].rsplit('/',1)[-1]; base=byid.get(oid,{}); loc=w.get('best_oa_location') or {}; pdf=loc.get('pdf_url')
  manifest.append({'openalex_id':w['id'],'title':w.get('title'),'corpus':base.get('corpus'),'doi':w.get('doi'),'is_oa':(w.get('open_access') or {}).get('is_oa',False),'oa_status':(w.get('open_access') or {}).get('oa_status'),'pdf_url':pdf,'landing_page_url':loc.get('landing_page_url')})
 with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
  sizes=list(ex.map(lambda x:size(x['pdf_url']),manifest))
 for x,n in zip(manifest,sizes):x['content_length_bytes']=n
 out=Path('data/articles/open_access_pdf_manifest.jsonl');out.write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in manifest)+'\n',encoding='utf-8')
 pdf=[x for x in manifest if x['pdf_url']]; known=[x['content_length_bytes'] for x in pdf if x['content_length_bytes']]
 report={'records':len(manifest),'open_access_records':sum(x['is_oa'] for x in manifest),'direct_pdf_urls':len(pdf),'sizes_known':len(known),'known_total_bytes':sum(known),'known_total_mb':round(sum(known)/1024/1024,2),'estimated_total_mb_if_avg':round((sum(known)/len(known)*len(pdf))/1024/1024,2) if known else None,'notice':'Only legal OA URLs; no paywall bypass. Size is an HTTP estimate.'}
 Path('data/articles/open_access_pdf_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(report)
if __name__=='__main__':main()
