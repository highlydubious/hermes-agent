"""Local patch policy is inherited and blocks both mutation surfaces."""
import argparse
import asyncio
import pytest
from hermes_cli import external_update_policy as policy
from hermes_cli import banner, config, main, update_contract
from hermes_cli.web_routers import actions


def test_profile_policy_inherits_root_and_can_override(tmp_path, monkeypatch):
    profile = tmp_path / 'profiles' / 'test'
    profile.mkdir(parents=True)
    monkeypatch.setattr(policy, 'get_hermes_home', lambda: profile)
    monkeypatch.setattr(policy, 'get_default_hermes_root', lambda: tmp_path)
    (tmp_path / '.external_update_command').write_text('hermes-stable-upgrade prepare latest\n')
    assert config.recommended_update_command() == 'hermes-stable-upgrade prepare latest'
    assert update_contract.evaluate_update_admission(tmp_path).code == 'external-policy'
    monkeypatch.setattr(banner, '_resolve_repo_dir', lambda: pytest.fail('unstable main check ran'))
    assert banner.check_for_updates() is None
    (profile / '.external_update_command').write_text('profile-upgrade\n')
    assert policy.external_update_command() == 'profile-upgrade'
    (profile / '.external_update_command').write_text('\n')
    assert policy.external_update_command() == 'hermes-stable-upgrade prepare latest'


def test_cli_and_dashboard_refuse_without_spawning(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, 'get_hermes_home', lambda: tmp_path)
    monkeypatch.setattr(policy, 'get_default_hermes_root', lambda: tmp_path)
    (tmp_path / '.external_update_command').write_text('guarded-upgrade\n')
    monkeypatch.setattr(update_contract, 'record_refusal_receipt', lambda *a: None)
    monkeypatch.setattr(main, '_install_hangup_protection', lambda **k: pytest.fail('updater started'))
    with pytest.raises(SystemExit) as exc:
        main.cmd_update(argparse.Namespace())
    assert exc.value.code == 2
    monkeypatch.setattr(actions, '_dashboard_local_update_managed_externally', lambda: False)
    monkeypatch.setattr(actions, '_record_completed_action', lambda *a, **k: None)
    monkeypatch.setattr(actions, '_spawn_hermes_action', lambda *a, **k: pytest.fail('updater spawned'))
    response = asyncio.run(actions.update_hermes())
    assert response['error'] == 'external_update_policy'
    from contextlib import nullcontext
    monkeypatch.setattr(actions, '_config_profile_scope', lambda p: nullcontext())
    status = asyncio.run(actions.check_hermes_update())
    assert not status['can_apply'] and status['update_command'] == 'guarded-upgrade'
