"""Behavioral tests for the intentionally small teaching API."""

import json
import os
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from api.opsboard.app import Handler, response_for


class RouteTests(unittest.TestCase):
    def test_status_has_components(self):
        code, data = response_for("/status", elapsed=20)
        self.assertEqual(code, 200)
        self.assertEqual(len(data["components"]), 2)

    def test_version_is_configurable(self):
        with patch.dict(os.environ, {"APP_VERSION": "v2"}):
            code, data = response_for("/version", elapsed=0)
        self.assertEqual((code, data["version"]), (200, "v2"))

    def test_readiness_does_not_require_liveness_failure(self):
        with patch.dict(
            os.environ, {"OPSBOARD_READY": "false", "OPSBOARD_LIVE": "true"}
        ):
            ready_code, _ = response_for("/health/ready", elapsed=10)
            live_code, _ = response_for("/health/live", elapsed=10)
        self.assertEqual(ready_code, 503)
        self.assertEqual(live_code, 200)

    def test_liveness_can_fail(self):
        with patch.dict(os.environ, {"OPSBOARD_LIVE": "false"}):
            code, _ = response_for("/health/live", elapsed=10)
        self.assertEqual(code, 503)

    def test_startup_is_delayed(self):
        with patch.dict(os.environ, {"STARTUP_DELAY_SECONDS": "15"}):
            self.assertEqual(response_for("/health/startup", 5)[0], 503)
            self.assertEqual(response_for("/health/startup", 16)[0], 200)

    def test_unknown_path(self):
        self.assertEqual(response_for("/missing", 0)[0], 404)


class HttpTests(unittest.TestCase):
    def test_real_http_json_contract(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=3)
            client.request("GET", "/version")
            response = client.getresponse()
            body = json.loads(response.read())
            self.assertEqual(response.status, 200)
            self.assertEqual(response.getheader("Content-Type"), "application/json; charset=utf-8")
            self.assertIn("version", body)
            client.close()
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
