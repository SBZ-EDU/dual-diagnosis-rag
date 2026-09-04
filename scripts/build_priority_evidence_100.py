"""Build a transparent 100-record priority evidence catalog from OpenAlex.
This is automated triage, not a substitute for full-text risk-of-bias appraisal.
"""
import json, math, urllib.parse, urllib.request
from pathlib import Path
QUERIES={
 'meth_treatment':'methamphetamine stimulant use disorder treatment contingency management CBT matrix',
 'psychosis_dual':'methamphetamine psychosis dual diagnosis integrated treatment schizophrenia substance use',
 'gambling':'gambling disorder substance use comorbidity treatment family financial harm',
 'family_finance':'addiction affected families caregiver financial burden coercion enabling boundaries',
 'family_intervention':'CRAFT community reinforcement family training substance use systematic review',
}
TOPIC=['methamphetamine','stimulant','psychosis','substance use','addiction','gambling','family','caregiver','financial','craft','contingency management','dual diagnosis']
DESIGNS={'systematic-review':30,'meta-analysis':35,'randomized-controlled-trial':30,'review':18,'article':5,'guideline':35}
def abstract(inv):
 if not inv:return ''
 return ' '.join(w for _,w in sorted((p,w) for w,ps in inv.items() for p in ps))
def fetch(q):
 url='https://api.openalex.org/works?search='+urllib.parse.quote(q)+'&filter='+urllib.parse.quote('from_publication_date:2015-01-01,to_publication_date:2026-09-04,has_abstract:true,is_retracted:false')+'&sort=cited_by_count:desc&per-page=200&mailto=research@example.invalid'
 return json.load(urllib.request.urlopen(url,timeout=60))['results']
def norm(w,topic):
 title=w.get('title') or ''; ab=abstract(w.get('abstract_inverted_index')); text=(title+' '+ab).lower(); typ=w.get('type') or 'article'; cited=w.get('cited_by_count',0); oa=w.get('open_access') or {}; loc=w.get('best_oa_location') or w.get('primary_location') or {}
 rel=sum(1 for x in TOPIC if x in text); score=DESIGNS.get(typ,3)+min(25,5*math.log10(cited+1))+rel*3+(5 if oa.get('is_oa') else 0)+(5 if loc.get('pdf_url') else 0)
 return {'openalex_id':w['id'],'doi':w.get('doi'),'title':title,'abstract':ab,'year':w.get('publication_year'),'journal':((w.get('primary_location') or {}).get('source') or {}).get('display_name'),'type':typ,'cited_by_count':cited,'is_retracted':False,'open_access':oa.get('is_oa',False),'pdf_url':loc.get('pdf_url'),'url':loc.get('landing_page_url') or w.get('doi') or w['id'],'topic_seed':topic,'topic_hits':rel,'priority_score':round(score,2),'screening_status':'automated_priority_not_clinician_approved','source':'OpenAlex'}
def main():
 pool={}
 for topic,q in QUERIES.items():
  for w in fetch(q):
   r=norm(w,topic); old=pool.get(r['openalex_id'])
   if not old or r['priority_score']>old['priority_score']:pool[r['openalex_id']]=r
 # Exclude non-clinical homonyms (e.g. "brand addiction") and non-paper material.
 substance=('methamphetamine','stimulant use','substance use','drug use','addiction','opioid','cannabis','alcohol use','gambling disorder')
 clinical=('treatment','therapy','intervention','psychosis','disorder','family','caregiver','financial burden','relapse','recovery','guideline','trial','review')
 eligible=[]
 for r in pool.values():
  text=(r['title']+' '+r['abstract']).lower()
  if r['type'] not in {'article','review','preprint'}:continue
  if not any(x in text for x in substance) or not any(x in text for x in clinical):continue
  if 'brand addiction' in text or 'social media addiction' in text:continue
  # transparent study-design inference from title only
  title=r['title'].lower()
  r['inferred_design']='systematic_review' if 'systematic review' in title else ('meta_analysis' if 'meta-analysis' in title or 'meta analysis' in title else ('randomized_trial' if 'randomized' in title or 'randomised' in title else ('guideline' if 'guideline' in title else 'other_peer_reviewed')))
  eligible.append(r)
 rows=sorted(eligible,key=lambda x:(x['inferred_design']!='other_peer_reviewed',x['priority_score'],x['cited_by_count']),reverse=True)
 # Require meaningful topical overlap; balance categories first, then fill globally.
 chosen=[]; used=set()
 for topic in QUERIES:
  for r in [x for x in rows if x['topic_seed']==topic and x['topic_hits']>=2][:15]:
   if r['openalex_id'] not in used:chosen.append(r);used.add(r['openalex_id'])
 for r in rows:
  if len(chosen)>=100:break
  if r['topic_hits']>=2 and r['openalex_id'] not in used:chosen.append(r);used.add(r['openalex_id'])
 out=Path('data/evidence');out.mkdir(parents=True,exist_ok=True)
 (out/'priority_evidence_100.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in chosen[:100])+'\n',encoding='utf-8')
 report={'pool_unique':len(pool),'selected':len(chosen[:100]),'open_access':sum(x['open_access'] for x in chosen[:100]),'direct_pdf':sum(bool(x['pdf_url']) for x in chosen[:100]),'retracted':sum(x['is_retracted'] for x in chosen[:100]),'by_topic':{k:sum(x['topic_seed']==k for x in chosen[:100]) for k in QUERIES},'by_type':{},'warning':'Automated priority screening only; full-text appraisal and clinician approval still required.'}
 for x in chosen[:100]:report['by_type'][x['type']]=report['by_type'].get(x['type'],0)+1
 (out/'priority_evidence_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
 if len(chosen)<100:raise SystemExit('Fewer than 100 eligible records')
if __name__=='__main__':main()
