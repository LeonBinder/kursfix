"""Die Anmelde-Engine: ein echtes Browserfenster, ein Tab pro Kurs.

Ablauf nach dem Start:

1. Browser mit persistentem Profil öffnen, LPIS-Loginseite laden. Der Nutzer
   loggt sich selbst ein (WU-SSO) — die App sieht keine Zugangsdaten.
2. Der Nutzer öffnet jede Kursseite (die mit den "anmelden"-Buttons). Die
   Engine erkennt sie an den Gruppennummern und merkt sich die URL.
3. Pro Kurs ein eigener Tab: Gruppen lesen, Öffnungszeit bestimmen, ARMED.
4. Uhr gegen WU abgleichen; Keepalive-Reloads halten die Session frisch;
   kurz vor der Öffnung wird neu synchronisiert.
5. Zur berechneten PC-Zeit neu laden und den echten "anmelden"-Button der
   ersten brauchbaren Gruppe klicken. Erfolg = der Button wird "abmelden".

Jeder Kurs läuft als eigene asyncio-Task; ein hängender Tab blockiert die
anderen nicht. Alle Zustandsänderungen gehen als Events an die UI.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from playwright.async_api import Error as PlaywrightError, Page, async_playwright

from . import lpis_page as lp
from . import timing
from .models import (AppConfig, ClockState, CourseConfig, CourseState,
                     EngineState, GroupInfo, Phase)


@dataclass
class EngineSettings:
    login_url: str = "https://lpis.wu.ac.at/lpis"
    ntp_host: Optional[str] = "timeserver.wu.ac.at"
    http_host: str = "lpis.wu.ac.at"
    http_port: Optional[int] = None
    https: bool = True
    headless: bool = False
    profile_dir: Optional[Path] = None      # None: flüchtiger Browser (Tests)
    snapshots_dir: Optional[Path] = None    # None: keine HTML-Snapshots schreiben
    keepalive_every: float = 120.0          # s zwischen Session-Reloads
    final_sync_before: float = 45.0         # s vor Öffnung: letzter Reload + Re-Sync
    nav_timeout_ms: int = 60_000            # LPIS ist zur Öffnungssekunde langsam
    give_up_after: float = 120.0            # s nach Öffnung aufgeben
    give_up_if_locked: float = 30.0         # s nach Öffnung, wenn weiter alles gesperrt
    tries_per_group: int = 3
    settle_timeout: float = 5.0             # s auf die Kurstabelle warten
    busy_timeout: float = 90.0              # s, wenn LPIS eine Warteseite zeigt
    clock_stub: Optional[timing.ClockSync] = None  # feste Uhr (Tests)
    clock_max_age: float = 30.0             # s, bevor ein Re-Sync wieder misst
    observe_only: bool = False              # Prüflauf: alles lesen, nie klicken
    drift_check_wait: float = 10.0          # s zwischen den zwei Uhr-Messungen im Prüflauf
    drift_warn: float = 0.25                # s Offset-Änderung, ab der die PC-Uhr als instabil gilt


class Stop(Exception):
    """Beendet den Lauf mit einer Meldung an den Nutzer."""


@dataclass
class RuntimeCourse:
    n: int
    cfg: CourseConfig
    state: CourseState
    groups: list[str] = field(default_factory=list)  # normalisierte Nummern
    url: str = ""
    page: Optional[Page] = None
    opens_at: float = 0.0
    fire_at: float = 0.0
    open_now: bool = False  # keine Öffnungszeit, aber Button schon klickbar


class Engine:
    """Ein Lauf der Anmelde-Maschine. ``listener`` bekommt alle Events als dicts."""

    def __init__(self, listener: Callable[[dict], None]):
        self.listener = listener
        self.settings = EngineSettings()
        self.state = EngineState()
        self.courses: list[RuntimeCourse] = []
        self._task: Optional[asyncio.Task] = None
        self._pw = None
        self._context = None
        self._clock_lock = asyncio.Lock()
        self._clock_at = 0.0
        self._relogin_lock = asyncio.Lock()
        self._unknown_pages: set[str] = set()

    # --- Events an die UI -------------------------------------------------------

    def _emit(self, type_: str, **payload):
        self.listener({"type": type_, "ts": time.time(), **payload})

    def log(self, text: str, course: Optional[int] = None, alarm: bool = False):
        self._emit("alarm" if alarm else "log", course=course, text=text)

    def push_state(self):
        self.state.courses = [c.state for c in self.courses]
        self.state.now = timing.now()
        self._emit("state", state=self.state.model_dump())

    # --- Start / Stop -------------------------------------------------------------

    def start(self, config: AppConfig, settings: EngineSettings):
        if self._task and not self._task.done():
            raise RuntimeError("Die Engine läuft bereits.")
        self.settings = settings
        self._unknown_pages = set()
        with_groups = [cfg for cfg in config.courses if any(g.strip() for g in cfg.groups)]
        self.courses = [
            RuntimeCourse(n=n, cfg=cfg,
                          state=CourseState(config=cfg),
                          groups=[lp.normalize_group(g) for g in cfg.groups if g.strip()])
            for n, cfg in enumerate(with_groups, 1)
        ]
        mode = "check" if settings.observe_only else "live" if settings.https else "dry"
        target = settings.http_host + (f":{settings.http_port}" if settings.http_port else "")
        self.state = EngineState(running=True, dry_run=not settings.https,
                                 mode=mode, target=target)
        self.push_state()
        self._task = asyncio.create_task(self._run_guarded())

    async def stop(self):
        was_running = self.state.running
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, PlaywrightError):
                pass
        await self._close_browser()
        self.state.running = False
        for c in self.courses:
            if c.state.phase not in (Phase.DONE, Phase.ERROR):
                c.state.phase = Phase.IDLE
        if was_running:
            self.push_state()
            self.log("Gestoppt.")

    async def _close_browser(self):
        for obj in (self._context, self._pw):
            try:
                if obj:
                    await (obj.close() if self._context is obj else obj.stop())
            except PlaywrightError:
                pass
        self._context = self._pw = None

    async def _run_guarded(self):
        try:
            await self._run()
        except asyncio.CancelledError:
            raise
        except Stop as e:
            self.log(str(e), alarm=True)
        except PlaywrightError as e:
            self.log(f"Browser geschlossen oder abgestürzt — Lauf beendet. "
                     f"({str(e).splitlines()[0]})", alarm=True)
        except Exception as e:  # noqa: BLE001 — alles Unerwartete sichtbar machen
            self.log(f"Unerwarteter Fehler: {e!r}", alarm=True)
        finally:
            if self.state.running:
                self.state.running = False
                await self._close_browser()
                self.push_state()

    # --- Browser --------------------------------------------------------------------

    async def _launch(self):
        self._pw = await async_playwright().start()
        s = self.settings
        kwargs = dict(headless=s.headless, no_viewport=True, locale="de-AT")
        last_error = None
        for channel in ("chrome", "msedge", None):
            try:
                if s.profile_dir:
                    s.profile_dir.mkdir(parents=True, exist_ok=True)
                    self._context = await self._pw.chromium.launch_persistent_context(
                        str(s.profile_dir), channel=channel, **kwargs)
                else:
                    browser = await self._pw.chromium.launch(channel=channel, headless=s.headless)
                    self._context = await browser.new_context(no_viewport=True, locale="de-AT")
                return
            except PlaywrightError as e:
                last_error = e
        raise Stop(f"Kein Browser startbar (Chrome/Edge/Chromium): {last_error}")

    async def _snapshot(self, page: Page) -> dict | None:
        """Die Kurstabelle als Daten, oder None (Seite navigiert gerade, Tab zu, ...)."""
        try:
            return await page.evaluate(lp.SNAPSHOT_JS)
        except PlaywrightError:
            return None

    async def _goto(self, page: Page, url: str, course: Optional[int] = None,
                    timeout_ms: Optional[int] = None) -> bool:
        try:
            await page.goto(url, wait_until="domcontentloaded",
                            timeout=timeout_ms or self.settings.nav_timeout_ms)
            return True
        except PlaywrightError as e:
            if page.is_closed():
                raise
            self.log(f"Seite lädt nicht: {str(e).splitlines()[0]}", course=course)
            return False

    async def _settle(self, page: Page, course: Optional[int] = None) -> dict | None:
        """Auf die Kurstabelle warten; LPIS-Warteseiten bekommen mehr Geduld."""
        s = self.settings
        started = timing.now()
        while True:
            snap = await self._snapshot(page)
            if snap and snap["hasTable"]:
                return snap
            body = snap["bodyStart"] if snap else ""
            limit = s.busy_timeout if lp.BUSY_RE.search(body) else s.settle_timeout
            if timing.now() - started > limit:
                self.log(f"Keine Kurstabelle auf der Seite: {body[:150]!r}", course=course)
                return snap
            await asyncio.sleep(0.25)

    async def _dump(self, page: Page, name: str):
        """Die aktuelle Seite als HTML sichern — nur wenn Snapshots eingeschaltet sind."""
        target = self.settings.snapshots_dir
        if not target:
            return
        try:
            target.mkdir(parents=True, exist_ok=True)
            (target / name).write_text(await page.content(), encoding="utf-8")
        except (PlaywrightError, OSError):
            pass

    # --- Kursseiten finden -------------------------------------------------------------

    async def _find_pages(self, courses: list[RuntimeCourse], first_time: bool = False):
        """Warten, bis der Nutzer jede Kursseite geöffnet hat; URLs merken.

        Beim ersten Mal werden auch die zwei leichten Fehler abgefangen: Gruppen
        eines Kurses auf mehrere Einträge verteilt, und geöffnete Kursseiten,
        deren Gruppen in keiner Liste stehen.
        """
        for c in courses:
            c.url = ""
            c.state.phase = Phase.WAITING
            c.state.message = "Warte, bis die Kursseite im Browser offen ist"
        self.push_state()
        names = "; ".join(f"[{c.n}] Gruppen {', '.join(c.groups)}" for c in courses)
        self.log("Im Browserfenster einloggen und die Kursseite(n) mit den "
                 f"'anmelden'-Buttons öffnen: {names}")
        while True:
            if not self._context.pages:
                raise PlaywrightError("Das Browserfenster wurde geschlossen.")
            for page in list(self._context.pages):
                rows = lp.rows_by_group(await self._snapshot(page))
                hits = [c for c in courses if rows.keys() & set(c.groups)]
                if first_time and len(hits) > 1:
                    raise Stop(f"GESTOPPT: Die Gruppen von Kurs {hits[0].n} und {hits[1].n} "
                               "gehören zur selben LPIS-Seite. Gruppen eines Kurses gehören "
                               "in EINEN Eintrag, nach Priorität sortiert.")
                ids = [r["id"] for r in rows.values()]
                if (first_time and not hits and ids and all(i.isdigit() for i in ids)
                        and page.url not in self._unknown_pages):
                    self._unknown_pages.add(page.url)
                    self.log(f"Offene Kursseite mit den Gruppen {', '.join(ids)} — keine davon "
                             "steht in deiner Liste. Nummern prüfen!", alarm=True)
                for c in courses:
                    if not c.url and rows.keys() & set(c.groups):
                        c.url = page.url
                        c.state.name = next(
                            (rows[g]["title"] for g in c.groups if rows.get(g, {}).get("title")),
                            "") or c.cfg.label
                        self.log(f"{c.state.name or 'Kursseite'} gefunden.", course=c.n)
                        self.push_state()
            if all(c.url for c in courses):
                # logged_in erst wieder True, wenn ein frischer Reload klappt —
                # ein alter Tab kann hier noch veraltetes DOM zeigen.
                self.push_state()
                return
            await asyncio.sleep(1)

    async def _relogin(self, c: RuntimeCourse):
        """Nach einem Logout: Nutzer warnen und warten, bis die Seite wieder offen ist."""
        first_notice = self.state.logged_in is not False
        self.state.logged_in = False
        c.state.message = "AUSGELOGGT — im Browserfenster neu einloggen und die Kursseite öffnen!"
        self.push_state()
        if first_notice:  # eine Warnung pro Ausfall reicht
            self.log(f"LPIS hat dich ausgeloggt — im Bot-Fenster neu einloggen und die "
                     f"Seite von Kurs {c.n} wieder öffnen!", course=c.n, alarm=True)
        async with self._relogin_lock:  # mehrere Kurse warten hier nacheinander
            await self._find_pages([c])

    async def _reload(self, c: RuntimeCourse) -> dict[str, dict]:
        """Den Kurs im eigenen Tab (neu) laden; bei Logout auf den Nutzer warten."""
        while True:
            snap = None
            if await self._goto(c.page, c.url, course=c.n):
                snap = await self._settle(c.page, course=c.n)
                rows = lp.rows_by_group(snap)
                if rows.keys() & set(c.groups):
                    if self.state.logged_in is not True:
                        self.state.logged_in = True
                        self.push_state()
                    return rows
            await self._dump(c.page, f"reload_{c.n}.html")
            await self._relogin(c)
            await asyncio.sleep(1)  # dem Nutzer Luft lassen, statt eng zu loopen

    # --- Gruppen & Zeiten -------------------------------------------------------------

    def _update_groups(self, c: RuntimeCourse, rows: dict[str, dict]):
        c.state.groups = []
        for rank, g in enumerate(c.groups, 1):
            r = rows.get(g)
            if not r:
                c.state.groups.append(GroupInfo(id=g, rank=rank, on_page=False))
                continue
            c.state.groups.append(GroupInfo(
                id=r["id"], rank=rank, who=r["who"], title=r["title"],
                button=r["button"], enabled=r["enabled"], free=r["free"],
                status=r["status"], opens=r["opens"]))
        self.push_state()

    async def _sync_clock(self, force: bool = False):
        """Uhr abgleichen; gleichzeitige Aufrufe teilen sich eine Messung."""
        s = self.settings
        async with self._clock_lock:
            if not force and timing.now() - self._clock_at < s.clock_max_age:
                return
            if s.clock_stub:
                sync = s.clock_stub
            else:
                sync = await timing.measure_async(s.ntp_host, s.http_host,
                                                  s.http_port, s.https)
            previous = self.state.clock if self.state.clock.synced_at else None
            self._clock_at = timing.now()
            self.state.clock = ClockState(
                offset=sync.offset, uncertainty=sync.uncertainty,
                trip=sync.trip, source=sync.source, synced_at=self._clock_at)
            self.push_state()
            direction = "hinter" if sync.offset > 0 else "vor"
            self.log(f"Uhr: dieser PC geht {abs(sync.offset):.3f} s {direction} LPIS "
                     f"(±{sync.uncertainty:.3f} s, via {sync.source}), "
                     f"Latenz {sync.trip * 1000:.0f} ms")
            if previous and abs(sync.offset - previous.offset) > s.drift_warn:
                self.log(f"WARNUNG: Der Uhr-Offset hat sich seit dem letzten Abgleich um "
                         f"{sync.offset - previous.offset:+.2f} s verändert — die PC-Uhr läuft "
                         "instabil, das Timing zur Öffnung ist unzuverlässig.", alarm=True)

    def _current_sync(self) -> timing.ClockSync:
        ck = self.state.clock
        return timing.ClockSync(ck.offset, ck.uncertainty, ck.trip, ck.source)

    def _arm(self, c: RuntimeCourse):
        c.fire_at = timing.fire_time(c.opens_at, self._current_sync())
        c.state.opens_at = c.opens_at
        c.state.fire_at = c.fire_at
        c.state.phase = Phase.ARMED
        c.state.message = "ARMED"
        self.push_state()

    # --- Hauptablauf --------------------------------------------------------------------

    async def _run(self):
        if not self.courses or not any(c.groups for c in self.courses):
            raise Stop("Keine Kurse mit Gruppennummern eingetragen.")
        s = self.settings
        kind = "ECHTES LPIS" if s.https else "lokaler Fake-LPIS, nichts geht an die WU"
        self.log(f"Ziel: {s.login_url} — {kind}.")
        if s.observe_only:
            self.log("PRÜFLAUF: Die Seiten werden nur gelesen, es wird nichts geklickt.")
        await self._launch()
        first_page = self._context.pages[0] if self._context.pages \
            else await self._context.new_page()
        # Die Loginseite kommt sonst in ~1 s; hängt der erste Aufruf, lieber kurz
        # neu versuchen als eine Minute auf about:blank zu warten.
        for _ in range(3):
            if await self._goto(first_page, s.login_url, timeout_ms=15_000):
                break
        else:
            self.log(f"Die Loginseite lädt nicht von selbst — im Bot-Fenster die Adresse "
                     f"{s.login_url} von Hand öffnen.", alarm=True)
        await self._find_pages(self.courses, first_time=True)

        armed: list[RuntimeCourse] = []
        for c in self.courses:
            c.page = await self._context.new_page()  # eigener Tab pro Kurs
            c.state.phase = Phase.PREPARING
            self.push_state()
            rows = await self._reload(c)
            await self._dump(c.page, f"course_{c.n}.html")
            self._update_groups(c, rows)
            missing_button = [g for g in c.groups if g in rows and not rows[g]["button"]]
            if missing_button:
                self.log(f"WARNUNG: In Zeile {', '.join(missing_button)} wurde kein "
                         "'anmelden'-Button gefunden — LPIS-Layout geändert? "
                         "Nicht auf die App verlassen!", course=c.n, alarm=True)
            if done := lp.registered_row(rows):
                c.state.phase = Phase.DONE
                c.state.result = f"bereits angemeldet: {done['id']} ({done['who']})"
                self.log(f"Du bist hier schon angemeldet ({done['id']}) — Kurs wird "
                         "übersprungen.", course=c.n)
                continue
            opens = None
            if c.cfg.start_at:
                opens = lp.parse_start_at(c.cfg.start_at)
                if opens < timing.now() - 60:
                    self.log(f"WARNUNG: Die manuelle Startzeit {c.cfg.start_at!r} liegt in der "
                             "Vergangenheit — es wird sofort versucht. Alter Eintrag?",
                             course=c.n, alarm=True)
            else:
                opens = next(filter(None, (lp.parse_opening(rows[g])
                                           for g in c.groups if g in rows)), None)
            if opens is None:
                if any(rows[g]["enabled"] for g in c.groups if g in rows):
                    opens = timing.now()  # schon offen: sofort versuchen
                    c.open_now = True
                else:
                    c.state.phase = Phase.ERROR
                    deadline = next((rows[g]["opens"] for g in c.groups if g in rows
                                     and lp.DEADLINE_RE.search(rows[g]["opens"])), "")
                    if deadline:  # gesperrt und nur ein Fristende: die Anmeldung ist vorbei
                        c.state.result = f"Anmeldung geschlossen (Frist war {deadline})"
                        self.log(f"Die Anmeldung ist gesperrt und die Seite nennt nur ein "
                                 f"Fristende ({deadline}) — hier ist nichts mehr anzumelden. "
                                 "Kurs wird übersprungen.", course=c.n)
                        continue
                    c.state.result = "keine Öffnungszeit gefunden"
                    self.log("Keine Öffnungszeit auf der Seite — bitte manuelle Startzeit "
                             "eintragen und neu starten. Kurs wird übersprungen.", course=c.n)
                    continue
            c.opens_at = opens
            c.page.on("dialog", self._accept_dialog)
            armed.append(c)
        self.push_state()
        if s.observe_only:
            await self._check_report(armed)
            self._finish()
            await asyncio.Event().wait()  # Browser offen lassen, bis der Nutzer stoppt
        if armed:
            await self._sync_clock(force=True)
            for c in armed:
                self._arm(c)
                self.log(f"ARMED — öffnet {_day_clock(c.opens_at)} LPIS-Zeit; "
                         f"Reload um {_clock(c.fire_at + self.state.clock.offset)} LPIS-Zeit.",
                         course=c.n)
            self.log("Das Browserfenster ab jetzt in Ruhe lassen.")
            await asyncio.gather(*(self._course_task(c) for c in armed))
        self._finish()
        await asyncio.Event().wait()  # Browser offen lassen, bis der Nutzer stoppt

    async def _check_report(self, readable: list[RuntimeCourse]):
        """Prüflauf: pro Kurs festhalten, ob alles lesbar war. Klickt nichts."""
        s = self.settings
        await self._sync_clock(force=True)  # prüft Zeitserver und Latenz gleich mit
        if self.state.clock.source.startswith("PC-Uhr"):
            self.log("WARNUNG: Uhrabgleich fehlgeschlagen — weder Zeitserver noch "
                     "LPIS-Serveruhr erreichbar.", alarm=True)
        clock_problem = ""
        if not s.clock_stub:
            # Zweite Messung nach kurzer Pause: läuft die PC-Uhr gleichmäßig?
            first = self.state.clock.offset
            self.log(f"Prüfe {s.drift_check_wait:.0f} s lang, ob die PC-Uhr stabil läuft …")
            await asyncio.sleep(s.drift_check_wait)
            await self._sync_clock(force=True)
            drift = self.state.clock.offset - first
            if abs(drift) > s.drift_warn:
                clock_problem = (f"PC-Uhr instabil ({drift:+.2f} s in "
                                 f"{s.drift_check_wait:.0f} s) — Timing unzuverlässig")
        for c in self.courses:
            for g in c.state.groups:
                if g.on_page:
                    self.log(f"Gelesen {g.id}: Button {g.button!r} "
                             f"({'klickbar' if g.enabled else 'gesperrt'}), frei {g.free}, "
                             f"Status {g.status!r}, Zeitangabe {g.opens!r}", course=c.n)
        for c in readable:
            found = {g.id: g for g in c.state.groups}
            problems = [clock_problem] if clock_problem else []
            missing = [g.id for g in c.state.groups if not g.on_page]
            if missing:
                problems.append(f"nicht auf der Seite: {', '.join(missing)}")
            no_button = [g.id for g in c.state.groups if g.on_page and not g.button]
            if no_button:
                problems.append(f"kein Button bei {', '.join(no_button)}")
            unknown_free = [g.id for g in c.state.groups if g.on_page and g.free is None]
            if unknown_free:
                problems.append(f"freie Plätze nicht lesbar bei {', '.join(unknown_free)}")
            if c.open_now:
                problems.append("Anmeldung ist BEREITS OFFEN — 'Start' würde sofort anmelden")
            elif c.cfg.start_at and c.opens_at < timing.now() - 60:
                problems.append(f"manuelle Startzeit {c.cfg.start_at!r} liegt in der Vergangenheit")
            c.state.opens_at = c.opens_at
            when = _day_clock(c.opens_at)
            source = "manuelle Startzeit" if c.cfg.start_at else "von der Kursseite"
            if problems:
                c.state.phase = Phase.ERROR
                c.state.result = "Prüflauf: " + "; ".join(problems)
                self.log(f"PRÜFLAUF — PROBLEM: {'; '.join(problems)} "
                         f"(Öffnung laut App: {'sofort' if c.open_now else when}, {source})",
                         course=c.n, alarm=True)
            else:
                c.state.phase = Phase.DONE
                c.state.result = f"geprüft: alles lesbar — öffnet {when}, nichts geklickt"
                self.log(f"PRÜFLAUF ok — {len(found)} Gruppe(n) gelesen, öffnet {when} "
                         f"({source}).", course=c.n)
            c.state.message = ""
        self.push_state()

    def _finish(self):
        self.log("ZUSAMMENFASSUNG")
        for c in self.courses:
            self.log(f"[{c.n}] {c.state.name or ', '.join(c.groups)}: "
                     f"{c.state.result or 'nicht versucht'}")
        if self.settings.observe_only:
            self.log("Prüflauf fertig — es wurde nichts geklickt. 'Stop' schließt den Browser.")
        else:
            self.log("Fertig. Ergebnis in der LPIS-Anmeldeliste prüfen; "
                     "'Stop' schließt den Browser.")
        self.push_state()

    async def _accept_dialog(self, dialog):
        self.log(f"LPIS fragt: {dialog.message!r} -> OK")
        await dialog.accept()

    async def _course_task(self, c: RuntimeCourse):
        """Keepalive bis kurz vor der Öffnung, dann Re-Sync und Anmeldeversuche."""
        s = self.settings
        next_reload = timing.now()  # sofort einmal laden: beweist, dass Reload geht
        while (left := c.fire_at - s.final_sync_before - timing.now()) > 0:
            if timing.now() >= next_reload:
                rows = await self._reload(c)
                self._update_groups(c, rows)
                next_reload = timing.now() + s.keepalive_every
                c.state.message = (f"ARMED — Session ok, "
                                   f"{(c.fire_at - timing.now()) / 60:.1f} min bis zum Schuss")
                self.push_state()
            await asyncio.sleep(max(0.05, min(left, next_reload - timing.now(), 30)))
        if c.fire_at - timing.now() > 5:
            rows = await self._reload(c)
            self._update_groups(c, rows)
            await self._sync_clock()  # geteilte Messung: der erste Kurs misst, der Rest nutzt sie
            self._arm(c)
            self.log(f"Letzter Check ok; Reload um "
                     f"{_clock(c.fire_at + self.state.clock.offset)} LPIS-Zeit.", course=c.n)
        await self._register(c)

    async def _register(self, c: RuntimeCourse):
        s = self.settings
        c.state.phase = Phase.FIRING
        c.state.message = "Warte auf die Öffnungssekunde …"
        self.push_state()
        await timing.sleep_until(c.fire_at)
        tries = dict.fromkeys(c.groups, 0)
        while timing.now() < c.fire_at + s.give_up_after:
            started = timing.now()
            snap = None
            if await self._goto(c.page, c.url, course=c.n):
                snap = await self._settle(c.page, course=c.n)
            rows = lp.rows_by_group(snap)
            if done := lp.registered_row(rows):
                return self._success(c, done, snap)
            if not rows:
                if lp.looks_logged_out(c.page.url):
                    await self._relogin(c)
                    continue
            else:
                self._update_groups(c, rows)
            candidates = [g for g in c.groups
                          if g in rows and rows[g]["enabled"] and tries[g] < s.tries_per_group]
            if candidates:
                with_space = [g for g in candidates if rows[g]["free"] != 0]
                if with_space:
                    target = with_space[0]
                elif c.cfg.waitlist:
                    target = candidates[0]
                    self.log("Alle Wunschgruppen zeigen 0 freie Plätze — versuche die "
                             "Warteliste.", course=c.n)
                else:
                    target = None
                    c.state.message = "Alle Gruppen voll; Warteliste ist aus — beobachte weiter"
                    self.push_state()
                if target:
                    tries[target] += 1
                    r = rows[target]
                    self.log(f"Klicke '{r['button']}' bei {r['id']} ({r['who']}, "
                             f"{r['free']} frei)", course=c.n)
                    after = await self._click(c, r["id"])
                    if after and after["alert"]:
                        self.log(f"LPIS sagt: {after['alert']}", course=c.n)
                    if done := lp.registered_row(lp.rows_by_group(after)):
                        return self._success(c, done, after)
                    if after and lp.ALREADY_RE.search(after["alert"]):
                        c.state.phase = Phase.DONE
                        c.state.result = f"gestoppt — LPIS sagt: {after['alert']}"
                        self.push_state()
                        return
            elif rows:
                if timing.now() > c.fire_at + s.give_up_if_locked:
                    c.state.phase = Phase.ERROR
                    c.state.result = "Anmeldung hat für deine Gruppen nie geöffnet"
                    self.log("Die Anmeldung ist für deine Gruppen nicht aufgegangen — "
                             "Nummern und Zeit prüfen.", course=c.n, alarm=True)
                    self.push_state()
                    return
                c.state.message = "Noch gesperrt — lade gleich erneut"
                self.push_state()
            # Schnelle Retries nur direkt an der Öffnung (falls wir einen Hauch zu
            # früh waren), danach deutlich sachter — LPIS nicht fluten.
            since = timing.now() - c.fire_at
            pause = 0.15 if since < 2 else 0.5 if since < 10 else 2.0
            await timing.sleep_until(started + pause)
        c.state.phase = Phase.ERROR
        c.state.result = "aufgegeben — bitte von Hand in LPIS prüfen"
        self.log(f"Nach {s.give_up_after:.0f} s aufgegeben — von Hand prüfen!",
                 course=c.n, alarm=True)
        self.push_state()

    async def _click(self, c: RuntimeCourse, row_id: str) -> dict | None:
        """Den Button klicken, auf die Antwortseite warten, deren Snapshot liefern."""
        s = self.settings
        if s.observe_only:  # Schutz in der Tiefe: der Prüflauf darf nie klicken
            raise Stop("Prüflauf: Klick verweigert.")
        try:
            if not await c.page.evaluate(lp.CLICK_JS, row_id):
                self.log("Der Button war doch nicht klickbar.", course=c.n)
                return None
        except PlaywrightError:
            if c.page.is_closed():
                raise
            # Die Seite hat schon navigiert, bevor evaluate zurückkam: geklickt.
        try:
            await c.page.wait_for_function(lp.PAGE_TURNED_JS,
                                           timeout=s.nav_timeout_ms, polling=50)
        except PlaywrightError:
            if c.page.is_closed():
                raise
            self.log(f"Keine Antwort von LPIS binnen {s.nav_timeout_ms // 1000} s.",
                     course=c.n)
            return None
        snap = await self._settle(c.page, course=c.n)
        await self._dump(c.page, f"result_{c.n}.html")
        return snap

    def _success(self, c: RuntimeCourse, row: dict, snap: dict | None):
        c.state.phase = Phase.DONE
        if snap and lp.WAITLIST_RE.search(snap["alert"]):
            c.state.result = f"WARTELISTE bei {row['id']} ({row['who']})"
            self.log(f"FERTIG — aber auf der WARTELISTE von {row['id']} ({row['who']}).",
                     course=c.n, alarm=True)
            others = [f"{r['id']}: {r['free']} frei"
                      for g, r in lp.rows_by_group(snap).items()
                      if g in c.groups and r["id"] != row["id"]]
            if others:
                self.log(f"Deine anderen Gruppen gerade: {', '.join(others)} — bei "
                         "Bedarf von Hand wechseln.", course=c.n)
        else:
            c.state.result = f"angemeldet: {row['id']} ({row['who']})"
            self.log(f"FERTIG — angemeldet für {row['id']} ({row['who']}); der Button "
                     f"zeigt jetzt '{row['button']}'.", course=c.n)
        self._update_groups(c, lp.rows_by_group(snap))
        self.push_state()


def _day_clock(t: float) -> str:
    import datetime as dt
    return dt.datetime.fromtimestamp(t, lp.VIENNA).strftime("%d.%m. %H:%M:%S")


def _clock(t: float) -> str:
    import datetime as dt
    d = dt.datetime.fromtimestamp(t)
    return f"{d:%H:%M:%S}.{d.microsecond // 1000:03d}"
