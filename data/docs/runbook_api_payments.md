# Payments API Runbook

## Overview
The Payments API handles card charges and refunds. Dependencies: Postgres (primary), Redis cache, `charge-jobs` queue workers, and the external GatewayX.

## Common Symptoms → Likely Causes
- **High CPU on API pods** → runaway background tasks after deploy, retry storm, log spam.
- **P95 latency > 800ms** → DB index regressions, cache misses, N+1 queries, cold start after rollout.
- **5xx rate > 5%** → gateway timeouts, DB pool exhaustion, config mismatch during rollout.

## First-Response Diagnostics
1. **Logs:** Search for `"Retrying charge"` or `"Timeout on charge gateway"` in the last 15 min.
2. **Queue depth:** Ensure `charge-jobs` < 100.
3. **DB pool:** Check `no available connections` errors and current pool size.
4. **Cache:** Inspect Redis hit rate; if < 0.85, investigate hot keys or TTLs.
5. **Rollback check:** If last deploy < 30 min ago and 5xx sustained, consider rollback to previous image.

## Detailed Procedures
### A) Investigate CPU Spike
1. Get recent logs for `payments` service.
2. If repeated lines match `"Retrying charge"`, a retry loop may exist → **pause** worker scale-up.
3. Verify queue depth; if > 100, scale **workers** x2 and **API** +1 pod.

### B) High Latency (P95 > 800ms)
1. Run slow query checklist: look for full table scans on `transactions`.
2. Confirm `idx_transactions_created_at` exists.
3. If cache miss rate > 15%, increase TTLs for product config keys.

### C) Rollback Procedure
1. Switch image to `payments-api:<previous_sha>`.
2. Validate: 5xx < 1%, P95 < 500ms for 10 min, error budget burn rate < 1.0.
3. Create incident note and root-cause follow-up task.

## Gotchas
- Post-deploy migration can shrink DB pool size via ORM defaults. Bump to 50 for peak.
- GatewayX has a stricter timeout; match client timeout to 2s with 2 retries max.

## References
- incident_2024_11_db_pool.md
- alerts_cheatsheet.md
