# Alert Cheatsheet

- **High CPU > 85% for 5 min** → Investigate background jobs, retry storms, or log spam.
- **P95 latency > 800ms** → Check DB indexes, cache miss rate, and N+1 queries.
- **5xx rate > 5%** → Inspect gateway timeouts, DB pool, recent deploys.
- **Queue depth > 100** → Scale workers; check gateway health and DLQ rate.
