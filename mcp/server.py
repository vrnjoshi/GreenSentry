from mcp.server.fastmcp import FastMCP
import psutil

# Initialize the GreenSentry MCP Server
mcp = FastMCP("GreenSentry-Auditor")

@mcp.tool()
def get_green_metrics() -> str:
    """Calculates estimated carbon impact based on current Mac hardware load."""
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    
    # 🧪 The Science:  
    # Average Mac power draw is roughly 5W (idle) to 60W (load). Source: https://eclecticlight.co/2024/02/23/apple-silicon-2-power-and-thermal-glory/
    # Carbon Intensity (avg): 0.475g CO2 per kWh
    
    est_watts = 5 + (cpu * 0.55) 
    carbon_impact = (est_watts / 1000) * 0.475 
    
    return (f"🌱 GreenSentry Audit Report:\n"
            f"- CPU Usage: {cpu}%\n"
            f"- RAM Usage: {ram}%\n"
            f"- Est. Power Draw: {est_watts:.2f}W\n"
            f"- Carbon Footprint: {carbon_impact:.5f}g CO2/hr")

if __name__ == "__main__":
    mcp.run()