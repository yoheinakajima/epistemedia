from __future__ import annotations

import asyncio
import base64
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from epistemedia.cli import main
from epistemedia.core import (
    PROTOCOL_VERSION,
    PublicCatalog,
    audit_public,
    build_public,
    stable_id,
    topic_projection,
    validate_repository,
)
from epistemedia.server import Gateway, Request, tool_definitions

ROOT = Path(__file__).resolve().parents[1]
SLUG = "corrections-and-familiarity-backfire"
CASE_003 = "gpt-4-bar-exam-percentile"
CASE_004 = "mehrabian-7-38-55"


class PageStructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.headings: list[int] = []
        self.ids: list[str] = []
        self.nav_labels: list[str] = []
        self.skip_targets: list[str] = []
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if len(tag) == 2 and tag[0] == "h" and tag[1].isdigit():
            self.headings.append(int(tag[1]))
        if values.get("id"):
            self.ids.append(str(values["id"]))
        if tag == "nav" and values.get("aria-label"):
            self.nav_labels.append(str(values["aria-label"]))
        classes = (values.get("class") or "").split()
        if tag == "a" and "skip-link" in classes and values.get("href"):
            self.skip_targets.append(str(values["href"]))
        if tag == "a" and values.get("href"):
            self.hrefs.append(str(values["href"]))


def test_repo_receipt_command_does_not_overwrite_cli_dispatch(tmp_path: Path) -> None:
    result = main(
        [
            "--root",
            str(tmp_path),
            "repo",
            "receipt",
            "EM-0008",
            "--run",
            "local-test",
            "--command",
            "make check",
        ]
    )
    assert result == 0
    receipts = list((tmp_path / "runs" / "proposals").glob("*.json"))
    assert len(receipts) == 1
    receipt = json.loads(receipts[0].read_text())
    assert receipt["kind"] == "run-receipt"
    assert receipt["task_id"] == "EM-0008"
    assert receipt["run_id"] == "local-test"
    assert receipt["command"] == "make check"


def test_repository_is_valid() -> None:
    assert validate_repository(ROOT) == []


def test_catalog_is_deterministic() -> None:
    first = PublicCatalog.build(ROOT)
    second = PublicCatalog.build(ROOT)
    assert first.catalog_id == second.catalog_id
    assert first.frontier == second.frontier
    assert [obj.id for obj in first.objects] == [obj.id for obj in second.objects]


