"""End-zu-End gegen den Fake-LPIS: Priorität, Warteliste, Retry, Logout.

Alles läuft headless und nur gegen 127.0.0.1 — es geht kein Request an die WU.
Die Öffnungszeit wird als manuelle Startzeit (sekundengenau) gesetzt, wie es
auch der Nutzer täte, wenn LPIS nur Minuten anzeigt.
"""
import asyncio
import datetime as dt
import time

from backend import timing
from backend.lpis_page import VIENNA
from backend.models import AppConfig, Phase
from fakelpis.server import FakeLpis

from .helpers import course, fast_settings, run_to_end, wait_for


def start_at(fake) -> str:
    return dt.datetime.fromtimestamp(fake.opens_at, VIENNA).strftime("%H:%M:%S")


async def test_priority_fallback_three_courses():
    """Erste Wahl voll zur Öffnung -> die Engine nimmt die zweite; drei Kurse parallel."""
    fake = FakeLpis(opens_in=10, full_at_open={"1111", "2221"}).start()
    try:
        at = start_at(fake)
        engine, _ = await run_to_end(fake, [
            course("a", ["1111", "1112", "1113"], start_at=at),
            course("b", ["2221", "2222"], start_at=at),
            course("c", ["3331"], start_at=at),
        ])
    finally:
        fake.stop()
    assert fake.registered == {"1112": "fix", "2222": "fix", "3331": "fix"}
    for c in engine.courses:
        assert c.state.phase == Phase.DONE
        assert c.state.result.startswith("angemeldet")


async def test_waitlist_when_everything_is_full():
    fake = FakeLpis(opens_in=8, full_at_open={"1111", "1112", "1113"}).start()
    try:
        engine, _ = await run_to_end(fake, [
            course("a", ["1111", "1112"], start_at=start_at(fake), waitlist=True),
        ])
    finally:
        fake.stop()
    assert fake.registered == {"1111": "warteliste"}   # Warteliste der ersten Wahl
    assert "WARTELISTE" in engine.courses[0].state.result


async def test_waitlist_disabled_keeps_waiting():
    fake = FakeLpis(opens_in=8, full_at_open={"1111", "1112", "1113"}).start()
    try:
        settings = fast_settings(fake, give_up_after=6.0)
        engine, _ = await run_to_end(fake, [
            course("a", ["1111", "1112"], start_at=start_at(fake), waitlist=False),
        ], settings=settings)
    finally:
        fake.stop()
    assert fake.registered == {}                        # nichts geklickt
    assert engine.courses[0].state.phase == Phase.ERROR
    assert "aufgegeben" in engine.courses[0].state.result


async def test_retry_after_failed_clicks():
    """Die ersten zwei Klicks schlagen fehl -> der dritte (von max. 3) sitzt."""
    fake = FakeLpis(opens_in=8, reject_clicks={"3331": 2}).start()
    try:
        engine, events = await run_to_end(fake, [
            course("c", ["3331"], start_at=start_at(fake)),
        ])
    finally:
        fake.stop()
    assert fake.registered == {"3331": "fix"}
    assert engine.courses[0].state.result.startswith("angemeldet")
    clicks = [e for e in events if e["type"] == "log" and e["text"].startswith("Klicke")]
    assert len(clicks) == 3


async def test_logout_warning_and_relogin():
    """Session läuft beim Keepalive ab -> Alarm; nach Re-Login meldet die Engine an."""
    fake = FakeLpis(opens_in=18, session_ttl=5,
                    courses={"a": ("Beispielkurs A", {"1111": "Lektor A."})}).start()
    try:
        settings = fast_settings(fake, keepalive_every=2.0, final_sync_before=3.0,
                                 settle_timeout=1.0)
        engine, events = await run_to_end(fake, [
            course("a", ["1111"], start_at=start_at(fake)),
        ], timeout=40)
    finally:
        fake.stop()
    alarms = [e for e in events if e["type"] == "alarm"]
    assert any("ausgeloggt" in e["text"] for e in alarms)
    # Der Pilot hat neu eingeloggt, die Anmeldung ging trotzdem durch:
    assert fake.registered == {"1111": "fix"}
    assert engine.courses[0].state.result.startswith("angemeldet")


async def test_split_course_is_rejected():
    """Gruppen EINES Kurses auf zwei Einträge verteilt -> harter Stopp mit Erklärung."""
    from backend.engine import Engine
    from .helpers import pilot_login

    fake = FakeLpis(opens_in=30).start()
    events: list[dict] = []
    engine = Engine(listener=events.append)
    try:
        engine.start(AppConfig(courses=[course("a1", ["1111"]), course("a2", ["1112"])]),
                     fast_settings(fake))
        pilot = asyncio.create_task(pilot_login(engine))
        try:
            await wait_for(lambda: not engine.state.running, 20, "Engine stoppt")
        finally:
            pilot.cancel()
    finally:
        await engine.stop()
        fake.stop()
    assert any(e["type"] == "alarm" and "selben LPIS-Seite" in e["text"] for e in events)
    assert fake.registered == {}


