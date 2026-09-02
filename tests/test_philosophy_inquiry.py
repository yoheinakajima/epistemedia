from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from epistemedia.core import canonical_json
from epistemedia.philosophy_inquiry import (
    PhilosophyInquiryValidationError,
    assert_public_noninterference,
    compare_branches,
    import_bundles,
    private_projection,
    public_projection,
    read_adapter,
    render_twins,
    stamp_bundle,
    trace_manuscript_claim,
    validate_bundle,
)

FIXTURE = Path(__file__).parent / "fixtures" / "philosophy-inquiry" / "lighthouse.json"


@pytest.fixture
def bundle():
    return stamp_bundle(json.loads(FIXTURE.read_text(encoding="utf-8")))


def test_fictional_bundle_validates_and_is_content_addressed(bundle):
    validate_bundle(bundle)
    assert bundle["bundle_id"].startswith("em:philosophy-inquiry-bundle:")


def test_reordered_and_duplicate_imports_collapse(bundle):
    reordered = copy.deepcopy(bundle)
    reordered["nodes"].reverse()
    reordered["relations"].reverse()
    receipt = import_bundles([bundle, reordered, bundle])
    assert len(receipt["bundles"]) == 1


def test_unknown_reference_fails_closed(bundle):
    bundle["relations"][0]["target"] = "missing"
    with pytest.raises(PhilosophyInquiryValidationError, match="referentially closed"):
        validate_bundle(bundle)


def test_source_span_hash_mismatch_fails_closed(bundle):
    span = next(item for item in bundle["nodes"] if item["kind"] == "source_span")
    span["exact_text"] += " altered"
    with pytest.raises(PhilosophyInquiryValidationError, match="source span hash"):
        validate_bundle(bundle)


@pytest.mark.parametrize("field", ["truth", "confidence", "quality"])
def test_intrinsic_claim_fields_are_forbidden(bundle, field):
    proposition = next(item for item in bundle["nodes"] if item["kind"] == "proposition")
    proposition[field] = True
    with pytest.raises(PhilosophyInquiryValidationError, match="intrinsic field"):
        validate_bundle(bundle)


def test_inferential_and_evidential_support_cannot_be_collapsed(bundle):
    bundle["relations"][0]["semantic_class"] = "evidential"
    with pytest.raises(PhilosophyInquiryValidationError, match="collapsed"):
        validate_bundle(bundle)


def test_policy_relative_evaluation_requires_frontier(bundle):
    bundle["evaluations"][0]["frontier"] = ""
    with pytest.raises(PhilosophyInquiryValidationError, match="policy and frontier"):
        validate_bundle(bundle)


def test_private_projection_contains_traceable_state(bundle):
    projection = private_projection(bundle)
    assert projection["source_spans"] == 1
    assert projection["branch_count"] == 2
    trace = trace_manuscript_claim(bundle, "node-manuscript")
    assert {item["id"] for item in trace["sources_and_premises"]} == {
        "node-span",
        "node-proposition",
    }
    assert trace["inclusion_decision"]


def test_branch_comparison_is_semantic(bundle):
    diff = compare_branches(bundle["branches"][0], bundle["branches"][1])
    assert diff["concessions"]["added"] == ["color-neutral cases"]
    assert diff["scope_changes"]["added"] == ["violet lenses only"]
    assert diff["manuscript_consequences"]["added"] == ["state the lens restriction"]


def test_markdown_and_json_twins_derive_from_same_projection(bundle):
    projection = private_projection(bundle)
    markdown, json_text = render_twins(projection)
    assert projection["bundle_id"] in markdown
    assert json.loads(json_text) == projection


def test_read_adapter_returns_one_projection(bundle):
    projection = private_projection(bundle)
    assert read_adapter(projection, "candidate-funnel") == 1
    assert read_adapter(projection, "branches") == bundle["branches"]


def test_public_projection_is_constant_under_private_mutation(bundle):
    other = copy.deepcopy(bundle)
    other["nodes"].append(
        {
            "id": "node-secret",
            "kind": "candidate_thesis",
            "text": "secret",
            "visibility": "private",
        }
    )
    other = stamp_bundle(other)
    assert_public_noninterference(bundle, other)
    first = public_projection(bundle)
    second = public_projection(other)
    assert canonical_json(first) == canonical_json(second)
    assert "candidate_funnel" not in first


def test_public_state_requires_human_release_approval(bundle):
    bundle["release_state"] = "public"
    bundle = stamp_bundle(bundle)
    with pytest.raises(PermissionError, match="explicit human"):
        public_projection(bundle)


def test_unknown_fields_fail_closed(bundle):
    bundle["private_note"] = "not part of profile"
    with pytest.raises(PhilosophyInquiryValidationError, match="fields"):
        validate_bundle(bundle)
