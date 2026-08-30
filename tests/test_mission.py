# ruff: noqa: E501
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from epistemedia.cli import main
from epistemedia.core import audit_public, build_public
from epistemedia.mission import MissionError, load_mission
from epistemedia.server import Gateway, Request, tool_definitions

ROOT = Path(__file__).resolve().parents[1]

ACCEPTED_CASE_FILES = {
    "catalog/dossiers/agent-citation-lineage.json": "31f9e7642c7c0c51209e8827551bb9893c59336284c0ddf529fef96ef67b7904",
    "catalog/dossiers/corrections-and-familiarity-backfire.json": "5c96dead036b527793ba5a0de59bf7316efdfeb591470d4a23e5bf979f3b9288",
    "catalog/dossiers/gpt-4-bar-exam-percentile.json": "1a73f01732134b4da7e6a95fa6cc95fdef0f1ef63b4c74fd00245e8b908c7ff2",
    "catalog/dossiers/mehrabian-7-38-55.json": "fd4ad4a47fdfea92c20812cd594f687864e5b4e2039658fbf9b55a2f5803f05e",
    "research/how-we-know/corrections-backfire/candidate-dossier.json": "7003413e286e4d310f81441db33f4a467ba2eb3e08f41ddfa3cef5abb34707ca",
    "research/how-we-know/corrections-backfire/review-receipts/20260822T183134Z-codex-independent-reviewer.json": "503d16396b25b1c22d7fc10ac6fb7db2e530e6ce348d63fa8b639db5a5288f0a",
    "research/how-we-know/agent-citation-lineage/candidate-dossier.json": "1ae06b54fe6c6ce1803836bbf2ecaf3e652bed2c6878b7e095c01a1c689ab87b",
    "research/how-we-know/agent-citation-lineage/independent-em0029-review-receipt.json": "dd7f8ad5f760137d91346c3bf38b2bbfffbc7e5c2e74a8a987b76d857e4f244e",
    "research/how-we-know/gpt-4-bar-exam-percentile/candidate-dossier.json": "32c4457b3823237b2f988a26d51b2f6222af8060e662993524aff1c1a5d79e5d",
    "research/how-we-know/gpt-4-bar-exam-percentile/independent-em0034-review-receipt.json": "f35f8c093778ad1cdeafc57746575f1a82d12fe6e6fbf0d1d4a546e3c5296e1e",
    "research/how-we-know/mehrabian-7-38-55/candidate-dossier.json": "44e7bf407091d7665d4f1ab2aabc285255364e790e2d17520913f9ba9c57b418",
    "research/how-we-know/mehrabian-7-38-55/independent-em0035-review-receipt.json": "0bb9184660deb3ef83addbcdb7be61d49f234026d6d484747b51628a4f8f087f",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mission_copy(tmp_path: Path) -> tuple[Path, dict]:
    root = tmp_path / "repo"
    path = root / "catalog" / "mission.json"
    path.parent.mkdir(parents=True)
    data = json.loads((ROOT / "catalog" / "mission.json").read_text())
    path.write_text(json.dumps(data), encoding="utf-8")
    return root, data


def test_mission_source_is_versioned_and_future_services_fail_closed() -> None:
    mission = load_mission(ROOT)
    assert mission["format"] == "epistemedia-mission-v0.3"
    assert mission["version"] == "0.3"
    assert mission["mission_id"].startswith("em:mission:sha256:")
    assert mission["source"]["path"] == "catalog/mission.json"
    assert mission["source"]["sha256"] == _sha256(ROOT / "catalog/mission.json")
    assert [(item["number"], item["failure_mode"]) for item in mission["cases"]] == [
        ("001", "Overgeneralization"),
        ("002", "False independence"),
        ("003", "Missing comparison class"),
        ("004", "Scope inflation"),
    ]
    state = mission["current_state"]
    assert state["hosted_api_live"] is False
    assert state["hosted_mcp_live"] is False
    assert state["authenticated_submission_queue_live"] is False
    assert state["second_realm_live"] is False
    assert "not evidence, policy, constitution, or a stored verdict" in (
        mission["governance_note"]
    )


@pytest.mark.parametrize("mutation", ["extra", "case", "service", "link"])
def test_mission_source_tampering_fails_closed(tmp_path: Path, mutation: str) -> None:
    root, data = _mission_copy(tmp_path)
    if mutation == "extra":
        data["unreviewed"] = True
    elif mutation == "case":
        data["cases"][0]["slug"] = "another-case"
    elif mutation == "service":
        data["current_state"]["hosted_mcp_live"] = True
    else:
        data["participation"][0]["href"] = "https://collector.example/submit"
    (root / "catalog" / "mission.json").write_text(json.dumps(data))
    with pytest.raises(MissionError):
        load_mission(root)


def test_about_home_and_library_compile_from_one_mission(tmp_path: Path) -> None:
    public = tmp_path / "public"
    manifest = build_public(ROOT, public)
    assert audit_public(ROOT, public) == []
    for relative in (
        "about/index.html",
        "about/index.md",
        "about/index.json",
        "about/reader-check/index.html",
        "about/reader-check/index.md",
        "about/reader-check/index.json",
    ):
        assert (public / relative).is_file(), relative

    mission = load_mission(ROOT)
    about_json = json.loads((public / "about" / "index.json").read_text())
    about_html = (public / "about" / "index.html").read_text()
    about_markdown = (public / "about" / "index.md").read_text()
    assert about_json["data"]["mission_id"] == mission["mission_id"]
    assert about_json["content_digest"]
    assert about_html.count("<h1") == 1
    assert "<script" not in about_html
    assert '<link rel="canonical" href="https://epistemedia.org/about/">' in about_html
    assert 'type="text/markdown" href="https://epistemedia.org/about/index.md"' in (
        about_html
    )
    assert "Knowledge that can show its work" in about_html
    assert "Knowledge that can show its work" in about_markdown
    assert mission["mission_id"] in about_html
    assert mission["mission_id"] in about_markdown
    for item in mission["cases"]:
        assert item["failure_mode"] in about_html
        assert item["failure_mode"] in about_markdown
        assert item["defining_count"] in about_html
        assert item["defining_count"] in about_markdown
    assert manifest["catalog_id"] in about_html

    home = (public / "index.html").read_text()
    assert home.count('class="failure-card"') == 4
    assert home.count('class="participation-card"') == 3
    assert "From assertion to inspectable reading" in home
    assert home.index("Does repeating misinformation") < home.index(
        "Claims arrive without their history"
    )
    assert home.index("Claims arrive without their history") < home.index(
        "Explore how the record is built"
    )
    library = (public / "how-we-know" / "index.html").read_text()
    assert "Four unit tests for how knowledge fails" in library
    assert library.count('class="failure-card"') == 4
    assert "No future case is advertised as available" in library


def test_navigation_discovery_and_sitemap_keep_human_and_agent_doors_open(
    tmp_path: Path,
) -> None:
    public = tmp_path / "public"
    build_public(ROOT, public)
    home = (public / "index.html").read_text()
    assert '<nav class="primary-nav" aria-label="Primary">' in home
    assert '>How We Know</a>' in home
    assert '>About</a>' in home
    assert '>For agents</a>' in home
    assert '<nav class="utility-nav" aria-label="Utility">' in home
    for label in ("Substrate", "Docs", "Status", "GitHub"):
        assert f">{label}</a>" in home
    assert '<details class="utility-menu"><summary>Project</summary>' in home
    assert "@media (max-width:640px)" in home
    assert ".utility-menu{display:block}" in home

    llms = (public / "llms.txt").read_text()
    assert "Mission v0.3" in llms
    assert "/about/index.md" in llms
    assert "/about/index.json" in llms
    assert "/about/reader-check/index.md" in llms
    discovery = json.loads(
        (public / ".well-known" / "epistemedia.json").read_text()
    )
    mission = load_mission(ROOT)
    assert discovery["about"]["mission_id"] == mission["mission_id"]
    assert discovery["about"]["human"] == "https://epistemedia.org/about/"
    assert discovery["about"]["reader_check"].endswith("/about/reader-check/")
    sitemap = (public / "sitemap.xml").read_text()
    assert "https://epistemedia.org/about/" in sitemap
    assert "https://epistemedia.org/about/reader-check/" in sitemap


def test_mission_has_static_rest_mcp_and_cli_parity(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    public = tmp_path / "public"
    build_public(ROOT, public)
    expected = load_mission(ROOT)
    status = json.loads((public / "status.json").read_text())
    assert status["mission"] == {
        "id": expected["mission_id"],
        "version": expected["version"],
        "human": "https://epistemedia.org/about/",
        "machine": "https://epistemedia.org/about/index.json",
    }
    openapi = json.loads((public / "openapi.json").read_text())
    assert openapi["paths"]["/mission"]["get"]["operationId"] == "getMission"

    gateway = Gateway(ROOT)
    code, _, response = gateway.handle_api(
        Request("GET", "/v1/mission", {}, {}, b"")
    )
    assert code == 200
    assert response["data"] == expected
    assert gateway.call_tool("get_mission", {}) == expected
    assert gateway.read_resource("epistemedia://mission") == expected
    resources = gateway.mcp_method("resources/list", {})
    assert "epistemedia://mission" in {
        item["uri"] for item in resources["resources"]
    }

    assert main(["--root", str(ROOT), "mission"]) == 0
    cli = json.loads(capsys.readouterr().out)
    assert cli["data"] == expected


def test_reader_check_requires_a_real_human_and_records_no_synthetic_result(
    tmp_path: Path,
) -> None:
    public = tmp_path / "public"
    build_public(ROOT, public)
    document = json.loads(
        (public / "about" / "reader-check" / "index.json").read_text()
    )["data"]
    assert document["status"] == "awaiting-human-response"
    assert len(document["questions"]) == 5
    assert [item["id"] for item in document["questions"]] == [
        "evidence-unit",
        "run-independence",
        "lens-difference",
        "current-limit",
        "inspect-source",
    ]
    assert "actual human" in document["recording_boundary"]
    assert "Automated route, browser, and model checks do not satisfy" in document[
        "recording_boundary"
    ]
    assert "answers" not in document
    assert "result" not in document


def test_no_public_write_or_admission_surface_is_implied(tmp_path: Path) -> None:
    public = tmp_path / "public"
    build_public(ROOT, public)
    mission = json.loads((public / "about" / "index.json").read_text())["data"]
    state = mission["current_state"]
    assert not state["hosted_api_live"]
    assert not state["hosted_mcp_live"]
    assert not state["authenticated_submission_queue_live"]
    submission = json.loads(
        (public / "agents" / "submission-status.json").read_text()
    )
    assert submission["hosted_submission_available"] is False
    assert submission["github_submission_available"] is True
    assert submission["queue_status"] == "github-draft-pr-pilot"
    names = {item["name"].lower() for item in tool_definitions()}
    assert not any(
        token in name
        for name in names
        for token in ("submit", "admit", "merge", "publish")
    )


def test_accepted_case_inputs_are_byte_identical() -> None:
    for relative, expected in ACCEPTED_CASE_FILES.items():
        assert _sha256(ROOT / relative) == expected, relative
