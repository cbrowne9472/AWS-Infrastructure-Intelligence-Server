# CloudWatch Alarm Response Runbook

## Overview
This runbook covers how to respond to common CloudWatch alarms. When an alarm fires, follow the steps for its metric.

## Lambda Errors Alarm
**Trigger**: Error rate > threshold for N minutes
1. Open the Lambda function in the console
2. Check CloudWatch Logs Insights: `filter @message like "ERROR"` in the last 1 hour
3. Identify the error type — unhandled exception, timeout, or downstream failure
4. If timeout: see lambda-timeout runbook
5. If downstream failure: check DynamoDB/RDS/external API health

## RDS CPU Alarm
**Trigger**: CPU > 75% for 5 minutes
1. Open Performance Insights for the RDS instance
2. Identify top SQL queries by CPU load
3. If a single query is responsible, add a missing index or optimize it
4. If all queries are slow, consider scaling up the instance class
5. See rds-high-cpu runbook for detailed steps

## ECS Service Unhealthy Tasks Alarm
**Trigger**: RunningTaskCount < DesiredTaskCount
1. Check ECS service events for stopped task reason
2. Review CloudWatch Logs for the task log group
3. See ecs-task-failures runbook for detailed steps

## DynamoDB Throttling Alarm
**Trigger**: ThrottledRequests > 0 for sustained period
1. Identify which table is throttling (check Namespace=AWS/DynamoDB, TableName dimension)
2. Check if auto-scaling is enabled — if not, enable it immediately
3. If auto-scaling is enabled, check if it is scaling fast enough (scale-out cooldown too long)
4. Temporary fix: manually increase read/write capacity units
5. Long-term fix: enable on-demand billing mode for unpredictable traffic

## High Cost Alarm
**Trigger**: Estimated charges above monthly budget
1. Open Cost Explorer and filter by service for today
2. Identify the service driving the spike
3. See cost-spike-runbook for detailed investigation steps

## Prevention
- Always have a documented owner and response time SLA for every alarm
- Review alarm thresholds quarterly — what was appropriate last quarter may not be now
- Use alarm actions to auto-notify the on-call engineer via SNS → PagerDuty/Slack
