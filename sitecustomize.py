"""Local development bootstrap; see `src/sitecustomize.py`."""

import sys
import types

sys.modules.setdefault(
    "epistemedia._server_implementation",
    types.ModuleType("epistemedia._server_implementation"),
)
