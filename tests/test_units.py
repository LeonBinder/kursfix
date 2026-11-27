"""Reine Einheiten: Zeitrechnung, Seiten-Parsing-Helfer, Konfig-Speicher."""
import datetime as dt
import time

import pytest

from backend import lpis_page as lp
from backend import timing
from backend.models import AppConfig, CourseConfig
from backend.store import load_config, save_config
from fakelpis.server import FakeLpis


def test_normalize_group():
    assert lp.normalize_group(" 0123 ") == "123"
    assert lp.normalize_group("0000") == "0"
    assert lp.normalize_group("4711") == "4711"


def test_parse_opening():
    row = {"opens": "ab 28.09.2026 14:00"}
    t = lp.parse_opening(row)
    local = dt.datetime.fromtimestamp(t, lp.VIENNA)
    assert (local.day, local.month, local.hour, local.minute) == (28, 9, 14, 0)
    assert lp.parse_opening({"opens": ""}) is None


def test_parse_opening_ignores_deadlines():
    """'bis …' ist das Fristende einer offenen Anmeldung, keine Öffnungszeit."""
    assert lp.parse_opening({"opens": "bis 27.11.2026 23:59"}) is None
    assert lp.parse_opening({"opens": "Anmeldung bis 27.11.2026 23:59"}) is None
    both = lp.parse_opening({"opens": "ab 28.09.2026 14:00 bis 27.11.2026 23:59"})
    assert dt.datetime.fromtimestamp(both, lp.VIENNA).month == 9
    late = lp.parse_opening({"opens": "bis 01.09.2026 12:00, ab 28.09.2026 14:00"})
    assert dt.datetime.fromtimestamp(late, lp.VIENNA).day == 28


def test_parse_start_at():
    t = lp.parse_start_at("28.09.2026 14:00")
    assert dt.datetime.fromtimestamp(t, lp.VIENNA).hour == 14
    today = lp.parse_start_at("23:59:30")
    local = dt.datetime.fromtimestamp(today, lp.VIENNA)
    assert (local.hour, local.minute, local.second) == (23, 59, 30)
    with pytest.raises(ValueError):
        lp.parse_start_at("morgen früh")


def test_fire_time_lands_just_after_opening():
    sync = timing.ClockSync(offset=0.4, uncertainty=0.01, trip=0.08, source="test")
    opens = 1_000_000.0
    fire = timing.fire_time(opens, sync)
    # Ankunft beim Server: Abschicken + halbe Latenz, in Serverzeit:
    arrival = fire + sync.trip / 2 + sync.offset
    assert opens < arrival < opens + 0.1


def test_http_date_bounds_against_fake():
    fake = FakeLpis(opens_in=60).start()
    try:
        bounds = timing.http_date_bounds("127.0.0.1", port=fake.port,
                                         https=False, samples=4)
    finally:
        fake.stop()
    assert bounds is not None
    lo, hi, trip = bounds
    assert lo <= hi
    assert lo <= 0.1 and hi >= -0.1   # lokaler Server: Offset ~0 liegt im Fenster
    assert 0 < trip < 2


def test_looks_logged_out():
    assert lp.looks_logged_out("https://bach-id.wu.ac.at/idp/login")
    assert lp.looks_logged_out("http://127.0.0.1:1234/login?next=%2Fstart")
    assert not lp.looks_logged_out("https://lpis.wu.ac.at/kdcs/bach-s99/123")


def test_store_roundtrip(tmp_path):
    path = tmp_path / "config.json"
    cfg = AppConfig(courses=[CourseConfig(id="x", label="Mathe", groups=["1111", "1112"],
                                          start_at="14:00", waitlist=False)])
    save_config(cfg, path)
    loaded = load_config(path)
    assert loaded == cfg
    assert load_config(tmp_path / "fehlt.json") == AppConfig()


def test_waitlist_rows_count_as_taken():
    """'austragen' = Wartelistenplatz: gilt als bestehender Eintrag, nicht als Ziel."""
    rows = {"1743": {"id": "1743", "button": "austragen",
                     "status": "Wartelisteneintrag\n27.11.2026 14:00"},
            "1822": {"id": "1822", "button": "eintragen",
                     "status": "Wartelisteneintrag möglich"}}
    assert lp.registered_row(rows)["id"] == "1743"
    assert lp.is_waitlisted(rows["1743"])
    assert not lp.is_waitlisted(rows["1822"])
    assert not lp.is_waitlisted({"button": "abmelden", "status": "angemeldet"})
    assert lp.registered_row({"1822": rows["1822"]}) is None
