# AWS Infrastructure Intelligence Server — Build Guide
## For Claude Code

---

## CRITICAL: Git Configuration (Do This First, Every Session)

Before writing a single line of code or making any commit, run these commands:

```bash
git config user.name "Christopher Browne"
git config user.email "cbrowne9472@gmail.com"
```

Verify before every commit:
```bash
git config user.name   # must return: Christopher Browne
git config user.email  # must return: cbrowne9472@gmail.com
```

Never commit without verifying this first.

---

## Project Overview

An MCP (Model Context Protocol) server that connects any AI client (Claude Desktop, Cursor, etc.) to your live AWS infrastructure AND a RAG knowledge base of runbooks, architecture docs, and past incidents.

When you ask "why is my Lambda throwing errors?" it simultaneously:
- Queries live CloudWatch metrics via MCP tools
- Retrieves relevant past incidents and runbooks via RAG
- Returns both so the AI can give an answer grounded in real data AND institutional knowledge

This is not a chatbot. It is a production-grade MCP server with live AWS integration and semantic knowledge retrieval.

---

## How It Works

```
Claude Desktop asks: "Why is the payment Lambda erroring?"
                              ↓
                    Your MCP Server receives the request
                              ↓
              ┌───────────────────────────────┐
              │  MCP Tools (live AWS)         │
              │  get_lambda_metrics()         │
              │  → error rate: 12%            │
              │  → duration p99: 8,200ms      │
              │  get_cloudwatch_alarms()      │
              │  → DynamoDB throttling ALARM  │
              └───────────────────────────────┘
              ┌───────────────────────────────┐
              │  RAG (knowledge base)         │
              │  search_runbooks(             │
              │    "Lambda errors payment")   │
              │  → Past incident #47:         │
              │    DynamoDB capacity caused   │
              │    payment Lambda timeouts    │
              │  → Lambda timeout runbook     │
              └───────────────────────────────┘
                              ↓
              Claude combines both and responds:
              "Your Lambda is erroring because
              DynamoDB is throttling it. This
              matches incident #47 — fix is to
              increase read capacity units."
```

---

## Tech Stack

| Component | Technology |
|---|---|
| MCP Server | Python + MCP SDK (Anthropic official) |
| RAG Engine | LangChain |
| Vector Store | Pinecone (free tier) |
| Embeddings | OpenAI text-embedding-3-small |
| AWS Integration | boto3 |
| Observability | LangSmith |
| Containerization | Docker + Docker Compose |
| Deployment | AWS ECS Fargate |
| Infrastructure | Terraform |

---

## Project Structure

```
aws-intelligence-server/
├── BUILDGUIDE.md
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
├── server/
│   ├── __init__.py
│   ├── main.py                    # MCP server entry point
│   ├── config.py                  # settings + env vars
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── lambda_tools.py        # Lambda metrics + listing
│   │   ├── ec2_tools.py           # EC2 instance queries
│   │   ├── rds_tools.py           # RDS status + metrics
│   │   ├── ecs_tools.py           # ECS service health
│   │   ├── cloudwatch_tools.py    # alarms + metrics
│   │   ├── cost_tools.py          # Cost Explorer
│   │   └── vpc_tools.py           # VPC + networking info
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── ingestor.py            # doc chunking + embedding + upsert
│   │   ├── retriever.py           # semantic search against Pinecone
│   │   └── knowledge_base.py      # unified RAG interface
│   └── tests/
│       ├── test_lambda_tools.py
│       ├── test_cloudwatch_tools.py
│       ├── test_rag.py
│       └── test_integration.py
├── knowledge_base/
│   ├── runbooks/
│   │   ├── lambda-timeout.md
│   │   ├── rds-high-cpu.md
│   │   ├── ec2-memory-pressure.md
│   │   └── ecs-task-failures.md
│   ├── incidents/
│   │   ├── incident-001.md
│   │   ├── incident-002.md
│   │   └── incident-003.md
│   └── architecture/
│       ├── overview.md
│       └── services.md
├── scripts/
│   └── ingest.py                  # CLI to batch ingest documents
├── Dockerfile
└── terraform/
    └── deploy/
        ├── main.tf
        ├── variables.tf
        ├── outputs.tf
        └── iam.tf
```

---

## Environment Variables

Create `.env` in root. Never commit this file.

```bash
# AWS
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1

# OpenAI (embeddings)
OPENAI_API_KEY=sk-...

# Pinecone
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=aws-intelligence
PINECONE_ENVIRONMENT=gcp-starter

# LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_PROJECT=aws-intelligence-server

# App
MCP_SERVER_NAME=aws-intelligence
MCP_SERVER_VERSION=0.1.0
RAG_TOP_K=5
RAG_CHUNK_SIZE=500
RAG_CHUNK_OVERLAP=50
```

---

## .gitignore

```
.env
__pycache__/
*.pyc
.venv/
*.egg-info/
dist/
.pytest_cache/
```

---

## requirements.txt

```
mcp==1.0.0
boto3==1.34.0
langchain==0.2.0
langchain-openai==0.1.0
langchain-pinecone==0.1.0
langchain-community==0.2.0
langsmith==0.1.0
openai==1.12.0
pinecone-client==3.0.0
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
```

