"""Datenmodelle: Kurskonfiguration, Laufzeitstatus, Events für die UI."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CourseConfig(BaseModel):
    """Ein Kurs, wie ihn der Nutzer eingibt."""
    id: str
    label: str = ""                      # frei wählbarer Name, nur für die Anzeige
    groups: list[str] = Field(default_factory=list)  # LV-Nummern, Wunschreihenfolge
    start_at: Optional[str] = None       # manuelle Öffnungszeit ("HH:MM" oder "TT.MM.JJJJ HH:MM")
    waitlist: bool = True                # bei vollen Gruppen auf die Warteliste gehen


class AppConfig(BaseModel):
    """Alles, was lokal in data/config.json gespeichert wird."""
    courses: list[CourseConfig] = Field(default_factory=list)
    save_snapshots: bool = False         # HTML-Seiten mitschreiben (enthalten Name + Matrikelnr.)


class Phase(str, Enum):
    IDLE = "idle"            # noch nicht gestartet
    WAITING = "waiting"      # wartet, bis der Nutzer die Kursseite öffnet
    PREPARING = "preparing"  # eigener Tab offen, Gruppen werden gelesen
    ARMED = "armed"          # Öffnungszeit bekannt, wartet auf den Schuss
    FIRING = "firing"        # Anmeldeversuche laufen
    DONE = "done"
    ERROR = "error"


class GroupInfo(BaseModel):
    """Eine Gruppenzeile, wie sie auf der LPIS-Seite steht."""
    id: str
    rank: int                            # Position in der Wunschliste (1 = erste Wahl)
    who: str = ""
    title: str = ""
    button: str = ""                     # Beschriftung des gefundenen Buttons
    enabled: bool = False
    free: Optional[int] = None
    status: str = ""
    opens: str = ""
    on_page: bool = True                 # False: Nummer steht nicht auf der Seite


class CourseState(BaseModel):
    config: CourseConfig
    phase: Phase = Phase.IDLE
    name: str = ""
    groups: list[GroupInfo] = Field(default_factory=list)
    opens_at: Optional[float] = None     # LPIS-Zeit (Unix)
    fire_at: Optional[float] = None      # Engine-Uhr (timing.now), zu der neu geladen wird
    result: str = ""
    message: str = ""                    # letzte Statuszeile für die Karte


class ClockState(BaseModel):
    offset: float = 0.0                  # LPIS-Zeit = Engine-Uhr + offset
    uncertainty: float = 0.5
    trip: float = 0.0                    # gemessene Latenz (round trip)
    source: str = "none"
    synced_at: Optional[float] = None


class EngineState(BaseModel):
    """Der komplette Zustand, den die UI anzeigt."""
    running: bool = False
    dry_run: bool = False
    mode: str = "live"                   # "live" | "dry" (Fake-LPIS) | "check" (Prüflauf, klickt nie)
    target: str = ""                     # Host, gegen den der Lauf geht (z. B. lpis.wu.ac.at)
    logged_in: Optional[bool] = None     # None: noch unbekannt
    now: float = 0.0                     # Engine-Uhr beim Senden (die UI gleicht ihre Uhr daran ab)
    clock: ClockState = Field(default_factory=ClockState)
    courses: list[CourseState] = Field(default_factory=list)
