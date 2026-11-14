from __future__ import annotations

import json
import shutil
import subprocess
import webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from helios.data.loader import get_meteo_settings
from helios.data.meteo import MeteoSwissClient, MeteoSwissError

WEB_DIR = Path(__file__).resolve().parents[1] / "web"
ECON_DIR = Path(__file__).resolve().parent / "economics"
HOST = "127.0.0.1"
PORT = 8000


class HeliosHandler(SimpleHTTPRequestHandler):
    """HTTP handler with a small MeteoSwiss proxy endpoint."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):  # noqa: N802 - signature imposed by BaseHTTPRequestHandler
        parsed = urlparse(self.path)
        if parsed.path == "/api/meteo":
            self._handle_meteo(parsed)
            return
        if parsed.path == "/api/economics":
            self._handle_economics(parsed)
            return
        super().do_GET()

    def _handle_meteo(self, parsed):
        params = parse_qs(parsed.query or "")
        try:
            lat = float(params.get("lat", [""])[0])
            lon = float(params.get("lon", [""])[0])
        except ValueError:
            self._send_json({"error": "Invalid lat/lon"}, status=400)
            return

        settings = get_meteo_settings()
        client = MeteoSwissClient(
            lang=settings.get("lang", "fr"),
            base_url=settings.get(
                "base_url", "https://app-prod-ws.meteoswiss.ch/v1/plasma/rest"
            ),
            timeout=int(settings.get("timeout", 10)),
            allow_fallback=bool(settings.get("allow_fallback", True)),
        )

        try:
            payload = client.fetch_weather(lat, lon)
        except MeteoSwissError as exc:
            self._send_json({"error": str(exc)}, status=502)
            return

        self._send_json(payload, status=200)

    def _send_json(self, payload, *, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_economics(self, parsed):
        params = parse_qs(parsed.query or "")
        kind = (params.get("kind", [""])[0] or "").lower()
        mapping = {
            "panels": ("Comparatif de 20 panneaux photovoltaïques.csv", "windows-1252"),
            "inverters": ("Comparatif de 10 onduleurs.csv", "utf-8"),
            "batteries": ("Comparatif de 10 batteries.csv", "utf-8"),
        }
        if kind not in mapping:
            self._send_json({"error": "Invalid kind"}, status=400)
            return
        filename, encoding = mapping[kind]
        path = ECON_DIR / filename
        if not path.exists():
            self._send_json({"error": "File not found"}, status=404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"text/csv; charset={encoding}")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run_server() -> None:
    """Serve the static web UI and open it in a browser."""
    if not WEB_DIR.exists():
        raise FileNotFoundError(f"Web directory not found: {WEB_DIR}")

    url = f"http://{HOST}:{PORT}/?v=1"
    if not webbrowser.open(url):
        opener = shutil.which("xdg-open")
        if opener:
            subprocess.Popen([opener, url])

    with ThreadingHTTPServer((HOST, PORT), HeliosHandler) as httpd:
        print(f"Serving HELIOS UI at {url} (dir={WEB_DIR})")
        httpd.serve_forever()


if __name__ == "__main__":
    run_server()
