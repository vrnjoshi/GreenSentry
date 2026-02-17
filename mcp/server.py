from mcp.server.fastmcp import FastMCP

# Initialize the GreenSentry MCP Server
mcp = FastMCP("GreenSentry-Auditor")

@mcp.tool()
def get_system_metrics() -> str:
    """Returns local CPU and Memory usage for green auditing."""
    import psutil
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    return f"Current System Load: CPU {cpu}%, RAM {mem}%"

if __name__ == "__main__":
    mcp.run()