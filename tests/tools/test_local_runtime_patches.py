"""Regression coverage for the local Hermes runtime patch stack."""

from __future__ import annotations

import inspect
import json
from unittest.mock import patch


def test_terminal_oauth_error_returns_non_retryable_reauth_result():
    from tools.mcp_oauth import OAuthNonInteractiveError
    from tools.mcp_tool import _handle_auth_error_and_retry

    retry_called = False

    def retry_call():
        nonlocal retry_called
        retry_called = True
        return '{"ok": true}'

    result = json.loads(
        _handle_auth_error_and_retry(
            "notion",
            OAuthNonInteractiveError("browser authorization is unavailable"),
            retry_call,
            "tools/call search",
        )
    )

    assert retry_called is False
    assert result["needs_reauth"] is True
    assert result["terminal"] is True
    assert result["server"] == "notion"
    assert "hermes mcp login notion" in result["error"]


def test_lead_mosaic_clickup_guard_blocks_unscoped_search(monkeypatch, tmp_path):
    from tools.mcp_tool import _make_tool_handler

    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "lead-mosaic-cta"))
    result = json.loads(
        _make_tool_handler("clickup", "clickup_search", 30.0)({"query": "open tasks"})
    )

    assert result["scope_guard"] is True
    assert result["terminal"] is True
    assert result["server"] == "clickup"
    assert result["tool"] == "clickup_search"


def test_lead_mosaic_clickup_guard_accepts_scope_keyword(monkeypatch, tmp_path):
    from tools import mcp_tool

    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "lead-mosaic-cta"))
    policy = mcp_tool._tool_policy_for("clickup", "clickup_search", {})

    assert policy is not None
    assert mcp_tool._args_satisfy_tool_policy(
        {"query": "open Saratoga tasks"}, policy
    ) is True


def test_mcp_result_cap_returns_bounded_truncation_payload():
    from tools.mcp_tool import _serialize_tool_success_payload

    serialized = _serialize_tool_success_payload(
        {"result": "x" * 2_000},
        "clickup",
        "clickup_search",
        {"max_result_chars": 400},
    )
    result = json.loads(serialized)

    assert len(serialized) <= 400
    assert result["truncated"] is True
    assert result["original_chars"] > 2_000


def test_requested_mcp_alias_triggers_discovery_before_tool_filtering():
    import model_tools

    config = {
        "mcp_servers": {
            "google_workspace_saratoga": {"enabled": True},
            "disabled_server": {"enabled": False},
        }
    }
    with (
        patch("hermes_cli.config.load_config", return_value=config),
        patch("tools.mcp_tool.discover_mcp_tools") as discover,
    ):
        model_tools._ensure_mcp_toolsets_registered(
            ["google_workspace_saratoga"]
        )

    discover.assert_called_once_with()


def test_tui_agent_wait_allows_slow_profile_mcp_initialization():
    from tui_gateway.server import _wait_agent

    assert inspect.signature(_wait_agent).parameters["timeout"].default == 180.0
