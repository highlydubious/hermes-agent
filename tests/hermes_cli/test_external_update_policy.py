from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest


def test_external_update_command_reads_profile_marker(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    (tmp_path / ".external_update_command").write_text(
        "/usr/local/bin/hermes-stable-upgrade status\n",
        encoding="utf-8",
    )

    from hermes_cli.config import get_external_update_command

    assert (
        get_external_update_command()
        == "/usr/local/bin/hermes-stable-upgrade status"
    )


def test_cmd_update_defers_to_external_workflow(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    (tmp_path / ".external_update_command").write_text(
        "hermes-stable-upgrade status\n",
        encoding="utf-8",
    )

    from hermes_cli.main import cmd_update

    with pytest.raises(SystemExit) as exc:
        cmd_update(SimpleNamespace(check=False))

    assert exc.value.code == 1
    output = capsys.readouterr().out
    assert "patched checkout" in output
    assert "hermes-stable-upgrade status" in output


def test_dashboard_update_defers_to_external_workflow(monkeypatch):
    from hermes_cli import web_server

    monkeypatch.setattr(
        web_server,
        "get_external_update_command",
        lambda: "hermes-stable-upgrade status",
    )
    monkeypatch.setattr(web_server, "_record_completed_action", lambda *args, **kwargs: None)

    result = asyncio.run(web_server.update_hermes())

    assert result["ok"] is False
    assert result["error"] == "external_update_policy"
    assert result["update_command"] == "hermes-stable-upgrade status"


def test_dashboard_check_reports_operator_managed(monkeypatch):
    from hermes_cli import web_server

    monkeypatch.setattr(
        web_server,
        "get_external_update_command",
        lambda: "hermes-stable-upgrade status",
    )

    result = asyncio.run(web_server.check_hermes_update(force=True))

    assert result["install_method"] == "operator-managed"
    assert result["can_apply"] is False
    assert result["update_available"] is False
    assert result["update_command"] == "hermes-stable-upgrade status"
