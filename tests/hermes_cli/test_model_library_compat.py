"""The shortcut library keeps CRUD behavior and profile boundaries."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from hermes_cli.web_routers import model_library as library
from hermes_cli.web_server_profiles import _hermes_home_scope


def test_library_crud_is_scoped_and_deduplicated(tmp_path, monkeypatch):
    monkeypatch.setattr(library, '_config_profile_scope', lambda p: _hermes_home_scope(tmp_path / (p or 'default')))
    monkeypatch.setattr(library, 'load_config', lambda: {'model': {'provider': 'openai-codex', 'default': 'gpt-6-sol'}})
    app = FastAPI()
    app.include_router(library.router)
    client = TestClient(app)
    route = '/api/model/library'
    body = {'provider': 'openai-codex', 'model': 'gpt-6-luna'}
    first = client.post(route, params={'profile':'a'}, json=body).json()
    assert client.post(route, params={'profile':'a'}, json=body).json()['id'] == first['id']
    assert len(client.get(route, params={'profile':'a'}).json()['models']) == 2
    assert len(client.get(route, params={'profile':'b'}).json()['models']) == 1
    item = route + '/' + first['id']
    assert client.patch(item, params={'profile':'a'}, json={'name':'Fast'}).json()['model']['name'] == 'Fast'
    assert client.delete(item, params={'profile':'b'}).status_code == 404
    assert client.delete(item, params={'profile':'a'}).json() == {'ok':True}
    assert client.post(route, json={'model':'missing-provider'}).status_code == 400
