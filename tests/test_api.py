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


    def test_status_defaults_and_overrides(self):
        with patch.dict(os.environ, {}, clear=True):
            code, data = response_for("/status", elapsed=0)
        self.assertEqual(code, 200)
        self.assertEqual(data["environment"], "lab")
        self.assertEqual(data["message"], "Kubernetes est prêt !")

        with patch.dict(
            os.environ,
            {"ENVIRONNEMENT": "staging", "MESSAGE_BANNIERE": "Ready"},
            clear=True,
        ):
            code, data = response_for("/status", elapsed=0)
        self.assertEqual(code, 200)
        self.assertEqual(data["environment"], "staging")
        self.assertEqual(data["message"], "Ready")

    def test_version_uses_dev_when_not_configured(self):
        with patch.dict(os.environ, {}, clear=True):
            code, data = response_for("/version", elapsed=0)
        self.assertEqual((code, data), (200, {"version": "dev"}))

    def test_liveness_defaults_to_healthy(self):
        with patch.dict(os.environ, {}, clear=True):
            code, data = response_for("/health/live", elapsed=0)
        self.assertEqual((code, data), (200, {"status": "alive"}))

    def test_readiness_defaults_to_ready(self):
        with patch.dict(os.environ, {}, clear=True):
            code, data = response_for("/health/ready", elapsed=0)
        self.assertEqual((code, data), (200, {"status": "ready"}))

    def test_failed_probes_have_expected_payloads(self):
        with patch.dict(
            os.environ,
            {"OPSBOARD_LIVE": "false", "OPSBOARD_READY": "false"},
            clear=True,
        ):
            live = response_for("/health/live", elapsed=0)
            ready = response_for("/health/ready", elapsed=0)
        self.assertEqual(live, (503, {"status": "failed"}))
        self.assertEqual(ready, (503, {"status": "not-ready"}))

    def test_startup_without_delay_is_ready(self):
        with patch.dict(os.environ, {}, clear=True):
            code, data = response_for("/health/startup", elapsed=0)
        self.assertEqual((code, data), (200, {"status": "started"}))

    def test_startup_matches_exact_threshold(self):
        with patch.dict(os.environ, {"STARTUP_DELAY_SECONDS": "15"}, clear=True):
            before = response_for("/health/startup", elapsed=14.99)
            at_threshold = response_for("/health/startup", elapsed=15.0)
        self.assertEqual(before, (503, {"status": "starting"}))
        self.assertEqual(at_threshold, (200, {"status": "started"}))

    def test_invalid_startup_delay_falls_back_to_zero(self):
        with patch.dict(
            os.environ, {"STARTUP_DELAY_SECONDS": "invalid"}, clear=True
        ):
            code, data = response_for("/health/startup", elapsed=0)
        self.assertEqual((code, data), (200, {"status": "started"}))

    def test_negative_startup_delay_is_clamped_to_zero(self):
        with patch.dict(os.environ, {"STARTUP_DELAY_SECONDS": "-10"}, clear=True):
            code, data = response_for("/health/startup", elapsed=0)
        self.assertEqual((code, data), (200, {"status": "started"}))

    def test_unrecognized_path_returns_json_404(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                response_for("/health/unknown", elapsed=0),
                (404, {"error": "not found"}),
            )


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
