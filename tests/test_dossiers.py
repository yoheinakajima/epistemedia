from __future__ import annotations

import hashlib
import json
from urllib.parse import quote

import pytest

from epistemedia.core import canonical_json
from epistemedia.dossier import (
    DOSSIER_FORMAT,
    DossierProjection,
    DossierValidationError,
    dossier_id,
    independence_summary,
    public_dossier,
    record_id,
    stamp_dossier,
    validate_dossier,
)


def exact_bytes(value: object) -> bytes:
    if isinstance(value, str):
        return value.encode("utf-8")
    return canonical_json(value).encode("utf-8")


def sha256(value: object) -> str:
    return "sha256:" + hashlib.sha256(exact_bytes(value)).hexdigest()


def edition(
    key: str,
    work_key: str,
    label: str,
    content: str | dict | list,
    *,
    visibility: str = "public",
) -> dict:
    raw = exact_bytes(content)
    return {
        "key": key,
        "work_key": work_key,
        "edition_label": label,
        "media_type": "text/plain" if isinstance(content, str) else "application/json",
        "retrieved_at": "2026-08-22T00:00:00Z",
        "content": content,
        "content_digest": sha256(content),
        "content_length": len(raw),
        "visibility": visibility,
    }


def text_span(
    key: str,
    edition_key: str,
    text: str,
    *,
    visibility: str = "public",
) -> dict:
    return {
        "key": key,
        "edition_key": edition_key,
        "locator": {
            "type": "text-offset",
            "start": 0,
            "end": len(text),
            "label": f"characters 0-{len(text)}",
        },
        "extent": {"type": "quote", "text": text},
        "digest": sha256(text),
        "visibility": visibility,
    }


