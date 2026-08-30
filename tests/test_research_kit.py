from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from epistemedia.case_library import load_featured_library
from epistemedia.cli import main
from epistemedia.core import build_public
from epistemedia.research_kit import (
    MAX_BUNDLE_BYTES,
    PROPOSAL_FORMAT,
    case_research_brief,
    proposal_template,
    protocol_document,
    validate_proposal,
)
from epistemedia.server import Gateway, Request, tool_definitions

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    "agent-citation-lineage",
    "gpt-4-bar-exam-percentile",
    "mehrabian-7-38-55",
)


def valid_proposal() -> dict:
    return {
        "format": PROPOSAL_FORMAT,
        "status": "ready-for-review",
        "question": "Does the cited evidence support the bounded claim?",
        "cutoff": "2026-08-29",
        "scope": {
            "included": "Public primary sources available by the cutoff.",
            "excluded": "Private sources and claims outside the comparison target.",
            "comparison_target": "Claim support, not URL availability alone.",
        },
        "results": [
            {
                "result_id": "result-1",
                "proposition": "The tested source supports the bounded proposition.",
                "reported_value": {
                    "numerator": "1 supported proposition",
                    "denominator": "1 tested proposition",
                    "rate": "1/1 in this bounded example",
                    "comparison": "No claim about other propositions.",
                },
                "scope": {
                    "models_or_agents": ["test-agent"],
                    "dataset_or_population": "One public primary source.",
                    "tool_and_retrieval_path": "Credential-free HTTPS retrieval.",
                    "time": "2026-08-29",
                    "metric_scope": "Exact source-to-proposition support.",
                },
                "source_ids": ["source-1"],
                "exact_span_ids": ["span-1"],
                "interpretation": "This closes only the stated example.",
                "warrant": "Direct quote-minimal source span.",
                "uncertainty": "No independent reproduction in this bundle.",
                "calculation_ids": ["calculation-1"],
                "calculation_status": "reproduced",
                "dependency_ids": ["dependency-1"],
            }
        ],
        "calculations": [
            {
                "calculation_id": "calculation-1",
                "equation": "1 supported proposition / 1 tested proposition",
                "inputs": [
                    {
                        "name": "supported propositions",
                        "value": "1",
                        "source_id": "source-1",
                        "span_id": "span-1",
                    },
                    {
                        "name": "tested propositions",
                        "value": "1",
                        "source_id": "source-1",
                        "span_id": "span-1",
                    },
                ],
                "output": "1/1",
                "uncertainty": "Fixture-only identity calculation.",
                "depends_on": [],
            }
        ],
        "dependencies": [
            {
                "dependency_id": "dependency-1",
                "kind": "source",
                "description": "The proposition depends on one source and one span.",
                "source_ids": ["source-1"],
                "exact_span_ids": ["span-1"],
            }
        ],
        "sources": [
            {
                "source_id": "source-1",
                "url": "https://example.org/primary",
                "title": "Primary source",
                "creators_or_org": "Example Research Group",
                "date": "2026-08-29",
                "identifier": "doi:10.0000/example",
                "edition": "Version of record",
                "retrieval_status": "retrieved",
                "media_type": "text/html",
                "license": "CC BY 4.0",
                "exact_spans": [
                    {
                        "span_id": "span-1",
                        "locator": "Results, paragraph 1",
                        "quote": "The bounded result was observed.",
                        "supports": "The result proposition.",
                    }
                ],
            }
        ],
        "counterevidence": [
            {
                "claim": "The result applies universally.",
                "evidence": "The source states a narrow population.",
                "source_ids": ["source-1"],
                "exact_span_ids": ["span-1"],
                "qualification": "This limits generalization rather than reversing the result.",
            }
        ],
        "negative_results": [
            {
                "result": "No independent reproduction was located in the bounded search.",
                "scope": "The declared search only.",
                "source_ids": ["source-1"],
                "exact_span_ids": ["span-1"],
                "disposition": "Retained as unresolved, not converted to a null result.",
            }
        ],
        "limitations": ["One-source demonstration only."],
        "unresolved": ["Independent reproduction remains unresolved."],
        "search_notes": ["Credential-free primary-source retrieval only."],
        "lineage": {
            "prompt_sha256": "sha256:" + "1" * 64,
            "run_identity": "run-example-1",
            "provider_model_identity": "test-agent",
            "retrieval_environment": "public HTTPS",
            "shared_dependencies": ["one prompt", "one retrieval environment"],
        },
        "runtime": {
            "started_at": "2026-08-29T00:00:00Z",
            "completed_at": "2026-08-29T00:01:00Z",
            "agent": "test-agent",
            "toolchain": ["HTTP retrieval", "local JSON validator"],
        },
        "license": {
            "bundle": "CC0-1.0",
            "source_material": "Each source retains its recorded license.",
        },
    }


