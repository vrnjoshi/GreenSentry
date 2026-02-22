# GreenSentry: Agentic Carbon Auditor 🌍

An AI agent that monitors the carbon footprint of your local machine and Azure cloud — and reviews your code for energy efficiency. Built for the **Microsoft AI Dev Days Hackathon 2026**.

---

## What It Does

You talk to GreenSentry in plain English. It decides which tools to call, gets real data, and gives you concrete green engineering recommendations.

```
You: What is my current carbon footprint?
GreenSentry: Your machine is drawing 11.6W (CPU 12%, RAM 54%).
             That's 0.0055g CO₂/hr. Suggestion: enable sleep timers
             on idle processes to cut this by ~40%.

You: /audit for url in urls: response = requests.get(url)
GreenSentry: Green Code Audit [fine-tuned auditor]:
             REFACTOR: use asyncio.gather() with aiohttp
             WHY: Sequential HTTP requests keep the CPU busy waiting;
                  async fetch runs all requests concurrently.
```

---

## Hero Technologies

| Technology | How We Use It |
|---|---|
| **Microsoft AI Foundry** | Fine-tuned `gpt-4o-mini` on 10 green code examples to create a specialised code auditor |
| **Microsoft Agent Framework (Semantic Kernel)** | Orchestrates the agent — decides which tool to call based on your question |
| **Azure MCP (Model Context Protocol)** | Exposes local hardware metrics and Azure cloud spend as callable tools |

---

## Architecture

```
┌─────────────────────────────────────────┐
│           GreenSentry Agent             │
│   (Semantic Kernel + gpt-4o-mini)       │
│                                         │
│  Reads your question → decides which    │
│  tool(s) to call → streams an answer   │
└────────┬──────────┬──────────┬──────────┘
         │          │          │
         ▼          ▼          ▼
  get_green_   get_azure_   audit_code
  metrics()    carbon_      (code)
               estimate()
         │          │          │
         ▼          ▼          ▼
   Local CPU/   Azure        Fine-tuned
   RAM via      Consumption  gpt-4o-mini
   psutil       API          (Azure AI
                             Foundry)
```

**Three tools, one agent:**
1. `get_green_metrics` — reads local CPU/RAM via `psutil`, estimates watts and gCO₂/hr
2. `get_azure_carbon_estimate` — queries the live Azure Consumption API, converts spend → kWh → kg CO₂
3. `audit_code` — sends code to a fine-tuned gpt-4o-mini model, returns `REFACTOR / WHY` in a consistent format

---

## How to Run

**Prerequisites:** Python 3.11+, an Azure subscription, `az login` completed.

```bash
# 1. Clone and set up the virtual environment
git clone https://github.com/vrnjoshi/GreenSentry.git
cd GreenSentry
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure credentials
cp .env.example .env
# Fill in your values in .env (see .env.example for descriptions)

# 3. Run the agent
python agents/green_agent.py
```

**Available commands inside the agent:**
```
What is my current carbon footprint?        → calls get_green_metrics
How much carbon is my Azure usage?          → calls get_azure_carbon_estimate
Check both my local and cloud footprint     → calls both tools
/audit <code snippet>                       → calls the fine-tuned code auditor directly
quit                                        → exit
```

---

## Project Structure

```
GreenSentry/
├── agents/
│   └── green_agent.py        # Semantic Kernel agent (Day 2–3)
├── mcp/
│   └── server.py             # FastMCP server exposing tools (Day 1)
├── data/
│   ├── fine_tuning_samples.jsonl   # 10 green code training examples (Day 3)
│   └── generate_dataset.py
├── requirements.txt
├── .env.example              # Credential template (safe to share)
└── README.md
```

---

## Fine-Tuning

The `audit_code` tool uses a `gpt-4o-mini` model fine-tuned on 10 green code patterns via **Azure AI Foundry**. Training examples cover:

- Busy-loop → sleep timer
- List comprehension → generator
- Chunked file reads (Pandas)
- Webhooks vs polling
- Selective SQL columns
- LRU cache / memoisation
- String join vs `+=` concatenation
- File reads outside loops
- Async HTTP (aiohttp vs sequential requests)
- Batch DB queries vs N+1

The fine-tuned model produces a consistent `REFACTOR: / WHY:` format that the base model requires prompting for. Set `AZURE_OPENAI_FT_DEPLOYMENT` in `.env` to activate it; the agent falls back to the base model automatically if unset.

---

## Carbon Estimation Sources

- **Local power draw:** `5W idle + (CPU% × 0.55W)` — Apple Silicon profile ([source](https://eclecticlight.co/2024/02/23/apple-silicon-2-power-and-thermal-glory/))
- **Local carbon intensity:** `0.475 g CO₂/Wh` — US grid average
- **Azure carbon intensity:** `0.297 kg CO₂/kWh` — Microsoft 2023 Sustainability Report
- **Azure compute cost proxy:** `$0.10/kWh` — general workload estimate
