"""SoundSight offline PS core; no board adapter is qualified."""

__version__ = "0.1.0"
SCOPE = "OFFLINE_SOFTWARE_ONLY"

from .contracts import Profile, ProtocolError, Refusal
from .session import Session

__all__ = ["Profile", "ProtocolError", "Refusal", "Session"]
