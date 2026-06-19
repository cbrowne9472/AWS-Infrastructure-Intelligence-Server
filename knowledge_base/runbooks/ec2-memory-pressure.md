# EC2 Memory Pressure Runbook

## Symptoms
- Application OOM (out of memory) kills or crashes
- High swap usage on the instance
- System becoming unresponsive or very slow
- CloudWatch memory metric (requires CloudWatch Agent) showing > 85% used

## Diagnostic Steps
1. SSH into the instance and check memory: `free -h` and `top` or `htop`
2. Identify the top memory consumers: `ps aux --sort=-%mem | head -20`
3. Check for memory leaks — is usage growing over time or is it a sustained high baseline?
4. Check swap usage: `swapon --show` and `vmstat 1 5`
5. Review application heap dumps or memory profiles if available
6. Check if the instance type is appropriate: `curl http://169.254.169.254/latest/meta-data/instance-type`
7. Verify CloudWatch Agent is publishing `mem_used_percent` metric — if not, you are flying blind

## Resolution
- **Immediate**: Restart the memory-leaking process (not the instance) to reclaim memory
- **Short-term**: Increase instance type to one with more RAM (requires stop/start)
- **Correct fix**: Profile and fix the memory leak in the application
- **If swap thrashing**: Add swap space as temporary relief (`dd if=/dev/zero of=/swapfile bs=1G count=4`)

## Prevention
- Always install the CloudWatch Agent on EC2 instances and publish memory metrics
- Set CloudWatch alarm on `mem_used_percent > 80%` for 5 minutes
- Right-size instances based on actual memory usage, not CPU alone
- For Java applications: explicitly set `-Xmx` heap size to less than the instance RAM
- Consider ECS or Lambda for stateless workloads — managed compute handles OOM restarts automatically
