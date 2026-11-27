"""Uhrabgleich gegen WU und punktgenaues Warten.

Zwei unabhängige Quellen, die sich gegenseitig prüfen:

- SNTP gegen ``timeserver.wu.ac.at`` (präzise, aber UDP kann gefiltert sein)
- Der ``Date``-Header des LPIS-Servers selbst (nur sekundengenau, liefert aber
  harte Schranken: die Serverantwort muss innerhalb des Request-Fensters liegen)

Liegt der SNTP-Wert innerhalb der HTTP-Schranken, wird er genommen; sonst die
Mitte der Schranken. Geht beides schief, bleibt die PC-Uhr mit großer
Unsicherheit.
"""
from __future__ import annotations

import asyncio
import email.utils
import http.client
import socket
import statistics
import struct
import time
from dataclasses import dataclass

NTP_UNIX_DELTA = 2_208_988_800  # Sekunden zwischen NTP-Epoche (1900) und Unix-Epoche (1970)
SAFETY_MARGIN = 0.02            # s nach der Öffnung, zu denen der Request ankommen soll


# --- Stabile Uhr ---------------------------------------------------------------
# Die Systemuhr (time.time) kann springen oder zu schnell/langsam laufen, wenn
# ein Zeitdienst sie nachstellt — in WSL2 wurden 8 % Fehlgang und 3-s-Sprünge
# alle 35 s gemessen. Für das Timing zählt nur, dass die Uhr GLEICHMÄSSIG läuft;
# den Abstand zur LPIS-Zeit misst der Uhrabgleich ohnehin. Darum läuft alles auf
# der Rohuhr des Kernels (CLOCK_MONOTONIC_RAW), die niemand verstellt, einmal
# beim Start an die Systemuhr angelegt, damit die Werte wie Unix-Zeit aussehen.
_RAW_CLOCK = getattr(time, "CLOCK_MONOTONIC_RAW", None)


def _raw() -> float:
    if _RAW_CLOCK is not None:
        return time.clock_gettime(_RAW_CLOCK)
    return time.perf_counter()  # Windows: gleichmäßig, ohne Sprünge


_ANCHOR = time.time() - _raw()


def now() -> float:
    """Gleichmäßig laufende Uhr in Unix-Sekunden (springt nie). LPIS-Zeit = now() + offset."""
    return _ANCHOR + _raw()


@dataclass
class ClockSync:
    offset: float        # Serverzeit = now() + offset
    uncertainty: float   # geschätzter Fehler des Offsets in s
    trip: float          # Latenz (round trip) in s
    source: str


def _ntp_timestamp(packet: bytes, pos: int) -> float:
    whole, frac = struct.unpack("!II", packet[pos:pos + 8])
    return whole - NTP_UNIX_DELTA + frac / 2**32


def sntp_sample(host: str, attempts: int = 4, timeout: float = 1.5):
    """Bestes (offset, round trip) aus mehreren SNTP-Anfragen, oder None."""
    best = None
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            for _ in range(attempts):
                sent = now()
                sock.sendto(b"\x1b" + 47 * b"\0", (host, 123))
                packet = sock.recv(48)
                received = now()
                if len(packet) < 48 or packet[1] == 0:  # Stratum 0: Kiss-o'-Death
                    continue
                srv_rx = _ntp_timestamp(packet, 32)
                srv_tx = _ntp_timestamp(packet, 40)
                offset = ((srv_rx - sent) + (srv_tx - received)) / 2
                trip = (received - sent) - (srv_tx - srv_rx)
                if best is None or trip < best[1]:
                    best = (offset, trip)
    except OSError:
        pass
    return best


def http_date_bounds(host: str, port: int | None = None, https: bool = True,
                     samples: int = 12, timeout: float = 5.0):
    """Schranken (lo, hi) für Serverzeit minus PC-Zeit aus dem Date-Header, plus Median-Latenz.

    Der Header ist nur sekundengenau; jede Antwort engt das Fenster aber weiter ein.
    """
    lo, hi, trips = -1e9, 1e9, []
    conn_cls = http.client.HTTPSConnection if https else http.client.HTTPConnection
    conn = conn_cls(host, port, timeout=timeout)
    try:
        for _ in range(samples):
            sent = now()
            conn.request("HEAD", "/")
            resp = conn.getresponse()
            resp.read()
            received = now()
            header = resp.getheader("Date")
            server = email.utils.parsedate_to_datetime(header).timestamp()
            # Der Server hat den Header irgendwann zwischen sent und received gestempelt,
            # und die Sekunde "server" deckt [server, server+1) ab.
            lo = max(lo, server - received)
            hi = min(hi, server + 1 - sent)
            trips.append(received - sent)
            time.sleep(0.05)
    except (OSError, http.client.HTTPException, TypeError, ValueError):
        if not trips:
            return None
    finally:
        conn.close()
    return lo, hi, statistics.median(trips)


def measure(ntp_host: str, http_host: str, http_port: int | None = None,
            https: bool = True) -> ClockSync:
    """Beide Quellen messen und kombinieren. Blockiert einige Sekunden."""
    web = http_date_bounds(http_host, port=http_port, https=https)
    ntp = sntp_sample(ntp_host) if ntp_host else None
    trip = web[2] if web else 0.05
    if ntp and (web is None or web[0] - 0.1 <= ntp[0] <= web[1] + 0.1):
        return ClockSync(ntp[0], ntp[1] / 2 + 0.005, trip, "WU-Zeitserver")
    if web:
        lo, hi, _ = web
        return ClockSync((lo + hi) / 2, min((hi - lo) / 2, 0.5), trip, "LPIS-Serveruhr")
    return ClockSync(0.0, 0.5, trip, "PC-Uhr (Abgleich fehlgeschlagen)")


async def measure_async(ntp_host: str, http_host: str, http_port: int | None = None,
                        https: bool = True) -> ClockSync:
    """measure() in einem Thread, damit der Event-Loop weiterläuft."""
    return await asyncio.to_thread(measure, ntp_host, http_host, http_port, https)


def fire_time(opens_at: float, sync: ClockSync) -> float:
    """PC-Zeit, zu der der Reload losgeschickt wird, damit er kurz nach Öffnung ankommt."""
    return opens_at - sync.offset - sync.trip / 2 + sync.uncertainty + SAFETY_MARGIN


async def sleep_until(t: float):
    """Bis zum Zeitpunkt t (auf der now()-Uhr) schlafen; die letzten Millisekunden aktiv warten.

    asyncio schläft auf der Monotonuhr des Systems, die zu langsam oder zu schnell
    gehen kann — darum in Etappen annähern und jedes Mal neu auf now() schauen.
    """
    while (remaining := t - now()) > 0.03:
        await asyncio.sleep(max(0.005, (remaining - 0.03) * 0.8))
    while now() < t:
        pass
