"""Prove that lab fault injection is opt-in and works in a running process."""

import os
import signal
import socket
import subprocess
import sys
import time
import unittest
from unittest.mock import call, patch
from urllib.error import HTTPError
from urllib.request import urlopen

from api.opsboard import lab_faults
from api.opsboard.app import response_for


class LabFaultUnitTests(unittest.TestCase):
    def setUp(self):
        lab_faults.state.ready = True
        lab_faults.state.live = True

    def tearDown(self):
        lab_faults.state.ready = True
        lab_faults.state.live = True

    def test_lab_signals_are_disabled_by_default(self):
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("api.opsboard.lab_faults.signal.signal") as install,
        ):
            self.assertFalse(lab_faults.register_lab_signals())
        install.assert_not_called()

    @unittest.skipUnless(os.name == "posix", "Unix signals required")
    def test_explicit_opt_in_registers_two_signal_handlers(self):
        with (
            patch.dict(os.environ, {"OPSBOARD_ENABLE_LAB_SIGNALS": "true"}),
            patch("api.opsboard.lab_faults.signal.signal") as install,
        ):
            self.assertTrue(lab_faults.register_lab_signals())
        install.assert_has_calls(
            [
                call(signal.SIGUSR1, lab_faults.toggle_readiness),
                call(signal.SIGUSR2, lab_faults.toggle_liveness),
            ]
        )
        self.assertEqual(install.call_count, 2)

    def test_readiness_toggle_does_not_kill_liveness(self):
        lab_faults.toggle_readiness(None, None)
        with patch.dict(
            os.environ, {"OPSBOARD_READY": "true", "OPSBOARD_LIVE": "true"}
        ):
            self.assertEqual(response_for("/health/ready", 1)[0], 503)
            self.assertEqual(response_for("/health/live", 1)[0], 200)
            lab_faults.toggle_readiness(None, None)
            self.assertEqual(response_for("/health/ready", 1)[0], 200)

    def test_liveness_toggle_is_independent(self):
        lab_faults.toggle_liveness(None, None)
        with patch.dict(
            os.environ, {"OPSBOARD_READY": "true", "OPSBOARD_LIVE": "true"}
        ):
            self.assertEqual(response_for("/health/live", 1)[0], 503)
            self.assertEqual(response_for("/health/ready", 1)[0], 200)


@unittest.skipUnless(os.name == "posix", "Unix signals required")
class LabFaultProcessTests(unittest.TestCase):
    def test_running_process_changes_health_without_http_admin_endpoint(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]

        env = os.environ.copy()
        env.update(
            {
                "PORT": str(port),
                "OPSBOARD_ENABLE_LAB_SIGNALS": "true",
                "OPSBOARD_LIVE": "true",
                "OPSBOARD_READY": "true",
            }
        )
        proc = subprocess.Popen(
            [sys.executable, "-m", "api.opsboard.app"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        def probe(endpoint):
            try:
                with urlopen(f"http://127.0.0.1:{port}{endpoint}", timeout=1) as res:
                    return res.status
            except HTTPError as exc:
                return exc.code

        def wait_for(endpoint, expected):
            for _ in range(60):
                if proc.poll() is not None:
                    self.fail("API process exited unexpectedly")
                try:
                    if probe(endpoint) == expected:
                        return
                except OSError:
                    pass
                time.sleep(0.05)
            self.fail(f"{endpoint} never returned HTTP {expected}")

        try:
            wait_for("/health/ready", 200)
            wait_for("/health/live", 200)
            proc.send_signal(signal.SIGUSR1)
            wait_for("/health/ready", 503)
            self.assertEqual(probe("/health/live"), 200)
            proc.send_signal(signal.SIGUSR1)
            wait_for("/health/ready", 200)
            proc.send_signal(signal.SIGUSR2)
            wait_for("/health/live", 503)
            self.assertEqual(probe("/health/ready"), 200)
            self.assertEqual(probe("/status"), 200)
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)


if __name__ == "__main__":
    unittest.main()
