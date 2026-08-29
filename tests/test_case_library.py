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
    BoundedPropositionDossier,
    load_featured_library,
)
from epistemedia.cli import main
from epistemedia.core import build_public
from epistemedia.featured import FeaturedDossierError
from epistemedia.server import Gateway, Request

ROOT = Path(__file__).resolve().parents[1]
CASE_001 = "corrections-and-familiarity-backfire"
CASE_002 = "agent-citation-lineage"
CASE_003 = "gpt-4-bar-exam-percentile"
CASE_004 = "mehrabian-7-38-55"
CASE_SLUGS = [CASE_001, CASE_002, CASE_003, CASE_004]
CASE_002_DOSSIER_ID = (
    "em:dossier:sha256:cbd7a14096a956f642f5c76046d3b49ed648fbe6bf24144c992404a01415af82"
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
BOUNDED_CASES = {
    CASE_003: {
        "dossier_id": (
            "em:dossier:sha256:babe89ba3bda594a8d9f2db86a5a2987f284437a069b940d19b6928856d936d1"
        ),
        "dossier_sha256": "32c4457b3823237b2f988a26d51b2f6222af8060e662993524aff1c1a5d79e5d",
        "dossier_bytes": 224_792,
        "receipt_sha256": "f35f8c093778ad1cdeafc57746575f1a82d12fe6e6fbf0d1d4a546e3c5296e1e",
        "receipt_bytes": 13_568,
        "counts": {
            "historical_model_runs": 1,
            "administration_sensitivities": 3,
            "independent_evidence_roots": 7,
            "unresolved_boundaries": 3,
        },
    },
    CASE_004: {
        "dossier_id": (
            "em:dossier:sha256:57e80c9a44c478c1c81ba7adedc1bafdef43ff57b4f2984015dcbef84ba66e87"
        ),
        "dossier_sha256": "44e7bf407091d7665d4f1ab2aabc285255364e790e2d17520913f9ba9c57b418",
        "dossier_bytes": 176_885,
        "receipt_sha256": "0bb9184660deb3ef83addbcdb7be61d49f234026d6d484747b51628a4f8f087f",
        "receipt_bytes": 71_345,
        "counts": {
            "original_experiments": 2,
            "participant_data_roots": 5,
            "zero_credit_propagation": 3,
            "unresolved_derivations": 1,
        },
    },
}


def case002() -> AgentLineageDossier:
    library = load_featured_library(ROOT, required=True)
    assert library is not None
    selected = library.get(CASE_002)
    assert isinstance(selected, AgentLineageDossier)
    return selected


def bounded_case(slug: str) -> BoundedPropositionDossier:
    library = load_featured_library(ROOT, required=True)
    assert library is not None
    selected = library.get(slug)
    assert isinstance(selected, BoundedPropositionDossier)
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


def test_library_discovers_four_cases_deterministically_and_preserves_lead() -> None:
    library = load_featured_library(ROOT, required=True)
    assert library is not None
    assert [item.manifest["number"] for item in library.dossiers] == [
        "001",
        "002",
        "003",
        "004",
    ]
    assert [item.slug for item in library.dossiers] == CASE_SLUGS
    assert library.lead.slug == CASE_001
    assert library.get(CASE_002).dossier["dossier_id"] == CASE_002_DOSSIER_ID


@pytest.mark.parametrize("slug", [CASE_003, CASE_004])
def test_bounded_cases_bind_exact_inputs_counts_and_review(slug: str) -> None:
    selected = bounded_case(slug)
    expected = BOUNDED_CASES[slug]
    dossier_path = ROOT / selected.manifest["dossier_path"]
    receipt_path = ROOT / selected.manifest["review_receipt_path"]
    assert selected.dossier["dossier_id"] == expected["dossier_id"]
    assert hashlib.sha256(dossier_path.read_bytes()).hexdigest() == expected["dossier_sha256"]
    assert dossier_path.stat().st_size == expected["dossier_bytes"]
    assert hashlib.sha256(receipt_path.read_bytes()).hexdigest() == expected["receipt_sha256"]
    assert receipt_path.stat().st_size == expected["receipt_bytes"]
    assert selected.receipt["decision"] == "pass"
    assert selected.derived_counts() == expected["counts"]
    assert {key: len(value) for key, value in selected.count_ledgers().items()} == expected[
        "counts"
    ]


@pytest.mark.parametrize("slug", [CASE_003, CASE_004])
def test_bounded_case_sources_close_and_policy_views_diverge(slug: str) -> None:
    selected = bounded_case(slug)
    encyclopedia = selected.projection("encyclopedia")
    skeptical = selected.projection("skeptical")
    assert not encyclopedia["title"].startswith(f"Case {selected.manifest['number']}:")
    assert encyclopedia["dossier"] == skeptical["dossier"]
    assert encyclopedia["counts"] == skeptical["counts"]
    assert encyclopedia["view"]["label"] != skeptical["view"]["label"]
    assert encyclopedia["practical_reading"]["text"] != skeptical["practical_reading"]["text"]
    assert [item["relation"]["key"] for item in encyclopedia["featured_relations"]] != [
        item["relation"]["key"] for item in skeptical["featured_relations"]
    ]
    for projection in (encyclopedia, skeptical):
        for relation in projection["featured_relations"]:
            assert relation["statement"]
            assert relation["statement"] == relation["proposition"]["text"]
            assert relation["assertion"]["proposition_key"] == relation["proposition"]["key"]
            assert relation["assertion"]["lineage_key"] == relation["lineage"]["key"]
            assert relation["relation"]["to_ref"] == relation["proposition"]["key"]
            assert relation["sources"]
            for source in relation["sources"]:
                assert source["source_work"]["id"].startswith("em:dossier-source-work:sha256:")
                assert source["edition"]["id"].startswith("em:dossier-edition:sha256:")
                assert re.fullmatch(
                    r"(?:sha256:)?[0-9a-f]{64}", source["edition"]["content_digest"]
                )
                assert source["span"]["id"].startswith("em:dossier-span:sha256:")
                assert re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", source["span"]["digest"])
                assert source["span"]["locator"]["label"]
                assert source["license_treatment"] is not None


def test_bounded_case_human_projection_closes_calculations_and_provenance(
    tmp_path: Path,
) -> None:
    case003 = bounded_case(CASE_003).projection("encyclopedia")
    calculations = [
        calculation
        for relation in case003["featured_relations"]
        for calculation in relation["calculations"]
    ]
    assert calculations
    calculation_spans = [
        source["span"]
        for calculation in calculations
        for source in calculation["sources"]
        if source["span"]["key"].startswith("span-calculation-")
    ]
    assert calculation_spans
    records = [span["extent"]["value"] for span in calculation_spans]
    assert any(record["derivation"].get("equation") for record in records)
    assert any(record["derivation"].get("input_cell_ids") for record in records)
    assert any(record.get("resolved_input_cells") for record in records)
    assert any(record["derivation"].get("depends_on") for record in records)
    assert any(relation["dependencies"] for relation in case003["featured_relations"])

    public = tmp_path / "public"
    build_public(ROOT, public)
    case003_html = (public / "how-we-know" / CASE_003 / "index.html").read_text()
    case003_markdown = (public / "how-we-know" / CASE_003 / "index.md").read_text()
    case004_html = (public / "how-we-know" / CASE_004 / "index.html").read_text()
    for rendered in (case003_html, case003_markdown):
        assert "OpenAI&#x27;s launch-edition report" in rendered or (
            "OpenAI's launch-edition report" in rendered
        )
        assert "relation-assertion-claim-launch-score-label" in rendered
        assert "lineage-model-performance-root" in rendered
        assert "span-calculation-derive-illinois-feb-2018-298" in rendered
        assert "p298 = p290 + ((298 - 290) / 10) * (p300 - p290)" in rendered
        assert "resolved_input_cells" in rendered
        assert "edge-derivation-comparison-inputs" in rendered
        assert "Basis span" in rendered
        assert "Basis edition" in rendered
        assert "Basis work" in rendered
    assert "P1 found tone dominance" in case004_html
    assert "edge-p1-p2-method" in case004_html
    assert "lineage-participant-p1" in case004_html


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
    assert selected.manifest["reviewed_head"] == ("16b8e8ebc26948f8d9fa86120c3d495bca3f74e9")
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
    assert encyclopedia["practical_reading"]["text"] != (skeptical["practical_reading"]["text"])
    assert [item["relation"]["key"] for item in encyclopedia["featured_relations"]] != [
        item["relation"]["key"] for item in skeptical["featured_relations"]
    ]
    assert "independence" in encyclopedia["dependence_warning"].lower()

    for projection in (encyclopedia, skeptical):
        for relation in projection["featured_relations"]:
            assert relation["statement"]
            assert relation["sources"]
            for source in relation["sources"]:
                assert source["source_work"]["id"].startswith("em:dossier-source-work:sha256:")
                assert source["edition"]["id"].startswith("em:dossier-edition:sha256:")
                assert re.fullmatch(
                    r"(?:sha256:)?[0-9a-f]{64}",
                    source["edition"]["content_digest"],
                )
                assert source["span"]["id"].startswith("em:dossier-span:sha256:")
                assert re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", source["span"]["digest"])
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
    manifest = json.loads((tmp_path / "catalog" / "dossiers" / f"{CASE_002}.json").read_text())
    receipt = tmp_path / manifest["review_receipt_path"]
    receipt.write_bytes(receipt.read_bytes() + b"\n")
    with pytest.raises(FeaturedDossierError, match="review receipt bytes differ"):
        load_featured_library(tmp_path, required=True)


@pytest.mark.parametrize("slug", [CASE_003, CASE_004])
def test_bounded_case_rejects_receipt_semantic_forgery(tmp_path: Path, slug: str) -> None:
    copy_library_inputs(tmp_path)
    manifest_path = tmp_path / "catalog" / "dossiers" / f"{slug}.json"
    manifest = json.loads(manifest_path.read_text())
    receipt_path = tmp_path / manifest["review_receipt_path"]
    receipt = json.loads(receipt_path.read_text())
    receipt["reviewer"]["id"] = "forged-author-reviewer"
    receipt_bytes = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()
    receipt_path.write_bytes(receipt_bytes)
    manifest["review_receipt_sha256"] = hashlib.sha256(receipt_bytes).hexdigest()
    manifest["review_receipt_bytes"] = len(receipt_bytes)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(FeaturedDossierError, match="reviewer differs"):
        load_featured_library(tmp_path, required=True)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"profile": "unsupported-profile"}, "unsupported bounded projection profile"),
        ({"reviewed_tree": "0" * 40}, "reviewed Git identity differs"),
    ],
)
def test_bounded_case_rejects_profile_and_review_identity_drift(
    tmp_path: Path, mutation: dict[str, str], message: str
) -> None:
    copy_library_inputs(tmp_path)
    manifest_path = tmp_path / "catalog" / "dossiers" / f"{CASE_003}.json"
    manifest = json.loads(manifest_path.read_text())
    manifest.update(mutation)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(FeaturedDossierError, match=message):
        load_featured_library(tmp_path, required=True)