def fixture_material() -> dict:
    origin_text = "Synthetic instrument output: value=10."
    copy_text = "Synthetic copy repeats value=10 and names the origin."
    unknown_text = "Synthetic unattributed summary repeats value=10."
    private_text = "Private fixture note; excluded from the public projection."
    relations = [
        {
            "key": "relation-support",
            "relation_type": "support",
            "from_ref": "span-origin",
            "to_ref": "proposition-value",
            "basis_span_keys": ["span-origin"],
            "note": "Synthetic structural support example only.",
            "visibility": "public",
        },
        {
            "key": "relation-rebuttal",
            "relation_type": "rebuttal",
            "from_ref": "assertion-copy",
            "to_ref": "assertion-origin",
            "basis_span_keys": ["span-copy"],
            "note": "Synthetic structural rebuttal example only.",
            "visibility": "public",
        },
        {
            "key": "relation-qualification",
            "relation_type": "qualification",
            "from_ref": "span-copy",
            "to_ref": "proposition-value",
            "basis_span_keys": ["span-copy"],
            "note": "Synthetic structural qualification example only.",
            "visibility": "public",
        },
        {
            "key": "relation-undercutting",
            "relation_type": "undercutting",
            "from_ref": "span-unknown",
            "to_ref": "assertion-unknown",
            "basis_span_keys": ["span-unknown"],
            "note": "Synthetic structural undercutting example only.",
            "visibility": "public",
        },
        {
            "key": "relation-replication",
            "relation_type": "replication",
            "from_ref": "assertion-copy",
            "to_ref": "assertion-origin",
            "basis_span_keys": ["span-copy"],
            "note": "Synthetic structural replication example only.",
            "visibility": "public",
        },
        {
            "key": "relation-failed-replication",
            "relation_type": "failed-replication",
            "from_ref": "assertion-unknown",
            "to_ref": "assertion-origin",
            "basis_span_keys": ["span-unknown"],
            "note": "Synthetic failed-replication shape; no empirical claim.",
            "visibility": "public",
        },
        {
            "key": "relation-dependence",
            "relation_type": "dependence",
            "from_ref": "lineage-copy",
            "to_ref": "lineage-origin",
            "basis_span_keys": ["span-copy"],
            "note": "The synthetic copy declares dependence on the synthetic origin.",
            "visibility": "public",
        },
    ]
    return {
        "format": DOSSIER_FORMAT,
        "title": "Synthetic lineage fixture",
        "question": (
            "Can copied and unknown support be represented without counting it as independent?"
        ),
        "scope": "Synthetic application validation only; no real-world conclusion.",
        "stage": "fixture",
        "visibility": "public",
        "source_works": [
            {
                "key": "work-origin",
                "kind": "instrument",
                "title": "Synthetic origin work",
                "creators": ["Epistemedia test suite"],
                "canonical_uri": "urn:epistemedia:fixture:origin",
                "license": "CC0-1.0",
                "visibility": "public",
            },
            {
                "key": "work-copy",
                "kind": "report",
                "title": "Synthetic copied report",
                "creators": ["Epistemedia test suite"],
                "canonical_uri": "urn:epistemedia:fixture:copy",
                "license": "CC0-1.0",
                "visibility": "public",
            },
            {
                "key": "work-unknown",
                "kind": "report",
                "title": "Synthetic unattributed report",
                "creators": ["Epistemedia test suite"],
                "canonical_uri": "urn:epistemedia:fixture:unknown",
                "license": "CC0-1.0",
                "visibility": "public",
            },
            {
                "key": "work-private",
                "kind": "other",
                "title": "Private synthetic note",
                "creators": ["Epistemedia test suite"],
                "canonical_uri": "urn:epistemedia:fixture:private",
                "license": "private-fixture",
                "visibility": "private",
            },
        ],
        "editions": [
            edition("edition-origin", "work-origin", "synthetic v1", origin_text),
            edition("edition-copy", "work-copy", "synthetic v1", copy_text),
            edition("edition-unknown", "work-unknown", "synthetic v1", unknown_text),
            edition(
                "edition-private",
                "work-private",
                "private synthetic v1",
                private_text,
                visibility="private",
            ),
        ],
        "spans": [
            text_span("span-origin", "edition-origin", origin_text),
            text_span("span-copy", "edition-copy", copy_text),
            text_span("span-unknown", "edition-unknown", unknown_text),
            text_span(
                "span-private",
                "edition-private",
                private_text,
                visibility="private",
            ),
        ],
        "propositions": [
            {
                "key": "proposition-value",
                "text": "The synthetic fixture represents the value 10.",
                "scope": "Synthetic fixture only.",
                "visibility": "public",
            }
        ],
        "lineages": [
            {
                "key": "lineage-origin",
                "status": "known",
                "dimensions": ["source"],
                "depends_on": [],
                "basis_span_keys": ["span-origin"],
                "assertion_keys": ["assertion-origin"],
                "note": "Known synthetic root lineage.",
                "visibility": "public",
            },
            {
                "key": "lineage-copy",
                "status": "known",
                "dimensions": ["source", "social"],
                "depends_on": ["lineage-origin"],
                "basis_span_keys": ["span-copy"],
                "assertion_keys": ["assertion-copy"],
                "note": "Known synthetic dependent lineage.",
                "visibility": "public",
            },
            {
                "key": "lineage-unknown",
                "status": "unknown",
                "dimensions": [],
                "depends_on": [],
                "basis_span_keys": ["span-unknown"],
                "assertion_keys": ["assertion-unknown"],
                "note": "Unknown lineage is explicit in the fixture.",
                "visibility": "public",
            },
            {
                "key": "lineage-private",
                "status": "known",
                "dimensions": ["source"],
                "depends_on": [],
                "basis_span_keys": ["span-private"],
                "assertion_keys": ["assertion-private"],
                "note": "Private synthetic lineage.",
                "visibility": "private",
            },
        ],
        "assertions": [
            {
                "key": "assertion-origin",
                "proposition_key": "proposition-value",
                "actor": {"id": "fixture-origin", "kind": "instrument"},
                "stance": "asserts",
                "span_keys": ["span-origin"],
                "lineage_key": "lineage-origin",
                "asserted_at": "2026-08-22T00:00:00Z",
                "visibility": "public",
            },
            {
                "key": "assertion-copy",
                "proposition_key": "proposition-value",
                "actor": {"id": "fixture-copy", "kind": "human"},
                "stance": "asserts",
                "span_keys": ["span-copy"],
                "lineage_key": "lineage-copy",
                "asserted_at": "2026-08-22T00:01:00Z",
                "visibility": "public",
            },
            {
                "key": "assertion-unknown",
                "proposition_key": "proposition-value",
                "actor": {"id": "fixture-unknown", "kind": "collective"},
                "stance": "questions",
                "span_keys": ["span-unknown"],
                "lineage_key": "lineage-unknown",
                "asserted_at": "2026-08-22T00:02:00Z",
                "visibility": "public",
            },
            {
                "key": "assertion-private",
                "proposition_key": "proposition-value",
                "actor": {"id": "fixture-private", "kind": "human"},
                "stance": "hypothesizes",
                "span_keys": ["span-private"],
                "lineage_key": "lineage-private",
                "asserted_at": "2026-08-22T00:03:00Z",
                "visibility": "private",
            },
        ],
        "evidence_relations": relations,
        "claim_families": [
            {
                "key": "family-value",
                "title": "Synthetic value family",
                "question": "How many independent lineages support the synthetic value?",
                "proposition_keys": ["proposition-value"],
                "assertion_keys": [
                    "assertion-origin",
                    "assertion-copy",
                    "assertion-unknown",
                ],
                "relation_keys": [relation["key"] for relation in relations],
                "visibility": "public",
            }
        ],
        "evaluations": [
            {
                "key": "evaluation-fixture",
                "claim_family_key": "family-value",
                "policy_id": "fixture-policy-v0",
                "frontier": "fixture-frontier-v0",
                "label": "Fixture only; no empirical assessment.",
                "reason_codes": ["fixture-only"],
                "visibility": "public",
            }
        ],
    }


