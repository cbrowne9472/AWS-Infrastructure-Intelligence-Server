# RDS High CPU Runbook

## Symptoms
- RDS CPU utilization above 80% sustained
- Application query latency increasing
- Connection timeouts from application layer

## Diagnostic Steps
1. Check RDS Performance Insights for top SQL queries by CPU
2. Identify queries without indexes using slow query log
3. Check for missing indexes on frequently joined columns
4. Check connection count — too many connections causes overhead
5. Check for long-running transactions holding locks

## Resolution
- Add indexes for queries identified in Performance Insights
- Kill long-running transactions if blocking others
- Implement connection pooling (RDS Proxy) if connection count is high
- Scale up instance class if CPU is consistently above 80%
- Read replicas for read-heavy workloads

## Prevention
- Enable Performance Insights on all production RDS instances
- Set CloudWatch alarm on CPU > 75% for 5 minutes
- Use RDS Proxy for all application database connections
- Review query execution plans before deploying schema changes
