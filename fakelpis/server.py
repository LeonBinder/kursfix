"""Lokaler Fake-LPIS für Trockenlauf und Tests. Sendet nichts an die WU.

Bildet die Eigenheiten der echten Seite nach, auf die sich die Engine stützt:

- Kurstabellen mit der Klasse ``b3k-data``, Kapazität "x / y", Status-Box,
  Öffnungszeit ("ab TT.MM.JJJJ HH:MM") und einem echten Submit-Button pro Zeile
- Anti-Bot-Felder: jedes gerenderte Formular bekommt einen ``seed`` und ein
  zufällig benanntes Hidden-Feld; ein POST ohne beide wird abgelehnt (selbst
  gebaute Requests scheitern, echte Klicks nicht)
- Login mit Session-Cookie; Sessions können ablaufen (Logout-Test)
- Gruppen, die sich zur Öffnung sofort füllen (Warteliste-Test), und Klicks,
  die erst beim n-ten Mal durchgehen (Retry-Test)

Standalone starten:  python -m fakelpis.server --opens-in 120
"""
from __future__ import annotations

import argparse
import datetime as dt
import http.server
import secrets
import threading
import time
import urllib.parse
from zoneinfo import ZoneInfo

VIENNA = ZoneInfo("Europe/Vienna")

DEFAULT_COURSES = {
    "a": ("Beispielkurs A", {"1111": "Lektor A.", "1112": "Lektor B.", "1113": "Lektor C."}),
    "b": ("Beispielkurs B", {"2221": "Lektor D.", "2222": "Lektor E."}),
    "c": ("Beispielkurs C", {"3331": "Lektor F.", "3332": "Lektor G."}),
}

CAPACITY = 23

# Nur der erste Tab läuft die Kursseiten ab (sessionStorage ist pro Tab),
# damit die eigenen Tabs der Engine nicht mitwandern.
TOUR_JS = """<script>
const tour = (sessionStorage.tour || '').split(',').filter(Boolean);
if (tour[0] === '%s') {
  const rest = tour.slice(1);
  sessionStorage.tour = rest.join(',');
  if (rest.length) setTimeout(() => location.href = '/course/' + rest[0], 1200);
}
</script>"""


