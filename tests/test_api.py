"""Die API-Schicht: Validierung beim Start und das Hello über den WebSocket."""
from fastapi.testclient import TestClient

import backend.app as app_module
from backend.models import AppConfig, CourseConfig


def client():
    return TestClient(app_module.app)


def test_start_without_courses(monkeypatch):
    monkeypatch.setattr(app_module, "load_config", lambda: AppConfig())
    with client() as c:
        resp = c.post("/api/start", json={"dry_run": False})
    assert resp.status_code == 400
    assert "Keine Kurse" in resp.json()["detail"]


def test_start_with_broken_start_time(monkeypatch):
    cfg = AppConfig(courses=[CourseConfig(id="x", label="Mathe",
                                          groups=["1111"], start_at="irgendwann")])
    monkeypatch.setattr(app_module, "load_config", lambda: cfg)
    with client() as c:
        resp = c.post("/api/start", json={"dry_run": False})
    assert resp.status_code == 400
    assert "Mathe" in resp.json()["detail"]


def test_websocket_hello(monkeypatch):
    monkeypatch.setattr(app_module, "load_config", lambda: AppConfig())
    with client() as c, c.websocket_connect("/ws") as ws:
        hello = ws.receive_json()
    assert hello["type"] == "hello"
    assert hello["state"]["running"] is False
    assert isinstance(hello["logs"], list)


def test_config_roundtrip(monkeypatch, tmp_path):
    saved = {}
    monkeypatch.setattr(app_module, "save_config", lambda cfg: saved.update(cfg=cfg))
    with client() as c:
        resp = c.put("/api/config", json={
            "courses": [{"id": "a", "label": "Statistik", "groups": ["1234", "5678"],
                         "start_at": None, "waitlist": True}],
            "save_snapshots": False,
        })
    assert resp.status_code == 200
    assert saved["cfg"].courses[0].groups == ["1234", "5678"]
