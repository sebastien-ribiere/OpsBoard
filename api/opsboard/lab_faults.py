"""Opt-in, process-local fault injection for the classroom.

No HTTP admin route, new listener, socket or external dependency.
These handlers are installed only in explicitly enabled Linux lab instances.
Do not enable them in production.
"""

import os
import signal
from dataclasses import dataclass


@dataclass(slots=True)
class FaultState:
    ready: bool = True
    live: bool = True


state = FaultState()


def toggle_readiness(_signum: int | None, _frame: object) -> None:
    """SIGUSR1: switch readiness between success and 503."""
    state.ready = not state.ready


def toggle_liveness(_signum: int | None, _frame: object) -> None:
    """SIGUSR2: switch liveness; kubelet can restart the container."""
    state.live = not state.live


def register_lab_signals() -> bool:
    """Enable local fault toggles only after explicit operator opt-in."""
    enabled = os.environ.get("OPSBOARD_ENABLE_LAB_SIGNALS", "false").lower()
    if os.name != "posix" or enabled not in {"1", "true", "yes", "on"}:
        return False

    signal.signal(signal.SIGUSR1, toggle_readiness)
    signal.signal(signal.SIGUSR2, toggle_liveness)
    return True
