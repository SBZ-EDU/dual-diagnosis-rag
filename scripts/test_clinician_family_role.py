"""Static regression checks for the clinician-family role and advanced module."""
from pathlib import Path
idx=Path('cloudflare/src/index.js').read_text(encoding='utf-8')
page=Path('cloudflare/src/page.js').read_text(encoding='utf-8')
checks={
 'role_whitelist': "'clinician_family'" in idx,
 'role_prompt': "clinician_family:'مخاطب هم پزشک است" in idx,
 'dual_role_boundary': 'رابطه دوگانه' in idx,
 'advanced_module': "id:'family-clinician-sister-advanced'" in idx,
 'twelve_questions': idx[idx.index("id:'family-clinician-sister-advanced'"):].split(']},',1)[0].count('{"q"') == 12,
 'separate_learning_track': "audience:'clinician_family'" in idx,
 'hard_pass_score': "passScore:83" in idx,
 'article_sources': idx[idx.index("id:'family-clinician-sister-advanced'"):].split('],type:',1)[0].count("url:'https://") >= 8,
 'question_evidence_metadata': idx[idx.index("id:'family-clinician-sister-advanced'"):].split('\n]},',1)[0].count('"evidence"') == 12,
 'feedback_has_why_source_method': all(x in idx for x in ['why:q.evidence?.why','sourceUrl:q.evidence?.url','method:q.evidence?.method']),
 'ui_explanations': all(x in page for x in ['پاسخ صحیح','چرا؟','روش منبع']),
 'answer_keys_hidden': 'MODULES.map(publicModule)' in idx and 'const {quiz=[],passScore=70,...safe}=m' in idx,
 'randomized_questions_options': 'quiz:shuffle(quiz.map' in idx and 'o:shuffle(q.o)' in idx,
 'text_answer_grading': 'byId.get(i)===q.o[q.a]' in idx,
 'dynamic_failure_message': 'حداقل ${passScore}٪ لازم است' in idx,
 'ui_demo': "demoRole('clinician_family')" in page,
 'ui_chat_option': 'value="clinician_family"' in page,
}
assert all(checks.values()),checks
print({'status':'PASS',**checks})
