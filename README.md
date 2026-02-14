# GreenSentry: Agentic Sustainability Auditor 🌍

**A Multi-Agent System for Carbon-Efficient Cloud Engineering**

GreenSentry is an autonomous "Sustainability SRE" that monitors Azure infrastructure telemetry, audits code for energy efficiency, and suggests "Green Refactors" automatically.

## 🚀 Hero Technologies
* **Microsoft AI Foundry:** Used for fine-tuning and deploying our core **Phi-4-mini** model.
* **Microsoft Agent Framework:** Orchestrates the multi-agent workflow (Auditor + Telemetry + Optimizer).
* **Azure MCP (Model Context Protocol):** Connects our agents to real-time Azure Monitor telemetry.
* **GitHub Copilot Agent Mode:** Enables the "Agentic DevOps" loop to refactor code within the IDE.

## 🧠 The Architecture


1. **Telemetry Agent:** Uses Azure MCP to pull live CPU/Memory/Energy metrics from Azure Monitor.
2. **Auditor Agent:** Uses a fine-tuned Phi-4-mini model to scan the repo for inefficient code patterns.
3. **Optimizer Agent:** Combines telemetry and audit data to propose code fixes via GitHub Copilot.

## 🛠️ Setup & Learning Goals
My primary goal for this hackathon is to master:
1. **Model Fine-Tuning:** Training Phi-4 on green vs. "hungry" code patterns.
2. **Agentic Orchestration:** Using the Microsoft Agent Framework to manage cross-agent communication.
3. **Production Deployment:** Hosting the solution as a secure Azure service.