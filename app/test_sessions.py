from __future__ import annotations

from dataclasses import dataclass
from threading import Lock


@dataclass
class SystemTestSession:
    session_id: str
    ready: bool = True


_lock = Lock()
_sessions: dict[str, SystemTestSession] = {}


def create_session(session_id: str) -> SystemTestSession:
    with _lock:
        if session_id in _sessions:
            raise KeyError(session_id)
        session = SystemTestSession(session_id=session_id)
        _sessions[session_id] = session
        return session


def get_session(session_id: str) -> SystemTestSession | None:
    with _lock:
        return _sessions.get(session_id)
