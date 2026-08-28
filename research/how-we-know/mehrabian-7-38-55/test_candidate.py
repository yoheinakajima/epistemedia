"""Adversarial tests for the EM-0035 Case 004 candidate and review gate."""

from __future__ import annotations

import copy

import pytest
from build_candidate import PACKET_PATH, build_candidate
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
    assert summary["accepted_relation_counts"]["participant_data_roots"] == 5
    assert summary["dossier_counts"]["evaluations"] == 2


def test_collapsing_the_two_1967_participant_roots_fails_closed() -> None:
    candidate = build_candidate()
    p2 = next(item for item in candidate["lineages"] if item["key"] == "lineage-participant-p2")
    p2["depends_on"] = ["lineage-participant-p1"]
    forged = restamp(candidate)
    with pytest.raises(VerificationError, match="five participant-data roots"):
        verify_candidate_document(forged, packet(), require_exact_build=False)


def test_promoting_the_missing_seven_percent_origin_fails_closed() -> None:
    candidate = build_candidate()
    lineage = next(
        item for item in candidate["lineages"] if item["key"] == "lineage-seven-origin-unknown"
    )
    lineage["status"] = "known"
    forged = restamp(candidate)
    with pytest.raises(VerificationError, match=r"missing \.07 derivation"):
        verify_candidate_document(forged, packet(), require_exact_build=False)


def test_incomplete_typed_lineage_evidence_fails_closed() -> None:
    candidate = build_candidate()
    edge = next(
        item for item in candidate["evidence_relations"] if item["key"] == "edge-p1-p2-material"
    )
    edge["basis_span_keys"].pop()
    forged = restamp(candidate)
    with pytest.raises(VerificationError, match="evidence-span closure"):
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
    packet_document = packet()
    summary = verify_candidate_document(candidate, packet_document, require_exact_build=True)
    summary["candidate_documentation"] = verify_candidate_documentation(summary)
    run_adversarial_self_test(candidate, packet_document, summary)
