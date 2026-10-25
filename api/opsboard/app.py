"""OpsBoard HTTP API.

No third-party Python dependencies. Health failure modes are controlled via
environment variables so that Kubernetes probes can be studied safely.
"""

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

STARTED_AT = time.monotonic()


def is_enabled(key: str) -> bool:
    """Parse explicit true/false environment flags."""
    return os.getenv(key, "true").lower() in {"1", "yes", "true", "on"}


def response_for(path: str, elapsed: float) -> tuple[int, dict]:
    """Return an HTTP status and JSON document for an endpoint."""
    if path == "/health/live":
        healthy = is_enabled("OPSBOARD_LIVE")
        return (200 if healthy else 503, {"status": "alive" if healthy else "failed"})

    if path == "/health/ready":
        ready = is_enabled("OPSBOARD_READY")
        return (200 if ready else 503, {"status": "ready" if ready else "not-ready"})

    if path == "/health/startup":
        try:
            delay = max(float(os.getenv("STARTUP_DELAY_SECONDS", "0")), 0)
        except ValueError:
            delay = 0
        started = elapsed >= delay
        return (200 if started else 503, {"status": "started" if started else "starting"})

    if path == "/version":
        return 200, {"version": os.getenv("APP_VERSION", "dev")}

    if path == "/status":
        return 200, {
            "application": "OpsBoard",
            "environment": os.getenv("ENVIRONNEMENT", "lab"),
            "message": os.getenv("MESSAGE_BANNIERE", "Kubernetes est prêt !"),
            "components": [
                {"name": "api", "status": "operational"},
                {"name": "frontend", "status": "operational"},
            ],
        }
    return 404, {"error": "not found"}


class Handler(BaseHTTPRequestHandler):
    """Serve a few intentionally simple JSON endpoints."""

    def do_GET(self) -> None:  # noqa: N802 (stdlib handler API)
        path = urlsplit(self.path).path
        status, document = response_for(path, time.monotonic() - STARTED_AT)
        payload = json.dumps(document, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    """Start the application on the unprivileged container port."""
    port = int(os.getenv("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)  # nosec B104
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