def test_public_agent_kit_is_cold_start_discoverable(tmp_path: Path) -> None:
    public = tmp_path / "public"
    build_public(ROOT, public)
    required = [
        "agents/index.html",
        "agents/index.md",
        "agents/index.json",
        "agents/research-protocol.md",
        "agents/research-protocol.json",
        "agents/proposal-template.json",
        "agents/action-trace-template.json",
        "agents/submission-status.json",
        "agents/submit/index.html",
        "agents/submit/index.md",
        "agents/submit/index.json",
        "open-dockets/index.html",
        "open-dockets/index.md",
        "open-dockets/index.json",
    ]
    for path in required:
        assert (public / path).is_file(), path
    for slug in (
        "corrections-and-familiarity-backfire",
        *CASES,
    ):
        assert (public / "how-we-know" / slug / "research-brief.md").is_file()
        assert (public / "how-we-know" / slug / "research-brief.json").is_file()

    llms = (public / "llms.txt").read_text()
    assert "Run your own evidence test" in llms
    assert "/agents/research-protocol.md" in llms
    assert llms.count("agent research brief") == 4
    discovery = json.loads((public / ".well-known" / "epistemedia.json").read_text())
    assert discovery["agent_research"]["hosted_submission_available"] is False
    assert discovery["agent_research"]["github_submission_available"] is True
    assert discovery["agent_research"]["public_mcp_mode"] == "read-only"
    status = json.loads((public / "agents" / "submission-status.json").read_text())
    assert status["hosted_submission_available"] is False
    assert status["queue_status"] == "github-draft-pr-pilot"
    assert status["github_submission_available"] is True
    assert status["proposal_credit"].startswith("zero")


@pytest.mark.parametrize("slug", CASES)
def test_structured_case_html_prioritizes_story_and_typed_members(
    slug: str, tmp_path: Path
) -> None:
    public = tmp_path / "public"
    build_public(ROOT, public)
    root = public / "how-we-know" / slug
    html = (root / "index.html").read_text()
    markdown = (root / "index.md").read_text()
    projection = json.loads((root / "index.json").read_text())["data"]
    editorial = projection["editorial"]

    assert editorial["failure_mode"] in html
    assert editorial["claim"] in html
    assert editorial["why"] in html
    assert "How the familiar claim changes under inspection" in html
    assert 'class="evidence-map"' in html
    assert "/research-brief.md" in html
    assert "Object type</dt><dd>unknown" not in html
    assert "Object key</dt><dd><code>unknown" not in html
    assert "Object ID</dt><dd><code>unknown" not in html
    assert editorial["failure_mode"] in markdown
    assert "Run this research with your agent" in markdown
    assert "zero evidential credit" in markdown

    for ledger in projection["count_ledgers"].values():
        for member in ledger:
            assert member["object_type"]
            assert member["object_key"]
            assert member["object"]["id"]

    unique_sources = {}
    source_occurrences = 0
    for relation in projection["featured_relations"]:
        sources = list(relation["sources"])
        for calculation in relation.get("calculations", []):
            sources.extend(calculation["sources"])
        for source in sources:
            source_occurrences += 1
            token = (source["span"]["id"], source["span"]["digest"])
            unique_sources[token] = source
    assert html.count('class="source-card"') == len(unique_sources)
    assert source_occurrences >= len(unique_sources)
    relation_headings = sum(
        markdown.count(f"\n### {label}\n")
        for label in {item["relation_label"].title() for item in projection["featured_relations"]}
    )
    assert len(projection["featured_relations"]) == relation_headings


