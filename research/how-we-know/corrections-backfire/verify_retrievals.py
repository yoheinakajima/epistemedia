"""Verify retrieved EM-0019 artifacts against the public excerpt packets."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

from build_candidate import CANDIDATE_PATH

ARTIFACTS = {
    "edition-skurnik-2005": {
        "filename": "epistemedia-skurnik-jcr2005.pdf",
        "format": "pdf",
    },
    "edition-handbook-2011": {
        "filename": "epistemedia-handbook-page.html",
        "format": "html",
    },
    "edition-ecker-2020": {
        "filename": "epistemedia-pmc7447737.xml",
        "format": "xml",
    },
    "edition-prike-2023": {
        "filename": "epistemedia-pmc10317933.xml",
        "format": "xml",
    },
    "edition-ecker-2023": {
        "filename": "epistemedia-pmc10096191.xml",
        "format": "xml",
    },
}


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def normalize(value: str) -> str:
    value = value.replace("\u00a0", " ")
    value = re.sub(r"(?<=\w)-\s+(?=\w)", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return re.sub(r"\s+([,.;:!?)\]])", r"\1", value)


def extract_text(path: Path, artifact_format: str) -> str:
    if artifact_format == "pdf":
        completed = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            check=True,
            capture_output=True,
            text=True,
        )
        return normalize(completed.stdout)
    if artifact_format == "html":
        parser = TextExtractor()
        parser.feed(path.read_text(encoding="utf-8"))
        return normalize(" ".join(parser.parts))
    root = ET.parse(path).getroot()
    return normalize(" ".join(root.itertext()))


def verify(artifact_dir: Path) -> dict[str, object]:
    candidate = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
    editions = {record["key"]: record for record in candidate["editions"]}
    verified: list[dict[str, object]] = []
    for edition_key, spec in ARTIFACTS.items():
        edition = editions[edition_key]
        artifact = edition["content"]["artifact"]
        path = artifact_dir / str(spec["filename"])
        payload = path.read_bytes()
        observed_digest = hashlib.sha256(payload).hexdigest()
        if observed_digest != artifact["sha256"]:
            raise SystemExit(
                f"{path}: digest {observed_digest} does not match {artifact['sha256']}"
            )
        if len(payload) != artifact["bytes"]:
            raise SystemExit(
                f"{path}: byte length {len(payload)} does not match {artifact['bytes']}"
            )
        full_text = extract_text(path, str(spec["format"]))
        excerpts = edition["content"]["excerpts"]
        for index, item in enumerate(excerpts):
            exact = normalize(item["text"])
            if exact not in full_text:
                raise SystemExit(
                    f"{path}: excerpt {index} not found after deterministic normalization"
                )
        verified.append(
            {
                "edition_key": edition_key,
                "sha256": observed_digest,
                "bytes": len(payload),
                "excerpts_verified": len(excerpts),
            }
        )
    return {
        "verified": verified,
        "not_machine_verified": [
            {
                "edition_key": "edition-schwarz-2016",
                "reason": (
                    "Publisher HTML was readable through web read-back but rejected automated "
                    "byte capture with HTTP 403; independent human or separately rooted agent "
                    "span review remains required."
                ),
            }
        ],
        "independent_review_complete": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, default=Path("/tmp"))
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    result = verify(args.artifact_dir)
    print(json.dumps(result, indent=2))
    if args.require_complete and not result["independent_review_complete"]:
        raise SystemExit("independent source-span review is incomplete")


if __name__ == "__main__":
    main()
