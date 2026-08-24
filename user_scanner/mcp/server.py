import asyncio
import sys
import argparse
import logging

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
except ImportError:
    print("Error: The 'mcp' dependency is not installed.", file=sys.stderr)
    print("Please install it using: pip install user-scanner[mcp]", file=sys.stderr)
    sys.exit(1)

from user_scanner.mcp.schemas import get_tool_list
from user_scanner.mcp.handlers import call_tool

# Configure logging to write to stderr so it doesn't corrupt the JSON-RPC stdout stream
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("user-scanner-mcp")

app = Server("user-scanner")


@app.list_tools()  # type: ignore[attr-defined]
async def handle_list_tools():
    """Provide the list of tools available from this server."""
    return get_tool_list()


@app.call_tool()  # type: ignore[attr-defined]
async def handle_call_tool(name: str, arguments: dict | None):
    """Execute the requested tool and return the OSINT scan results."""
    return await call_tool(name, arguments)


async def run():
    """Run the server over standard input/output streams."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


def main():
    """Entry point for the MCP server script."""
    parser = argparse.ArgumentParser(description="user-scanner MCP server")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging output to stderr",
    )
    args = parser.parse_args()

    if not args.verbose:
        logger.setLevel(logging.CRITICAL)
    else:
        logger.setLevel(logging.INFO)
        logger.info("Starting user-scanner MCP server over stdio in verbose mode...")

    asyncio.run(run())


if __name__ == "__main__":
    main()