---

## MCP Tools Reference

These are all the tools the server exposes to AI clients:

```
AWS Live Tools:
  list_lambdas(region)                     → all Lambda functions + status
  get_lambda_metrics(function_name, hours) → error rate, duration, throttles
  get_ec2_instances(state)                 → instances with type, AZ, tags
  get_rds_instances()                      → DB identifier, engine, status
  get_ecs_services(cluster_name)           → service health + task counts
  get_cloudwatch_alarms(state)             → alarms with metric + threshold
  get_cost_by_service(month)               → cost breakdown by AWS service
  get_cost_trend()                         → this month vs last month delta
  get_vpc_info()                           → VPCs, subnets, route tables

RAG Tools:
  search_runbooks(query)                   → semantic search over knowledge base
  ingest_document(content, title, type)    → add doc to knowledge base live
```

---

## Sample Knowledge Base Documents

Create these files before Day 6. They are what the RAG indexes.

### knowledge_base/runbooks/lambda-timeout.md

```markdown
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
```

### knowledge_base/runbooks/rds-high-cpu.md

```markdown
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
```

### knowledge_base/incidents/incident-001.md

```markdown
# Incident #001 — Payment Service Degradation

## Date
2025-03-15 14:22 UTC

## Duration
23 minutes

## Severity
P1 — revenue impacting

## Summary
Payment Lambda experienced 12% error rate due to DynamoDB read capacity exhaustion during flash sale event.

## Root Cause
The orders-table DynamoDB table had fixed read capacity of 100 RCUs. Flash sale traffic caused 8x normal read volume, exhausting capacity and causing Lambda timeouts.

## Timeline
- 14:22 — CloudWatch alarm fires: DynamoDB throttling on orders-table
- 14:25 — Payment Lambda error rate reaches 12%
- 14:31 — On-call engineer identifies DynamoDB throttling as root cause
- 14:38 — RCU increased from 100 to 800
- 14:45 — Error rate returns to baseline

## Resolution
Increased orders-table read capacity from 100 to 800 RCUs and enabled auto-scaling with min=100, max=2000.

## Action Items
- Enable DynamoDB auto-scaling on all payment-critical tables
- Add CloudWatch alarm when DynamoDB throttling exceeds 10 events/minute
- Pre-scale before known traffic events (sales, launches)

## Lessons Learned
Fixed DynamoDB capacity is dangerous for tables with variable traffic. Always enable auto-scaling on tables accessed by payment-critical services.
```

### knowledge_base/architecture/overview.md

```markdown
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
```

---

## Day-by-Day Build Plan

---

### DAY 1 — Project Setup + First MCP Tool

**Goal:** Repo connected, dependencies installed, MCP server running, Claude Desktop connected, first tool working.

**Setup Steps:**

1. Verify git config is Christopher Browne before anything
2. Create full folder structure (empty files for now)
3. Create `.env` from `.env.example` and fill in real values
4. Create `.gitignore`
5. Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

6. Verify MCP SDK installed: `python -c "import mcp; print(mcp.__version__)"`

7. Create `server/config.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_default_region: str = "us-east-1"
    openai_api_key: str
    pinecone_api_key: str
    pinecone_index_name: str = "aws-intelligence"
    langchain_api_key: str
    langchain_project: str = "aws-intelligence-server"
    mcp_server_name: str = "aws-intelligence"
    mcp_server_version: str = "0.1.0"
    rag_top_k: int = 5
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 50

    class Config:
        env_file = ".env"

settings = Settings()
```

8. Create `server/main.py` with first tool:

```python
import asyncio
import boto3
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from server.config import settings

app = Server(settings.mcp_server_name)

lambda_client = boto3.client(
    "lambda",
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_default_region
)

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_lambdas",
            description="List all Lambda functions in the AWS account with their status, runtime, memory, and last modified time.",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "AWS region to query. Defaults to us-east-1.",
                        "default": "us-east-1"
                    }
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "list_lambdas":
        response = lambda_client.list_functions()
        functions = []
        for fn in response.get("Functions", []):
            functions.append({
                "name": fn["FunctionName"],
                "runtime": fn.get("Runtime", "N/A"),
                "memory_mb": fn["MemorySize"],
                "timeout_seconds": fn["Timeout"],
                "last_modified": fn["LastModified"],
                "description": fn.get("Description", "")
            })
        return [TextContent(type="text", text=json.dumps(functions, indent=2))]
    
    raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

9. Connect to Claude Desktop. Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "aws-intelligence": {
      "command": "python",
      "args": ["-m", "server.main"],
      "cwd": "/path/to/aws-intelligence-server"
    }
  }
}
```

10. Restart Claude Desktop. Verify the server appears in Claude Desktop's tool list.
11. Ask Claude Desktop: "List my Lambda functions" — it should call your tool and return real data.

**Commit message:**
```
feat: initialize MCP server with list_lambdas tool — verified working in Claude Desktop
```

---

### DAY 2 — Lambda Metrics + CloudWatch Alarms Tools

