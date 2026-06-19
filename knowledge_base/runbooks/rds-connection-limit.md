# RDS Connection Limit Runbook

## Symptoms
- Application errors: "too many connections" or "FATAL: remaining connection slots are reserved"
- `DatabaseConnections` CloudWatch metric at or near the instance max
- New application instances failing to start because they cannot acquire a DB connection
- Existing connections timing out under load

## Diagnostic Steps
1. Check current connection count: `SELECT count(*) FROM pg_stat_activity;` (PostgreSQL)
2. Compare to instance limit: `SHOW max_connections;`
3. Identify which applications or hosts hold the most connections: `SELECT client_addr, count(*) FROM pg_stat_activity GROUP BY client_addr ORDER BY count DESC;`
4. Look for idle connections that are not being released: `SELECT state, count(*) FROM pg_stat_activity GROUP BY state;`
5. Check if RDS Proxy is configured — if not, that is the likely root cause
6. Verify application connection pool settings (min/max pool size, idle timeout)

## Resolution
- **Immediate**: Restart application instances to force connection release if idle connections are stuck
- **Short-term**: Increase `max_connections` via RDS parameter group (requires reboot)
- **Correct fix**: Enable RDS Proxy — it multiplexes thousands of app connections into a small pool of real DB connections
- Set connection pool `max_size` in application to no more than `max_connections / num_app_instances * 0.8`

## Prevention
- Always use RDS Proxy for any application with more than 2 instances or serverless compute
- Set idle connection timeout in the connection pool (e.g., 10 minutes)
- Alert on DatabaseConnections > 80% of max to get ahead of the problem
- Use `pg_stat_activity` dashboards to track connection usage trends over time
