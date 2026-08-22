from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_cli_import_is_independent_of_checkout_sitecustomize(tmp_path: Path) -> None:
    source = ROOT / "src"
    script = (
        "import sys; "
        f"sys.path.insert(0, {str(source)!r}); "
        "from epistemedia.cli import main; "
        "main(['--version'])"
    )
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-I", "-c", script],
        cwd=tmp_path,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == "epistemedia 0.2.0"
    assert result.stderr == ""