async def test_check_run_never_clicks():
    """Prüflauf: liest alles, meldet 'geprüft' — und klickt auch nach der Öffnung nichts."""
    fake = FakeLpis(opens_in=6).start()
    try:
        engine, events = await run_to_end(fake, [
            course("a", ["1111", "1112"]),
            course("b", ["2221"]),
        ], settings=fast_settings(fake, observe_only=True), keep_running=fake.opens_at + 4)
    finally:
        fake.stop()
    assert fake.registered == {}
    assert engine.state.mode == "check"
    for c in engine.courses:
        assert c.state.phase == Phase.DONE
        assert c.state.result.startswith("geprüft")
        # Öffnungszeit von der Seite gelesen (LPIS zeigt sie nur minutengenau)
        assert c.state.opens_at == fake.opens_at - fake.opens_at % 60
        assert all(g.on_page and g.button == "anmelden" and g.free is not None
                   for g in c.state.groups)
    assert not any(e["type"] == "log" and e["text"].startswith("Klicke") for e in events)


async def test_check_run_flags_already_open_course():
    """Prüflauf bei bereits offener Anmeldung: Problem melden statt anmelden."""
    fake = FakeLpis(opens_in=-30).start()
    try:
        engine, events = await run_to_end(fake, [
            course("a", ["1111"]),
        ], settings=fast_settings(fake, observe_only=True), keep_running=timing.now() + 6)
    finally:
        fake.stop()
    assert fake.registered == {}
    assert engine.courses[0].state.phase == Phase.ERROR
    assert "BEREITS OFFEN" in engine.courses[0].state.result
    assert any(e["type"] == "alarm" and "BEREITS OFFEN" in e["text"] for e in events)


def _texts(events, prefix):
    return [e["text"] for e in events if e["type"] in ("log", "alarm")
            and e["text"].startswith(prefix)]


async def test_waitlist_entry_is_recognised_and_never_clicked_again():
    """Echtes LPIS: Wartelistenplatz = Button 'austragen'. Das ist ein Ergebnis —
    und darf nie angeklickt werden (das würde den Platz wieder hergeben)."""
    fake = FakeLpis(opens_in=8, full_at_open={"1111", "1112"}).start()
    try:
        engine, events = await run_to_end(fake, [
            course("a", ["1111", "1112"], start_at=start_at(fake), waitlist=True),
        ], keep_running=fake.opens_at + 6)
    finally:
        fake.stop()
    assert fake.registered == {"1111": "warteliste"}     # nicht wieder ausgetragen
    assert "WARTELISTE" in engine.courses[0].state.result
    assert len(_texts(events, "Klicke")) == 1
    assert _texts(events, "Klicke")[0].startswith("Klicke 'eintragen'")


async def test_existing_waitlist_entry_is_left_alone():
    """Schon auf der Warteliste -> Kurs überspringen, nichts klicken."""
    fake = FakeLpis(opens_in=-30, full_at_open={"1111"}).start()
    fake.registered["1111"] = "warteliste"
    try:
        engine, events = await run_to_end(fake, [
            course("a", ["1111", "1112"], waitlist=True),
        ], keep_running=timing.now() + 4)
    finally:
        fake.stop()
    assert fake.registered == {"1111": "warteliste"}
    assert engine.courses[0].state.result.startswith("bereits auf der Warteliste")
    assert not _texts(events, "Klicke")


async def test_direct_shot_registers_without_reload():
    """Direktschuss: Das vor der Öffnung geladene Formular wird angenommen."""
    fake = FakeLpis(opens_in=10).start()
    try:
        engine, events = await run_to_end(fake, [
            course("a", ["1111", "1112"], start_at=start_at(fake)),
        ], settings=fast_settings(fake, direct_shot=True), keep_running=fake.opens_at + 5)
    finally:
        fake.stop()
    assert fake.registered == {"1111": "fix"}            # genau eine Gruppe, nicht zwei
    assert engine.courses[0].state.result.startswith("angemeldet: 1111")
    assert _texts(events, "Direktschuss vorbereitet")
    assert _texts(events, "Direktschuss: Antwort nach")
    assert len(_texts(events, "FERTIG")) == 1            # Erfolg nur einmal gemeldet


async def test_direct_shot_rejected_falls_back_to_normal_path():
    """Lehnt LPIS das alte Formular ab, meldet der normale Weg trotzdem an."""
    fake = FakeLpis(opens_in=10, reject_stale_tokens=True).start()
    try:
        engine, events = await run_to_end(fake, [
            course("a", ["1111", "1112"], start_at=start_at(fake)),
        ], settings=fast_settings(fake, direct_shot=True), keep_running=fake.opens_at + 5)
    finally:
        fake.stop()
    assert fake.registered == {"1111": "fix"}
    assert engine.courses[0].state.result.startswith("angemeldet: 1111")
    assert _texts(events, "Direktschuss ohne Erfolg")
    assert _texts(events, "Klicke 'anmelden'")
    assert _texts(events, "Aufruf 1 seit Öffnung")


async def test_step_timing_is_logged():
    fake = FakeLpis(opens_in=8).start()
    try:
        _, events = await run_to_end(fake, [course("a", ["1111"], start_at=start_at(fake))])
    finally:
        fake.stop()
    assert _texts(events, "Aufruf 1 seit Öffnung")
    assert _texts(events, "Antwort auf den Klick nach")
