"""Stdio MCP entry point for local agent testing."""

import asyncio

from knowledge_ai.mcp.server import mcp_server


def main() -> None:
    """Run the MCP server over stdio (no HTTP auth — dev transport only)."""
    asyncio.run(mcp_server.run_stdio_async())


if __name__ == "__main__":
    main()
