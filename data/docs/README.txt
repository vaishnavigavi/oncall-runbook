OCRA Sample Corpus
==================

This folder contains example documents and logs you can ingest for the On-Call Runbook Agent.

Place the `docs/` directory into your app's data path (e.g., `/app/data/docs`) and the `mock/logs/` under `/app/data/mock/logs/`.

Files:
- runbook_api_payments.md — Primary Payments API runbook with diagnostics and rollback steps
- runbook_queue_worker.md — Queue worker procedures
- incident_2024_11_db_pool.md — Postmortem on DB pool exhaustion
- incident_2025_03_cache_eviction.md — Postmortem on cache eviction incident
- alerts_cheatsheet.md — Mapping from alerts to first checks
- sla_latency_policy.md — SLO/SLA thresholds
- service_map.md — Service dependencies
- faq_known_issues.md — Known failure patterns
- troubleshooting_checklist.md — First 10-min checklist
- mock/logs/payments.log — Sample application log
- mock/logs/worker.log — Sample worker log
