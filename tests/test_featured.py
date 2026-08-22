from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from epistemedia.cli import main
from epistemedia.core import PublicCatalog, build_public
from epistemedia.dossier import independence_summary
from epistemedia.featured import FEATURE_VIEWS, FeaturedDossier, FeaturedDossierError
from epistemedia.server import Gateway, Request

ROOT = Path(__file__).resolve().parents[1]
SLUG = "corrections-and-familiarity-backfire"


def test_feature_manifest_binds_exact_reviewed_dossier_and_derives_counts() -> None:
    featured = FeaturedDossier.load(ROOT)
    counts = featured.derived_counts()

    assert featured.slug == SLUG
    assert featured.dossier["dossier_id"] == (
        "em:dossier:sha256:4339d6d6d52b9b534d2e63c95f52ff3cf90be5264f567762f47bab9af4d945a7"
    )
    assert featured.receipt["decision"] == "pass"
    assert featured.receipt["repository"]["reviewed_head"] == featured.manifest["reviewed_head"]
    assert counts["apparent_support_assertion_count"] == 10
    assert counts["known_support_data_root_count"] == 6
    assert counts["unresolved_support_data_root_count"] == 1
    assert counts["target_comparable_support_data_root_count"] == 4
    assert counts["target_comparable_unresolved_data_root_count"] == 1
    assert counts["review_report_assertion_count"] == 4
    assert counts["counter_assertion_count"] == 12
    assert counts["counter_data_root_count"] == 12


def test_real_shared_ancestor_collapses_without_collapsing_new_participant_data() -> None:
    dossier = FeaturedDossier.load(ROOT).dossier
    reported_unpublished = independence_summary(
        dossier,
        [
            "assert-handbook-claim",
            "assert-schwarz-flu-result",
            "assert-ecker-2020-historical-report",
        ],
    )
    assert reported_unpublished["independent_lineage_count"] == 0
    assert reported_unpublished["unknown_lineage_count"] == 1
    assert reported_unpublished["unknown_lineages"] == ["lineage-skurnik-2007-data"]

    new_participants_shared_program = independence_summary(
        dossier,
        ["assert-pluviano-2017-result", "assert-pluviano-2019-result"],
    )
    assert new_participants_shared_program["independent_lineage_count"] == 2
    assert new_participants_shared_program["unknown_lineage_count"] == 0


def test_every_featured_sentence_resolves_exact_span_edition_and_work_identity() -> None:
    featured = FeaturedDossier.load(ROOT)
    for view in FEATURE_VIEWS:
        projection = featured.projection(view)
        assert projection["featured_relations"]
        for item in projection["featured_relations"]:
            assert item["statement"]
            assert item["statement"] == item["relation"]["note"]
            assert item["sources"]
            for source in item["sources"]:
                span = source["span"]
                edition = source["edition"]
                work = source["source_work"]
                assert span["edition_key"] == edition["key"]
                assert edition["work_key"] == work["key"]
                assert span["id"].startswith("em:dossier-span:sha256:")
                assert edition["id"].startswith("em:dossier-edition:sha256:")
                assert work["id"].startswith("em:dossier-source-work:sha256:")
                assert span["locator"]["label"]
                assert span["extent"]["type"] in {"quote", "json-value"}
                assert work["canonical_uri"].startswith("http")
                assert work["license"]

    encyclopedia = featured.projection("encyclopedia")
    pluviano = encyclopedia["featured_relations"][0]
    thomas = encyclopedia["featured_relations"][1]
    assert "two vaccine-message studies" not in pluviano["statement"].lower()
    assert "later direct replication" not in pluviano["statement"].lower()
    assert {source["source_work"]["key"] for source in pluviano["sources"]} == {
        "work-pluviano-2017"
    }
    assert "did not reach significance in every experiment" not in thomas["statement"]
    assert {source["source_work"]["key"] for source in thomas["sources"]} == {
        "work-thomas-2024"
    }


def test_policy_views_share_dossier_sources_but_materially_differ() -> None:
    catalog = PublicCatalog.build(ROOT)
    featured = FeaturedDossier.load(ROOT)
    encyclopedia = featured.envelope(catalog, "encyclopedia")
    skeptical = featured.envelope(catalog, "skeptical")

    assert encyclopedia["catalog_id"] == skeptical["catalog_id"]
    assert encyclopedia["frontier"] == skeptical["frontier"]
    assert encyclopedia["commit"] == skeptical["commit"]
    assert encyclopedia["policies"] == skeptical["policies"]
    assert encyclopedia["data"]["dossier"] == skeptical["data"]["dossier"]
    assert encyclopedia["data"]["source_works"] == skeptical["data"]["source_works"]
    assert encyclopedia["data"]["view"]["policy_id"] != skeptical["data"]["view"]["policy_id"]
    assert encyclopedia["data"]["view"]["label"] != skeptical["data"]["view"]["label"]
    assert [
        item["relation"]["key"] for item in encyclopedia["data"]["featured_relations"]
    ] != [item["relation"]["key"] for item in skeptical["data"]["featured_relations"]]
    skeptical_replication = next(
        item
        for item in skeptical["data"]["featured_relations"]
        if item["relation"]["key"]
        == "relation-ecker-2023-failed-replication-pluviano-2017"
    )
    assert "did not reproduce" in skeptical_replication["statement"]
    assert (
        skeptical_replication["statement"]
        != skeptical_replication["proposition"]["text"]
    )
    assert encyclopedia["content_digest"] != skeptical["content_digest"]


