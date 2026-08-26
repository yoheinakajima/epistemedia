from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse

import pytest

from epistemedia.case_library import (
    AgentLineageDossier,
    load_featured_library,
)
from epistemedia.cli import main
from epistemedia.core import PublicCatalog, build_public
from epistemedia.featured import FeaturedDossierError
from epistemedia.server import Gateway, Request


ROOT = Path(__file__).resolve().parents[1]
CASE_001 = "corrections-and-familiarity-backfire"
CASE_002 = "agent-citation-lineage"
CASE_002_DOSSIER_ID = (
    "em:dossier:sha256:"
    "cbd7a14096a956f642f5c76046d3b49ed648fbe6bf24144c992404a01415af82"
)
CASE_002_COUNTS = {
    "captured_reports": 8,
    "citation_occurrences": 48,
    "cited_url_strings": 30,
    "resolving_url_roots": 27,
    "source_work_roots": 11,
    "examined_edition_roots": 14,
    "accepted_exact_span_roots": 72,
    "candidate_warrant_roots": 7,
    "independently_confirmed_warrant_roots": 0,
    "pending_warrant_groups": 4,
    "independently_rejected_claim_occurrences": 9,
    "inaccessible_citations": 3,
    "unresolved_citations": 34,
    "unsupported_or_force_raised_claims": 20,
}


def case002() -> AgentLineageDossier:
    library = load_featured_library(ROOT, required=True)
    assert library is not None
    selected = library.get(CASE_002)
    assert isinstance(selected, AgentLineageDossier)
    return selected


def copy_library_inputs(target: Path) -> None:
    for manifest_source in sorted((ROOT / "catalog" / "dossiers").glob("*.json")):
        manifest = json.loads(manifest_source.read_text())
        relative_manifest = manifest_source.relative_to(ROOT)
        for relative in (
            relative_manifest,
            Path(manifest["dossier_path"]),
            Path(manifest["review_receipt_path"]),
        ):
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, destination)


def test_library_discovers_two_cases_deterministically_and_preserves_lead() -> None:
    library = load_featured_library(ROOT, required=True)
    assert library is not None
    assert [item.manifest["number"] for item in library.dossiers] == ["001", "002"]
    assert [item.slug for item in library.dossiers] == [CASE_001, CASE_002]
    assert library.lead.slug == CASE_001
    assert library.get(CASE_002).dossier["dossier_id"] == CASE_002_DOSSIER_ID


def test_case002_exact_inputs_counts_ledgers_and_review_are_bound() -> None:
    selected = case002()
    manifest_path = ROOT / "catalog" / "dossiers" / f"{CASE_002}.json"
    dossier_path = ROOT / selected.manifest["dossier_path"]
    receipt_path = ROOT / selected.manifest["review_receipt_path"]
    assert hashlib.sha256(dossier_path.read_bytes()).hexdigest() == (
        "1ae06b54fe6c6ce1803836bbf2ecaf3e652bed2c6878b7e095c01a1c689ab87b"
    )
    assert dossier_path.stat().st_size == 483_595
    assert hashlib.sha256(receipt_path.read_bytes()).hexdigest() == (
        "dd7f8ad5f760137d91346c3bf38b2bbfffbc7e5c2e74a8a987b76d857e4f244e"
    )
    assert receipt_path.stat().st_size == 14_968
    assert selected.manifest_path == manifest_path
    assert selected.manifest["reviewed_head"] == (
        "16b8e8ebc26948f8d9fa86120c3d495bca3f74e9"
    )
    assert selected.receipt["decision"] == "pass"
    assert selected.derived_counts() == CASE_002_COUNTS

    ledgers = selected.count_ledgers()
    assert {key: len(value) for key, value in ledgers.items()} == {
        "reports": 8,
        "citation_occurrences": 48,
        "cited_urls": 30,
        "resolving_urls": 27,
        "source_works": 11,
        "editions": 14,
        "exact_spans": 72,
        "candidate_warrants": 7,
        "confirmed_warrants": 0,
        "pending_warrants": 4,
        "unresolved_citations": 34,
        "unsupported_claims": 20,
        "rejected_claims": 9,
        "inaccessible_citations": 3,
    }


