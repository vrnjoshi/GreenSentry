"""
GreenSentry Tool Tests
======================
Unit tests for the three GreenSentry tools. These run without Azure credentials
by mocking external API calls — only the local metrics test calls real hardware.

Run with:  pytest tests/test_tools.py -v
"""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from agents.green_agent import GreenSentryPlugin


# =============================================================================
# Tool 1: get_green_metrics (local hardware — no mocking needed)
# =============================================================================

def test_green_metrics_returns_string():
    """get_green_metrics should return a non-empty string."""
    plugin = GreenSentryPlugin()
    result = plugin.get_green_metrics()
    assert isinstance(result, str)
    assert len(result) > 0


def test_green_metrics_contains_expected_fields():
    """Output should contain all four key fields."""
    plugin = GreenSentryPlugin()
    result = plugin.get_green_metrics()
    assert "CPU Usage" in result
    assert "RAM Usage" in result
    assert "Power Draw" in result
    assert "Carbon Footprint" in result


def test_green_metrics_carbon_is_positive():
    """Carbon footprint should always be a positive number."""
    plugin = GreenSentryPlugin()
    result = plugin.get_green_metrics()
    # Extract the carbon value from "Carbon Footprint: 0.00123g CO2/hr"
    for line in result.splitlines():
        if "Carbon Footprint" in line:
            value = float(line.split(":")[1].strip().split("g")[0])
            assert value > 0
            break


# =============================================================================
# Tool 2: get_azure_carbon_estimate (mocked — no Azure credentials needed)
# =============================================================================

def test_azure_estimate_missing_subscription():
    """Should return a clear error message when subscription ID is missing."""
    plugin = GreenSentryPlugin()
    with patch.dict(os.environ, {"AZURE_SUBSCRIPTION_ID": ""}):
        result = plugin.get_azure_carbon_estimate()
    assert "AZURE_SUBSCRIPTION_ID" in result


def test_azure_estimate_returns_string_on_auth_failure():
    """Should return an error string (not raise) if Azure auth fails."""
    plugin = GreenSentryPlugin()
    with patch.dict(os.environ, {"AZURE_SUBSCRIPTION_ID": "fake-sub-id"}):
        with patch("azure.identity.DefaultAzureCredential", side_effect=Exception("no credentials")):
            result = plugin.get_azure_carbon_estimate()
    assert isinstance(result, str)
    assert "failed" in result.lower() or "error" in result.lower() or "Azure query failed" in result


# =============================================================================
# Tool 3: audit_code (mocked — no Azure OpenAI call made)
# =============================================================================

@pytest.mark.asyncio
async def test_audit_code_returns_refactor_format():
    """audit_code output should contain REFACTOR and WHY."""
    plugin = GreenSentryPlugin()

    mock_response = MagicMock()
    mock_response.choices[0].message.content = (
        "REFACTOR: import time\nwhile True:\n    check()\n    time.sleep(60)\n"
        "WHY: Adding a sleep timer prevents 100% CPU usage during idle loops."
    )

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("agents.green_agent.AsyncAzureOpenAI", return_value=mock_client):
        result = await plugin.audit_code("while True: check()")

    assert "REFACTOR" in result
    assert "WHY" in result


@pytest.mark.asyncio
async def test_audit_code_labels_fine_tuned_model():
    """Label should say 'fine-tuned auditor' when FT_DEPLOYMENT is set."""
    plugin = GreenSentryPlugin()

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "REFACTOR: fixed\nWHY: saves energy."

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch.dict(os.environ, {"AZURE_OPENAI_FT_DEPLOYMENT": "gpt-4o-mini-greensentry-ft"}):
        with patch("agents.green_agent.AsyncAzureOpenAI", return_value=mock_client):
            result = await plugin.audit_code("for x in data: process(x)")

    assert "fine-tuned auditor" in result


@pytest.mark.asyncio
async def test_audit_code_labels_base_model_fallback():
    """Label should say 'base model' when FT_DEPLOYMENT is not set."""
    plugin = GreenSentryPlugin()

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "REFACTOR: fixed\nWHY: saves energy."

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch.dict(os.environ, {"AZURE_OPENAI_FT_DEPLOYMENT": ""}):
        with patch("agents.green_agent.AsyncAzureOpenAI", return_value=mock_client):
            result = await plugin.audit_code("for x in data: process(x)")

    assert "base model" in result


@pytest.mark.asyncio
async def test_audit_code_handles_api_failure_gracefully():
    """Should return an error string (not raise) if the API call fails."""
    plugin = GreenSentryPlugin()

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API timeout"))

    with patch("agents.green_agent.AsyncAzureOpenAI", return_value=mock_client):
        result = await plugin.audit_code("while True: pass")

    assert isinstance(result, str)
    assert "failed" in result.lower()