def test_public_timestamp_is_the_accepted_commit_time() -> None:
    epoch = int(
        subprocess.check_output(
            ["git", "show", "-s", "--format=%ct", "HEAD"], cwd=ROOT, text=True
        ).strip()
    )
    expected = (
        datetime.fromtimestamp(epoch, timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    assert PublicCatalog.build(ROOT).generated_at == expected


def test_deployment_url_does_not_change_catalog_identity(tmp_path: Path) -> None:
    a = build_public(ROOT, tmp_path / "a", base_url="https://epistemedia.org")
    b = build_public(ROOT, tmp_path / "b", base_url="https://mirror.example")
    assert a["catalog_id"] == b["catalog_id"]
    assert a["frontier"] == b["frontier"]
    # A release manifest includes rendered files, so its own ID may change with links.
    assert (tmp_path / "a" / "catalog.json").read_text() == (
        tmp_path / "b" / "catalog.json"
    ).read_text()


def test_public_build_emits_every_interface(tmp_path: Path) -> None:
    public = tmp_path / "public"
    manifest = build_public(ROOT, public)
    expected = [
        "index.html",
        "index.md",
        "register.css",
        "llms.txt",
        "llms-full.txt",
        "catalog.json",
        "search.json",
        "status.json",
        "manifest.json",
        "openapi.json",
        ".well-known/epistemedia.json",
        "mcp/server.json",
        "about/index.html",
        "about/index.md",
        "about/index.json",
        "about/reader-check/index.html",
        "about/reader-check/index.md",
        "about/reader-check/index.json",
        "docs/llms.txt",
        "how-we-know/index.html",
        "how-we-know/corrections-and-familiarity-backfire/index.html",
        "how-we-know/corrections-and-familiarity-backfire/index.md",
        "how-we-know/corrections-and-familiarity-backfire/index.json",
        "how-we-know/corrections-and-familiarity-backfire/encyclopedia/index.html",
        "how-we-know/corrections-and-familiarity-backfire/skeptical/index.html",
        "how-we-know/corrections-and-familiarity-backfire/review/index.html",
        "how-we-know/corrections-and-familiarity-backfire/review/index.md",
        "how-we-know/corrections-and-familiarity-backfire/review/index.json",
        "how-we-know/corrections-and-familiarity-backfire/share-card.svg",
        "how-we-know/corrections-and-familiarity-backfire/encyclopedia/share-card.svg",
        "how-we-know/corrections-and-familiarity-backfire/skeptical/share-card.svg",
        "how-we-know/agent-citation-lineage/index.html",
        "how-we-know/agent-citation-lineage/index.md",
        "how-we-know/agent-citation-lineage/index.json",
        "how-we-know/agent-citation-lineage/encyclopedia/index.html",
        "how-we-know/agent-citation-lineage/skeptical/index.html",
        "how-we-know/agent-citation-lineage/review/index.html",
        "how-we-know/agent-citation-lineage/review/index.md",
        "how-we-know/agent-citation-lineage/review/index.json",
        "how-we-know/agent-citation-lineage/share-card.svg",
        "how-we-know/agent-citation-lineage/encyclopedia/share-card.svg",
        "how-we-know/agent-citation-lineage/skeptical/share-card.svg",
    ]
    for case_slug in (CASE_003, CASE_004):
        expected.extend(
            [
                f"how-we-know/{case_slug}/index.html",
                f"how-we-know/{case_slug}/index.md",
                f"how-we-know/{case_slug}/index.json",
                f"how-we-know/{case_slug}/encyclopedia/index.html",
                f"how-we-know/{case_slug}/skeptical/index.html",
                f"how-we-know/{case_slug}/review/index.html",
                f"how-we-know/{case_slug}/review/index.md",
                f"how-we-know/{case_slug}/review/index.json",
                f"how-we-know/{case_slug}/share-card.svg",
                f"how-we-know/{case_slug}/encyclopedia/share-card.svg",
                f"how-we-know/{case_slug}/skeptical/share-card.svg",
            ]
        )
    assert all((public / path).exists() for path in expected)
    assert manifest["file_count"] > 10
    assert audit_public(ROOT, public) == []

    discovery = json.loads((public / ".well-known" / "epistemedia.json").read_text())
    assert discovery["human"] == "https://epistemedia.org"
    assert discovery["api"] == "https://api.epistemedia.org/v1"
    assert discovery["openapi"] == "https://epistemedia.org/openapi.json"
    assert discovery["mcp"] == "https://mcp.epistemedia.org/mcp"
    assert discovery["featured_dossier"]["human"] == (
        "https://epistemedia.org/how-we-know/corrections-and-familiarity-backfire/"
    )
    assert [item["number"] for item in discovery["dossiers"]] == [
        "001",
        "002",
        "003",
        "004",
    ]

    llms = (public / "llms.txt").read_text()
    assert "Static OpenAPI contract — hosted API not live" in llms
    assert "https://epistemedia.org/openapi.json" in llms
    assert "Static MCP descriptor — remote MCP not live" in llms
    assert "https://epistemedia.org/mcp/server.json" in llms
    assert "https://api.epistemedia.org/openapi.json" not in llms
    assert "Case 002 evidence dossier" in llms
    assert "Case 003 evidence dossier" in llms
    assert "Case 004 evidence dossier" in llms

    obj = next(obj for obj in PublicCatalog.build(ROOT).objects if obj.kind == "documentation")
    file_key = quote(obj.id, safe="")
    route_key = quote(file_key, safe="")
    docs_html = (public / "docs" / "index.html").read_text()
    docs_llms = (public / "docs" / "llms.txt").read_text()
    assert f"/objects/{route_key}/" in docs_html
    assert f"/objects/{route_key}.md" in docs_llms
    assert unquote(route_key) == file_key
    assert (public / "objects" / file_key / "index.html").exists()
    assert (public / "objects" / f"{file_key}.md").exists()
    assert '<link rel="canonical" href="https://epistemedia.org/docs/">' in docs_html

    object_html = (public / "objects" / file_key / "index.html").read_text()
    expected_canonical = f"https://epistemedia.org/objects/{route_key}/"
    assert f'<link rel="canonical" href="{expected_canonical}">' in object_html
    assert object_html.count("<h1>") == 1
    assert 'id="source-content-title"' in object_html
    assert "<h3>" in object_html
    assert obj.id in object_html
    assert manifest["catalog_id"] in object_html

    home_html = (public / "index.html").read_text()
    design_css = (public / "register.css").read_text()
    assert "overflow-wrap:anywhere;word-break:break-word" in design_css
    assert "pre code{padding:0;overflow-wrap:normal;word-break:normal}" in design_css
    assert "minmax(min(100%,245px),1fr)" in design_css
    assert '<link rel="stylesheet" href="https://epistemedia.org/register.css">' in home_html
    assert "<style>" not in home_html
    assert "Does repeating misinformation" in home_html
    assert "How We Know" in home_html
    assert "Case 001" in home_html
    assert "evidence-tally" in home_html
    assert "Ten source assertions sound like support" in home_html
    assert "Share the scoreboard" in home_html
    assert 'property="og:image"' in home_html
    assert "86 exact spans" in home_html
    assert home_html.count('class="purpose-note"') == 1
    assert "Information tells you what was said" in home_html
    assert "These counts follow evidence lineage, not paper titles" in home_html
    assert 'aria-label="How to read Case 001"' in home_html
    assert f'href="https://epistemedia.org/how-we-know/{SLUG}/skeptical/"' in home_html
    assert f'href="https://epistemedia.org/how-we-know/{SLUG}/#evidence-record-title"' in home_html
    assert home_html.index("Does repeating misinformation") < home_html.index(
        "Explore how the record is built"
    )
    assert (
        home_html.index("Does repeating misinformation")
        < home_html.index("Information tells you what was said")
        < home_html.index("Explore how the record is built")
    )
    assert "projection-receipt" in home_html
    assert manifest["catalog_id"] in home_html
    assert ">Substrate</a>" in home_html
    assert "Four cases · four failure modes" in home_html
    assert "False independence" in home_html
    assert "Run a claim through the research kit" in home_html
    assert "Case 003" in home_html
    assert "Case 004" in home_html
    assert "View all four cases" in home_html

    home_markdown = (public / "index.md").read_text()
    assert "## Why this exists" in home_markdown
    assert "The counts follow evidence lineage, not paper titles." in home_markdown
    assert f"[Skeptical](https://epistemedia.org/how-we-know/{SLUG}/skeptical/)" in (home_markdown)

    how_we_know_html = (public / "how-we-know" / "index.html").read_text()
    assert "Case 001" in how_we_know_html
    assert "Case 002" in how_we_know_html
    assert "Case 003" in how_we_know_html
    assert "Case 004" in how_we_know_html
    assert "4 accepted cases" in how_we_know_html
    assert "No future case is advertised as available" in how_we_know_html
    assert "home-case" not in how_we_know_html
    assert how_we_know_html.count("<h1>") == 1

    explore_html = (public / "explore" / "index.html").read_text()
    explore_markdown = (public / "explore" / "index.md").read_text()
    assert "<h1>Substrate</h1>" in explore_html
    assert explore_markdown.startswith("# Substrate\n")

    share_card = (
        public / "how-we-know" / "corrections-and-familiarity-backfire" / "share-card.svg"
    ).read_text()
    assert share_card.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert "CASE 001" in share_card
    assert manifest["catalog_id"] in share_card

    topic = PublicCatalog.build(ROOT).topics[0]
    topic_html = (public / "topics" / topic.slug / "index.html").read_text()
    topic_markdown = (public / "topics" / topic.slug / "index.md").read_text()
    assert topic_html.count("<h1>") == 1
    assert f"<h1>{topic.title}</h1>" in topic_html
    assert topic_html.count(topic.description) == 1
    assert "Experimental lens manifests (shared inventory)" in topic_html
    assert "not yet materially different editorial products" in topic_html
    assert topic_markdown.startswith(f"# {topic.title}\n")
    assert "## Projection manifest" in topic_markdown
    assert "projection-receipt" in topic_html
    assert (
        f'<link rel="canonical" href="https://epistemedia.org/topics/{topic.slug}/">' in topic_html
    )

    experimental_html = (public / "topics" / topic.slug / "skeptical" / "index.html").read_text()
    assert experimental_html.count("<h1>") == 1
    assert "Experimental lens manifest." in experimental_html
    assert "not a differentiated editorial result" in experimental_html

    status_markdown = (public / "status" / "index.md").read_text()
    status_html = (public / "status" / "index.html").read_text()
    assert "Canonical human site" in status_markdown
    assert status_markdown.count("not verified live") == 3
    assert "4 independently reviewed How We Know dossiers" in status_markdown
    assert "Verified live · HTTPS" in status_html
    assert status_html.count("Reserved · unverified") == 3


def test_homepage_count_language_reconciles_distinct_objects_and_memberships(
    tmp_path: Path,
) -> None:
    public = tmp_path / "public"
    build_public(ROOT, public)
    catalog = PublicCatalog.build(ROOT)
    home_html = (public / "index.html").read_text()
    home_markdown = (public / "index.md").read_text()
    membership_counts = [len(catalog.selected_objects(topic)) for topic in catalog.topics]
    membership_total = sum(membership_counts)

    assert catalog.topic_membership_count() == membership_total
    assert membership_total > len(catalog.objects)
    summary = (
        f"{len(catalog.objects)} distinct public objects · {membership_total} "
        f"topic memberships across {len(catalog.topics)} topics"
    )
    assert summary in home_html
    assert summary + "." in home_markdown
    for count in membership_counts:
        assert f"{count} objects in this topic" in home_html
    assert f"{len(catalog.topics)} topics · {len(catalog.objects)} public objects" not in (
        home_html
    )


def test_public_design_system_is_shared_accessible_and_structured(tmp_path: Path) -> None:
    public = tmp_path / "public"
    build_public(ROOT, public)
    catalog = PublicCatalog.build(ROOT)
    home_html = (public / "index.html").read_text()
    design_css = (public / "register.css").read_text()

    for token in (
        "--paper:",
        "--ink:",
        "--deep:",
        "--accent:",
        "--open:",
        "--stop:",
        "--sans:",
        "--mono:",
        "--space-1:",
        "--rule:",
    ):
        assert token in design_css
    assert "a:focus-visible,summary:focus-visible" in design_css
    assert "@media(max-width:600px)" in design_css
    assert "word-break:break-word" in design_css
    assert "brand-mark" in home_html
    assert "docket-card" in home_html
    assert "Reproducible projection" in home_html
    assert "h1{font-size:clamp(30px,4vw,44px)" in design_css
    assert "font-size:clamp(28px,9vw,38px)" in design_css
    assert "text-transform:uppercase" not in design_css
    assert "#000" not in design_css
    assert "Epistemedia Register adapter" in design_css
    assert "MIT License" in design_css
    assert "5.25rem" not in design_css

    pages = sorted(public.rglob("index.html"))
    assert pages
    for page in pages:
        page_html = page.read_text()
        parser = PageStructureParser()
        parser.feed(page_html)
        relative = page.relative_to(public)
        assert parser.headings, relative
        assert parser.headings[0] == 1, relative
        assert parser.headings.count(1) == 1, relative
        assert len(parser.ids) == len(set(parser.ids)), relative
        assert "content" in parser.ids, relative
        assert parser.nav_labels[0] == "Primary", relative
        assert parser.nav_labels.count("Primary") == 1, relative
        base_navigation = ["Primary", "Utility", "Utility menu"]
        if relative == Path("index.html"):
            assert parser.nav_labels == [
                *base_navigation,
                "Evidence policy",
                "How to read Case 001",
            ], relative
        elif "Evidence policy" in parser.nav_labels:
            assert parser.nav_labels == [*base_navigation, "Evidence policy"], relative
            assert str(relative).startswith("how-we-know/"), relative
        else:
            assert parser.nav_labels == base_navigation, relative
        assert parser.skip_targets == ["#content"], relative
        assert '<link rel="stylesheet" href="https://epistemedia.org/register.css">' in page_html
        assert "<style>" not in page_html
        assert "<script" not in page_html
        assert "projection-receipt" in page_html, relative
        assert catalog.catalog_id in page_html, relative
        assert catalog.frontier in page_html, relative
        assert catalog.policies["epistemic"] in page_html, relative
        assert catalog.policies["disclosure"] in page_html, relative


def test_topic_lenses_share_source_frontier() -> None:
    catalog = PublicCatalog.build(ROOT)
    topic = catalog.topics[0]
    encyclopedia = topic_projection(catalog, topic, "encyclopedia", "https://a.example")
    skeptical = topic_projection(catalog, topic, "skeptical", "https://b.example")
    assert encyclopedia["catalog_id"] == skeptical["catalog_id"]
    assert encyclopedia["frontier"] == skeptical["frontier"]
    assert [o["id"] for o in encyclopedia["objects"]] == [o["id"] for o in skeptical["objects"]]
    assert encyclopedia["projection_id"] != skeptical["projection_id"]


def test_topic_relations_are_exact_catalog_navigation_only(tmp_path: Path) -> None:
    root = tmp_path / "realm"
    docs = root / "docs"
    catalog_source = root / "catalog"
    private = root / "private"
    docs.mkdir(parents=True)
    catalog_source.mkdir()
    private.mkdir()
    (root / "README.md").write_text(
        """# Root

A readable public root.

[Child](docs/child.md)
[Duplicate child](docs/child.md#detail)
[External](https://example.com/docs/child.md)
[Fragment](#local)
[Root absolute](/docs/child.md)
[Missing](docs/missing.md)
[Private](private/secret.md)
[Escaping traversal](../../outside.md)
[Encoded escape](%2e%2e/%2e%2e/outside.md)
`[Inline code](docs/code.md)`

```markdown
[Fenced code](docs/fenced.md)
```

![Image](docs/image.md)
"""
    )
    (docs / "child.md").write_text(
        """# Child

Readable child summary.

[Root](../README.md)
[Local sibling](nested.md)
[Unsafe escape](../../outside.md)
"""
    )
    (docs / "nested.md").write_text("# Nested\n\nNested public object.\n")
    (docs / "code.md").write_text("# Code\n\nMust not be inferred from inline code.\n")
    (docs / "fenced.md").write_text("# Fenced\n\nMust not be inferred from a fence.\n")
    (docs / "image.md").write_text("# Image\n\nMust not be inferred from image syntax.\n")
    (private / "secret.md").write_text("not public")
    (catalog_source / "topics.json").write_text(
        json.dumps(
            {
                "topics": [
                    {
                        "slug": "fixture",
                        "title": "Fixture",
                        "description": "Fixture topic.",
                        "include": ["README.md", "docs/**"],
                    },
                    {
                        "slug": "documentation",
                        "title": "Documentation",
                        "description": "Documentation topic.",
                        "include": ["docs/**"],
                    },
                ]
            }
        )
    )

    catalog = PublicCatalog.build(root)
    topic = catalog.topic_map()["fixture"]
    projection = topic_projection(catalog, topic, "encyclopedia", "https://example.test")
    records = {obj["path"]: obj for obj in projection["objects"]}

    assert [item["path"] for item in records["README.md"]["references_in_source"]] == [
        "docs/child.md"
    ]
    assert [item["path"] for item in records["docs/child.md"]["references_in_source"]] == [
        "README.md",
        "docs/nested.md",
    ]
    assert [item["slug"] for item in records["docs/child.md"]["also_filed_under"]] == [
        "documentation"
    ]
    assert records["README.md"]["also_filed_under"] == []
    serialized = json.dumps(projection)
    for rejected in (
        "docs/missing.md",
        "private/secret.md",
        "outside.md",
    ):
        assert rejected not in serialized
    assert "similar" not in serialized.lower()
    assert "support" not in serialized.lower()
    assert "independ" not in serialized.lower()


def test_topic_human_surface_and_projection_parity(tmp_path: Path, capsys: object) -> None:
    public = tmp_path / "public"
    catalog = PublicCatalog.build(ROOT)
    topic = catalog.topic_map()["epistemedia"]
    projection = topic_projection(
        catalog,
        topic,
        "encyclopedia",
        "https://epistemedia.org",
    )
    build_public(ROOT, public)
    topic_root = public / "topics" / topic.slug
    topic_html = (topic_root / "index.html").read_text()
    topic_markdown = (topic_root / "index.md").read_text()
    static_json = json.loads((topic_root / "index.json").read_text())

    assert static_json == projection
    assert topic_html.count('class="topic-object-card row"') == projection["object_count"]
    assert topic_html.count('class="object-kind id"') == projection["object_count"]
    assert topic_html.count('class="topic-group register"') == len(projection["kind_counts"])
    assert topic_html.count("<summary>Technical identity</summary>") == projection["object_count"]
    assert '<details class="object-identity" open' not in topic_html
    design_css = (public / "register.css").read_text()
    assert ".object-identity dd" in design_css
    assert "font:10.5px/1.45 var(--mono)" in design_css
    assert "Also filed under" in topic_html
    assert "References in source" in topic_html
    assert "related objects" not in topic_html.lower()
    assert "similar objects" not in topic_html.lower()
    relation_labels = set(re.findall(r'class="relation-label">([^<]+)</span>', topic_html))
    assert relation_labels == {"Also filed under", "References in source"}
    assert "/topics/epistemedia/architecture.md" not in topic_html
    assert "## Objects" in topic_markdown
    assert "**Also filed under:**" in topic_markdown
    assert "**References in source:**" in topic_markdown
    assert "<summary>Technical identity</summary>" in topic_markdown

    parser = PageStructureParser()
    parser.feed(topic_html)
    for href in parser.hrefs:
        parsed = urlsplit(href)
        if parsed.netloc and parsed.netloc != "epistemedia.org":
            continue
        if not parsed.path:
            continue
        relative = unquote(parsed.path).lstrip("/") or "index.html"
        if relative.endswith("/"):
            relative += "index.html"
        assert (public / relative).is_file(), href

    first_object = projection["objects"][0]
    assert first_object["links"]["html"] in topic_html
    assert first_object["links"]["markdown"] in topic_html
    assert first_object["links"]["accepted_source"] in topic_html
    object_file_key = quote(first_object["id"], safe="")
    object_html = (public / "objects" / object_file_key / "index.html").read_text()
    object_hero = object_html.split("</section>", 1)[0]
    assert "](" not in object_hero
    assert "font:11px/1.5 var(--mono)" in design_css
    assert "Also filed under" in object_html
    assert f"https://epistemedia.org/topics/{topic.slug}/" in object_html

    skeptical = topic_projection(
        catalog,
        topic,
        "skeptical",
        "https://epistemedia.org",
    )
    assert static_json["objects"] == skeptical["objects"]
    assert static_json["relation_counts"] == skeptical["relation_counts"]
    assert json.loads((topic_root / "skeptical" / "index.json").read_text()) == skeptical
    skeptical_markdown = (topic_root / "skeptical" / "index.md").read_text()
    assert "**Also filed under:**" in skeptical_markdown
    assert "**References in source:**" in skeptical_markdown

    gateway = Gateway(ROOT)
    status, _, rest = gateway.handle_api(Request("GET", f"/v1/topics/{topic.slug}", {}, {}, b""))
    assert status == 200
    assert rest["data"] == projection
    assert gateway.read_resource(f"epistemedia://topic/{topic.slug}") == projection
    assert (
        gateway.call_tool("get_topic", {"slug": topic.slug, "lens": "encyclopedia"}) == projection
    )

    assert main(["--root", str(ROOT), "project", topic.slug, "--lens", "encyclopedia"]) == 0
    cli_projection = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert cli_projection == projection


def test_public_status_copy_distinguishes_live_and_target_surfaces() -> None:
    readme = (ROOT / "README.md").read_text()
    launch_docs = (ROOT / "docs" / "launch.md").read_text()
    api_docs = (ROOT / "docs" / "api-mcp-cli.md").read_text()
    assert "canonical static site live at <https://epistemedia.org/>" in readme
    assert "sharing redirect and hosted API/MCP runtime" in readme
    assert "four independently reviewed, application-level dossiers" in readme
    assert "does not yet replay the normative event model" in readme
    assert "Case 001 remains the homepage lead" in readme
    assert "does **not** yet instantiate that claim/evidence graph" not in readme
    assert "The first public realm dogfoods Epistemedia itself" not in readme
    assert "Target architecture" in readme
    assert "Public hosting at `epistemedia.org`" not in readme
    assert "bootstrap topic projections from accepted dossier policy views" in launch_docs
    assert "Case 001 remains the homepage lead" in launch_docs
    assert "it remains in development" not in launch_docs
    assert api_docs.count("No hosted runtime at that hostname has passed") == 2


def test_object_ids_are_content_and_path_addressed() -> None:
    catalog = PublicCatalog.build(ROOT)
    obj = catalog.objects[0]
    assert obj.id.startswith("em:")
    assert len(obj.content_digest) == 64
    assert obj.id == stable_id(
        obj.kind,
        {"path": obj.path, "content_digest": obj.content_digest, "media_type": obj.media_type},
    )


def test_search_is_stable() -> None:
    catalog = PublicCatalog.build(ROOT)
    assert catalog.search("Epistemedia") == catalog.search("Epistemedia")


def mcp_params(**values: object) -> dict[str, object]:
    return {
        **values,
        "_meta": {
            "io.modelcontextprotocol/protocolVersion": PROTOCOL_VERSION,
            "io.modelcontextprotocol/clientInfo": {
                "name": "epistemedia-tests",
                "version": "1",
            },
            "io.modelcontextprotocol/clientCapabilities": {},
        },
    }


def mcp_request(
    method: str,
    params: dict[str, object] | None = None,
    *,
    request_id: object = 1,
    origin: str | None = "https://epistemedia.org",
) -> Request:
    body_params = params or mcp_params()
    headers = {
        "accept": "application/json, text/event-stream",
        "content-type": "application/json; charset=utf-8",
        "mcp-protocol-version": str(
            body_params.get("_meta", {}).get("io.modelcontextprotocol/protocolVersion", "")
        ),
        "mcp-method": method,
    }
    if origin is not None:
        headers["origin"] = origin
    if method in {"tools/call", "prompts/get"} and "name" in body_params:
        headers["mcp-name"] = str(body_params["name"])
    if method == "resources/read" and "uri" in body_params:
        headers["mcp-name"] = str(body_params["uri"])
    message = {"jsonrpc": "2.0", "method": method, "params": body_params}
    if request_id is not None:
        message["id"] = request_id
    return Request("POST", "/mcp", {}, headers, json.dumps(message).encode())


def test_api_and_mcp_expose_same_catalog() -> None:
    gateway = Gateway(ROOT)
    status, _, api = gateway.handle_api(Request("GET", "/v1/status", {}, {}, b""))
    assert status == 200
    mcp_status, _, mcp_response = gateway.handle_mcp(mcp_request("server/discover"))
    assert mcp_status == 200
    mcp = mcp_response["result"]
    assert api["catalog_id"] == gateway.catalog().catalog_id
    assert api["commit"] == gateway.catalog().commit
    assert api["policies"] == gateway.catalog().policies
    assert len(api["content_digest"]) == 64
    assert mcp["catalog_id"] == api["catalog_id"]
    assert mcp["frontier"] == api["frontier"]
    assert mcp["commit"] == api["commit"]
    assert mcp["policies"] == api["policies"]
    assert mcp["compiler"] == api["compiler"]
    assert len(mcp["content_digest"]) == 64
    assert gateway.decorate_mcp_result(mcp) == mcp
    assert mcp["supportedVersions"] == [PROTOCOL_VERSION]
    assert mcp["resultType"] == "complete"
    assert mcp["_meta"]["io.modelcontextprotocol/serverInfo"]["version"]

    error_status, _, error = gateway.handle_api(
        Request("GET", "/v1/objects/not-an-object", {}, {}, b"")
    )
    assert error_status == 404
    assert error["commit"] == gateway.catalog().commit
    assert error["policies"] == gateway.catalog().policies
    assert len(error["content_digest"]) == 64


def test_mcp_tool_result_carries_catalog_and_frontier() -> None:
    gateway = Gateway(ROOT)
    result = gateway.mcp_method(
        "tools/call", {"name": "search_knowledge", "arguments": {"query": "governance"}}
    )
    structured = result["structuredContent"]
    assert structured["catalog_id"] == gateway.catalog().catalog_id
    assert structured["frontier"] == gateway.catalog().frontier
    assert structured["policies"] == gateway.catalog().policies
    assert len(structured["content_digest"]) == 64
    assert result["isError"] is False

    resource = gateway.mcp_method("resources/read", {"uri": "epistemedia://status"})
    assert resource["resultType"] == "complete"
    assert resource["ttlMs"] == 60000
    assert resource["cacheScope"] == "public"


def test_mcp_rejects_unknown_protocol() -> None:
    gateway = Gateway(ROOT)
    request = mcp_request("tools/list")
    request.headers["mcp-protocol-version"] = "1900-01-01"
    message = json.loads(request.body)
    message["params"]["_meta"]["io.modelcontextprotocol/protocolVersion"] = "1900-01-01"
    request.body = json.dumps(message).encode()
    status, _, result = gateway.handle_mcp(request)
    assert status == 400
    assert result["error"]["code"] == -32022
    assert result["error"]["data"] == {
        "supported": [PROTOCOL_VERSION],
        "requested": "1900-01-01",
    }


def test_mcp_rejects_untrusted_origin() -> None:
    gateway = Gateway(ROOT)
    status, headers, result = gateway.handle_mcp(
        mcp_request("tools/list", origin="https://attacker.example")
    )
    assert status == 403
    assert "access-control-allow-origin" not in headers
    assert result["error"]["code"] == -32003

    rebinding = mcp_request("tools/list", origin="http://localhost:@attacker.example")
    assert gateway.handle_mcp(rebinding)[0] == 403


def test_mcp_accepts_controlled_production_origin() -> None:
    gateway = Gateway(ROOT)
    status, headers, result = gateway.handle_mcp(mcp_request("tools/list"))
    assert status == 200
    assert headers["access-control-allow-origin"] == "https://epistemedia.org"
    assert result["id"] == 1
    assert result["result"]["resultType"] == "complete"
    assert "io.modelcontextprotocol/serverInfo" in result["result"]["_meta"]


def test_mcp_rejects_header_body_mismatch_and_missing_name() -> None:
    gateway = Gateway(ROOT)
    request = mcp_request("tools/list")
    request.headers["mcp-method"] = "resources/list"
    status, _, result = gateway.handle_mcp(request)
    assert status == 400
    assert result["error"]["code"] == -32020

    call = mcp_request(
        "tools/call",
        mcp_params(name="search_knowledge", arguments={"query": "governance"}),
    )
    del call.headers["mcp-name"]
    status, _, result = gateway.handle_mcp(call)
    assert status == 400
    assert result["error"]["code"] == -32020


def test_mcp_accepts_base64_name_and_rejects_unknown_method() -> None:
    gateway = Gateway(ROOT)
    uri = "epistemedia://status"
    request = mcp_request("resources/read", mcp_params(uri=uri))
    request.headers["mcp-name"] = "=?base64?" + base64.b64encode(uri.encode()).decode() + "?="
    assert gateway.handle_mcp(request)[0] == 200

    status, _, result = gateway.handle_mcp(mcp_request("not/a-method"))
    assert status == 404
    assert result["error"]["code"] == -32601

    status, _, result = gateway.handle_mcp(
        mcp_request("prompts/get", mcp_params(name="not-supported"))
    )
    assert status == 404
    assert result["error"]["code"] == -32601


def test_mcp_streamable_http_rejects_get_delete_and_http_cancellation() -> None:
    gateway = Gateway(ROOT)
    for method in ("GET", "DELETE"):
        status, headers, result = gateway.handle_mcp(
            Request(method, "/mcp", {}, {"origin": "https://epistemedia.org"}, b"")
        )
        assert status == 405
        assert headers["allow"] == "POST, OPTIONS"
        assert result["error"]["code"] == -32600

    status, _, result = gateway.handle_mcp(mcp_request("notifications/cancelled", request_id=None))
    assert status == 404
    assert result["error"]["code"] == -32601
    assert "id" not in result

    missing_id = mcp_request("tools/list", request_id=None)
    status, _, result = gateway.handle_mcp(missing_id)
    assert status == 400
    assert result["error"]["code"] == -32600
    assert "id" not in result


def test_mcp_parse_error_omits_unknown_request_id() -> None:
    gateway = Gateway(ROOT)
    request = mcp_request("tools/list")
    request.body = b"{"
    status, _, result = gateway.handle_mcp(request)
    assert status == 400
    assert result["error"]["code"] == -32700
    assert "id" not in result


def test_mcp_request_meta_is_required_for_stdio() -> None:
    gateway = Gateway(ROOT)
    request_id, method, params = gateway.validate_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": "discover",
            "method": "server/discover",
            "params": mcp_params(),
        }
    )
    assert (request_id, method) == ("discover", "server/discover")
    assert params["_meta"]["io.modelcontextprotocol/protocolVersion"] == PROTOCOL_VERSION