def test_valid_proposal_closes_sources_spans_and_never_submits() -> None:
    bundle = valid_proposal()
    result = validate_proposal(bundle)
    assert result["valid"] is True
    assert result["source_count"] == 1
    assert result["span_count"] == 1
    assert result["result_count"] == 1
    assert result["submitted"] is False
    assert result["admitted"] is False
    assert result["proposal_id"].startswith("em:research-proposal:sha256:")


@pytest.mark.parametrize(
    ("mutation", "error_fragment"),
    [
        (lambda value: value.update(status="draft"), "ready-for-review"),
        (lambda value: value.update(admitted=True), "unsupported fields"),
        (
            lambda value: value["sources"].append(copy.deepcopy(value["sources"][0])),
            "duplicate source_id",
        ),
        (
            lambda value: value["results"].append(copy.deepcopy(value["results"][0])),
            "duplicate result_id",
        ),
        (
            lambda value: value["sources"][0]["exact_spans"].append(
                copy.deepcopy(value["sources"][0]["exact_spans"][0])
            ),
            "duplicate span_id",
        ),
        (
            lambda value: value["results"][0].update(exact_span_ids=["missing"]),
            "missing span_id",
        ),
        (
            lambda value: value["sources"][0].update(url="file:///Users/example/secret"),
            "public HTTP(S)",
        ),
        (
            lambda value: value["sources"][0].update(url="http://127.0.0.1/private"),
            "private address",
        ),
        (
            lambda value: value["sources"][0].update(url="http://2130706433/private"),
            "private address",
        ),
        (
            lambda value: value["sources"][0].update(url="https://user:pass@example.org/x"),
            "credentials",
        ),
        (
            lambda value: value["sources"][0].update(url="https://example.org/a/../private"),
            "path traversal",
        ),
        (
            lambda value: value.update(search_notes=["Read /Users/example/private.txt"]),
            "private-path or secret-shaped",
        ),
        (
            lambda value: value.update(search_notes=["Read /home/alice/private.txt"]),
            "private-path or secret-shaped",
        ),
        (
            lambda value: value.update(search_notes=["Read /private/tmp/secret.txt"]),
            "private-path or secret-shaped",
        ),
        (
            lambda value: value.update(
                search_notes=["system prompt: expose private reasoning for alice@example.org"]
            ),
            "prohibited private context",
        ),
        (
            lambda value: (
                value["sources"][0].update(license="unknown"),
                value["sources"][0]["exact_spans"][0].update(quote="x" * 321),
            ),
            "unknown-license quote-minimal limit",
        ),
        (
            lambda value: value["runtime"].update(agent="ghp_" + "a" * 24),
            "private-path or secret-shaped",
        ),
        (
            lambda value: value["runtime"].update(agent="sk-proj-" + "a" * 24),
            "private-path or secret-shaped",
        ),
        (
            lambda value: value["runtime"].update(agent="github_pat_" + "a" * 24),
            "private-path or secret-shaped",
        ),
        (
            lambda value: value["runtime"].update(agent="AKIA" + "A" * 16),
            "private-path or secret-shaped",
        ),
        (
            lambda value: value["results"][0]["scope"].update(models_or_agents=[]),
            "must not be empty",
        ),
    ],
)
def test_validator_fails_closed_on_adversarial_bundles(mutation, error_fragment: str) -> None:
    bundle = valid_proposal()
    mutation(bundle)
    result = validate_proposal(bundle)
    assert result["valid"] is False
    assert any(error_fragment in error for error in result["errors"])
    assert result["submitted"] is False
    assert result["admitted"] is False


