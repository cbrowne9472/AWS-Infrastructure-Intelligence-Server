# Services Reference

## Payment Service
- **Runtime**: Lambda (Node.js 18)
- **Memory**: 512MB, Timeout: 30s
- **Trigger**: API Gateway POST /payments
- **Dependencies**: orders-table (DynamoDB), Stripe API (external)
- **Key metrics**: ErrorRate, Duration p99, ThrottledRequests
- **Alarms**: ErrorRate > 1% for 2 minutes, Duration p99 > 25s
- **On-call priority**: P1 — revenue impacting

## User Service
- **Runtime**: ECS Fargate (Node.js 18, Express)
- **Resources**: 1 vCPU, 512MB memory per task
- **Scaling**: min 2 tasks, max 10 tasks (target CPU 60%)
- **Dependencies**: users-db (RDS PostgreSQL), sessions (ElastiCache Redis)
- **Key metrics**: CPUUtilization, MemoryUtilization, RunningTaskCount
- **Alarms**: RunningTaskCount < 2, CPU > 80% for 5 minutes
- **On-call priority**: P2 — user-facing but payment not affected

## Admin API
- **Runtime**: EC2 t3.large (single instance)
- **Known risk**: No auto-scaling, single point of failure
- **Dependencies**: users-db (RDS PostgreSQL), S3 (reports bucket)
- **Key metrics**: CPUUtilization, StatusCheckFailed
- **On-call priority**: P3 — internal tool only

## orders-table (DynamoDB)
- **Billing mode**: On-demand
- **TTL**: Enabled on `status` field (expired after 90 days)
- **Access patterns**: GetItem by orderId, Query by userId + createdAt
- **Key metrics**: ConsumedReadCapacityUnits, ThrottledRequests
- **Alarms**: ThrottledRequests > 10 per minute

## users-db (RDS PostgreSQL)
- **Version**: PostgreSQL 15
- **Instance class**: db.t3.medium
- **Multi-AZ**: Enabled
- **Max connections**: 170 (db.t3.medium default)
- **Connection pool**: 5 connections per app instance (user-service), RDS Proxy pending
- **Alarms**: CPU > 75%, DatabaseConnections > 119 (70% of max)

## sessions (ElastiCache Redis)
- **Node type**: cache.t3.micro
- **Cluster mode**: Single node (no replication)
- **Known risk**: Session loss on node failure — no replica
- **TTL**: Sessions expire after 24 hours of inactivity

## S3 Buckets
- **reports-bucket**: Admin-generated reports, versioning enabled, lifecycle to Glacier after 90 days
- **assets-bucket**: Static frontend assets, CloudFront distribution in front
- **logs-bucket**: ALB and CloudFront access logs, lifecycle delete after 30 days