def test_bounded_case_rejects_count_member_outside_dossier(tmp_path: Path) -> None:
    copy_library_inputs(tmp_path)
    manifest_path = tmp_path / "catalog" / "dossiers" / f"{CASE_004}.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["count_cards"][0]["members"][0]["object_key"] = "missing-lineage"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(FeaturedDossierError, match="count member is not in dossier"):
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


@pytest.mark.parametrize("slug", [CASE_002, CASE_003, CASE_004])
def test_structured_case_static_api_mcp_cli_and_discovery_are_equivalent(
    slug: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    public = tmp_path / "public"
    build_public(ROOT, public)
    static = json.loads((public / "how-we-know" / slug / "skeptical" / "index.json").read_text())
    gateway = Gateway(ROOT)
    status, _, api = gateway.handle_api(
        Request(
            "GET",
            f"/v1/dossiers/{slug}",
            {"policy": ["skeptical"]},
            {},
            b"",
        )
    )
    assert status == 200
    assert api == static
    listed_status, _, listed = gateway.handle_api(Request("GET", "/v1/dossiers", {}, {}, b""))
    assert listed_status == 200
    assert [item["slug"] for item in listed["data"]] == CASE_SLUGS

    resource = gateway.mcp_method(
        "resources/read",
        {"uri": f"epistemedia://dossier/{slug}/skeptical"},
    )
    assert json.loads(resource["contents"][0]["text"]) == static
    tool = gateway.mcp_method(
        "tools/call",
        {
            "name": "get_dossier",
            "arguments": {"slug": slug, "policy": "skeptical"},
        },
    )
    assert tool["structuredContent"] == static
    resources = gateway.mcp_method("resources/list", {})["resources"]
    dossier_uris = [
        item["uri"] for item in resources if item["uri"].startswith("epistemedia://dossier/")
    ]
    assert dossier_uris == [
        f"epistemedia://dossier/{case_slug}/{policy}"
        for case_slug in CASE_SLUGS
        for policy in ("encyclopedia", "skeptical")
    ]

    assert main(["--root", str(ROOT), "dossier", slug, "--policy", "skeptical"]) == 0
    assert json.loads(capsys.readouterr().out) == static

    discovery = json.loads((public / ".well-known" / "epistemedia.json").read_text())
    assert [item["slug"] for item in discovery["dossiers"]] == CASE_SLUGS
    sitemap = (public / "sitemap.xml").read_text()
    assert f"/how-we-know/{slug}/" in sitemap
    assert f"/how-we-know/{slug}/skeptical/" in sitemap
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

    document = json.loads((public / urlparse(json_url).path.lstrip("/")).read_text())
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


@pytest.mark.parametrize(("number", "slug"), [("003", CASE_003), ("004", CASE_004)])
def test_cold_start_agent_discovers_bounded_cases(tmp_path: Path, number: str, slug: str) -> None:
    public = tmp_path / "public"
    build_public(ROOT, public)
    llms = (public / "llms.txt").read_text()
    links = dict(re.findall(r"^- \[([^]]+)\]\(([^)]+)\)$", llms, re.MULTILINE))
    markdown_url = links[f"Case {number} evidence dossier"]
    json_url = links[f"Case {number} dossier JSON"]
    review_url = links[f"Case {number} review receipt"]
    assert markdown_url.endswith(f"/how-we-know/{slug}/index.md")
    assert review_url.endswith(f"/how-we-know/{slug}/review/index.md")
    data = json.loads((public / urlparse(json_url).path.lstrip("/")).read_text())["data"]
    assert data["question"]
    assert data["view"]["label"]
    assert data["counts"] == BOUNDED_CASES[slug]["counts"]
    assert data["dependence_warning"]
    assert data["review"]["limitations"]
    assert data["review"]["decision"] == "pass"


def test_case002_human_routes_are_no_script_accessible_and_count_closed(
    tmp_path: Path,
) -> None:
    public = tmp_path / "public"
    build_public(ROOT, public)
    default_html = (public / "how-we-know" / CASE_002 / "index.html").read_text()
    skeptical_html = (public / "how-we-know" / CASE_002 / "skeptical" / "index.html").read_text()
    data = json.loads((public / "how-we-know" / CASE_002 / "index.json").read_text())["data"]
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
        "overflow-wrap:anywhere;word-break:break-word}" in default_html
    )
