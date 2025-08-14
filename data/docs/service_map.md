# Service Map: Payments

- `payments-api` → depends on Postgres `txdb`, Redis `cache`, and queue `charge-jobs`.
- External: GatewayX for card charges.
- Critical DB indexes: `idx_transactions_created_at`, `idx_transactions_user_id`.
