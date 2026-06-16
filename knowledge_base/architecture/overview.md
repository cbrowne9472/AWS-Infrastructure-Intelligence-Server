# Infrastructure Architecture Overview

## Regions
Primary: us-east-1
Disaster recovery: us-west-2

## Compute
- Payment service: Lambda (Node.js 18, 512MB, 30s timeout)
- User service: ECS Fargate (t3.medium equivalent, 2 tasks min)
- Admin API: EC2 (t3.large, single instance, not HA)

## Databases
- orders-table: DynamoDB, on-demand billing, TTL enabled on status field
- users-db: RDS PostgreSQL 15, db.t3.medium, Multi-AZ enabled
- sessions: ElastiCache Redis, cache.t3.micro, single node

## Critical Dependencies
- Payment Lambda depends on: orders-table (DynamoDB), Stripe API
- User service depends on: users-db (RDS), sessions (ElastiCache)
- All services depend on: us-east-1 being available

## Known Risks
- Admin API is a single EC2 instance with no auto-scaling — single point of failure
- ElastiCache Redis is single node — session loss on node failure
- Payment Lambda timeout is 30s but Stripe API can take up to 25s under load