def test_strict_dossier_is_content_addressed_and_separates_object_layers() -> None:
    dossier = stamp_dossier(fixture_material())
    validate_dossier(dossier)
    assert dossier["dossier_id"] == dossier_id(dossier)
    ids: set[str] = set()
    for collection in (
        "source_works",
        "editions",
        "spans",
        "propositions",
        "lineages",
        "assertions",
        "evidence_relations",
        "claim_families",
        "evaluations",
    ):
        for record in dossier[collection]:
            assert record["id"] == record_id(collection, record)
            assert record["id"] not in ids
            ids.add(record["id"])
    assert dossier["source_works"][0]["id"] != dossier["editions"][0]["id"]
    assert "policy_id" not in dossier["propositions"][0]
    assert dossier["evaluations"][0]["claim_family_key"] == "family-value"


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda material: material["spans"][0]["locator"].update({"end": 10_000}),
            "out of bounds",
        ),
        (
            lambda material: material["spans"][0]["extent"].update({"text": "wrong"}),
            "does not match edition text",
        ),
        (
            lambda material: material["spans"][0].update({"digest": "sha256:" + "0" * 64}),
            "does not match exact extent",
        ),
        (
            lambda material: material["editions"][0].update(
                {"content_digest": "sha256:" + "0" * 64}
            ),
            "does not match edition content",
        ),
    ],
)
def test_invalid_edition_or_span_fails_closed(mutation, message: str) -> None:
    material = fixture_material()
    mutation(material)
    with pytest.raises(DossierValidationError, match=message):
        stamp_dossier(material)


def test_structured_span_verifies_json_pointer_value_and_digest() -> None:
    material = fixture_material()
    content = {"rows": [{"value": 10}]}
    material["editions"][0] = edition(
        "edition-origin", "work-origin", "synthetic structured v1", content
    )
    material["spans"][0] = {
        "key": "span-origin",
        "edition_key": "edition-origin",
        "locator": {
            "type": "json-pointer",
            "pointer": "/rows/0/value",
            "label": "row 0, value",
        },
        "extent": {"type": "json-value", "value": 10},
        "digest": sha256(10),
        "visibility": "public",
    }
    validate_dossier(stamp_dossier(material))

    material["spans"][0]["locator"]["pointer"] = "/rows/00/value"
    with pytest.raises(DossierValidationError, match="does not resolve"):
        stamp_dossier(material)


def test_nonfinite_content_typed_relations_and_private_root_fail_closed() -> None:
    nonfinite = fixture_material()
    nonfinite["editions"][0] = edition(
        "edition-origin",
        "work-origin",
        "invalid structured v1",
        {"value": float("nan")},
    )
    with pytest.raises(DossierValidationError, match="NaN or infinity"):
        stamp_dossier(nonfinite)

    mistyped = fixture_material()
    mistyped["evidence_relations"][0]["from_ref"] = "work-origin"
    with pytest.raises(DossierValidationError, match="span/assertion source"):
        stamp_dossier(mistyped)

    private_root = fixture_material()
    private_root["visibility"] = "private"
    dossier = stamp_dossier(private_root)
    with pytest.raises(DossierValidationError, match="private dossier root"):
        public_dossier(dossier)


