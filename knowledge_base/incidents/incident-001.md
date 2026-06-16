# Incident #001 — Payment Service Degradation

## Date
2025-03-15 14:22 UTC

## Duration
23 minutes

## Severity
P1 — revenue impacting

## Summary
Payment Lambda experienced 12% error rate due to DynamoDB read capacity exhaustion during flash sale event.

## Root Cause
The orders-table DynamoDB table had fixed read capacity of 100 RCUs. Flash sale traffic caused 8x normal read volume, exhausting capacity and causing Lambda timeouts.

## Timeline
- 14:22 — CloudWatch alarm fires: DynamoDB throttling on orders-table
- 14:25 — Payment Lambda error rate reaches 12%
- 14:31 — On-call engineer identifies DynamoDB throttling as root cause
- 14:38 — RCU increased from 100 to 800
- 14:45 — Error rate returns to baseline

## Resolution
Increased orders-table read capacity from 100 to 800 RCUs and enabled auto-scaling with min=100, max=2000.

## Action Items
- Enable DynamoDB auto-scaling on all payment-critical tables
- Add CloudWatch alarm when DynamoDB throttling exceeds 10 events/minute
- Pre-scale before known traffic events (sales, launches)

## Lessons Learned
Fixed DynamoDB capacity is dangerous for tables with variable traffic. Always enable auto-scaling on tables accessed by payment-critical services.
