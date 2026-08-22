from __future__ import annotations

import hashlib
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APACHE_2_LICENSE_SHA256 = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"


def test_license_is_canonical_apache_2() -> None:
    assert hashlib.sha256((ROOT / "LICENSE").read_bytes()).hexdigest() == APACHE_2_LICENSE_SHA256


def test_package_and_readme_license_metadata_agree() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    assert project["license"] == "Apache-2.0"
    assert project["license-files"] == ["LICENSE"]
    assert not any(item.startswith("License ::") for item in project["classifiers"])

    readme = (ROOT / "README.md").read_text()
    assert "Code is licensed under the [Apache License 2.0](LICENSE)." in readme