def test_stdio_mcp_serves_modern_discovery() -> None:
    message = {
        "jsonrpc": "2.0",
        "id": "discover",
        "method": "server/discover",
        "params": mcp_params(),
    }
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "epistemedia",
            "--root",
            str(ROOT),
            "mcp",
            "serve",
        ],
        cwd=ROOT,
        input=json.dumps(message) + "\n",
        text=True,
        capture_output=True,
        check=True,
    )
    response = json.loads(completed.stdout)
    assert response["id"] == "discover"
    assert response["result"]["supportedVersions"] == [PROTOCOL_VERSION]
    assert response["result"]["resultType"] == "complete"


def test_stdio_mcp_parse_error_does_not_reuse_a_prior_request_id() -> None:
    message = {
        "jsonrpc": "2.0",
        "id": "first",
        "method": "server/discover",
        "params": mcp_params(),
    }
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "epistemedia",
            "--root",
            str(ROOT),
            "mcp",
            "serve",
        ],
        cwd=ROOT,
        input=json.dumps(message) + "\n{\n",
        text=True,
        capture_output=True,
        check=True,
    )
    responses = [json.loads(line) for line in completed.stdout.splitlines()]
    assert responses[0]["id"] == "first"
    assert responses[1]["error"]["code"] == -32700
    assert "id" not in responses[1]


