# Incident: DB Pool Exhaustion (2024-11-07)

**Symptom:** 5xx surge on Payments API; messages: `no available connections`.
**Impact:** ~7% of requests failed for 18 minutes.
**Root Cause:** ORM upgrade changed default pool size to 5 per pod; at peak we needed 50.
**Fix:** Set `POOL_SIZE=50`, `MAX_OVERFLOW=20`; add connection reuse; add dashboard alert for pool saturation.
**Follow-ups:**
- Pre-deploy load smoke with pool metrics.
- Add migration checklist item for DB pool config.
