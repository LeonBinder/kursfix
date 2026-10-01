"""FastAPI-Schicht: REST für Konfiguration und Start/Stop, WebSocket für Live-Events.

Die App läuft nur auf 127.0.0.1 und serviert auch das gebaute Frontend
(frontend/dist). Im Trockenlauf wird ein Fake-LPIS mit genau den Kursen des
Nutzers gestartet — kein Request verlässt den Rechner.
"""
from __future__ import annotations

import asyncio
import time
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import lpis_page as lp
from .engine import Engine, EngineSettings
from .models import AppConfig
from .store import DATA_DIR, load_config, save_config

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
LOG_BUFFER = 400
DRY_RUN_OPENS_IN = 60.0  # s bis zur Öffnung im Trockenlauf


class Broadcaster:
    """Hält die WebSocket-Clients und die letzten Log-Zeilen."""

    def __init__(self):
        self.clients: set[WebSocket] = set()
        self.logs: deque[dict] = deque(maxlen=LOG_BUFFER)

    def handle(self, event: dict):
        """Listener der Engine — läuft synchron im Event-Loop."""
        if event["type"] in ("log", "alarm"):
            self.logs.append(event)
        asyncio.get_running_loop().create_task(self.send_all(event))

    async def send_all(self, event: dict):
        for ws in list(self.clients):
            try:
                await ws.send_json(event)
            except Exception:  # noqa: BLE001 — getrennte Clients still entfernen
                self.clients.discard(ws)


broadcaster = Broadcaster()
engine = Engine(listener=broadcaster.handle)
fake_server = None  # laufender Fake-LPIS im Trockenlauf


class StartRequest(BaseModel):
    dry_run: bool = False


def _real_settings(config: AppConfig) -> EngineSettings:
    return EngineSettings(
        profile_dir=DATA_DIR / "browser-profile",
        snapshots_dir=(DATA_DIR / "snapshots") if config.save_snapshots else None,
    )


def _dry_run_settings(config: AppConfig) -> tuple[EngineSettings, AppConfig]:
    """Fake-LPIS mit den Kursen des Nutzers bauen und die Engine darauf zeigen."""
    global fake_server
    from fakelpis.server import FakeLpis

    courses = {}
    for i, c in enumerate(config.courses):
        groups = [g.strip() for g in c.groups if g.strip()]
        if groups:
            courses[f"k{i}"] = (c.label or f"Kurs {i + 1}",
                                {g: f"Lektor {chr(65 + i)}." for g in groups})
    fake_server = FakeLpis(opens_in=DRY_RUN_OPENS_IN, courses=courses or None)
    fake_server.start()
    settings = EngineSettings(
        login_url=f"{fake_server.base_url}/overview",
        ntp_host=None,
        http_host="127.0.0.1", http_port=fake_server.port, https=False,
        profile_dir=DATA_DIR / "browser-profile-dry",
        snapshots_dir=None,
    )
    # Manuelle Startzeiten gelten für den echten Lauf, nicht für die Probe:
    rehearsal = AppConfig(courses=[c.model_copy(update={"start_at": None})
                                   for c in config.courses])
    return settings, rehearsal


def _stop_fake():
    global fake_server
    if fake_server:
        fake_server.stop()
        fake_server = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    try:
        await engine.stop()
    finally:
        _stop_fake()


app = FastAPI(title="kursfix", lifespan=lifespan)


@app.get("/api/config")
def get_config() -> AppConfig:
    return load_config()


@app.put("/api/config")
def put_config(config: AppConfig) -> AppConfig:
    save_config(config)
    return config


@app.post("/api/start")
async def start(req: StartRequest):
    if engine.state.running:
        raise HTTPException(409, "Die Engine läuft bereits.")
    config = load_config()
    if not any(any(g.strip() for g in c.groups) for c in config.courses):
        raise HTTPException(400, "Keine Kurse mit Gruppennummern eingetragen.")
    for c in config.courses:
        if c.start_at and not req.dry_run:
            try:
                lp.parse_start_at(c.start_at)
            except ValueError as e:
                raise HTTPException(400, f"Kurs '{c.label or c.id}': {e}") from e
    if req.dry_run:
        settings, config = _dry_run_settings(config)
    else:
        settings = _real_settings(config)
    engine.start(config, settings)
    return {"ok": True, "dry_run": req.dry_run}


@app.post("/api/stop")
async def stop():
    await engine.stop()
    _stop_fake()
    return {"ok": True}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    broadcaster.clients.add(ws)
    engine.state.courses = [c.state for c in engine.courses]
    await ws.send_json({
        "type": "hello", "ts": time.time(),
        "state": engine.state.model_dump(),
        "logs": list(broadcaster.logs),
        "config": load_config().model_dump(),
    })
    try:
        while True:
            await ws.receive_text()  # Clients senden nichts; hält die Verbindung
    except WebSocketDisconnect:
        pass
    finally:
        broadcaster.clients.discard(ws)


# --- Frontend ausliefern (falls gebaut) -------------------------------------------

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/")
    def index():
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    def index_missing():
        return {"hinweis": "Frontend nicht gebaut — python run.py nutzen oder "
                           "in frontend/ 'npm install && npm run build' ausführen."}