**Goal:** Two most important tools built — live Lambda performance data and alarm state.

**Tasks:**

1. Create `server/tools/lambda_tools.py`:

```python
import boto3
from datetime import datetime, timedelta
from server.config import settings

cw = boto3.client("cloudwatch", region_name=settings.aws_default_region)
lc = boto3.client("lambda", region_name=settings.aws_default_region)

def list_lambdas() -> list[dict]:
    response = lc.list_functions()
    return [
        {
            "name": fn["FunctionName"],
            "runtime": fn.get("Runtime", "N/A"),
            "memory_mb": fn["MemorySize"],
            "timeout_seconds": fn["Timeout"],
            "last_modified": fn["LastModified"],
        }
        for fn in response.get("Functions", [])
    ]

def get_lambda_metrics(function_name: str, hours: int = 24) -> dict:
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    period = 3600  # 1 hour periods

    def get_metric(metric_name: str, stat: str) -> list:
        response = cw.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName=metric_name,
            Dimensions=[{"Name": "FunctionName", "Value": function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            Statistics=[stat]
        )
        return sorted(
            [{"timestamp": str(dp["Timestamp"]), "value": dp[stat]}
             for dp in response["Datapoints"]],
            key=lambda x: x["timestamp"]
        )

    invocations = get_metric("Invocations", "Sum")
    errors = get_metric("Errors", "Sum")
    duration_p99 = get_metric("Duration", "p99")
    duration_avg = get_metric("Duration", "Average")
    throttles = get_metric("Throttles", "Sum")

    total_invocations = sum(dp["value"] for dp in invocations)
    total_errors = sum(dp["value"] for dp in errors)
    error_rate = (total_errors / total_invocations * 100) if total_invocations > 0 else 0

    return {
        "function_name": function_name,
        "time_range_hours": hours,
        "summary": {
            "total_invocations": total_invocations,
            "total_errors": total_errors,
            "error_rate_percent": round(error_rate, 2),
            "total_throttles": sum(dp["value"] for dp in throttles),
        },
        "duration_p99_ms": duration_p99,
        "duration_avg_ms": duration_avg,
        "invocations_per_hour": invocations,
        "errors_per_hour": errors,
    }
```

2. Create `server/tools/cloudwatch_tools.py`:

```python
import boto3
from server.config import settings

cw = boto3.client("cloudwatch", region_name=settings.aws_default_region)

def get_cloudwatch_alarms(state: str = "ALARM") -> list[dict]:
    """
    state options: ALARM | OK | INSUFFICIENT_DATA
    Pass state=ALL to get all alarms regardless of state.
    """
    kwargs = {}
    if state != "ALL":
        kwargs["StateValue"] = state

    response = cw.describe_alarms(**kwargs)
    alarms = []

    for alarm in response.get("MetricAlarms", []):
        alarms.append({
            "name": alarm["AlarmName"],
            "state": alarm["StateValue"],
            "reason": alarm.get("StateReason", ""),
            "metric": alarm.get("MetricName", ""),
            "namespace": alarm.get("Namespace", ""),
            "threshold": alarm.get("Threshold"),
            "comparison": alarm.get("ComparisonOperator", ""),
            "last_updated": str(alarm.get("StateUpdatedTimestamp", "")),
            "description": alarm.get("AlarmDescription", ""),
        })

    return sorted(alarms, key=lambda x: x["last_updated"], reverse=True)
```

3. Register both tools in `server/main.py` — add them to `list_tools()` and handle them in `call_tool()`
4. Write tests in `server/tests/test_lambda_tools.py` — mock boto3 responses and verify output shape
5. Test in Claude Desktop: "What are the error rates for my Lambda functions in the last 24 hours?"

**Commit message:**
```
feat: add Lambda metrics tool with error rate calculation and CloudWatch alarms tool
```

---

### DAY 3 — EC2, RDS, and ECS Tools

**Goal:** Infrastructure status tools for compute and database layers.

**Tasks:**

1. Create `server/tools/ec2_tools.py`:

```python
import boto3
from server.config import settings

ec2 = boto3.client("ec2", region_name=settings.aws_default_region)

def get_ec2_instances(state: str = "running") -> list[dict]:
    filters = []
    if state != "ALL":
        filters.append({"Name": "instance-state-name", "Values": [state]})

    response = ec2.describe_instances(Filters=filters)
    instances = []

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            name = next(
                (tag["Value"] for tag in instance.get("Tags", []) if tag["Key"] == "Name"),
                "unnamed"
            )
            instances.append({
                "instance_id": instance["InstanceId"],
                "name": name,
                "instance_type": instance["InstanceType"],
                "state": instance["State"]["Name"],
                "availability_zone": instance["Placement"]["AvailabilityZone"],
                "private_ip": instance.get("PrivateIpAddress"),
                "public_ip": instance.get("PublicIpAddress"),
                "launch_time": str(instance["LaunchTime"]),
                "tags": {t["Key"]: t["Value"] for t in instance.get("Tags", [])}
            })

    return instances
```

2. Create `server/tools/rds_tools.py`:

```python
import boto3
from server.config import settings

rds = boto3.client("rds", region_name=settings.aws_default_region)

def get_rds_instances() -> list[dict]:
    response = rds.describe_db_instances()
    return [
        {
            "identifier": db["DBInstanceIdentifier"],
            "engine": f"{db['Engine']} {db['EngineVersion']}",
            "instance_class": db["DBInstanceClass"],
            "status": db["DBInstanceStatus"],
            "storage_gb": db["AllocatedStorage"],
            "storage_type": db["StorageType"],
            "multi_az": db["MultiAZ"],
            "publicly_accessible": db["PubliclyAccessible"],
            "endpoint": db.get("Endpoint", {}).get("Address"),
            "port": db.get("Endpoint", {}).get("Port"),
        }
        for db in response["DBInstances"]
    ]
```

3. Create `server/tools/ecs_tools.py`:

```python
import boto3
from server.config import settings

ecs = boto3.client("ecs", region_name=settings.aws_default_region)

def get_ecs_services(cluster_name: str) -> list[dict]:
    service_arns = ecs.list_services(cluster=cluster_name)["serviceArns"]
    if not service_arns:
        return []

    services = ecs.describe_services(cluster=cluster_name, services=service_arns)
    return [
        {
            "name": svc["serviceName"],
            "status": svc["status"],
            "desired_count": svc["desiredCount"],
            "running_count": svc["runningCount"],
            "pending_count": svc["pendingCount"],
            "task_definition": svc["taskDefinition"].split("/")[-1],
            "launch_type": svc.get("launchType", "FARGATE"),
            "health": "healthy" if svc["runningCount"] >= svc["desiredCount"] else "degraded"
        }
        for svc in services["services"]
    ]

def list_ecs_clusters() -> list[str]:
    arns = ecs.list_clusters()["clusterArns"]
    return [arn.split("/")[-1] for arn in arns]
```

4. Register all three in `main.py`
5. Test each against your real AWS account

**Commit message:**
```
feat: add EC2 instance status, RDS database health, and ECS service monitoring tools
```

---

### DAY 4 — Cost Explorer + VPC Tools

**Goal:** Cost breakdown tool and network topology tool.

**Tasks:**

1. Create `server/tools/cost_tools.py`:

```python
import boto3
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from server.config import settings

ce = boto3.client("ce", region_name="us-east-1")  # Cost Explorer is always us-east-1

def get_cost_by_service(month: str = "current") -> dict:
    today = date.today()

    if month == "current":
        start = today.replace(day=1).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
    elif month == "last":
        first_of_current = today.replace(day=1)
        last_month_end = first_of_current - relativedelta(days=1)
        start = last_month_end.replace(day=1).strftime("%Y-%m-%d")
        end = first_of_current.strftime("%Y-%m-%d")
    else:
        start = month + "-01"
        end = (datetime.strptime(start, "%Y-%m-%d") + relativedelta(months=1)).strftime("%Y-%m-%d")

    response = ce.get_cost_and_usage(
        TimePeriod={"Start": start, "End": end},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}]
    )

    services = []
    total = 0.0

    for group in response["ResultsByTime"][0]["Groups"]:
        cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
        if cost > 0.001:
            services.append({
                "service": group["Keys"][0],
                "cost_usd": round(cost, 4)
            })
            total += cost

    return {
        "period": f"{start} to {end}",
        "total_usd": round(total, 4),
        "by_service": sorted(services, key=lambda x: x["cost_usd"], reverse=True)
    }

def get_cost_trend() -> dict:
    current = get_cost_by_service("current")
    last = get_cost_by_service("last")
    delta = current["total_usd"] - last["total_usd"]
    return {
        "current_month_usd": current["total_usd"],
        "last_month_usd": last["total_usd"],
        "delta_usd": round(delta, 4),
        "trend": "up" if delta > 0 else "down",
        "current_breakdown": current["by_service"],
        "last_breakdown": last["by_service"]
    }
```

2. Create `server/tools/vpc_tools.py`:

```python
import boto3
from server.config import settings

ec2 = boto3.client("ec2", region_name=settings.aws_default_region)

def get_vpc_info() -> list[dict]:
    vpcs_response = ec2.describe_vpcs()
    subnets_response = ec2.describe_subnets()
    igw_response = ec2.describe_internet_gateways()

    subnets_by_vpc = {}
    for subnet in subnets_response["Subnets"]:
        vpc_id = subnet["VpcId"]
        if vpc_id not in subnets_by_vpc:
            subnets_by_vpc[vpc_id] = []
        subnets_by_vpc[vpc_id].append({
            "subnet_id": subnet["SubnetId"],
            "cidr": subnet["CidrBlock"],
            "az": subnet["AvailabilityZone"],
            "public": subnet["MapPublicIpOnLaunch"],
            "available_ips": subnet["AvailableIpAddressCount"]
        })

    igws_by_vpc = {}
    for igw in igw_response["InternetGateways"]:
        for attachment in igw.get("Attachments", []):
            igws_by_vpc[attachment["VpcId"]] = igw["InternetGatewayId"]

    vpcs = []
    for vpc in vpcs_response["Vpcs"]:
        name = next(
            (tag["Value"] for tag in vpc.get("Tags", []) if tag["Key"] == "Name"),
            "unnamed"
        )
        vpcs.append({
            "vpc_id": vpc["VpcId"],
            "name": name,
            "cidr": vpc["CidrBlock"],
            "is_default": vpc["IsDefault"],
            "state": vpc["State"],
            "internet_gateway": igws_by_vpc.get(vpc["VpcId"]),
            "subnets": subnets_by_vpc.get(vpc["VpcId"], [])
        })

    return vpcs
```

