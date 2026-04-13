"""Backward-compatibility shim — all config lives in api.core.config.

Import from api.core.config going forward.
"""

from api.core.config import Settings as APISettings, api_settings, get_settings

__all__ = ["APISettings", "api_settings", "get_settings"]