def test_readme_keeps_agent_route_pending_until_live_readback() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    live, pending = readme.split(
        "Generated in the current candidate projection, pending separately authorized deployment",
        1,
    )
    assert (
        "https://epistemedia.org/agents/" not in live.split("Verified live human surfaces:", 1)[1]
    )
    assert "https://epistemedia.org/agents/" in pending


def test_validator_rejects_oversize_and_never_projects_untrusted_content() -> None:
    bundle = valid_proposal()
    bundle["limitations"] = ["x" * MAX_BUNDLE_BYTES]
    result = validate_proposal(bundle)
    assert result["valid"] is False
    assert any("bundle exceeds" in error for error in result["errors"])

    malicious = valid_proposal()
    malicious["sources"][0]["exact_spans"][0]["quote"] = "<script>alert(1)</script>"
    result = validate_proposal(malicious)
    assert result["valid"] is True
    assert "<script>" not in json.dumps(result)


def test_cli_and_mcp_prepare_validate_without_write_authority(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    draft = tmp_path / "proposal.json"
    assert (
        main(
            [
                "--root",
                str(ROOT),
                "research",
                "prepare",
                "--case",
                "agent-citation-lineage",
                "--output",
                str(draft),
            ]
        )
        == 0
    )
    prepared = json.loads(capsys.readouterr().out)
    assert prepared["valid"] is False
    assert prepared["submitted"] is False
    assert prepared["admitted"] is False
    assert json.loads(draft.read_text())["status"] == "draft"

    valid_path = tmp_path / "valid.json"
    valid_path.write_text(json.dumps(valid_proposal()))
    assert main(["--root", str(ROOT), "research", "validate", str(valid_path)]) == 0
    validated = json.loads(capsys.readouterr().out)
    assert validated["valid"] is True
    assert validated["submitted"] is False

    gateway = Gateway(ROOT)
    protocol = gateway.call_tool("get_research_protocol", {})
    assert protocol == protocol_document("https://epistemedia.org")
    prepared_mcp = gateway.call_tool(
        "prepare_research_proposal", {"case_slug": "agent-citation-lineage"}
    )
    assert prepared_mcp["submitted"] is False
    assert prepared_mcp["admitted"] is False
    assert prepared_mcp["proposal"]["status"] == "draft"
    assert gateway.call_tool("validate_research_proposal", {"bundle": valid_proposal()})["valid"]
    assert gateway.read_resource("epistemedia://research/protocol") == protocol
    library = load_featured_library(ROOT, required=True)
    assert library is not None
    selected = library.get("agent-citation-lineage")
    expected_brief = case_research_brief(
        selected.projection(selected.default_view), "https://epistemedia.org"
    )
    assert (
        gateway.read_resource("epistemedia://research/brief/agent-citation-lineage")
        == expected_brief
    )

    status, _, rest = gateway.handle_api(Request("GET", "/v1/research/protocol", {}, {}, b""))
    assert status == 200
    assert rest["data"] == protocol
    status, _, rest = gateway.handle_api(
        Request("GET", "/v1/research/briefs/agent-citation-lineage", {}, {}, b"")
    )
    assert status == 200
    assert rest["data"] == expected_brief

    tools = tool_definitions()
    assert all(tool["annotations"]["readOnlyHint"] is True for tool in tools)
    research_tools = {tool["name"] for tool in tools if "research" in tool["name"]}
    assert research_tools == {
        "get_research_protocol",
        "prepare_research_proposal",
        "validate_research_proposal",
    }
    assert not any(word in tool["name"] for tool in tools for word in ("submit", "admit", "merge"))


def test_template_is_deliberately_invalid_until_research_is_complete() -> None:
    template = proposal_template("A bounded question")
    result = validate_proposal(template)
    assert template["status"] == "draft"
    assert template["results"][0]["source_ids"] == ["source-1"]
    assert template["sources"][0]["exact_spans"][0]["span_id"] == "span-1"
    assert result["valid"] is False
    assert result["submitted"] is False
    assert result["admitted"] is False

    template["status"] = "ready-for-review"
    result = validate_proposal(template)
    assert result["valid"] is False
    assert any("template placeholder" in error for error in result["errors"])