def test_public_gateway_exposes_only_read_only_closed_world_tools() -> None:
    source = (ROOT / "src" / "epistemedia" / "server.py").read_text()
    assert "urlopen(" not in source
    assert "httpx" not in source
    assert "requests." not in source
    tools = tool_definitions()
    assert tools
    assert all(tool["annotations"]["readOnlyHint"] is True for tool in tools)
    assert all(tool["annotations"]["destructiveHint"] is False for tool in tools)
    assert all(tool["annotations"]["openWorldHint"] is False for tool in tools)


def test_public_projection_excludes_private_tree(tmp_path: Path) -> None:
    root = tmp_path / "realm"
    root.mkdir()
    (root / "README.md").write_text("# Public\n\nPublic statement.\n")
    (root / "AGENTS.md").write_text("# Agents\n")
    (root / "pyproject.toml").write_text("[project]\nname='x'\nversion='0'\n")
    private = root / "private"
    private.mkdir()
    (private / "secret.md").write_text("PRIVATE-ONLY-EVIDENCE")
    catalog = PublicCatalog.build(root)
    serialized = json.dumps(catalog.public_dict())
    assert "PRIVATE-ONLY-EVIDENCE" not in serialized
    assert all(not obj.path.startswith("private/") for obj in catalog.objects)


