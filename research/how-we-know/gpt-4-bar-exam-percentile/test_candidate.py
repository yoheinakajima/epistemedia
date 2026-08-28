"""Adversarial tests for the EM-0034 Case 003 candidate and review gate."""

from __future__ import annotations

import copy

import pytest
from build_candidate import (
    PACKET_PATH,
    build_candidate,
    canonical_json,
    digest,
    sha256_bytes,
)
from verify_candidate import (
    VerificationError,
    load,
    run_adversarial_self_test,
    verify_candidate_document,
    verify_candidate_documentation,
)

from epistemedia.dossier import COLLECTIONS, stamp_dossier


def restamp(dossier: dict) -> dict:
    material = copy.deepcopy(dossier)
    material.pop("dossier_id")
    for collection in COLLECTIONS:
        for record in material[collection]:
            record.pop("id")
    return stamp_dossier(material)


def packet() -> dict:
    return load(PACKET_PATH)


def test_deterministic_candidate_passes_exact_semantic_validation() -> None:
    candidate = build_candidate()
    summary = verify_candidate_document(candidate, packet(), require_exact_build=True)
    assert summary["counts"]["independent_roots"] == 7
    assert summary["counts"]["evaluations"] == 2


def test_documents_cannot_inflate_the_model_performance_root() -> None:
    candidate = build_candidate()
    model = next(
        item for item in candidate["lineages"] if item["key"] == "lineage-model-performance-root"
    )
    model["note"] = model["note"].replace("independent_roots=1", "independent_roots=2")
    forged = restamp(candidate)
    with pytest.raises(VerificationError, match="projected independent-root count drift"):
        verify_candidate_document(forged, packet(), require_exact_build=False)


def test_score_discrepancy_cannot_be_erased() -> None:
    candidate = build_candidate()
    proposition = next(
        item for item in candidate["propositions"] if item["key"] == "claim-score-discrepancy"
    )
    proposition["text"] = "The report and study describe the same score."
    forged = restamp(candidate)
    with pytest.raises(VerificationError, match="297/298 discrepancy"):
        verify_candidate_document(forged, packet(), require_exact_build=False)


def test_martinez_internal_discrepancy_cannot_be_erased() -> None:
    candidate = build_candidate()
    proposition = next(
        item
        for item in candidate["propositions"]
        if item["key"] == "claim-martinez-passers-conflict"
    )
    proposition["text"] = proposition["text"].replace("45/48", "48")
    forged = restamp(candidate)
    with pytest.raises(VerificationError, match="45/48 discrepancy"):
        verify_candidate_document(forged, packet(), require_exact_build=False)


def test_incomplete_typed_lineage_evidence_fails_closed() -> None:
    candidate = build_candidate()
    edge = next(
        item
        for item in candidate["evidence_relations"]
        if item["key"] == "edge-benchmark-illinois-charts"
    )
    edge["basis_span_keys"].pop()
    forged = restamp(candidate)
    with pytest.raises(VerificationError, match="typed edge evidence drift"):
        verify_candidate_document(forged, packet(), require_exact_build=False)


def test_calculation_record_cannot_drop_exact_input_cells() -> None:
    candidate = build_candidate()
    span = next(
        item
        for item in candidate["spans"]
        if item["key"] == "span-calculation-derive-martinez-parameters"
    )
    span["extent"]["value"]["resolved_input_cells"].pop()
    span["digest"] = digest(span["extent"]["value"])
    edition = next(
        item
        for item in candidate["editions"]
        if item["key"] == "edition-em0032-calculation-register"
    )
    encoded = canonical_json(edition["content"])
    edition["content_digest"] = "sha256:" + sha256_bytes(encoded)
    edition["content_length"] = len(encoded)
    forged = restamp(candidate)
    with pytest.raises(VerificationError, match="input-cell closure drift"):
        verify_candidate_document(forged, packet(), require_exact_build=False)


def test_multi_source_typed_edge_cannot_drop_new_york_endpoint() -> None:
    candidate = build_candidate()
    relation = next(
        item
        for item in candidate["evidence_relations"]
        if item["key"] == "edge-comparison-class-first-time-passers--2"
    )
    relation["from_ref"] = "lineage-ncbe-comparison-root"
    forged = restamp(candidate)
    with pytest.raises(VerificationError, match="typed edge endpoint drift"):
        verify_candidate_document(forged, packet(), require_exact_build=False)


def test_collapsing_policy_views_fails_closed() -> None:
    candidate = build_candidate()
    evaluations = {item["policy_id"]: item for item in candidate["evaluations"]}
    encyclopedia = evaluations["epistemedia-encyclopedia-v1"]
    skeptical = evaluations["epistemedia-skeptical-v1"]
    skeptical["label"] = encyclopedia["label"]
    skeptical["reason_codes"] = encyclopedia["reason_codes"]
    forged = restamp(candidate)
    with pytest.raises(VerificationError, match="not materially distinct"):
        verify_candidate_document(forged, packet(), require_exact_build=False)


def test_review_receipt_adversarial_suite_rejects_all_mutations() -> None:
    candidate = build_candidate()
    summary = verify_candidate_document(candidate, packet(), require_exact_build=True)
    summary["candidate_documentation"] = verify_candidate_documentation(summary)
    run_adversarial_self_test(summary)
