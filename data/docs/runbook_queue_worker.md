# Queue Worker Runbook (charge-jobs)

## Purpose
Processes asynchronous charge attempts and retries with exponential backoff.

## Alerts
- Queue depth > 120 for 10 min.
- Age of oldest job > 5 min.

## Diagnostics
1. Inspect worker logs for `"Retrying charge job id="`.
2. Confirm backoff not stuck at max.
3. Check GatewayX status page (if available).

## Remediation
- Scale workers by +2 replicas temporarily.
- Clear poisoned jobs (marked failed > 5 attempts) into DLQ.
- If retry storm, cap concurrency to 50% until gateway stabilizes.
