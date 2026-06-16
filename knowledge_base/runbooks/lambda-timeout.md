# Lambda Timeout Runbook

## Symptoms
- Lambda duration approaching or exceeding configured timeout
- Downstream services reporting errors
- CloudWatch showing p99 duration spikes

## Diagnostic Steps
1. Check if the Lambda timeout is set appropriately for the workload
2. Inspect downstream dependencies — DynamoDB, RDS, external APIs
3. Check if DynamoDB table is throttling (read or write capacity)
4. Review Lambda memory allocation — more memory = more CPU
5. Check for cold start patterns — high p99 with low p50 suggests cold starts
6. Review VPC configuration — Lambdas in VPCs have higher cold start times

## Resolution
- Increase Lambda timeout if workload genuinely requires it
- Increase DynamoDB capacity units if throttling is the cause
- Enable DynamoDB auto-scaling to handle traffic spikes
- Increase Lambda memory allocation if CPU-bound
- Use provisioned concurrency if cold starts are the cause
- Move Lambda out of VPC if VPC is not required

## Prevention
- Always set DynamoDB auto-scaling on tables used by Lambda
- Monitor p99 duration, not just average
- Set CloudWatch alarms at 80% of timeout threshold
