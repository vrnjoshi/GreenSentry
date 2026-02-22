"""
GreenSentry Agent - Day 3
An AI agent powered by Semantic Kernel (Microsoft Agent Framework) that can
audit your system's carbon footprint and review code for energy efficiency.

How it works:
  1. You type a question in plain English
  2. The agent decides which tool(s) to call to get real data
  3. It combines the data and gives you a concrete recommendation
  4. It remembers the full conversation so you can ask follow-up questions

Tools:
  - get_green_metrics        — local CPU/RAM carbon audit
  - get_azure_carbon_estimate — live Azure cloud spend → carbon estimate
  - audit_code               — green code review powered by fine-tuned model
"""

import asyncio
import os
import psutil
from datetime import datetime, timezone
from typing import Annotated

from dotenv import load_dotenv
from openai import AsyncAzureOpenAI
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function

# =============================================================================
# Few-shot examples for the code auditor
# =============================================================================
# These are the same examples used to fine-tune the model.
# When the fine-tuned deployment isn't available yet, this system prompt
# teaches the base model to respond in exactly the same REFACTOR/WHY format.
# Think of it like handing an intern a cheat sheet before their first shift.

_AUDITOR_SYSTEM_PROMPT = """You are a Green Software SRE. Identify carbon-heavy code and provide a green refactor.

Always respond in this exact format:
REFACTOR: <the improved code>
WHY: <one sentence explaining the energy/carbon saving>

Examples:
---
User: Audit this code for energy efficiency: while True: print('Checking updates...')
REFACTOR: import time
while True:
    print('Checking updates...')
    time.sleep(60)
WHY: Adding a sleep timer prevents 100% CPU usage during idle loops.
---
User: Audit this code for energy efficiency: data = [i for i in range(1000000)]
for x in data: print(x)
REFACTOR: for x in range(1000000): print(x)
WHY: Using a generator/range instead of a full list saves significant RAM.
---
User: Audit this code for energy efficiency: import pandas as pd
df = pd.read_csv('huge_file.csv')
REFACTOR: import pandas as pd
for chunk in pd.read_csv('huge_file.csv', chunksize=1000): process(chunk)
WHY: Processing data in chunks prevents memory spikes and disk swapping.
---
User: Audit this code for energy efficiency: cursor.execute('SELECT * FROM global_users')
REFACTOR: cursor.execute('SELECT username FROM global_users WHERE user_id = ?', (uid,))
WHY: Selecting only necessary columns reduces data transfer energy (Network Carbon).
---
User: Audit this code for energy efficiency: for x in big_list:
    result = heavy_computation(x)
    process(result)
REFACTOR: import functools
@functools.lru_cache(maxsize=128)
def cached_heavy(x): return heavy_computation(x)

for x in big_list:
    process(cached_heavy(x))
WHY: Caching/Memoization prevents the CPU from repeating expensive calculations.
"""


# =============================================================================
# SECTION 1: The Plugin (the agent's "senses")
# =============================================================================
# A Plugin is a class whose methods the agent can call as tools.
# The agent reads each function's description to decide WHEN to use it —
# just like a doctor deciding which test to run based on your symptoms.

