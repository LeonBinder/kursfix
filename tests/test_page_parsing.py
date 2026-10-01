"""Der DOM-Scanner gegen echte, vom Fake gerenderte Seiten (headless Chromium)."""
import asyncio

from playwright.async_api import async_playwright

from backend import lpis_page as lp
from fakelpis.server import FakeLpis


async def _scan_course(fake: FakeLpis, key: str = "a") -> dict:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(f"{fake.base_url}/course/{key}")
        # Landet auf /login: einloggen, dann zurück zur Kursseite
        if "/login" in page.url:
            await page.click("input[type=submit]")
            await page.wait_for_url("**/course/*")
        snap = await page.evaluate(lp.SNAPSHOT_JS)
        await browser.close()
        return snap


async def test_scan_before_opening():
    fake = FakeLpis(opens_in=120, full_at_open={"1111"}).start()
    try:
        snap = await _scan_course(fake)
    finally:
        fake.stop()
    assert snap["hasTable"]
    rows = lp.rows_by_group(snap)
    assert set(rows) == {"1111", "1112", "1113"}
    r = rows["1111"]
    assert r["button"] == "anmelden" and not r["enabled"]   # noch gesperrt
    assert r["free"] == 23                                  # füllt sich erst zur Öffnung
    assert r["status"] == "Anmeldung nicht möglich"
    assert r["opens"].startswith("ab ")
    assert r["who"] == "Lektor A."
    assert lp.registered_row(rows) is None


async def test_scan_after_opening_and_login_page():
    fake = FakeLpis(opens_in=0, full_at_open={"1111"}).start()
    try:
        snap = await _scan_course(fake)
        rows = lp.rows_by_group(snap)
        assert rows["1112"]["enabled"] and rows["1112"]["free"] == 23
        assert rows["1111"]["free"] == 0                    # zur Öffnung sofort voll
        # Login-Seite: keine Kurstabelle — so wird "ausgeloggt" erkannt
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(f"{fake.base_url}/course/a")
            login_snap = await page.evaluate(lp.SNAPSHOT_JS)
            assert not login_snap["hasTable"]
            assert lp.looks_logged_out(page.url)
            await browser.close()
    finally:
        fake.stop()
