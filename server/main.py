import asyncio
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from server.config import settings
from server.tools.cloudwatch_tools import get_cloudwatch_alarms
from server.tools.cost_tools import get_cost_by_service, get_cost_trend
from server.tools.ec2_tools import get_ec2_instances
from server.tools.ecs_tools import get_ecs_services, list_ecs_clusters
from server.tools.lambda_tools import get_lambda_metrics, list_lambdas
from server.tools.rds_tools import get_rds_instances
from server.tools.vpc_tools import get_vpc_info

app = Server(settings.mcp_server_name)


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_lambdas",
            description="List all Lambda functions with status, runtime, memory, and timeout.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_lambda_metrics",
            description="Get detailed CloudWatch metrics for a Lambda function: error rate, duration p99, throttles, invocation count.",
            inputSchema={
                "type": "object",
                "properties": {
                    "function_name": {"type": "string"},
                    "hours": {"type": "integer", "default": 24},
                },
                "required": ["function_name"],
            },
        ),
        Tool(
            name="get_cloudwatch_alarms",
            description="Get CloudWatch alarms by state. Use state=ALARM to see active issues.",
            inputSchema={
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "default": "ALARM",
                        "enum": ["ALARM", "OK", "INSUFFICIENT_DATA", "ALL"],
                    }
                },
            },
        ),
        Tool(
            name="get_ec2_instances",
            description="List EC2 instances with type, state, AZ, and IP addresses.",
            inputSchema={
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "default": "running",
                        "enum": ["running", "stopped", "ALL"],
                    }
                },
            },
        ),
        Tool(
            name="get_rds_instances",
            description="List RDS database instances with engine, status, storage, and Multi-AZ configuration.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_ecs_services",
            description="List ECS services in a cluster with running vs desired task counts and health status.",
            inputSchema={
                "type": "object",
                "properties": {"cluster_name": {"type": "string"}},
                "required": ["cluster_name"],
            },
        ),
        Tool(
            name="list_ecs_clusters",
            description="List all ECS cluster names in the account.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_cost_by_service",
            description="Get AWS cost breakdown by service for a given month.",
            inputSchema={
                "type": "object",
                "properties": {"month": {"type": "string", "default": "current"}},
            },
        ),
        Tool(
            name="get_cost_trend",
            description="Compare current month vs last month AWS costs with delta and breakdown.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_vpc_info",
            description="Get VPC topology: VPCs, subnets with AZ and CIDR, internet gateways.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "list_lambdas":
        result = list_lambdas()
    elif name == "get_lambda_metrics":
        result = get_lambda_metrics(arguments["function_name"], arguments.get("hours", 24))
    elif name == "get_cloudwatch_alarms":
        result = get_cloudwatch_alarms(arguments.get("state", "ALARM"))
    elif name == "get_ec2_instances":
        result = get_ec2_instances(arguments.get("state", "running"))
    elif name == "get_rds_instances":
        result = get_rds_instances()
    elif name == "get_ecs_services":
        result = get_ecs_services(arguments["cluster_name"])
    elif name == "list_ecs_clusters":
        result = list_ecs_clusters()
    elif name == "get_cost_by_service":
        result = get_cost_by_service(arguments.get("month", "current"))
    elif name == "get_cost_trend":
        result = get_cost_trend()
    elif name == "get_vpc_info":
        result = get_vpc_info()
    else:
        raise ValueError(f"Unknown tool: {name}")

    return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
