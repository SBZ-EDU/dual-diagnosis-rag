"""Offline smoke test for topical coverage of the priority evidence catalog."""
import json,re
rows=[json.loads(x) for x in open('data/evidence/priority_evidence_100.jsonl',encoding='utf-8') if x.strip()]
queries={
 'meth_treatment':['methamphetamine','treatment'],
 'stimulant_psychosis':['stimulant','psychosis'],
 'gambling':['gambling','disorder'],
 'family_burden':['family','burden'],
 'family_intervention':['family','intervention'],
}
results={}
for name,terms in queries.items():
 scored=[]
 for r in rows:
  text=(r['title']+' '+r['abstract']).lower(); score=sum(text.count(t) for t in terms)
  if score:scored.append((score,r['title'],r['url']))
 scored.sort(reverse=True); hits=scored[:5]; results[name]=len(hits)
 assert len(hits)>=3,f'{name}: insufficient retrieval candidates'
 print('\n',name)
 for score,title,url in hits[:3]:print(score,title[:90],url)
print({'status':'PASS','topical_tests':results})
