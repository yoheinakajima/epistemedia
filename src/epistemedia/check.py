"""One local and CI validation contract for accepted repository candidates."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "generated" / "public"


def source_state() -> bytes:
    return subprocess.check_output(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT
    )


def tree_inventory(root: Path) -> list[tuple[str, str]]:
    return [
        (path.relative_to(root).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest())
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]


def run(label: str, *args: str, quiet: bool = False) -> None:
    print(f"==> {label}", flush=True)
    subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL if quiet else None,
    )


def main() -> int:
    before = source_state()
    with tempfile.TemporaryDirectory(prefix="epistemedia-check-") as temporary:
        second = Path(temporary) / "public"
        run("validate accepted inputs", "-m", "epistemedia", "validate")
        run(
            "build public projection",
            "-m",
            "epistemedia",
            "build",
            "--output",
            str(PUBLIC),
            quiet=True,
        )
        run("run tests", "-m", "pytest", "-q")
        run("audit public projection", "-m", "epistemedia", "audit", "--public", str(PUBLIC))
        run(
            "build independent comparison projection",
            "-m",
            "epistemedia",
            "build",
            "--output",
            str(second),
            quiet=True,
        )
        if tree_inventory(PUBLIC) != tree_inventory(second):
            raise SystemExit("generated public projection differs across independent builds")
        print("==> deterministic public projection verified", flush=True)

    after = source_state()
    if before != after:
        print("Repository state changed while make check was running.", file=sys.stderr)
        print("Before:\n" + before.decode(errors="replace"), file=sys.stderr)
        print("After:\n" + after.decode(errors="replace"), file=sys.stderr)
        return 1
    print("==> source-tree state unchanged", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
