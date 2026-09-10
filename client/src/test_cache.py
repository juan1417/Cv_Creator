import time
from uuid import UUID
from IA_rag.cv_analyzer import analyze_cv

uid = UUID('a99de9b3-0424-4343-9b38-11ef7d4ac695')

t0 = time.time()
r1 = analyze_cv(uid)
t1 = time.time() - t0

t0 = time.time()
r2 = analyze_cv(uid)
t2 = time.time() - t0

print(f"1ra llamada (IA): {t1:.2f}s  overall={r1.overall_score}")
print(f"2da llamada (cache): {t2:.3f}s  overall={r2.overall_score}")
print(f"mismo resultado: {r1.overall_score == r2.overall_score and r1.summary == r2.summary}")
