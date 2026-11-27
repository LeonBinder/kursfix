"""Gemeinsames Gerüst: Engine headless gegen den Fake-LPIS laufen lassen.

Ein "Pilot" spielt den Nutzer: Er klickt den Login-Button, wann immer die
Engine nicht eingeloggt ist, und der Fake-``/start`` führt den ersten Tab durch
alle Kursseiten — genau das, was der echte Nutzer von Hand macht.
"""
from __future__ import annotations

import asyncio
import time

from backend import timing
from backend.engine import Engine, EngineSettings
from backend.models import AppConfig, CourseConfig, Phase
from backend.timing import ClockSync

FINISHED = (Phase.DONE, Phase.ERROR)


def fast_settings(fake, **overrides) -> EngineSettings:
    defaults = dict(
        login_url=f"{fake.base_url}/start",
        ntp_host=None,
        http_host="127.0.0.1", http_port=fake.port, https=False,
        headless=True, profile_dir=None, snapshots_dir=None,
        keepalive_every=3.0, final_sync_before=4.0,
        give_up_after=20.0, give_up_if_locked=8.0,
        settle_timeout=1.5, busy_timeout=4.0,
        nav_timeout_ms=10_000,
        clock_stub=ClockSync(0.0, 0.0, 0.001, "Test-Stub"),  # Fake läuft auf der PC-Uhr
    )
    defaults.update(overrides)
    return EngineSettings(**defaults)


def course(id_: str, groups: list[str], **kw) -> CourseConfig:
    return CourseConfig(id=id_, groups=groups, **kw)


async def pilot_login(engine: Engine):
    """Spielt den Nutzer: loggt ein, sobald die Engine es braucht (Start oder
    nachdem sie den Logout bemerkt hat — nicht früher, sonst testet niemand
    die Logout-Erkennung)."""
    while True:
        if engine._context and engine.state.logged_in is not True:
            for page in list(engine._context.pages):
                if "/login" in page.url:
                    try:
                        await page.click("input[type=submit]", timeout=300)
                    except Exception:  # noqa: BLE001 — Seite kann gerade navigieren
                        pass
        await asyncio.sleep(0.3)


async def wait_for(predicate, timeout: float, message: str = "Bedingung"):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return
        await asyncio.sleep(0.2)
    raise AssertionError(f"Timeout ({timeout}s): {message}")


async def run_to_end(fake, configs, settings=None, timeout: float = 45.0,
                     keep_running: float | None = None):
    """Engine starten, Nutzer simulieren, bis alle Kurse fertig sind.

    ``keep_running``: Zeitpunkt (timing.now-Uhr), bis zu der die Engine danach noch weiterläuft —
    um zu zeigen, dass später nichts mehr passiert.
    """
    events: list[dict] = []
    engine = Engine(listener=events.append)
    engine.start(AppConfig(courses=configs), settings or fast_settings(fake))
    pilot = asyncio.create_task(pilot_login(engine))
    try:
        await wait_for(
            lambda: engine.courses and all(c.state.phase in FINISHED for c in engine.courses),
            timeout, "alle Kurse fertig")
        if keep_running:
            await asyncio.sleep(max(0.0, keep_running - timing.now()))
    finally:
        pilot.cancel()
        await engine.stop()
    return engine, events
