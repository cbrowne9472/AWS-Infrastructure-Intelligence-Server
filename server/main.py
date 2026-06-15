import asyncio
import json

import boto3
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from server.config import settings

app = Server(settings.mcp_server_name)

lambda_client = boto3.client(
    "lambda",
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_default_region,
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
                        "default": "us-east-1",
                    }
                },
            },
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "list_lambdas":
        response = lambda_client.list_functions()
        functions = []
        for fn in response.get("Functions", []):
            functions.append(
                {
                    "name": fn["FunctionName"],
                    "runtime": fn.get("Runtime", "N/A"),
                    "memory_mb": fn["MemorySize"],
                    "timeout_seconds": fn["Timeout"],
                    "last_modified": fn["LastModified"],
                    "description": fn.get("Description", ""),
                }
            )
        return [TextContent(type="text", text=json.dumps(functions, indent=2))]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