def test_dangling_relation_and_public_to_private_dependency_fail_closed() -> None:
    dangling = fixture_material()
    dangling["evidence_relations"][0]["from_ref"] = "missing-record"
    with pytest.raises(DossierValidationError, match="unknown reference"):
        stamp_dossier(dangling)

    malformed_lineage = fixture_material()
    malformed_lineage["lineages"][1]["depends_on"] = ["lineage-missing"]
    with pytest.raises(DossierValidationError, match="unknown reference"):
        stamp_dossier(malformed_lineage)

    disclosure_leak = fixture_material()
    disclosure_leak["assertions"][0]["span_keys"] = ["span-private"]
    dossier = stamp_dossier(disclosure_leak)
    with pytest.raises(DossierValidationError, match="not referentially closed"):
        public_dossier(dossier)


def test_duplicate_ids_forbidden_fields_and_dependence_cycles_fail_closed() -> None:
    dossier = stamp_dossier(fixture_material())
    dossier["source_works"][1]["id"] = dossier["source_works"][0]["id"]
    with pytest.raises(DossierValidationError, match="duplicate stable ID"):
        validate_dossier(dossier)

    forbidden = fixture_material()
    forbidden["propositions"][0]["confidence"] = 0.9
    with pytest.raises(DossierValidationError, match="intrinsic field 'confidence' is forbidden"):
        stamp_dossier(forbidden)

    cyclic = fixture_material()
    cyclic["lineages"][0]["depends_on"] = ["lineage-copy"]
    with pytest.raises(DossierValidationError, match="lineage dependence cycle"):
        stamp_dossier(cyclic)


def test_relations_remain_representable_and_unknown_lineage_gets_no_credit() -> None:
    dossier = stamp_dossier(fixture_material())
    assert {record["relation_type"] for record in dossier["evidence_relations"]} == {
        "support",
        "rebuttal",
        "qualification",
        "undercutting",
        "replication",
        "failed-replication",
        "dependence",
    }
    summary = independence_summary(
        dossier,
        ["assertion-origin", "assertion-copy", "assertion-unknown"],
    )
    assert summary == {
        "assertion_keys": ["assertion-origin", "assertion-copy", "assertion-unknown"],
        "independent_lineage_count": 1,
        "independent_lineage_roots": ["lineage-origin"],
        "unknown_lineage_count": 1,
        "unknown_lineages": ["lineage-unknown"],
    }

    tainted = fixture_material()
    tainted["lineages"][1]["depends_on"] = ["lineage-unknown"]
    tainted_summary = independence_summary(stamp_dossier(tainted), ["assertion-copy"])
    assert tainted_summary["independent_lineage_count"] == 0
    assert tainted_summary["unknown_lineages"] == ["lineage-unknown"]


def test_private_only_mutation_cannot_change_public_projection() -> None:
    first = stamp_dossier(fixture_material())
    changed = fixture_material()
    replacement = "A different private fixture note that must not affect public output."
    changed["editions"][3] = edition(
        "edition-private",
        "work-private",
        "private synthetic v2",
        replacement,
        visibility="private",
    )
    changed["spans"][3] = text_span(
        "span-private",
        "edition-private",
        replacement,
        visibility="private",
    )
    second = stamp_dossier(changed)
    assert first["dossier_id"] != second["dossier_id"]
    assert public_dossier(first) == public_dossier(second)


def test_all_adapters_preserve_one_disclosure_safe_dossier_identity() -> None:
    source = stamp_dossier(fixture_material())
    with pytest.raises(DossierValidationError, match="disclosure-safe public dossier"):
        DossierProjection(source)
    projection = DossierProjection.from_dossier(source)
    json_document = json.loads(projection.json_text())
    cli_document = json.loads(projection.cli_text())
    api = projection.api_envelope()
    mcp = projection.mcp_resource()
    mcp_document = json.loads(mcp["text"])
    identity = projection.id

    assert json_document["dossier_id"] == identity
    assert cli_document["dossier_id"] == identity
    assert api["dossier_id"] == identity == api["data"]["dossier_id"]
    assert mcp["_meta"]["dossier_id"] == identity
    assert mcp_document["dossier_id"] == identity
    assert identity in projection.markdown()
    assert f'data-dossier-id="{identity}"' in projection.html()
    assert quote(identity, safe="") in mcp["uri"]
    for rendered in (
        projection.json_text(),
        projection.cli_text(),
        projection.markdown(),
        projection.html(),
        mcp["text"],
    ):
        assert "Private fixture note" not in rendered
