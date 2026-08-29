"""Stable package facade for the Epistemedia core.

The sibling `core.py` remains the compact reference implementation. This facade loads it under a
private module identity, re-exports its API, and replaces the deliberately conservative bootstrap
audit with a precise scanner that does not flag the audit source code for mentioning indicators.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

_file = Path(__file__).resolve().parent.parent / "core.py"
_name = "epistemedia._core_implementation"
_spec = importlib.util.spec_from_file_location(_name, _file)
if _spec is None or _spec.loader is None:  # pragma: no cover
    raise ImportError(f"Unable to load Epistemedia core from {_file}")
_module = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _module
_spec.loader.exec_module(_module)

for _key, _value in vars(_module).items():
    if not _key.startswith("_"):
        globals()[_key] = _value


def audit_public(root: Path, public: Path) -> list[str]:
    """Audit exact identities, required interfaces, and high-specificity disclosure indicators."""

    findings: list[str] = []
    catalog = PublicCatalog.build(root)
    catalog_path = public / "catalog.json"
    manifest_path = public / "manifest.json"
    if not catalog_path.exists():
        return ["missing generated catalog.json"]
    if not manifest_path.exists():
        return ["missing generated manifest.json"]
    try:
        generated = json.loads(catalog_path.read_text())
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid public catalog or manifest: {exc}"]
    if generated.get("catalog_id") != catalog.catalog_id:
        findings.append("generated catalog ID differs from current accepted inputs")
    if generated.get("frontier") != catalog.frontier:
        findings.append("generated frontier differs from current accepted inputs")
    if manifest.get("catalog_id") != catalog.catalog_id:
        findings.append("release manifest references another catalog")
    required = [
        public / "index.html",
        public / "llms.txt",
        public / "openapi.json",
        public / ".well-known" / "epistemedia.json",
        public / "mcp" / "server.json",
        public / "about" / "index.html",
        public / "about" / "index.md",
        public / "about" / "index.json",
        public / "about" / "reader-check" / "index.html",
        public / "about" / "reader-check" / "index.md",
        public / "about" / "reader-check" / "index.json",
    ]
    for path in required:
        if not path.exists():
            findings.append(f"missing public interface: {path.relative_to(public)}")

    indicators = [
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        re.compile(r"\bghp_[A-Za-z0-9]{30,}\b"),
        re.compile(r"\bsk-[A-Za-z0-9]{30,}\b"),
        re.compile(r"/Users/[A-Za-z0-9._-]+/(?:[^\s<>'\"]+/){1,}"),
        re.compile(r"C:\\\\Users\\\\[A-Za-z0-9._-]+\\\\"),
    ]
    for path in public.rglob("*"):
        if not path.is_file() or path.stat().st_size > 5_000_000:
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for pattern in indicators:
            if pattern.search(text):
                findings.append(
                    f"public disclosure indicator in {path.relative_to(public)}: {pattern.pattern}"
                )
    return sorted(set(findings))


__all__ = sorted(
    name
    for name in globals()
    if not name.startswith("_") and name not in {"Any", "Path", "json", "re", "sys"}
)
