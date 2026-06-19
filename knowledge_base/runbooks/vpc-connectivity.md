# VPC Connectivity Troubleshooting Runbook

## Symptoms
- Service cannot reach a dependency (database, external API, another microservice)
- Connection timeouts with no response (as opposed to a refused connection)
- Lambda or ECS task failing to connect to RDS, ElastiCache, or external endpoints

## Diagnostic Steps

### Step 1 — Identify the direction of failure
- Is the source in a private subnet trying to reach the internet? → Check NAT Gateway
- Is the source in a VPC trying to reach another VPC? → Check VPC peering or Transit Gateway
- Is the source trying to reach another AWS service (S3, DynamoDB)? → Check VPC endpoints

### Step 2 — Check Security Groups
1. Source security group: does it allow outbound on the destination port?
2. Destination security group: does it allow inbound from the source security group (or CIDR)?
3. Security groups are stateful — only check the initiating direction

### Step 3 — Check Network ACLs
1. NACLs are stateless — both inbound AND outbound rules must allow the traffic
2. Check rule order — NACLs evaluate rules in order, lowest number first
3. Ephemeral port range (1024–65535) must be allowed outbound on the destination NACL

### Step 4 — Check Route Tables
1. Is there a route to the destination CIDR in the subnet's route table?
2. For internet access: is there a route to the Internet Gateway (0.0.0.0/0 → igw-xxx)?
3. For NAT access: is there a route 0.0.0.0/0 → nat-xxx in the private subnet's route table?

### Step 5 — Use VPC Reachability Analyzer
Run a path analysis from source ENI to destination ENI — it will identify the exact block.

## Resolution
- Add missing security group inbound rule on the destination
- Fix NACL to allow ephemeral return traffic outbound
- Add missing route in route table pointing to the correct gateway
- Add a VPC endpoint for AWS services to avoid routing through NAT Gateway

## Prevention
- Document security group rules with descriptions explaining what they allow and why
- Use VPC Flow Logs to capture all accepted and rejected traffic for post-incident analysis
- Prefer security group references over CIDR rules for intra-VPC traffic (more maintainable)
