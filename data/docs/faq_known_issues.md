# Known Issues & Patterns

- **Retry Storms:** Caused by misconfigured backoff or gateway partial outage. Look for repeated 'Retrying charge' lines.
- **Pool Exhaustion:** After ORM upgrade. Ensure POOL_SIZE=50.
- **N+1 Queries:** On `/transactions?user_id=...` when preload missing.