def test_private_mutation_has_no_public_effect(tmp_path: Path) -> None:
    root = tmp_path / "realm"
    root.mkdir()
    (root / "README.md").write_text("# Public\n\nPublic statement.\n")
    (root / "AGENTS.md").write_text("# Agents\n")
    (root / "pyproject.toml").write_text("[project]\nname='x'\nversion='0'\n")
    private = root / "private"
    private.mkdir()
    (private / "secret.md").write_text("first")
    first = PublicCatalog.build(root)
    (private / "secret.md").write_text("second and contradictory")
    second = PublicCatalog.build(root)
    assert first.catalog_id == second.catalog_id
    assert first.frontier == second.frontier


def test_asgi_status_smoke() -> None:
    gateway = Gateway(ROOT)
    sent: list[dict] = []
    incoming = iter(
        [
            {"type": "http.request", "body": b"", "more_body": False},
        ]
    )

    async def receive() -> dict:
        return next(incoming)

    async def send(message: dict) -> None:
        sent.append(message)

    asyncio.run(
        gateway(
            {
                "type": "http",
                "method": "GET",
                "path": "/v1/status",
                "query_string": b"",
                "headers": [],
            },
            receive,
            send,
        )
    )
    assert sent[0]["status"] == 200
    body = json.loads(sent[1]["body"])
    assert body["catalog_id"] == gateway.catalog().catalog_id
    assert body["commit"] == gateway.catalog().commit
    assert body["policies"] == gateway.catalog().policies
    assert len(body["content_digest"]) == 64


