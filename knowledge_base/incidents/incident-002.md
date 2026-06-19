# Incident #002 — RDS Connection Exhaustion During Deployment

## Date
2025-04-08 09:14 UTC

## Duration
41 minutes

## Severity
P2 — significant user impact, checkout partially degraded

## Summary
A rolling deployment of the user service tripled the number of application instances briefly, exhausting the RDS connection limit on users-db and causing login and checkout failures for approximately 30% of users.

## Root Cause
The user service opens 10 database connections per instance on startup. During the rolling deployment, old and new instances ran simultaneously, pushing the active connection count from 80 to 240 — exceeding the db.t3.medium max_connections of 170. New connections were refused with "FATAL: remaining connection slots are reserved for non-replication superuser connections."

## Timeline
- 09:14 — Deployment of user-service v2.4.1 begins (rolling update, 3 instances)
- 09:17 — DatabaseConnections alarm fires: 172 connections on users-db
- 09:19 — Login endpoint error rate reaches 28%
- 09:23 — On-call engineer identifies RDS connection exhaustion in CloudWatch
- 09:31 — Deployment paused; old instances begin terminating
- 09:47 — Connection count drops to 85; error rate returns to baseline
- 09:55 — Deployment resumed with max_surge=1 and connection pool max_size reduced to 5

## Resolution
Reduced connection pool `max_size` from 10 to 5 per instance and set deployment `max_surge` to 1 (no more than 1 extra instance during rollout). RDS Proxy scheduled for implementation in Q3.

## Action Items
- Implement RDS Proxy for users-db to multiplex connections
- Add pre-deployment check: verify projected connection count stays below 80% of max_connections
- Set DatabaseConnections alarm threshold to 70% (119) instead of 100% (170)

## Lessons Learned
Connection pool sizing must account for the maximum number of instances that can run simultaneously, not just the steady-state count. Rolling deployments can temporarily double or triple instance counts.
