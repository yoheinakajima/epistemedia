"""Compatibility bootstrap for editable Epistemedia installations.

The manually loaded gateway implementation uses a stable private module name. Registering that
name before package import gives dataclasses and annotation resolution a module namespace while
keeping remote CLI commands independent from the current working directory.
"""

import sys
import types

sys.modules.setdefault(
    "epistemedia._server_implementation",
    types.ModuleType("epistemedia._server_implementation"),
)
