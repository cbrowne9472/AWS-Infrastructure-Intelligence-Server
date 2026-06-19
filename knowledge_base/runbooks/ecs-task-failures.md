# ECS Task Failures Runbook

## Symptoms
- ECS service running count below desired count
- Tasks repeatedly starting and stopping (thrashing)
- Deployment stuck with unhealthy tasks
- Health check failures visible in service events

## Diagnostic Steps
1. Check ECS service events: `aws ecs describe-services --cluster <name> --services <name>`
2. Look for stopped task reasons in the console — OOMKilled, health check failure, or exit code
3. Check CloudWatch Logs for the task's log group to see application errors
4. Verify the task definition memory and CPU limits are appropriate for the workload
5. Check if the container health check command is correct and the grace period is sufficient
6. Confirm the target group health check path returns 200 for the ALB/NLB
7. Check if the ECS service IAM role has necessary permissions
8. Verify the container image exists in ECR and the task execution role can pull it

## Resolution
- **OOMKilled**: Increase task memory in the task definition
- **Health check failures**: Increase health check grace period or fix the health check endpoint
- **Exit code errors**: Fix the application bug — check CloudWatch Logs for the exception
- **Image pull errors**: Verify ECR permissions on the task execution role
- **Networking failures**: Confirm the task's security group allows outbound to its dependencies

## Prevention
- Always set realistic memory limits — add 20% headroom above peak observed usage
- Use health check grace periods of at least 60s for services with slow startup
- Set deployment minimum healthy percent to 100% for critical services
- Enable CloudWatch Container Insights for deeper task-level metrics
- Test new task definitions with a single task before full deployment