3. Register both tools in `main.py`
4. Test cost tool — verify it returns your real AWS costs for the current month

**Commit message:**
```
feat: add AWS Cost Explorer tool with trend analysis and VPC network topology tool
```

---

### DAY 5 — Register All Tools in Main

**Goal:** All 9 AWS tools registered and working together in the MCP server.

**Tasks:**

1. Refactor `server/main.py` to cleanly import and register all tools. The file should have one clean `list_tools()` that returns all tool definitions and one `call_tool()` dispatcher:

```python
import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from server.config import settings
from server.tools.lambda_tools import list_lambdas, get_lambda_metrics
from server.tools.cloudwatch_tools import get_cloudwatch_alarms
from server.tools.ec2_tools import get_ec2_instances
from server.tools.rds_tools import get_rds_instances
from server.tools.ecs_tools import get_ecs_services, list_ecs_clusters
from server.tools.cost_tools import get_cost_by_service, get_cost_trend
from server.tools.vpc_tools import get_vpc_info

app = Server(settings.mcp_server_name)

TOOLS = [
    Tool(name="list_lambdas", description="List all Lambda functions with status, runtime, memory, and timeout.", inputSchema={"type": "object", "properties": {"region": {"type": "string", "default": "us-east-1"}}}),
    Tool(name="get_lambda_metrics", description="Get detailed CloudWatch metrics for a Lambda function: error rate, duration p99, throttles, invocation count.", inputSchema={"type": "object", "properties": {"function_name": {"type": "string"}, "hours": {"type": "integer", "default": 24}}, "required": ["function_name"]}),
    Tool(name="get_ec2_instances", description="List EC2 instances with type, state, AZ, and IP addresses.", inputSchema={"type": "object", "properties": {"state": {"type": "string", "default": "running", "enum": ["running", "stopped", "ALL"]}}}),
    Tool(name="get_rds_instances", description="List RDS database instances with engine, status, storage, and Multi-AZ configuration.", inputSchema={"type": "object", "properties": {}}),
    Tool(name="get_ecs_services", description="List ECS services in a cluster with running vs desired task counts and health status.", inputSchema={"type": "object", "properties": {"cluster_name": {"type": "string"}}, "required": ["cluster_name"]}),
    Tool(name="list_ecs_clusters", description="List all ECS cluster names in the account.", inputSchema={"type": "object", "properties": {}}),
    Tool(name="get_cloudwatch_alarms", description="Get CloudWatch alarms by state. Use state=ALARM to see active issues.", inputSchema={"type": "object", "properties": {"state": {"type": "string", "default": "ALARM", "enum": ["ALARM", "OK", "INSUFFICIENT_DATA", "ALL"]}}}),
    Tool(name="get_cost_by_service", description="Get AWS cost breakdown by service for a given month.", inputSchema={"type": "object", "properties": {"month": {"type": "string", "default": "current"}}}),
    Tool(name="get_cost_trend", description="Compare current month vs last month AWS costs with delta and breakdown.", inputSchema={"type": "object", "properties": {}}),
    Tool(name="get_vpc_info", description="Get VPC topology: VPCs, subnets with AZ and CIDR, internet gateways.", inputSchema={"type": "object", "properties": {}}),
]

TOOL_MAP = {
    "list_lambdas": lambda args: list_lambdas(),
    "get_lambda_metrics": lambda args: get_lambda_metrics(args["function_name"], args.get("hours", 24)),
    "get_ec2_instances": lambda args: get_ec2_instances(args.get("state", "running")),
    "get_rds_instances": lambda args: get_rds_instances(),
    "get_ecs_services": lambda args: get_ecs_services(args["cluster_name"]),
    "list_ecs_clusters": lambda args: list_ecs_clusters(),
    "get_cloudwatch_alarms": lambda args: get_cloudwatch_alarms(args.get("state", "ALARM")),
    "get_cost_by_service": lambda args: get_cost_by_service(args.get("month", "current")),
    "get_cost_trend": lambda args: get_cost_trend(),
    "get_vpc_info": lambda args: get_vpc_info(),
}

@app.list_tools()
async def list_tools() -> list[Tool]:
    return TOOLS

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name not in TOOL_MAP:
        raise ValueError(f"Unknown tool: {name}")
    result = TOOL_MAP[name](arguments)
    return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

2. Test all 10 tools in Claude Desktop with real questions
3. Write integration test that calls every tool and verifies no exceptions

**Commit message:**
```
feat: register all 10 AWS tools in MCP server with clean dispatcher pattern
```

---

### DAY 6 — RAG Setup + Document Ingestion

**Goal:** Pinecone index created, documents chunked and embedded, ready for retrieval.

**Tasks:**

1. Sign up for Pinecone free tier at pinecone.io. Create an index named `aws-intelligence` with dimension=1536 (OpenAI embedding size) and metric=cosine.

2. Create `server/rag/ingestor.py`:

```python
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone
import uuid
from server.config import settings

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=settings.openai_api_key
)

