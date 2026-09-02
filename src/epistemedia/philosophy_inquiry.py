"""Reversible, non-normative philosophy inquiry application profile.

The profile is intentionally separate from protocol schemas and accepted knowledge. It
validates a portable argument/source bundle, renders deterministic read models, and
keeps the pre-release public projection constant under arbitrary private mutation.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Iterable
from typing import Any

from .core import canonical_json, stable_id

FORMAT = "epistemedia-philosophy-inquiry-v0.1"
ROOT_FIELDS = {
    "format",
    "bundle_id",
    "release_state",
    "nodes",
    "assertions",
    "relations",
    "branches",
    "evaluations",
    "interventions",
}
KINDS = {
    "source_work",
    "source_snapshot",
    "source_span",
    "proposition",
    "premise_role",
    "conclusion_role",
    "derivation",
    "observation",
    "thought_experiment_judgment",
    "model_run",
    "exposure_record",
    "manuscript_claim",
    "candidate_thesis",
}
RELATION_CLASSES = {"inferential", "evidential", "dialectical", "provenance", "structural"}
FORBIDDEN_FIELDS = {
    "truth",
    "truth_value",
    "global_truth",
    "confidence",
    "claim_confidence",
    "quality",
}
RELEASE_STATES = {
    "private",
    "sealed",
    "submitted",
    "finalists-announced",
    "results-announced",
    "release-approved",
    "public",
}
PUBLIC_PROFILE = {
    "format": "epistemedia-philosophy-public-v0.1",
    "status": "generic-profile-only",
    "fixture": "fictional-lighthouse-dispute",
    "capabilities": [
        "validate referential closure and source-span hashes",
        "distinguish propositions, assertions, premise roles, and evidence",
        "trace manuscript claims through sources, branches, and inclusion decisions",
        "compare branches and policy-relative evaluations",
        "render deterministic Markdown and JSON twins",
    ],
    "private_state_included": False,
}


class PhilosophyInquiryValidationError(ValueError):
    """Raised when an application bundle fails closed."""


def _sha256(text: str) -> str:
    import hashlib

    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _identity_payload(bundle: dict[str, Any]) -> dict[str, Any]:
    value = {key: copy.deepcopy(item) for key, item in bundle.items() if key != "bundle_id"}
    for name in ("nodes", "assertions", "relations", "branches", "evaluations", "interventions"):
        value[name] = sorted(value[name], key=lambda item: item["id"])
    return value


def bundle_id(bundle: dict[str, Any]) -> str:
    return stable_id("philosophy-inquiry-bundle", _identity_payload(bundle))


def stamp_bundle(material: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(material)
    value["bundle_id"] = bundle_id(value)
    validate_bundle(value)
    return value


def validate_bundle(bundle: dict[str, Any]) -> None:
    if not isinstance(bundle, dict) or set(bundle) != ROOT_FIELDS:
        raise PhilosophyInquiryValidationError("bundle fields do not match the v0.1 profile")
    if bundle["format"] != FORMAT:
        raise PhilosophyInquiryValidationError("unknown bundle format")
    if bundle["release_state"] not in RELEASE_STATES:
        raise PhilosophyInquiryValidationError("unknown release state")
    _scan_forbidden(bundle)
    collections = ("nodes", "assertions", "relations", "branches", "evaluations", "interventions")
    if any(not isinstance(bundle[name], list) for name in collections):
        raise PhilosophyInquiryValidationError("profile collections must be arrays")
    all_items = [item for name in collections for item in bundle[name]]
    if any(not isinstance(item, dict) or not isinstance(item.get("id"), str) for item in all_items):
        raise PhilosophyInquiryValidationError("every record requires a string id")
    ids = [item["id"] for item in all_items]
    if len(ids) != len(set(ids)):
        raise PhilosophyInquiryValidationError("duplicate record identity")
    node_ids = {item["id"] for item in bundle["nodes"]}
    assertion_ids = {item["id"] for item in bundle["assertions"]}
    for node in bundle["nodes"]:
        if node.get("kind") not in KINDS:
            raise PhilosophyInquiryValidationError(f"unknown node kind: {node.get('kind')}")
        if node["kind"] == "source_span":
            if node.get("text_sha256") != _sha256(node.get("exact_text", "")):
                raise PhilosophyInquiryValidationError("source span hash mismatch")
            if node.get("snapshot_id") not in node_ids:
                raise PhilosophyInquiryValidationError("source span has an unknown snapshot")
    for assertion in bundle["assertions"]:
        if assertion.get("proposition_id") not in node_ids:
            raise PhilosophyInquiryValidationError("assertion has an unknown proposition")
    allowed = node_ids | assertion_ids
    for relation in bundle["relations"]:
        if relation.get("source") not in allowed or relation.get("target") not in allowed:
            raise PhilosophyInquiryValidationError("relation is not referentially closed")
        if relation.get("semantic_class") not in RELATION_CLASSES:
            raise PhilosophyInquiryValidationError("unknown relation semantic class")
        relation_type = relation.get("relation_type")
        semantic_class = relation.get("semantic_class")
        if (
            relation_type in {"premise_in", "inferentially_supports"}
            and semantic_class != "inferential"
        ):
            raise PhilosophyInquiryValidationError(
                "inferential support was collapsed into evidence"
            )
        if (
            relation_type in {"textually_supported_by", "evidentially_supports"}
            and semantic_class != "evidential"
        ):
            raise PhilosophyInquiryValidationError("textual support was collapsed into inference")
    for evaluation in bundle["evaluations"]:
        if evaluation.get("subject_id") not in allowed:
            raise PhilosophyInquiryValidationError("evaluation has an unknown subject")
        if not evaluation.get("policy_id") or not evaluation.get("frontier"):
            raise PhilosophyInquiryValidationError("evaluation requires policy and frontier")
    if bundle["bundle_id"] != bundle_id(bundle):
        raise PhilosophyInquiryValidationError("bundle content identity mismatch")


def _scan_forbidden(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower().replace("-", "_") in FORBIDDEN_FIELDS:
                raise PhilosophyInquiryValidationError(f"intrinsic field {key!r} is forbidden")
            _scan_forbidden(child)
    elif isinstance(value, list):
        for child in value:
            _scan_forbidden(child)


def import_bundles(bundles: Iterable[dict[str, Any]]) -> dict[str, Any]:
    by_id = {}
    for incoming in bundles:
        validate_bundle(incoming)
        normalized = copy.deepcopy(incoming)
        for name in (
            "nodes",
            "assertions",
            "relations",
            "branches",
            "evaluations",
            "interventions",
        ):
            normalized[name] = sorted(normalized[name], key=lambda item: item["id"])
        prior = by_id.get(normalized["bundle_id"])
        if prior is not None and canonical_json(prior) != canonical_json(normalized):
            raise PhilosophyInquiryValidationError("conflicting records reused one bundle identity")
        by_id[normalized["bundle_id"]] = normalized
    result = {
        "format": "epistemedia-philosophy-import-v0.1",
        "bundles": [by_id[key] for key in sorted(by_id)],
    }
    result["import_id"] = stable_id("philosophy-inquiry-import", result)
    return result


def private_projection(bundle: dict[str, Any]) -> dict[str, Any]:
    validate_bundle(bundle)
    return {
        "format": "epistemedia-philosophy-private-projection-v0.1",
        "bundle_id": bundle["bundle_id"],
        "visibility": "private",
        "candidate_funnel": _count(bundle["nodes"], "candidate_thesis"),
        "source_spans": _count(bundle["nodes"], "source_span"),
        "branch_count": len(bundle["branches"]),
        "evaluation_count": len(bundle["evaluations"]),
        "bundle": copy.deepcopy(bundle),
    }


def public_projection(
    bundle: dict[str, Any], *, human_release_approval: bool = False
) -> dict[str, Any]:
    validate_bundle(bundle)
    if bundle["release_state"] == "public":
        if not human_release_approval:
            raise PermissionError("public projection requires explicit human release approval")
        raise NotImplementedError(
            "argument publication is deliberately outside this generic profile"
        )
    result = copy.deepcopy(PUBLIC_PROFILE)
    result["projection_id"] = stable_id("philosophy-public-profile", PUBLIC_PROFILE)
    return result


def assert_public_noninterference(first: dict[str, Any], second: dict[str, Any]) -> None:
    if canonical_json(public_projection(first)) != canonical_json(public_projection(second)):
        raise AssertionError("private mutation changed a pre-release public surface")


def compare_branches(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    dimensions = (
        "claims",
        "premise_roles",
        "inference_edges",
        "concessions",
        "scope_changes",
        "sources",
        "objections",
        "replies",
        "manuscript_consequences",
    )
    return {
        "left": left["id"],
        "right": right["id"],
        **{
            name: {
                "added": sorted(set(right.get(name, [])) - set(left.get(name, []))),
                "removed": sorted(set(left.get(name, [])) - set(right.get(name, []))),
            }
            for name in dimensions
        },
    }


def trace_manuscript_claim(bundle: dict[str, Any], claim_id: str) -> dict[str, Any]:
    validate_bundle(bundle)
    claim = next((item for item in bundle["nodes"] if item["id"] == claim_id), None)
    if claim is None or claim["kind"] != "manuscript_claim":
        raise KeyError(claim_id)
    references = set(claim.get("source_span_ids", [])) | set(claim.get("premise_ids", []))
    return {
        "claim": claim,
        "sources_and_premises": [item for item in bundle["nodes"] if item["id"] in references],
        "branches": [
            item
            for item in bundle["branches"]
            if item["id"] in claim.get("branch_ids", [])
        ],
        "model_runs": [
            item
            for item in bundle["nodes"]
            if item["id"] in claim.get("model_run_ids", [])
        ],
        "inclusion_decision": claim.get("inclusion_decision"),
    }


def render_twins(projection: dict[str, Any]) -> tuple[str, str]:
    json_text = json.dumps(projection, indent=2, sort_keys=True) + "\n"
    if projection["format"] == "epistemedia-philosophy-public-v0.1":
        lines = ["# Philosophy inquiry profile", "", "Generic fictional capabilities:", ""]
        lines.extend(f"- {item}" for item in projection["capabilities"])
    else:
        lines = [
            "# Private philosophy inquiry dossier",
            "",
            f"Bundle: `{projection['bundle_id']}`",
            "",
            f"Candidate funnel records: {projection['candidate_funnel']}",
            f"Source spans: {projection['source_spans']}",
            f"Branches: {projection['branch_count']}",
            f"Policy-relative evaluations: {projection['evaluation_count']}",
        ]
    return "\n".join(lines) + "\n", json_text


def read_adapter(projection: dict[str, Any], resource: str) -> Any:
    resources = {
        "overview": {key: projection.get(key) for key in ("format", "bundle_id", "visibility")},
        "candidate-funnel": projection.get("candidate_funnel", 0),
        "branches": projection.get("bundle", {}).get("branches", []),
        "evaluations": projection.get("bundle", {}).get("evaluations", []),
    }
    if resource not in resources:
        raise KeyError(resource)
    return copy.deepcopy(resources[resource])


def _count(nodes: list[dict[str, Any]], kind: str) -> int:
    return sum(1 for node in nodes if node.get("kind") == kind)
