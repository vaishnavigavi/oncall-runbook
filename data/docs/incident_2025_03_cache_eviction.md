# Incident: Cache Eviction & Hot Key (2025-03-18)

**Symptom:** P95 latency > 1.2s, DB CPU > 85%, Redis hit rate dropped to 60%.
**Root Cause:** Hot key `product:pricing:global` evicted due to low maxmemory; sudden fan-out to DB.
**Fix:** Raise Redis maxmemory, switch to `allkeys-lru`, pin hot key with TTL=900s and pre-warm on deploy.
**Actions:**
- Add alert when hit rate < 0.8 for 5 min.
- Add pre-warm step in CI/CD.
