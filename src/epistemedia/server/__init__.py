"""Lazy compatibility package for the ASGI gateway.

A package directory intentionally takes precedence over the legacy sibling `server.py` module.
It sets a non-authoritative fallback root before loading that implementation so importing the
remote CLI never requires the caller to be inside a repository. Local realm commands still
resolve and require an explicit repository through the CLI.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

_file = Path(__file__).resolve().parent.parent / "server.py"
# In an editable checkout this is the repository root. In an installed wheel it is merely a
# harmless package fallback; remote commands do not read it, and local commands resolve a root.
os.environ.setdefault("EPISTEMEDIA_ROOT", str(Path(__file__).resolve().parents[3]))
_spec = importlib.util.spec_from_file_location("epistemedia._server_implementation", _file)
if _spec is None or _spec.loader is None:  # pragma: no cover
    raise ImportError(f"Unable to load Epistemedia gateway from {_file}")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

Gateway = _module.Gateway
Request = _module.Request
tool_definitions = _module.tool_definitions
app = Gateway()

__all__ = ["Gateway", "Request", "app", "tool_definitions"]