def test_static_html_markdown_and_json_preserve_one_view_identity(tmp_path: Path) -> None:
    public = tmp_path / "public"
    build_public(ROOT, public)
    catalog = PublicCatalog.build(ROOT)
    featured = FeaturedDossier.load(ROOT)
    expected = featured.envelope(catalog, "encyclopedia")
    case = public / "how-we-know" / SLUG

    assert json.loads((case / "index.json").read_text()) == expected
    assert json.loads((case / "encyclopedia" / "index.json").read_text()) == expected
    markdown = (case / "index.md").read_text()
    html = (case / "index.html").read_text()
    home = (public / "index.html").read_text()
    assert expected["data"]["dossier_id"] in markdown
    assert expected["content_digest"] in markdown
    assert expected["data"]["dossier_id"] in html
    assert expected["content_digest"] in html
    assert html.count("<h1>") == 1
    assert html.count('<details class="source-xray">') == 6
    assert '<nav class="policy-switch" aria-label="Evidence policy">' in html
    assert 'aria-current="page"' in html
    assert "<script" not in html
    assert "source-xray" in html
    assert "86 exact spans" in home
    assert home.index("Does repeating misinformation") < home.index(
        "Explore how the record is built"
    )


def test_api_mcp_cli_and_static_json_are_exactly_equivalent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    public = tmp_path / "public"
    build_public(ROOT, public)
    static = json.loads(
        (public / "how-we-know" / SLUG / "skeptical" / "index.json").read_text()
    )
    gateway = Gateway(ROOT)

    status, _, api = gateway.handle_api(
        Request(
            "GET",
            f"/v1/dossiers/{SLUG}",
            {"policy": ["skeptical"]},
            {},
            b"",
        )
    )
    assert status == 200
    assert api == static

    tool = gateway.mcp_method(
        "tools/call",
        {
            "name": "get_dossier",
            "arguments": {"slug": SLUG, "policy": "skeptical"},
        },
    )
    assert tool["structuredContent"] == static
    resource = gateway.mcp_method(
        "resources/read", {"uri": f"epistemedia://dossier/{SLUG}/skeptical"}
    )
    resource_envelope = json.loads(resource["contents"][0]["text"])
    assert resource_envelope == static

    assert main(["--root", str(ROOT), "dossier", SLUG, "--policy", "skeptical"]) == 0
    cli = json.loads(capsys.readouterr().out)
    assert cli == static


def test_dossier_byte_drift_fails_closed(tmp_path: Path) -> None:
    manifest = json.loads(
        (ROOT / "catalog" / "dossiers" / f"{SLUG}.json").read_text()
    )
    dossier_source = ROOT / manifest["dossier_path"]
    receipt_source = ROOT / manifest["review_receipt_path"]
    manifest_target = tmp_path / "catalog" / "dossiers" / f"{SLUG}.json"
    dossier_target = tmp_path / manifest["dossier_path"]
    receipt_target = tmp_path / manifest["review_receipt_path"]
    for target in (manifest_target, dossier_target, receipt_target):
        target.parent.mkdir(parents=True, exist_ok=True)
    manifest_target.write_text(json.dumps(manifest))
    dossier_target.write_bytes(dossier_source.read_bytes())
    receipt_target.write_bytes(receipt_source.read_bytes())

    altered = json.loads(dossier_target.read_text())
    altered["title"] += " altered"
    dossier_target.write_text(json.dumps(altered))
    with pytest.raises(FeaturedDossierError):
        FeaturedDossier.load(tmp_path)


def test_review_receipt_byte_drift_and_forged_independence_fail_closed(
    tmp_path: Path,
) -> None:
    manifest = json.loads(
        (ROOT / "catalog" / "dossiers" / f"{SLUG}.json").read_text()
    )
    dossier_source = ROOT / manifest["dossier_path"]
    receipt_source = ROOT / manifest["review_receipt_path"]
    manifest_target = tmp_path / "catalog" / "dossiers" / f"{SLUG}.json"
    dossier_target = tmp_path / manifest["dossier_path"]
    receipt_target = tmp_path / manifest["review_receipt_path"]
    for target in (manifest_target, dossier_target, receipt_target):
        target.parent.mkdir(parents=True, exist_ok=True)
    manifest_target.write_text(json.dumps(manifest))
    dossier_target.write_bytes(dossier_source.read_bytes())
    receipt_target.write_bytes(receipt_source.read_bytes())

    forged = json.loads(receipt_target.read_text())
    forged["reviewer"]["id"] = "forged-author-reviewer"
    forged["reviewer"]["independent_retrieval"] = False
    forged["reviewer"]["authoring_agent_artifacts_used"] = True
    receipt_target.write_text(json.dumps(forged))
    with pytest.raises(FeaturedDossierError):
        FeaturedDossier.load(tmp_path)

    manifest["review_receipt_sha256"] = hashlib.sha256(
        receipt_target.read_bytes()
    ).hexdigest()
    manifest["review_receipt_bytes"] = receipt_target.stat().st_size
    manifest_target.write_text(json.dumps(manifest))
    with pytest.raises(FeaturedDossierError):
        FeaturedDossier.load(tmp_path)
