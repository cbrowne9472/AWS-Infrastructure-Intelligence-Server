# Cost Spike Investigation Runbook

## Symptoms
- AWS Cost Explorer showing unexpected month-over-month increase
- Daily spend alert firing above budget threshold
- Specific service cost jumping without a corresponding traffic increase

## Diagnostic Steps
1. Open Cost Explorer → group by Service → identify the top contributor to the spike
2. Drill into the service by Usage Type to pinpoint the specific resource dimension (e.g., EC2 `BoxUsage:t3.large` vs `DataTransfer-Out`)
3. Check if the spike correlates with a recent deployment, traffic event, or infrastructure change
4. For EC2: look for unintentionally running instances or instances left on after testing
5. For S3: check for unexpected `GetObject` request volume or data transfer costs from a new feature
6. For Lambda: check invocation count — runaway event-driven triggers can generate millions of invocations
7. For data transfer: identify which services are generating cross-region or internet-bound traffic
8. Check AWS Trusted Advisor for underutilized resources that are running unnecessarily

## Common Root Causes
- **Forgotten test infrastructure**: EC2/RDS instances left running after a spike test or proof of concept
- **Runaway Lambda trigger**: SQS or DynamoDB stream misconfiguration causes infinite retry loops
- **Data transfer**: New feature transferring large objects across regions or to the internet
- **Snapshot accumulation**: EBS or RDS snapshots never cleaned up, growing over time
- **NAT Gateway**: Traffic routing through NAT Gateway instead of VPC endpoints for AWS services

## Resolution
- Terminate unused instances, delete abandoned snapshots
- Fix the Lambda trigger configuration causing the loop
- Add VPC endpoints for S3 and DynamoDB to eliminate NAT Gateway costs
- Tag all resources with environment and owner to make future audits faster

## Prevention
- Set AWS Budgets alerts at 80% and 100% of monthly target by service
- Require tags (Environment, Owner, Project) as a deployment gate in CI/CD
- Schedule Lambda to check for untagged resources weekly
- Review Cost Explorer anomaly detection alerts every Monday
