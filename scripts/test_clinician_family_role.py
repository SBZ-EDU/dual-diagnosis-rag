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
 'ui_demo': "demoRole('clinician_family')" in page,
 'ui_chat_option': 'value="clinician_family"' in page,
}
assert all(checks.values()),checks
print({'status':'PASS',**checks})