def test_asgi_rejects_origin_before_consuming_mcp_body() -> None:
    gateway = Gateway(ROOT)
    sent: list[dict] = []
    receive_calls = 0

    async def receive() -> dict:
        nonlocal receive_calls
        receive_calls += 1
        raise AssertionError("untrusted MCP body must not be consumed")

    async def send(message: dict) -> None:
        sent.append(message)

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/mcp",
        "query_string": b"",
        "headers": [(b"origin", b"https://attacker.example")],
        "client": ("192.0.2.10", 1234),
    }
    asyncio.run(gateway(scope, receive, send))
    assert receive_calls == 0
    assert sent[0]["status"] == 403
    assert json.loads(sent[1]["body"])["error"]["code"] == -32003


def test_asgi_enforces_body_query_response_rate_and_timeout_limits() -> None:
    async def invoke(
        gateway: Gateway,
        *,
        path: str = "/v1/status",
        query: bytes = b"",
        headers: list[tuple[bytes, bytes]] | None = None,
        body: bytes = b"",
    ) -> list[dict]:
        sent: list[dict] = []
        incoming = iter([{"type": "http.request", "body": body, "more_body": False}])

        async def receive() -> dict:
            return next(incoming)

        async def send(message: dict) -> None:
            sent.append(message)

        await gateway(
            {
                "type": "http",
                "method": "GET" if path != "/mcp" else "POST",
                "path": path,
                "query_string": query,
                "headers": headers or [],
                "client": ("192.0.2.20", 4321),
            },
            receive,
            send,
        )
        return sent

    body_limited = Gateway(ROOT, max_body_bytes=10)
    oversized = asyncio.run(
        invoke(
            body_limited,
            path="/mcp",
            headers=[(b"content-length", b"11")],
        )
    )
    assert oversized[0]["status"] == 413

    query_limited = Gateway(ROOT, max_query_bytes=4)
    assert asyncio.run(invoke(query_limited, query=b"q=large"))[0]["status"] == 414

    response_limited = Gateway(ROOT, max_response_bytes=100)
    response = asyncio.run(invoke(response_limited))
    assert response[0]["status"] == 500
    assert json.loads(response[1]["body"])["error"] == "response_too_large"

    rate_limited = Gateway(ROOT, rate_limit_per_minute=1)
    assert asyncio.run(invoke(rate_limited))[0]["status"] == 200
    rate_response = asyncio.run(invoke(rate_limited))
    assert rate_response[0]["status"] == 429

    timeout_limited = Gateway(ROOT, request_timeout_seconds=0.001)
    original_dispatch = timeout_limited.dispatch

    def slow_dispatch(request: Request) -> tuple[int, dict[str, str], object]:
        time.sleep(0.02)
        return original_dispatch(request)

    timeout_limited.dispatch = slow_dispatch  # type: ignore[method-assign]
    timeout_response = asyncio.run(invoke(timeout_limited))
    assert timeout_response[0]["status"] == 504
    assert json.loads(timeout_response[1]["body"])["error"] == "request_timeout"