pc = Pinecone(api_key=settings.pinecone_api_key)
index = pc.Index(settings.pinecone_index_name)

def ingest_document(content: str, title: str, doc_type: str) -> dict:
    """
    doc_type: runbook | incident | architecture
    Chunks the document and upserts to Pinecone with metadata.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "]
    )

    chunks = splitter.split_text(content)
    vectors = []

    for i, chunk in enumerate(chunks):
        embedding = embeddings.embed_query(chunk)
        vectors.append({
            "id": str(uuid.uuid4()),
            "values": embedding,
            "metadata": {
                "text": chunk,
                "title": title,
                "doc_type": doc_type,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
        })

    index.upsert(vectors=vectors)

    return {
        "title": title,
        "doc_type": doc_type,
        "chunks_created": len(chunks),
        "status": "ingested"
    }

def ingest_file(file_path: str, doc_type: str) -> dict:
    with open(file_path, "r") as f:
        content = f.read()
    title = file_path.split("/")[-1].replace(".md", "")
    return ingest_document(content, title, doc_type)
```

3. Create `scripts/ingest.py`:

```python
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.rag.ingestor import ingest_file

def ingest_directory(directory: str, doc_type: str):
    files = [f for f in os.listdir(directory) if f.endswith(".md")]
    print(f"Ingesting {len(files)} files from {directory} as {doc_type}...")
    for filename in files:
        path = os.path.join(directory, filename)
        result = ingest_file(path, doc_type)
        print(f"  ✓ {result['title']} ({result['chunks_created']} chunks)")

if __name__ == "__main__":
    ingest_directory("knowledge_base/runbooks", "runbook")
    ingest_directory("knowledge_base/incidents", "incident")
    ingest_directory("knowledge_base/architecture", "architecture")
    print("\nIngestion complete.")
```

4. Create all the knowledge base documents from the sample files listed earlier in this guide
5. Run the ingestion: `python scripts/ingest.py`
6. Verify chunks appear in Pinecone console

**Commit message:**
```
feat: implement RAG document ingestion with chunking, OpenAI embeddings, and Pinecone upsert
```

---

### DAY 7 — RAG Retrieval + search_runbooks Tool

**Goal:** Semantic search working, search_runbooks exposed as MCP tool, LangSmith tracing all RAG calls.

**Tasks:**

1. Create `server/rag/retriever.py`:

```python
import os
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.callbacks.tracers import LangChainTracer
from pinecone import Pinecone
from server.config import settings

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=settings.openai_api_key
)

pc = Pinecone(api_key=settings.pinecone_api_key)

tracer = LangChainTracer(project_name=settings.langchain_project)

def search_knowledge_base(query: str, doc_type: str = None, top_k: int = None) -> list[dict]:
    """
    Semantic search over the knowledge base.
    Optionally filter by doc_type: runbook | incident | architecture
    """
    k = top_k or settings.rag_top_k

    vector_store = PineconeVectorStore(
        index_name=settings.pinecone_index_name,
        embedding=embeddings,
        pinecone_api_key=settings.pinecone_api_key
    )

    filter_dict = {}
    if doc_type:
        filter_dict["doc_type"] = {"$eq": doc_type}

    results = vector_store.similarity_search_with_score(
        query,
        k=k,
        filter=filter_dict if filter_dict else None
    )

    return [
        {
            "content": doc.page_content,
            "title": doc.metadata.get("title"),
            "doc_type": doc.metadata.get("doc_type"),
            "relevance_score": round(float(score), 4)
        }
        for doc, score in results
    ]
```

2. Create `server/rag/knowledge_base.py`:

```python
from server.rag.retriever import search_knowledge_base
from server.rag.ingestor import ingest_document

def search_runbooks(query: str) -> dict:
    results = search_knowledge_base(query)
    return {
        "query": query,
        "results_count": len(results),
        "results": results
    }

def add_document(content: str, title: str, doc_type: str) -> dict:
    return ingest_document(content, title, doc_type)
```

3. Register `search_runbooks` and `ingest_document` tools in `main.py`
4. Add to TOOLS list:

```python
Tool(name="search_runbooks", description="Semantically search the infrastructure knowledge base including runbooks, past incidents, and architecture docs. Use this when asked about how to fix issues, past incidents, or how services are configured.", inputSchema={"type": "object", "properties": {"query": {"type": "string"}, "doc_type": {"type": "string", "enum": ["runbook", "incident", "architecture"]}}, "required": ["query"]}),
Tool(name="ingest_document", description="Add a new document to the knowledge base. Use this to add runbooks, incident reports, or architecture documentation.", inputSchema={"type": "object", "properties": {"content": {"type": "string"}, "title": {"type": "string"}, "doc_type": {"type": "string", "enum": ["runbook", "incident", "architecture"]}}, "required": ["content", "title", "doc_type"]}),
```

5. Test in Claude Desktop: "Search for runbooks about Lambda timeouts"
6. Verify the search traces appear in LangSmith

**Commit message:**
```
feat: implement semantic RAG retrieval and expose search_runbooks and ingest_document MCP tools
```

---

### DAY 8 — End-to-End Integration Testing

**Goal:** All 12 tools working together. Test real combined queries that use both AWS tools and RAG simultaneously.

**Tasks:**

1. Write `server/tests/test_integration.py` — tests that call multiple tools for the same scenario:

```python
import pytest
from server.tools.lambda_tools import list_lambdas, get_lambda_metrics
from server.tools.cloudwatch_tools import get_cloudwatch_alarms
from server.rag.knowledge_base import search_runbooks

def test_lambda_diagnostic_flow():
    """Simulate a full diagnostic: get metrics + search runbooks"""
    lambdas = list_lambdas()
    assert isinstance(lambdas, list)

    if lambdas:
        fn_name = lambdas[0]["name"]
        metrics = get_lambda_metrics(fn_name, hours=1)
        assert "error_rate_percent" in metrics["summary"]

    alarms = get_cloudwatch_alarms(state="ALL")
    assert isinstance(alarms, list)

    results = search_runbooks("Lambda timeout errors")
    assert results["results_count"] >= 0

def test_cost_analysis_flow():
    from server.tools.cost_tools import get_cost_by_service, get_cost_trend
    current = get_cost_by_service("current")
    assert "total_usd" in current
    assert "by_service" in current

    trend = get_cost_trend()
    assert "delta_usd" in trend
    assert "trend" in trend
```

2. Test these combined prompts in Claude Desktop and document the results:
   - "My payment service seems slow. Check the Lambda metrics and search for relevant runbooks."
   - "What are my most expensive AWS services this month and how does that compare to last month?"
   - "Are there any CloudWatch alarms firing? Search for runbooks related to any issues found."
   - "List all my Lambda functions and tell me which ones have the highest error rates."
   - "Add this incident to the knowledge base: [paste an incident description]"

3. Fix any issues found during testing

**Commit message:**
```
test: integration tests for combined AWS tool and RAG scenarios — all passing
```

---

### DAY 9 — Ingest 20+ Documents + LangSmith Dashboard

**Goal:** Knowledge base populated with enough content to make retrieval genuinely useful. LangSmith traces reviewed and optimized.

**Tasks:**

1. Write 10 more knowledge base documents — runbooks for common AWS issues:
   - `ecs-task-failures.md` — ECS tasks crashing or failing to start
   - `rds-connection-limit.md` — too many database connections
   - `s3-access-denied.md` — S3 permission troubleshooting
   - `api-gateway-5xx.md` — API Gateway returning 5xx errors
   - `cloudwatch-alarm-runbook.md` — how to respond to common alarms
   - `cost-spike-runbook.md` — investigating unexpected cost increases
   - `vpc-connectivity.md` — diagnosing connectivity between services
   - `iam-permission-errors.md` — fixing IAM permission denied errors
   - `incident-002.md` — second past incident example
   - `incident-003.md` — third past incident example

2. Re-run `python scripts/ingest.py` to index all new documents

3. Open LangSmith at smith.langchain.com → your project. Review:
   - Which queries retrieved the most relevant chunks (high relevance scores)
   - Which queries retrieved irrelevant chunks (low scores)
   - Average retrieval latency

4. Tune `RAG_CHUNK_SIZE` and `RAG_CHUNK_OVERLAP` based on what you see. Re-ingest and compare results.

**Commit message:**
```
docs: expand knowledge base to 20+ documents and tune RAG chunking parameters based on LangSmith traces
```

---

### DAY 10 — Docker + Claude Desktop Config

**Goal:** Everything runs in Docker, Claude Desktop config documented, zero-friction setup for anyone cloning the repo.

**Tasks:**

1. Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "server.main"]
```

2. Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  mcp-server:
    build: .
    env_file: .env
    volumes:
      - ./knowledge_base:/app/knowledge_base
    stdin_open: true
    tty: true
```

3. Update Claude Desktop config to use Docker:

```json
{
  "mcpServers": {
    "aws-intelligence": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--env-file", "/absolute/path/to/.env",
        "aws-intelligence-server"
      ]
    }
  }
}
```

4. Verify it still works via Docker

**Commit message:**
```
feat: Dockerize MCP server and document Claude Desktop configuration
```

---

### DAY 11 — Terraform Deployment on ECS

**Goal:** MCP server deployed on AWS ECS Fargate so it runs 24/7 without your laptop.

**Tasks:**

1. Create `terraform/deploy/iam.tf`:

```hcl
resource "aws_iam_role" "mcp_server" {
  name = "aws-intelligence-mcp-server"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_policy" "mcp_server_policy" {
  name = "aws-intelligence-read-only"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:ListFunctions",
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:DescribeAlarms",
          "ec2:DescribeInstances",
          "ec2:DescribeVpcs",
          "ec2:DescribeSubnets",
          "ec2:DescribeInternetGateways",
          "ec2:DescribeRouteTables",
          "rds:DescribeDBInstances",
          "ecs:ListClusters",
          "ecs:ListServices",
          "ecs:DescribeServices",
          "ce:GetCostAndUsage"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach" {
  role       = aws_iam_role.mcp_server.name
  policy_arn = aws_iam_policy.mcp_server_policy.arn
}
```

2. Create `terraform/deploy/main.tf` with ECS Fargate task definition and service, ECR repository, and CloudWatch log group

3. Run `terraform apply` and verify the service is running

**Commit message:**
```
feat: Terraform deployment on ECS Fargate with least-privilege read-only IAM policy
```

---

### DAY 12 — GitHub Actions CI

**Goal:** On every push to main, run all tests automatically.

**Tasks:**

1. Create `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest server/tests/ -v
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: us-east-1
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          PINECONE_API_KEY: ${{ secrets.PINECONE_API_KEY }}
          PINECONE_INDEX_NAME: aws-intelligence
          LANGCHAIN_API_KEY: ${{ secrets.LANGCHAIN_API_KEY }}
```

2. Add secrets to GitHub repo settings
3. Push and verify CI passes

**Commit message:**
```
feat: GitHub Actions CI pipeline running all tests on push to main
```

---

### DAY 13 — README + Demo Video

**Goal:** README complete enough that anyone can clone and run in under 10 minutes. Demo recorded.

**README must include:**

- What it is (2 sentences)
- Architecture diagram
- Prerequisites (AWS account, Pinecone, OpenAI key)
- Setup steps (clone, env vars, ingest docs, connect Claude Desktop)
- All 12 tools listed with descriptions
- 10 example prompts that work well
- How to add new documents to the knowledge base
- LangSmith dashboard screenshot showing traces
- Link to demo video

**Best example prompts to document:**
```
"Check all CloudWatch alarms and search for runbooks related to any firing alarms"
"What are my top 3 most expensive AWS services this month?"
"My payment Lambda seems slow — get its metrics and find relevant past incidents"
"List all my ECS services and tell me which ones are unhealthy"
"Search for runbooks about RDS high CPU"
"What's the architecture of my VPC? How many subnets and availability zones?"
"Compare my AWS costs this month vs last month"
"Add this post-mortem to the knowledge base: [paste post-mortem]"
```

**Demo video script (3 minutes):**
1. Show Claude Desktop with the MCP server connected (30s)
2. Ask "are there any CloudWatch alarms firing?" — show live AWS data (30s)
3. Ask "search for runbooks about Lambda timeouts" — show RAG retrieval (30s)
4. Ask a combined question: "My Lambda is erroring — check metrics and find relevant runbooks" — show both tools firing simultaneously (60s)
5. Show LangSmith traces for the RAG call (30s)

**Commit message:**
```
docs: complete README with setup guide, example prompts, and demo video
```

---

### DAY 14 — Final Polish

**Goal:** Code clean, tests passing, repo presentation-ready.

**Tasks:**

1. Add docstrings to every tool function
2. Add type hints everywhere
3. Make sure every tool has a test
4. Add error handling for AWS API rate limits
5. Review README one more time
6. Make sure the repo has no secrets, no `.env` file, no `.terraform` directory

**Commit message:**
```
chore: final polish — docstrings, type hints, error handling, and test coverage
```

---

## Commit Checklist (Every Day)

```bash
# 1. Verify author identity — ALWAYS first
git config user.name   # must be: Christopher Browne
git config user.email  # must be: cbrowne9472@gmail.com

# 2. Review what you're staging
git status
git diff --staged

# 3. Commit
git add .
git commit -m "feat: [message from this day's plan]"

# 4. Push
git push origin main
```

---

## IAM Permissions Needed

The AWS credentials in `.env` need these permissions (read-only is enough for all tools except Cost Explorer which requires billing access):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:ListFunctions",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:DescribeAlarms",
        "ec2:DescribeInstances",
        "ec2:DescribeVpcs",
        "ec2:DescribeSubnets",
        "ec2:DescribeInternetGateways",
        "ec2:DescribeRouteTables",
        "rds:DescribeDBInstances",
        "ecs:ListClusters",
        "ecs:ListServices",
        "ecs:DescribeServices",
        "ce:GetCostAndUsage"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Connecting Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "aws-intelligence": {
      "command": "python",
      "args": ["-m", "server.main"],
      "cwd": "/absolute/path/to/aws-intelligence-server",
      "env": {
        "PYTHONPATH": "/absolute/path/to/aws-intelligence-server"
      }
    }
  }
}
```

Restart Claude Desktop after editing this file. The server name "aws-intelligence" will appear in Claude Desktop's connected tools list.

---

## Week Summary

| Week | Days | Focus |
|---|---|---|
| Week 1 | 1-5 | MCP server + all 10 AWS live tools |
| Week 1 | 6-7 | RAG setup + search tool |
| Week 2 | 8-9 | Integration testing + knowledge base population |
| Week 2 | 10-11 | Docker + Terraform deployment |
| Week 2 | 12-14 | CI + README + demo |
