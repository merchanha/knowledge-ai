"""Integration test for stdio MCP transport."""

import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.asyncio
async def test_stdio_client_lists_mcp_tools() -> None:
    """stdio transport exposes the same tool catalog without HTTP auth."""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "knowledge_ai.mcp.stdio"],
    )

    async with (
        stdio_client(server_params) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()
        tools = await session.list_tools()

    tool_names = {tool.name for tool in tools.tools}
    assert "search_knowledge_neurons" in tool_names
    assert "list_commands" in tool_names
    assert "get_project_context" in tool_names