class GreenSentryPlugin:
    """Carbon auditing tools available to the GreenSentry agent."""

    @kernel_function(
        name="get_green_metrics",
        description="Measures the current machine's CPU and RAM usage and calculates "
                    "the estimated power draw in watts and carbon footprint in grams "
                    "of CO2 per hour. Call this when the user asks about local machine "
                    "energy use, CPU load, or carbon footprint of their computer."
    )
    def get_green_metrics(self) -> Annotated[str, "Local hardware carbon audit report"]:
        """Reads Mac CPU/RAM and estimates carbon footprint using real power profiles."""
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent

        # Mac power draw: 5W idle, scales with CPU load
        # Source: https://eclecticlight.co/2024/02/23/apple-silicon-2-power-and-thermal-glory/
        # Carbon intensity: 0.475g CO2 per Wh (average US grid)
        est_watts = 5 + (cpu * 0.55)
        carbon_impact = (est_watts / 1000) * 0.475

        return (
            f"Local Hardware Audit:\n"
            f"- CPU Usage: {cpu}%\n"
            f"- RAM Usage: {ram}%\n"
            f"- Estimated Power Draw: {est_watts:.2f}W\n"
            f"- Carbon Footprint: {carbon_impact:.5f}g CO2/hr"
        )

    @kernel_function(
        name="get_azure_carbon_estimate",
        description="Queries the Azure Consumption API to get real cloud spending for "
                    "the current month and estimates the carbon footprint of that cloud "
                    "usage. Call this when the user asks about Azure cloud costs, cloud "
                    "carbon footprint, or cloud energy usage."
    )
    def get_azure_carbon_estimate(self) -> Annotated[str, "Azure cloud carbon audit report"]:
        """Calls the live Azure Consumption API and converts spend to a carbon estimate."""
        subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")

        if not subscription_id:
            return "AZURE_SUBSCRIPTION_ID not set in .env file."

        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.consumption import ConsumptionManagementClient

            credential = DefaultAzureCredential()
            client = ConsumptionManagementClient(credential, subscription_id)

            now = datetime.now(timezone.utc)
            billing_period = now.strftime("%Y-%m")
            scope = f"/subscriptions/{subscription_id}"
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

            # Azure carbon intensity: 0.297 kg CO2/kWh (Microsoft 2023 Sustainability Report)
            # Avg Azure compute cost: ~$0.10/kWh (estimate for general workloads)
            if total_cost_usd > 0:
                estimated_kwh = total_cost_usd / 0.10
                estimated_carbon_kg = estimated_kwh * 0.297
                return (
                    f"Azure Cloud Audit ({billing_period}):\n"
                    f"- Usage Items: {item_count}\n"
                    f"- Total Spend: ${total_cost_usd:.4f} {currency}\n"
                    f"- Estimated Energy: {estimated_kwh:.4f} kWh\n"
                    f"- Carbon Footprint: {estimated_carbon_kg:.6f} kg CO2\n"
                    f"- Source: Azure Consumption API (live data)"
                )
            else:
                return (
                    f"Azure Cloud Audit ({billing_period}):\n"
                    f"- Usage Items Found: {item_count}\n"
                    f"- Total Spend: $0.00 (no billable usage this month)\n"
                    f"- Carbon Footprint: 0.000000 kg CO2\n"
                    f"- Source: Azure Consumption API (live data)"
                )

        except Exception as e:
            return f"Azure query failed: {str(e)}"

    @kernel_function(
        name="audit_code",
        description="Audits a snippet of Python code for energy efficiency and returns "
                    "a greener refactored version with an explanation. Call this when the "
                    "user shares code and asks for a green refactor, energy audit, carbon "
                    "review, or sustainability analysis of their code."
    )
    async def audit_code(
        self,
        code: Annotated[str, "The Python code snippet to audit for energy efficiency"]
    ) -> Annotated[str, "Green code audit with refactor and explanation"]:
        """Sends code to the fine-tuned auditor model and returns a green refactor.

        Uses AZURE_OPENAI_FT_DEPLOYMENT if set (the fine-tuned model).
        Falls back to AZURE_OPENAI_DEPLOYMENT (base gpt-4o-mini) automatically.
        """
        # Use the fine-tuned model if available, otherwise fall back to base model
        ft_deployment = os.getenv("AZURE_OPENAI_FT_DEPLOYMENT")
        deployment = ft_deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        model_label = "fine-tuned auditor" if ft_deployment else "base model (fine-tuning pending)"

        client = AsyncAzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-08-01-preview",
        )

        try:
            response = await client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": _AUDITOR_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Audit this code for energy efficiency: {code}"},
                ],
                temperature=0.2,
                max_tokens=400,
            )
            result = response.choices[0].message.content
            return f"Green Code Audit [{model_label}]:\n\n{result}"
        except Exception as e:
            return f"Code audit failed: {str(e)}"