class FakeLpis:
    def __init__(self, port: int = 0, opens_in: float = 20.0,
                 opens_at: float | None = None,
                 courses: dict | None = None,
                 full_at_open: set[str] | frozenset[str] = frozenset(),
                 reject_clicks: dict[str, int] | None = None,
                 session_ttl: float | None = None,
                 auto_login: bool = False,
                 latency: float = 0.05):
        self.opens_at = opens_at if opens_at is not None else float(int(time.time() + opens_in))
        self.courses = courses or DEFAULT_COURSES
        self.full_at_open = set(full_at_open)
        self.reject_clicks = dict(reject_clicks or {})   # lv -> Zahl absichtlicher Fehlklicks
        self.session_ttl = session_ttl
        self.auto_login = auto_login
        self.latency = latency
        self.registered: dict[str, str] = {}             # lv -> "fix" | "warteliste"
        self.sessions: dict[str, dict] = {}              # sid -> {created, tokens}
        self.lock = threading.Lock()
        fake = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            # --- Antworten -----------------------------------------------------

            def send_html(self, html: str, status: int = 200,
                          cookie: str | None = None):
                time.sleep(fake.latency)
                body = html.encode()
                self.send_response(status)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                if cookie:
                    self.send_header("Set-Cookie", f"sid={cookie}; Path=/")
                self.end_headers()
                self.wfile.write(body)

            def redirect(self, where: str):
                self.send_response(302)
                self.send_header("Location", where)
                self.send_header("Content-Length", "0")
                self.end_headers()

            # --- Session ------------------------------------------------------

            def session(self) -> dict | None:
                cookies = self.headers.get("Cookie", "")
                sid = next((p.split("=", 1)[1] for p in cookies.split(";")
                            if p.strip().startswith("sid=")), "").strip()
                with fake.lock:
                    sess = fake.sessions.get(sid)
                    if not sess:
                        return None
                    if fake.session_ttl and time.time() - sess["created"] > fake.session_ttl:
                        del fake.sessions[sid]
                        return None
                    return sess

            # --- Routen --------------------------------------------------------

            def do_GET(self):
                path, _, query = self.path.partition("?")
                if path == "/login":
                    return self.send_html(fake.login_page(query))
                sess = self.session()
                if not sess:
                    return self.redirect("/login?next=" + urllib.parse.quote(self.path))
                if path == "/" or path == "/overview":
                    return self.send_html(fake.overview_page())
                if path == "/start":
                    keys = ",".join(fake.courses)
                    return self.send_html(
                        f"<script>sessionStorage.tour='{keys}';"
                        f"location.href='/course/{next(iter(fake.courses))}';</script>")
                if path.startswith("/course/"):
                    key = path.rsplit("/", 1)[-1]
                    if key not in fake.courses:
                        return self.send_error(404)
                    return self.send_html(fake.course_page(key, sess))
                return self.send_error(404)

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                form = urllib.parse.parse_qs(self.rfile.read(length).decode())
                field = lambda name: form.get(name, [""])[0]  # noqa: E731
                if self.path.startswith("/login"):
                    sid = secrets.token_hex(16)
                    with fake.lock:
                        fake.sessions[sid] = {"created": time.time(), "tokens": {}}
                    query = urllib.parse.urlparse(self.path).query
                    target = urllib.parse.parse_qs(query).get("next", ["/overview"])[0]
                    html = f"<script>location.href={target!r};</script>"
                    return self.send_html(html, cookie=sid)
                sess = self.session()
                if not sess:
                    return self.redirect("/login")
                key = self.path.rsplit("/", 1)[-1]
                if key not in fake.courses:
                    return self.send_error(404)
                lv = field("lv")
                alert = fake.attempt(sess, key, lv, form)
                return self.send_html(fake.course_page(key, sess, alert=alert))

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
        self.port = self.server.server_address[1]
        self.base_url = f"http://127.0.0.1:{self.port}"
        self._thread: threading.Thread | None = None

    # --- Anmeldelogik ------------------------------------------------------------

    def attempt(self, sess: dict, key: str, lv: str, form: dict) -> str:
        """Ein Anmeldeklick; gibt den Alert-Text der Antwortseite zurück."""
        with self.lock:
            token = sess["tokens"].get(form.get("seed", [""])[0])
            if (not token or token["lv"] != lv
                    or form.get(token["name"], [""])[0] != token["value"]):
                return "Ungültige Anfrage (seed). Bitte die Seite neu laden."
            if lv not in self.courses[key][1]:
                return "Unbekannte Lehrveranstaltung."
            if time.time() < self.opens_at:
                return "Die Anmeldung ist derzeit nicht möglich."
            if self.reject_clicks.get(lv, 0) > 0:
                self.reject_clicks[lv] -= 1
                return "Technischer Fehler. Bitte versuchen Sie es erneut."
            if lv in self.full_at_open:
                self.registered[lv] = "warteliste"
                return ("Die Lehrveranstaltung ist bereits voll. "
                        "Sie wurden auf die Warteliste gesetzt.")
            self.registered[lv] = "fix"
            return "Sie haben sich erfolgreich angemeldet."

    # --- Seiten ---------------------------------------------------------------------

    def login_page(self, query: str = "") -> str:
        auto = "<script>document.forms[0].submit();</script>" if self.auto_login else ""
        action = "/login" + (f"?{query}" if query else "")
        return ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
                "<title>Fake-WU-Login</title></head><body>"
                "<h1>Fake-LPIS — Login</h1>"
                "<p>So loggst du dich beim echten LPIS per WU-SSO ein. Hier reicht ein Klick.</p>"
                f"<form method='post' action='{action}'>"
                "<input type='submit' value='Login'></form>"
                f"{auto}</body></html>")

    def overview_page(self) -> str:
        links = "".join(f"<li><a href='/course/{k}'>{title}</a></li>"
                        for k, (title, _) in self.courses.items())
        opens = dt.datetime.fromtimestamp(self.opens_at, VIENNA).strftime("%H:%M:%S")
        return ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
                "<title>Fake-LPIS</title></head><body>"
                f"<h1>Fake-LPIS</h1><p>Anmeldung öffnet um {opens}.</p>"
                f"<p>Kursseiten (nacheinander öffnen):</p><ul>{links}</ul>"
                "<p><a href='/start'>Automatische Tour durch alle Kurse</a></p>"
                "</body></html>")

    def course_page(self, key: str, sess: dict, alert: str = "") -> str:
        title, groups = self.courses[key]
        is_open = time.time() >= self.opens_at
        opens_text = dt.datetime.fromtimestamp(self.opens_at, VIENNA).strftime(
            "ab %d.%m.%Y %H:%M")
        rows = []
        for lv, who in groups.items():
            state = self.registered.get(lv)
            if is_open and lv in self.full_at_open:
                free = 0
            else:
                free = CAPACITY - (1 if state == "fix" else 0)
            seed = secrets.token_hex(8)
            fname, fvalue = "f" + secrets.token_hex(4), secrets.token_hex(8)
            with self.lock:
                sess["tokens"][seed] = {"lv": lv, "name": fname, "value": fvalue}
            hidden = (f"<input type='hidden' name='lv' value='{lv}'>"
                      f"<input type='hidden' name='seed' value='{seed}'>"
                      f"<input type='hidden' name='{fname}' value='{fvalue}'>")
            form_open = f"<form method='post' action='/course/{key}'>{hidden}"
            if state:
                box = "angemeldet" if state == "fix" else "Warteliste"
                action = form_open + "<input type='submit' name='cmd' value='abmelden'></form>"
            elif is_open:
                box = "Anmeldung möglich"
                action = form_open + "<input type='submit' name='cmd' value='anmelden'></form>"
            else:
                box = "Anmeldung nicht möglich"
                action = (form_open + "<input type='submit' name='cmd' value='anmelden' disabled>"
                          f"</form><div class='timestamp'><span>{opens_text}</span></div>")
            rows.append(
                f"<tr><td class='ver_id'><a href='#'>{lv}</a><br>WiSe 2026</td>"
                f"<td class='ver_title'><div>{who}</div><span>{title}</span></td>"
                f"<td class='capacity'><div>frei</div><div>{free} / {CAPACITY}</div></td>"
                f"<td class='box'><div class='box'>{box}</div></td>"
                f"<td class='action'>{action}</td></tr>")
        alert_html = (f"<div class='b3k_alert'><div class='b3k_alert_content'>{alert}</div></div>"
                      if alert else "")
        return ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>Fake-LPIS — {title}</title></head><body>{alert_html}"
                f"<h2>{title}</h2>"
                "<table class='b3k-data'><thead><tr><th colspan='2'>Veranstaltung</th>"
                "<th>Plätze</th><th colspan='2'> </th></tr></thead>"
                f"<tbody>{''.join(rows)}</tbody></table>"
                f"{TOUR_JS % key}</body></html>")

    # --- Lebenszyklus ------------------------------------------------------------------

    def start(self):
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self.server.shutdown()
        self.server.server_close()


def main():
    parser = argparse.ArgumentParser(description="Fake-LPIS standalone starten")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--opens-in", type=float, default=120.0,
                        help="Sekunden bis zur Anmeldeöffnung")
    parser.add_argument("--session-ttl", type=float, default=None,
                        help="Sekunden, nach denen die Session abläuft")
    args = parser.parse_args()
    fake = FakeLpis(port=args.port, opens_in=args.opens_in,
                    full_at_open={"1111", "2221"}, session_ttl=args.session_ttl)
    fake.start()
    opens = dt.datetime.fromtimestamp(fake.opens_at, VIENNA).strftime("%H:%M:%S")
    print(f"Fake-LPIS läuft auf {fake.base_url} — Anmeldung öffnet um {opens}. Strg+C beendet.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        fake.stop()


if __name__ == "__main__":
    main()
