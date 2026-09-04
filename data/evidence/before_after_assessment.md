# Before/After RAG assessment

Benchmark question (same in both calls):

> برای درمان اختلال مصرف مت‌آمفتامین همراه روان‌پریشی، کدام مداخلات روانی‌اجتماعی بیشترین پشتوانه را دارند و محدودیت شواهد چیست؟

## Before: base Llama without retrieved evidence

The answer was generic, listed family/group/individual interventions, provided no citations, and omitted the strongest guideline signal for contingency management.

## After: same Llama with five priority-evidence records

The answer became more topical and mentioned CBT, CM and family interventions, but failed citation-format compliance and mistranslated CM as «مدیریت تنبیهی». This is unsafe terminology; CM is now fixed in the production system prompt as «مدیریت اقتضایی مبتنی بر تقویت مثبت».

## Verdict

- Retrieval coverage: improved.
- Specificity: improved.
- Citation faithfulness: not yet sufficient.
- Persian terminology: required a guardrail fix.
- Clinical readiness: **FAIL / review required**.
- Fine-tuning should not be deployed until a clinician-approved instruction dataset and held-out safety benchmark exist.

The raw outputs and retrieved source list are in `before_after_rag_comparison.json`.