def test_case002_material_relations_close_to_exact_sources_and_views_diverge() -> None:
    selected = case002()
    encyclopedia = selected.projection("encyclopedia")
    skeptical = selected.projection("skeptical")
    assert encyclopedia["dossier"] == skeptical["dossier"]
    assert encyclopedia["counts"] == skeptical["counts"] == CASE_002_COUNTS
    assert encyclopedia["view"]["label"] != skeptical["view"]["label"]
    assert encyclopedia["practical_reading"]["text"] != (
        skeptical["practical_reading"]["text"]
    )
    assert [
        item["relation"]["key"] for item in encyclopedia["featured_relations"]
    ] != [item["relation"]["key"] for item in skeptical["featured_relations"]]
    assert "independence" in encyclopedia["dependence_warning"].lower()

    for projection in (encyclopedia, skeptical):
        for relation in projection["featured_relations"]:
            assert relation["statement"]
            assert relation["sources"]
            for source in relation["sources"]:
                assert source["source_work"]["id"].startswith(
                    "em:dossier-source-work:sha256:"
                )
                assert source["edition"]["id"].startswith(
                    "em:dossier-edition:sha256:"
                )
                assert re.fullmatch(
                    r"(?:sha256:)?[0-9a-f]{64}",
                    source["edition"]["content_digest"],
                )
                assert source["span"]["id"].startswith(
                    "em:dossier-span:sha256:"
                )
                assert re.fullmatch(
                    r"(?:sha256:)?[0-9a-f]{64}", source["span"]["digest"]
                )
                assert source["span"]["locator"]["label"]
                assert source["license_treatment"] is not None


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({}, "duplicate accepted dossier number"),
        ({"number": "003"}, "duplicate accepted dossier slug"),
        (
            {"number": "003", "slug": "agent-citation-lineage-copy"},
            "duplicate accepted dossier identity",
        ),
    ],
)
def test_library_rejects_duplicate_case_identity(
    tmp_path: Path, mutation: dict[str, str], message: str
) -> None:
    copy_library_inputs(tmp_path)
    source = tmp_path / "catalog" / "dossiers" / f"{CASE_002}.json"
    duplicate = json.loads(source.read_text())
    duplicate.update(mutation)
    (source.parent / "zz-duplicate.json").write_text(
        json.dumps(duplicate, indent=2, sort_keys=True) + "\n"
    )
    with pytest.raises(FeaturedDossierError, match=message):
        load_featured_library(tmp_path, required=True)


def test_library_rejects_unsupported_manifest_and_receipt_drift(tmp_path: Path) -> None:
    copy_library_inputs(tmp_path)
    extra = tmp_path / "catalog" / "dossiers" / "00-unsupported.json"
    extra.write_text(json.dumps({"format": "unknown-dossier-format"}))
    with pytest.raises(FeaturedDossierError, match="unsupported dossier manifest format"):
        load_featured_library(tmp_path, required=True)

    extra.unlink()
    manifest = json.loads(
        (tmp_path / "catalog" / "dossiers" / f"{CASE_002}.json").read_text()
    )
    receipt = tmp_path / manifest["review_receipt_path"]
    receipt.write_bytes(receipt.read_bytes() + b"\n")
    with pytest.raises(FeaturedDossierError, match="review receipt bytes differ"):
        load_featured_library(tmp_path, required=True)


def test_case001_accepted_bytes_remain_exact() -> None:
    expected = {
        "catalog/dossiers/corrections-and-familiarity-backfire.json": (
            "5c96dead036b527793ba5a0de59bf7316efdfeb591470d4a23e5bf979f3b9288"
        ),
        "research/how-we-know/corrections-backfire/candidate-dossier.json": (
            "7003413e286e4d310f81441db33f4a467ba2eb3e08f41ddfa3cef5abb34707ca"
        ),
        (
            "research/how-we-know/corrections-backfire/review-receipts/"
            "20260822T183134Z-codex-independent-reviewer.json"
        ): "503d16396b25b1c22d7fc10ac6fb7db2e530e6ce348d63fa8b639db5a5288f0a",
    }
    for relative, digest in expected.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest


def test_case002_static_api_mcp_cli_and_discovery_are_equivalent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    public = tmp_path / "public"
    build_public(ROOT, public)
    static = json.loads(
        (public / "how-we-know" / CASE_002 / "skeptical" / "index.json").read_text()
    )
    gateway = Gateway(ROOT)
    status, _, api = gateway.handle_api(
        Request(
            "GET",
            f"/v1/dossiers/{CASE_002}",
            {"policy": ["skeptical"]},
            {},
            b"",
        )
    )
    assert status == 200
    assert api == static
    listed_status, _, listed = gateway.handle_api(
        Request("GET", "/v1/dossiers", {}, {}, b"")
    )
    assert listed_status == 200
    assert [item["slug"] for item in listed["data"]] == [CASE_001, CASE_002]

    resource = gateway.mcp_method(
        "resources/read",
        {"uri": f"epistemedia://dossier/{CASE_002}/skeptical"},
    )
    assert json.loads(resource["contents"][0]["text"]) == static
    tool = gateway.mcp_method(
        "tools/call",
        {
            "name": "get_dossier",
            "arguments": {"slug": CASE_002, "policy": "skeptical"},
        },
    )
    assert tool["structuredContent"] == static
    resources = gateway.mcp_method("resources/list", {})["resources"]
    dossier_uris = [
        item["uri"] for item in resources if item["uri"].startswith("epistemedia://dossier/")
    ]
    assert dossier_uris == [
        f"epistemedia://dossier/{CASE_001}/encyclopedia",
        f"epistemedia://dossier/{CASE_001}/skeptical",
        f"epistemedia://dossier/{CASE_002}/encyclopedia",
        f"epistemedia://dossier/{CASE_002}/skeptical",
    ]

    assert main(
        ["--root", str(ROOT), "dossier", CASE_002, "--policy", "skeptical"]
    ) == 0
    assert json.loads(capsys.readouterr().out) == static

    discovery = json.loads((public / ".well-known" / "epistemedia.json").read_text())
    assert [item["slug"] for item in discovery["dossiers"]] == [CASE_001, CASE_002]
    sitemap = (public / "sitemap.xml").read_text()
    assert f"/how-we-know/{CASE_002}/" in sitemap
    assert f"/how-we-know/{CASE_002}/skeptical/" in sitemap
    assert "/dossiers/{slug}" in json.loads((public / "openapi.json").read_text())["paths"]


def test_cold_start_agent_discovers_and_summarizes_case002(tmp_path: Path) -> None:
    public = tmp_path / "public"
    build_public(ROOT, public)
    llms = (public / "llms.txt").read_text()
    links = dict(re.findall(r"^- \[([^]]+)\]\(([^)]+)\)$", llms, re.MULTILINE))
    markdown_url = links["Case 002 evidence dossier"]
    json_url = links["Case 002 dossier JSON"]
    review_url = links["Case 002 review receipt"]
    assert markdown_url.endswith(f"/how-we-know/{CASE_002}/index.md")
    assert review_url.endswith(f"/how-we-know/{CASE_002}/review/index.md")

    document = json.loads(
        (public / urlparse(json_url).path.lstrip("/")).read_text()
    )
    data = document["data"]
    summary = {
        "question": data["question"],
        "verdict": data["view"]["label"],
        "counts": data["counts"],
        "dependence": data["dependence_warning"],
        "unresolved": data["count_ledgers"]["unresolved_citations"],
        "limitations": data["review"]["limitations"],
    }
    assert summary["question"].startswith("What empirical evidence")
    assert "bounded" in summary["verdict"].lower()
    assert summary["counts"] == CASE_002_COUNTS
    assert "independence" in summary["dependence"].lower()
    assert len(summary["unresolved"]) == 34
    assert summary["limitations"]
    assert (public / urlparse(markdown_url).path.lstrip("/")).exists()


def test_case002_human_routes_are_no_script_accessible_and_count_closed(
    tmp_path: Path,
) -> None:
    public = tmp_path / "public"
    build_public(ROOT, public)
    default_html = (public / "how-we-know" / CASE_002 / "index.html").read_text()
    skeptical_html = (
        public / "how-we-know" / CASE_002 / "skeptical" / "index.html"
    ).read_text()
    data = json.loads(
        (public / "how-we-know" / CASE_002 / "index.json").read_text()
    )["data"]
    assert default_html.count("<h1>") == 1
    assert skeptical_html.count("<h1>") == 1
    assert "<script" not in default_html.lower()
    assert "<script" not in skeptical_html.lower()
    assert '<nav class="policy-switch" aria-label="Evidence policy">' in default_html
    assert 'aria-current="page"' in default_html
    assert default_html != skeptical_html
    assert data["view"]["label"] in default_html
    assert data["practical_reading"]["text"] in default_html
    assert "ledger-list" in default_html
    for card in data["count_cards"]:
        assert f'href="#{card["anchor"]}"' in default_html
        assert f'id="{card["anchor"]}"' in default_html
        assert len(data["count_ledgers"][card["ledger_key"]]) == card["value"]
    assert "work, edition, span, retrieval, digest, and license" in default_html
    assert "overflow-wrap:anywhere" in default_html
    assert (
        ".receipt-grid dd{min-width:0;margin:0;overflow-wrap:anywhere;word-break:break-word}"
        in default_html
    )
    assert (
        ".source-card blockquote{max-width:78ch;color:var(--ink);font-family:var(--serif);"
        "overflow-wrap:anywhere;word-break:break-word}"
        in default_html
    )