# =============================================================================
# SECTION 2: Build the Kernel and Agent
# =============================================================================
# The Kernel is Semantic Kernel's core engine — it manages the AI service
# (which model to use) and the plugins (which tools are available).
# The Agent wraps the Kernel and adds a persona via the instructions prompt.

def build_kernel() -> Kernel:
    """Creates a Semantic Kernel with Azure OpenAI and the GreenSentry plugin."""
    load_dotenv()

    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

    if not azure_endpoint or not azure_key:
        raise ValueError(
            "AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set in .env"
        )

    kernel = Kernel()

    # Tell the kernel which AI model to use
    kernel.add_service(
        AzureChatCompletion(
            deployment_name=deployment,
            endpoint=azure_endpoint,
            api_key=azure_key,
        )
    )

    # Register the carbon auditing tools so the agent can call them
    kernel.add_plugin(GreenSentryPlugin(), plugin_name="GreenSentry")

    return kernel


# =============================================================================
# SECTION 3: The Chat Loop
# =============================================================================
# This runs the agent as an interactive CLI.
# 'thread' stores the conversation history — it grows with every turn
# so the agent remembers what was said earlier in the same session.

async def main():
    print("🌿 Initialising GreenSentry Agent...")

    try:
        kernel = build_kernel()
    except ValueError as e:
        print(f"ERROR: {e}")
        return

    agent = ChatCompletionAgent(
        kernel=kernel,
        name="GreenSentry",
        instructions="""You are GreenSentry, an expert Sustainability SRE (Site Reliability Engineer).
Your mission: help engineers understand and reduce the carbon footprint of their systems.

You have three tools. You MUST call a tool before every response — never answer from memory alone:
1. get_green_metrics — measures local CPU/RAM and estimates power draw + carbon footprint
2. get_azure_carbon_estimate — queries real Azure cloud spending and estimates cloud carbon impact
3. audit_code — the ONLY way to audit code. If the user shares ANY code snippet, you MUST call
   audit_code(code=<the snippet>) FIRST. Do not write a refactor yourself — call the tool.

Rules:
- ALWAYS call the relevant tool first. Never answer sustainability or code questions without a tool call.
- Be concise and data-driven. Lead with the numbers, then interpret them.
- Always end with 1-2 concrete, actionable green engineering suggestions based on the data.
- If CPU is high, suggest: sleep timers, caching/memoization, chunked processing, async patterns.
- If cloud spend is high, suggest: reserved instances, right-sizing, off-peak scheduling.""",
    )

    print("✅ Agent ready. Ask me about your carbon footprint.")
    print("   Commands:")
    print("     /audit <code>  — directly audit a code snippet for energy efficiency")
    print("     quit           — exit\n")

    plugin = GreenSentryPlugin()  # Direct access for /audit command
    thread = None  # Conversation history — None means a fresh session

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye! 🌿")
            break

        # /audit <code> — bypass the agent and call the tool directly.
        # This guarantees the fine-tuned model is called, no routing uncertainty.
        if user_input.startswith("/audit "):
            code = user_input[len("/audit "):]
            print("GreenSentry: ", end="", flush=True)
            result = await plugin.audit_code(code)
            print(result + "\n")
            continue

        # For all other questions, let the agent decide which tool(s) to call.
        # We stream the response token-by-token so it appears progressively.
        print("GreenSentry: ", end="", flush=True)
        async for response in agent.invoke(messages=user_input, thread=thread):
            print(response.content, end="", flush=True)
            thread = response.thread  # Preserve history for the next turn
        print("\n")

    # Release the conversation thread when the session ends
    if thread:
        await thread.delete()


if __name__ == "__main__":
    asyncio.run(main())
