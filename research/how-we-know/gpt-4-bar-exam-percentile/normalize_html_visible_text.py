"""Deterministically extract disclosure-safe visible text from captured HTML bytes."""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

EXCLUDED_ELEMENTS = frozenset({"script", "style", "template", "noscript", "svg"})


class VisibleTextExtractor(HTMLParser):
    """Collect visible text under one exact HTML ``id`` attribute."""

    def __init__(self, root_id: str) -> None:
        super().__init__(convert_charrefs=True)
        self.root_id = root_id
        self.parts: list[str] = []
        self.root_tag: str | None = None
        self.root_nesting = 0
        self.root_matches = 0
        self.excluded_depth = 0

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = dict(attrs)
        if attributes.get("id") == self.root_id:
            self.root_matches += 1
            if self.root_tag is None:
                self.root_tag = tag.lower()
                self.root_nesting = 1
        elif self.root_tag is not None and tag.lower() == self.root_tag:
            self.root_nesting += 1
        if self.root_tag is not None and tag.lower() in EXCLUDED_ELEMENTS:
            self.excluded_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self.root_tag is not None and tag.lower() in EXCLUDED_ELEMENTS:
            if not self.excluded_depth:
                raise ValueError(f"unbalanced excluded element: {tag}")
            self.excluded_depth -= 1
        if self.root_tag is not None and tag.lower() == self.root_tag:
            self.root_nesting -= 1
            if not self.root_nesting:
                self.root_tag = None

    def handle_startendtag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        if self.root_tag is not None and not self.excluded_depth:
            self.parts.append(data)


def normalize_html_visible_text(payload: bytes, *, root_id: str) -> bytes:
    """Return UTF-8 text with excluded elements removed and whitespace collapsed."""
    text = payload.decode("utf-8")
    parser = VisibleTextExtractor(root_id)
    parser.feed(text)
    parser.close()
    if parser.root_tag is not None:
        raise ValueError(f"unclosed selected element: {parser.root_tag}")
    if parser.root_matches != 1:
        raise ValueError(
            f"expected one element with id={root_id!r}; found {parser.root_matches}"
        )
    normalized = re.sub(r"\s+", " ", " ".join(parser.parts)).strip()
    return normalized.encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collapse-whitespace", action="store_true", required=True)
    parser.add_argument("--root-id", required=True)
    parser.add_argument("input", type=Path, nargs="?")
    args = parser.parse_args()
    payload = args.input.read_bytes() if args.input else sys.stdin.buffer.read()
    sys.stdout.buffer.write(normalize_html_visible_text(payload, root_id=args.root_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
