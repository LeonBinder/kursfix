#!/usr/bin/env python3
"""kursfix starten: Frontend bei Bedarf bauen, Server hochfahren, Browser öffnen.

    python run.py            # http://127.0.0.1:8237
    python run.py --port 9000 --no-browser
"""
import argparse
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "frontend" / "dist" / "index.html"


def build_frontend():
    if DIST.exists():
        return
    npm = shutil.which("npm")
    if not npm:
        print("Hinweis: npm nicht gefunden und frontend/dist fehlt — die UI ist "
              "nicht verfügbar. Node.js installieren und erneut starten.")
        return
    print("Baue das Frontend (einmalig) …")
    frontend = ROOT / "frontend"
    if not (frontend / "node_modules").exists():
        subprocess.run([npm, "install"], cwd=frontend, check=True)
    subprocess.run([npm, "run", "build"], cwd=frontend, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8237)
    parser.add_argument("--no-browser", action="store_true",
                        help="Browser nicht automatisch öffnen")
    args = parser.parse_args()

    try:
        import uvicorn  # noqa: F401
    except ImportError:
        sys.exit("Abhängigkeiten fehlen — erst:  pip install -r requirements.txt "
                 "&& playwright install chromium")

    build_frontend()
    url = f"http://127.0.0.1:{args.port}"
    if not args.no_browser:
        threading.Thread(target=lambda: (time.sleep(1.2), webbrowser.open(url)),
                         daemon=True).start()
    print(f"kursfix läuft auf {url}  (Strg+C beendet)")
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
