"""Build 100 international + 100 Iran-affiliated paper metadata corpora from OpenAlex.
No copyrighted full text is copied. Persian-language status is preserved, never fabricated.
"""
import json, re, urllib.parse, urllib.request
from pathlib import Path
QUERY='("substance use" OR addiction OR opioid OR cannabis) AND (psychosis OR schizophrenia OR "dual diagnosis" OR treatment)'
TAGS={
 'pharmacotherapy':['methadone','buprenorphine','naltrexone','antipsychotic','clozapine','medication'],
 'psychotherapy':['psychotherapy','cbt','dbt','motivational','counseling'],
 'harm_reduction':['harm reduction','naloxone','overdose','needle'],
 'rehabilitation':['rehabilitation','recovery','residential','daycare'],
 'family':['family','caregiver'], 'prevention':['prevention','screening','early intervention'],
 'opioid':['opioid','opiate','heroin'], 'stimulant':['amphetamine','methamphetamine','stimulant'],
 'cannabis':['cannabis','marijuana'], 'alcohol':['alcohol'], 'psychosis':['psychosis','schizophrenia']}
def get(filter_):
 u='https://api.openalex.org/works?search='+urllib.parse.quote(QUERY)+'&filter='+urllib.parse.quote(filter_)+'&sort=relevance_score:desc&per-page=100&mailto=research@example.invalid'
 with urllib.request.urlopen(u,timeout=60) as r:return json.load(r)['results']
def inv(idx):
 if not idx:return ''
 a=[]
 for word,poss in idx.items():
  for p in poss:a.append((p,word))
 return ' '.join(w for _,w in sorted(a))
def norm(x,corpus):
 title=x.get('title') or ''; abstract=inv(x.get('abstract_inverted_index')); text=(title+' '+abstract).lower()
 return {'openalex_id':x.get('id'),'doi':x.get('doi'),'title':title,'abstract':abstract,'year':x.get('publication_year'),'date':x.get('publication_date'),'language':x.get('language') or 'unknown','journal':((x.get('primary_location') or {}).get('source') or {}).get('display_name'),'url':(x.get('primary_location') or {}).get('landing_page_url') or x.get('doi') or x.get('id'),'open_access':(x.get('open_access') or {}).get('is_oa',False),'corpus':corpus,'iran_affiliated':any(i.get('country_code')=='IR' for a in x.get('authorships',[]) for i in a.get('institutions',[])),'treatment_tags':[k for k,vs in TAGS.items() if any(v in text for v in vs)],'type':x.get('type'),'cited_by_count':x.get('cited_by_count',0),'source':'OpenAlex'}
def save(name,rows):
 p=Path('data/articles')/name;p.write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in rows)+'\n',encoding='utf-8');print(name,len(rows),sum(x['language']=='fa' for x in rows))
def main():
 international=[norm(x,'international') for x in get('from_publication_date:2020-01-01,has_doi:true')]
 iran=[norm(x,'iran_affiliated') for x in get('institutions.country_code:IR,from_publication_date:2015-01-01')]
 save('international_100.jsonl',international[:100]);save('iran_affiliated_100.jsonl',iran[:100])
 report={'international':len(international[:100]),'iran_affiliated':len(iran[:100]),'original_persian':sum(x['language']=='fa' for x in iran[:100]),'notice':'Iran-affiliated does not mean Persian-language. Titles are not machine-translated or misrepresented.'}
 Path('data/articles/extended_corpora_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(report)
if __name__=='__main__':main()
