from mcp.server.fastmcp import FastMCP
import psutil
import os
from dotenv import load_dotenv

# Load secrets from .env file into the environment
load_dotenv()

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

    return (f"🌱 GreenSentry Local Audit Report:\n"
            f"- CPU Usage: {cpu}%\n"
            f"- RAM Usage: {ram}%\n"
            f"- Est. Power Draw: {est_watts:.2f}W\n"
            f"- Carbon Footprint: {carbon_impact:.5f}g CO2/hr")

@mcp.tool()
def get_azure_carbon_estimate() -> str:
    """Fetches real Azure cloud spend for the current month and estimates its carbon footprint."""
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")

    if not subscription_id:
        return "⚠️ AZURE_SUBSCRIPTION_ID not set. Create a .env file based on .env.example."

    try:
        from azure.identity import DefaultAzureCredential
        from azure.mgmt.consumption import ConsumptionManagementClient
        from datetime import datetime, timezone

        credential = DefaultAzureCredential()
        client = ConsumptionManagementClient(credential, subscription_id)

        # Query current month's usage summary
        now = datetime.now(timezone.utc)
        billing_period = now.strftime("%Y-%m")
        scope = f"/subscriptions/{subscription_id}"

        # Get usage details for the current billing period
        total_cost_usd = 0.0
        currency = "USD"
        item_count = 0

        usage = client.usage_details.list(
            scope=scope,
            filter=f"properties/usageStart ge '{now.strftime('%Y-%m-01')}'"
        )

        for item in usage:
            if hasattr(item, 'cost_in_billing_currency'):
                total_cost_usd += item.cost_in_billing_currency or 0
            if hasattr(item, 'billing_currency'):
                currency = item.billing_currency or currency
            item_count += 1

        # 🧪 Carbon estimation:
        # Azure's global average carbon intensity: ~0.297 kg CO2 per kWh (2023 Sustainability Report)
        # Average Azure cost per kWh of compute: ~$0.10 (rough estimate for general workloads)
        # Formula: cost_usd / cost_per_kwh * carbon_intensity_kg
        if total_cost_usd > 0:
            estimated_kwh = total_cost_usd / 0.10
            estimated_carbon_kg = estimated_kwh * 0.297
            return (f"☁️ GreenSentry Azure Audit Report ({billing_period}):\n"
                    f"- Subscription: AIDevDaysHackathon\n"
                    f"- Usage Items Found: {item_count}\n"
                    f"- Total Cloud Spend: {total_cost_usd:.4f} {currency}\n"
                    f"- Est. Energy Consumed: {estimated_kwh:.4f} kWh\n"
                    f"- Est. Carbon Footprint: {estimated_carbon_kg:.6f} kg CO2\n"
                    f"- Source: Azure Consumption API (live data)")
        else:
            return (f"☁️ GreenSentry Azure Audit Report ({billing_period}):\n"
                    f"- Subscription: AIDevDaysHackathon\n"
                    f"- Usage Items Found: {item_count}\n"
                    f"- Total Cloud Spend: $0.00 (no billable usage this month)\n"
                    f"- Carbon Footprint: 0.000000 kg CO2\n"
                    f"- Source: Azure Consumption API (live data)")

    except Exception as e:
        return f"⚠️ Azure query failed: {str(e)}"

if __name__ == "__main__":
    mcp.run()
