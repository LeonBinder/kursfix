"""Lesen und Klicken der LPIS-Kursseite — alles passiert im echten DOM.

Es wird bewusst der Button geklickt, den auch ein Mensch klicken würde: LPIS
schützt seine Formulare mit einem ``seed`` und einem zufällig benannten
Hidden-Feld pro Seitenaufruf. Selbst gebaute Requests scheitern daran, ein
echter Klick nicht.

Nur die Tabellenklasse ``b3k-data`` wird als fix angenommen; der Button einer
Zeile ist das erste Steuer-Element, dessen Beschriftung nach An-/Abmelden
aussieht (Formular-Elemente bevorzugt), damit Änderungen an Zellklassen die App
nicht brechen.
"""
from __future__ import annotations

import datetime as dt
import re
from zoneinfo import ZoneInfo

VIENNA = ZoneInfo("Europe/Vienna")

# Button-Beschriftungen, die "schon angemeldet" bedeuten
REGISTERED_RE = re.compile(r"abmelden|deregist|unregist", re.I)
# Alert-Texte, die "auf der Warteliste gelandet" bedeuten
WAITLIST_RE = re.compile(r"warteliste|waiting list", re.I)
# Alert-Texte, die "bereits angemeldet / nicht mehr möglich" bedeuten
ALREADY_RE = re.compile(r"bereits|already", re.I)
# Seitentexte, die auf eine Warte-/Queue-Seite von LPIS hindeuten
BUSY_RE = re.compile(r"warte|queue|wait", re.I)
# URL-Bestandteile, die auf die Login-Seite hindeuten (= ausgeloggt)
LOGIN_URL_MARKERS = ("bach-id.", "/login")

_COMMON_JS = r"""
  const ACTION_RE = /anmelden|abmelden|warteliste|regist/i;
  const allRows = () => Array.from(document.querySelectorAll('table.b3k-data'))
    .flatMap(t => Array.from(t.querySelectorAll(':scope > tbody > tr')));
  const groupIdOf = row =>
    ((row.cells[0] && row.cells[0].innerText) || '').trim().split(/\s+/)[0];
  const labelOf = el =>
    ((el.value || el.innerText || el.title || el.alt || '') + '').trim();
  const controlOf = row => {
    const candidates = [
      ...row.querySelectorAll('form input[type="submit"], form input[type="image"], form button'),
      ...row.querySelectorAll('input[type="submit"], button, a'),
    ];
    const el = candidates.find(c => ACTION_RE.test(labelOf(c)))
            || candidates.find(c => c.tagName !== 'A')
            || null;
    if (!el) return { el: null, label: '', usable: false };
    const label = labelOf(el);
    const usable = !el.disabled && !el.classList.contains('disabled')
                 && !/abmelden|deregist|unregist/i.test(label);
    return { el, label, usable };
  };
"""

# Liest die ganze Kurstabelle als Daten; verändert nichts.
SNAPSHOT_JS = "() => {" + _COMMON_JS + r"""
  const rows = allRows().map(row => {
    const { label, usable } = controlOf(row);
    const flat = row.innerText.replace(/\s+/g, ' ').trim();
    const capCell = row.querySelector('td.capacity');
    const cap = ((capCell && capCell.innerText) || flat).match(/(\d+)\s*\/\s*(\d+)/);
    const info = ((row.cells[1] && row.cells[1].innerText) || '').trim().split('\n');
    const statusEl = row.querySelector('.box');
    const timeEl = row.querySelector('.timestamp');
    const opensInline = flat.match(/\bab\s+\d{1,2}\.\d{1,2}\.\d{4}\s+\d{1,2}:\d{2}/i);
    return {
      id: groupIdOf(row),
      button: label,
      enabled: usable,
      who: info[0] || '',
      title: info.slice(1).join(' ').replace(/\s+[A-Z]{2}$/, '').trim(),
      free: cap ? Number(cap[1]) : null,
      status: ((statusEl && statusEl.innerText) || '').trim(),
      opens: ((timeEl && timeEl.innerText) || (opensInline ? opensInline[0] : '')).trim(),
      text: flat,
    };
  });
  const alert = Array.from(document.querySelectorAll('.b3k_alert_content, [class*="alert"]'))
    .filter(el => el.getClientRects().length)
    .map(el => el.innerText.replace(/\s+/g, ' ').trim())
    .filter(Boolean)[0] || '';
  return {
    hasTable: !!document.querySelector('table.b3k-data'),
    rows, alert,
    bodyStart: ((document.body && document.body.innerText) || '').replace(/\s+/g, ' ').slice(0, 300),
  };
}"""

# Klickt den Button der Gruppe mit der gegebenen Nummer. Markiert die Seite
# vorher als "alt", damit der Aufrufer erkennt, wann die Antwortseite da ist.
CLICK_JS = "(wanted) => {" + _COMMON_JS + r"""
  const row = allRows().find(r => groupIdOf(r) === wanted);
  if (!row) return false;
  const { el, usable } = controlOf(row);
  if (!el || !usable) return false;
  window.__kursfixStalePage = true;
  el.click();
  return true;
}"""

# Wird nach dem Klick true: die alte Seite ist weg und die neue fertig geladen.
PAGE_TURNED_JS = "() => !window.__kursfixStalePage && document.readyState !== 'loading'"


def normalize_group(lv: str) -> str:
    """LV-Nummern vergleichbar machen (führende Nullen weg)."""
    return lv.strip().lstrip("0") or "0"


def rows_by_group(snapshot: dict | None) -> dict[str, dict]:
    """Die Zeilen eines Snapshots als {normalisierte LV-Nummer: Zeile}."""
    if not snapshot:
        return {}
    return {normalize_group(r["id"]): r for r in snapshot["rows"] if r["id"]}


def registered_row(rows: dict[str, dict]) -> dict | None:
    """Die Zeile, deren Button 'abmelden' zeigt — also die bestehende Anmeldung."""
    return next((r for r in rows.values() if REGISTERED_RE.search(r["button"])), None)


def parse_opening(row: dict) -> float | None:
    """Öffnungszeitpunkt (Unix, Wiener Zeit) aus dem opens-Feld einer Zeile."""
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})\D+(\d{1,2}):(\d{2})", row.get("opens", ""))
    if not m:
        return None
    day, month, year, hour, minute = map(int, m.groups())
    return dt.datetime(year, month, day, hour, minute, tzinfo=VIENNA).timestamp()


def parse_start_at(text: str) -> float:
    """Manuelle Startzeit: 'HH:MM', 'HH:MM:SS' oder 'TT.MM.JJJJ HH:MM[:SS]' (Wiener Zeit)."""
    for fmt in ("%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%H:%M:%S", "%H:%M"):
        try:
            parsed = dt.datetime.strptime(text.strip(), fmt)
        except ValueError:
            continue
        if not fmt.startswith("%d"):
            parsed = dt.datetime.combine(dt.datetime.now(VIENNA).date(), parsed.time())
        return parsed.replace(tzinfo=VIENNA).timestamp()
    raise ValueError(f"Startzeit {text!r} nicht lesbar — HH:MM oder TT.MM.JJJJ HH:MM")


def looks_logged_out(url: str) -> bool:
    return any(marker in url for marker in LOGIN_URL_MARKERS)
