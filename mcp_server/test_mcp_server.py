"""
Minimal MCP Test Server - Federation Canary 🐤
Zero dependencies beyond the mcp SDK.
If this works in Antigravity, Python MCP is supported.
"""

import json
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

app = Server("federation-canary")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="hello_federation",
            description="🐤 Canary test: proves Python MCP servers work in this IDE. Returns a greeting.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Who to greet (default: Federation)"
                    }
                },
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "hello_federation":
        who = arguments.get("name", "Federation")
        return [TextContent(type="text", text=json.dumps({
            "status": "alive",
            "message": f"🐤 Hello {who}! The canary lives. Python MCP is working!",
            "server": "federation-canary",
            "tools": 1
        }, indent=2))]
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
