"""Reversible application-level claim dossiers for the first vertical slice.

This module is deliberately not a protocol schema. It validates an alpha application
document, produces a disclosure-safe public projection, and exposes small rendering
adapters that all preserve one public dossier identity.
"""

from __future__ import annotations

import copy
import hashlib
import html
import json
import math
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import quote

from .core import canonical_json, stable_id

DOSSIER_FORMAT = "epistemedia-dossier-v0.1"
VISIBILITIES = {"public", "private"}
COLLECTIONS = (
    "source_works",
    "editions",
    "spans",
    "propositions",
    "lineages",
    "assertions",
    "evidence_relations",
    "claim_families",
    "evaluations",
)
ROOT_FIELDS = {
    "format",
    "dossier_id",
    "title",
    "question",
    "scope",
    "stage",
    "visibility",
    *COLLECTIONS,
}
RECORD_FIELDS = {
    "source_works": {
        "key",
        "id",
        "kind",
        "title",
        "creators",
        "canonical_uri",
        "license",
        "visibility",
    },
    "editions": {
        "key",
        "id",
        "work_key",
        "edition_label",
        "media_type",
        "retrieved_at",
        "content",
        "content_digest",
        "content_length",
        "visibility",
    },
    "spans": {
        "key",
        "id",
        "edition_key",
        "locator",
        "extent",
        "digest",
        "visibility",
    },
    "propositions": {"key", "id", "text", "scope", "visibility"},
    "lineages": {
        "key",
        "id",
        "status",
        "dimensions",
        "depends_on",
        "basis_span_keys",
        "assertion_keys",
        "note",
        "visibility",
    },
    "assertions": {
        "key",
        "id",
        "proposition_key",
        "actor",
        "stance",
        "span_keys",
        "lineage_key",
        "asserted_at",
        "visibility",
    },
    "evidence_relations": {
        "key",
        "id",
        "relation_type",
        "from_ref",
        "to_ref",
        "basis_span_keys",
        "note",
        "visibility",
    },
    "claim_families": {
        "key",
        "id",
        "title",
        "question",
        "proposition_keys",
        "assertion_keys",
        "relation_keys",
        "visibility",
    },
    "evaluations": {
        "key",
        "id",
        "claim_family_key",
        "policy_id",
        "frontier",
        "label",
        "reason_codes",
        "visibility",
    },
}
ID_KINDS = {
    "source_works": "dossier-source-work",
    "editions": "dossier-edition",
    "spans": "dossier-span",
    "propositions": "dossier-proposition",
    "lineages": "dossier-lineage",
    "assertions": "dossier-assertion",
    "evidence_relations": "dossier-evidence-relation",
    "claim_families": "dossier-claim-family",
    "evaluations": "dossier-evaluation",
}
SOURCE_KINDS = {
    "paper",
    "webpage",
    "dataset",
    "book",
    "report",
    "conversation",
    "instrument",
    "other",
}
ACTOR_KINDS = {"human", "agent", "instrument", "service", "collective"}
STANCES = {"asserts", "denies", "questions", "hypothesizes", "predicts"}
RELATION_TYPES = {
    "support",
    "rebuttal",
    "qualification",
    "undercutting",
    "replication",
    "failed-replication",
    "dependence",
}
LINEAGE_DIMENSIONS = {
    "source",
    "data",
    "method",
    "apparatus",
    "model",
    "retrieval",
    "prompt",
    "social",
    "other",
}
FORBIDDEN_SEMANTIC_FIELDS = {
    "truth",
    "truth_value",
    "global_truth",
    "confidence",
    "confidence_score",
    "probability",
}
KEY_PATTERN = re.compile(r"^[a-z][a-z0-9-]{1,79}$")
DIGEST_PATTERN = re.compile(r"^sha256:[a-f0-9]{64}$")


class DossierValidationError(ValueError):
    """Raised when an application dossier fails closed."""


def _error(context: str, message: str) -> DossierValidationError:
    return DossierValidationError(f"{context}: {message}")


def _require_dict(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _error(context, "must be an object")
    return value


def _require_list(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise _error(context, "must be an array")
    return value


def _require_string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _error(context, "must be a non-empty string")
    return value


def _require_exact_fields(value: dict[str, Any], expected: set[str], context: str) -> None:
    missing = sorted(expected - value.keys())
    extra = sorted(value.keys() - expected)
    if missing:
        raise _error(context, "missing fields: " + ", ".join(missing))
    if extra:
        raise _error(context, "unknown fields: " + ", ".join(extra))


def _require_key(value: Any, context: str) -> str:
    key = _require_string(value, context)
    if KEY_PATTERN.fullmatch(key) is None:
        raise _error(context, "must match ^[a-z][a-z0-9-]{1,79}$")
    return key


def _require_unique_strings(value: Any, context: str) -> list[str]:
    items = _require_list(value, context)
    if any(not isinstance(item, str) or not item for item in items):
        raise _error(context, "must contain non-empty strings")
    if len(items) != len(set(items)):
        raise _error(context, "must not contain duplicates")
    return items


def _require_visibility(value: Any, context: str) -> str:
    visibility = _require_string(value, context)
    if visibility not in VISIBILITIES:
        raise _error(context, "must be public or private")
    return visibility


def _require_timestamp(value: Any, context: str) -> str:
    timestamp = _require_string(value, context)
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise _error(context, "must be an ISO 8601 date-time") from exc
    if parsed.tzinfo is None:
        raise _error(context, "must include a timezone")
    return timestamp


def _digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _content_bytes(value: Any) -> bytes:
    if isinstance(value, str):
        return value.encode("utf-8")
    if isinstance(value, (dict, list, int, float, bool)) or value is None:
        return canonical_json(value).encode("utf-8")
    raise DossierValidationError("content must be a JSON value")


def _validate_json_value(value: Any, context: str) -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise _error(context, "must not contain NaN or infinity")
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _validate_json_value(child, f"{context}[{index}]")
        return
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise _error(context, "object keys must be strings")
            _validate_json_value(child, f"{context}.{key}")
        return
    raise _error(context, "must contain only JSON values")


def _scan_forbidden_fields(value: Any, context: str = "dossier") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in FORBIDDEN_SEMANTIC_FIELDS:
                raise _error(context, f"intrinsic field {key!r} is forbidden")
            _scan_forbidden_fields(child, f"{context}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_forbidden_fields(child, f"{context}[{index}]")


def record_id(collection: str, record: dict[str, Any]) -> str:
    """Return the stable ID for one record, excluding only its existing ID field."""
    if collection not in ID_KINDS:
        raise ValueError(f"unknown dossier collection: {collection}")
    material = {key: copy.deepcopy(value) for key, value in record.items() if key != "id"}
    return stable_id(ID_KINDS[collection], material)


def dossier_id(dossier: dict[str, Any]) -> str:
    material = {key: copy.deepcopy(value) for key, value in dossier.items() if key != "dossier_id"}
    return stable_id("dossier", material)


def stamp_dossier(material: dict[str, Any]) -> dict[str, Any]:
    """Create content IDs for construction-time material before strict validation."""
    stamped = copy.deepcopy(material)
    for collection in COLLECTIONS:
        for record in _require_list(stamped.get(collection), collection):
            item = _require_dict(record, collection)
            item["id"] = record_id(collection, item)
    stamped["dossier_id"] = dossier_id(stamped)
    validate_dossier(stamped)
    return stamped


def _validate_source_work(record: dict[str, Any], context: str) -> None:
    if _require_string(record["kind"], context + ".kind") not in SOURCE_KINDS:
        raise _error(context + ".kind", "unsupported source kind")
    _require_string(record["title"], context + ".title")
    if not _require_unique_strings(record["creators"], context + ".creators"):
        raise _error(context + ".creators", "must name at least one creator or Unknown")
    _require_string(record["canonical_uri"], context + ".canonical_uri")
    _require_string(record["license"], context + ".license")


def _validate_edition(record: dict[str, Any], context: str) -> None:
    _require_key(record["work_key"], context + ".work_key")
    _require_string(record["edition_label"], context + ".edition_label")
    _require_string(record["media_type"], context + ".media_type")
    _require_timestamp(record["retrieved_at"], context + ".retrieved_at")
    if not isinstance(record["content"], (str, dict, list)):
        raise _error(context + ".content", "must be text, an object, or an array")
    _validate_json_value(record["content"], context + ".content")
    content = _content_bytes(record["content"])
    digest_value = _require_string(record["content_digest"], context + ".content_digest")
    if DIGEST_PATTERN.fullmatch(digest_value) is None:
        raise _error(context + ".content_digest", "must be a sha256 digest")
    if digest_value != _digest_bytes(content):
        raise _error(context + ".content_digest", "does not match edition content")
    if not isinstance(record["content_length"], int) or isinstance(record["content_length"], bool):
        raise _error(context + ".content_length", "must be an integer")
    if record["content_length"] != len(content):
        raise _error(context + ".content_length", "does not match UTF-8 or canonical JSON bytes")


def _json_pointer(value: Any, pointer: str, context: str) -> Any:
    if pointer == "":
        return value
    if not pointer.startswith("/"):
        raise _error(context, "JSON Pointer must be empty or begin with /")
    current = value
    for raw_part in pointer[1:].split("/"):
        if re.search(r"~(?:[^01]|$)", raw_part):
            raise _error(context, f"JSON Pointer segment {raw_part!r} has an invalid escape")
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif (
            isinstance(current, list)
            and re.fullmatch(r"0|[1-9][0-9]*", part)
            and int(part) < len(current)
        ):
            current = current[int(part)]
        else:
            raise _error(context, f"JSON Pointer segment {part!r} does not resolve")
    return current


def _validate_span(
    record: dict[str, Any], editions: dict[str, dict[str, Any]], context: str
) -> None:
    edition_key = _require_key(record["edition_key"], context + ".edition_key")
    edition = editions.get(edition_key)
    if edition is None:
        raise _error(context + ".edition_key", f"unknown edition {edition_key!r}")
    locator = _require_dict(record["locator"], context + ".locator")
    extent = _require_dict(record["extent"], context + ".extent")
    digest_value = _require_string(record["digest"], context + ".digest")
    if DIGEST_PATTERN.fullmatch(digest_value) is None:
        raise _error(context + ".digest", "must be a sha256 digest")
    locator_type = locator.get("type")
    if locator_type == "text-offset":
        _require_exact_fields(locator, {"type", "start", "end", "label"}, context + ".locator")
        _require_exact_fields(extent, {"type", "text"}, context + ".extent")
        if extent.get("type") != "quote" or not isinstance(extent.get("text"), str):
            raise _error(context + ".extent", "text offsets require a quote extent")
        content = edition["content"]
        if not isinstance(content, str):
            raise _error(context, "text offsets require a text edition")
        start, end = locator["start"], locator["end"]
        if any(not isinstance(bound, int) or isinstance(bound, bool) for bound in (start, end)):
            raise _error(context + ".locator", "start and end must be integers")
        if start < 0 or end <= start or end > len(content):
            raise _error(context + ".locator", "text offset is out of bounds")
        _require_string(locator["label"], context + ".locator.label")
        exact = content[start:end]
        if extent["text"] != exact:
            raise _error(context + ".extent.text", "does not match edition text at locator")
        extent_bytes = exact.encode("utf-8")
    elif locator_type == "json-pointer":
        _require_exact_fields(locator, {"type", "pointer", "label"}, context + ".locator")
        _require_exact_fields(extent, {"type", "value"}, context + ".extent")
        if extent.get("type") != "json-value":
            raise _error(context + ".extent", "JSON Pointers require a json-value extent")
        if not isinstance(edition["content"], (dict, list)):
            raise _error(context, "JSON Pointers require a structured edition")
        pointer = locator["pointer"]
        if not isinstance(pointer, str):
            raise _error(context + ".locator.pointer", "must be a string")
        _require_string(locator["label"], context + ".locator.label")
        exact = _json_pointer(edition["content"], pointer, context + ".locator.pointer")
        if extent["value"] != exact:
            raise _error(context + ".extent.value", "does not match edition value at locator")
        extent_bytes = _content_bytes(exact)
    else:
        raise _error(context + ".locator.type", "must be text-offset or json-pointer")
    if digest_value != _digest_bytes(extent_bytes):
        raise _error(context + ".digest", "does not match exact extent")


def _validate_proposition(record: dict[str, Any], context: str) -> None:
    _require_string(record["text"], context + ".text")
    _require_string(record["scope"], context + ".scope")


def _validate_lineage(record: dict[str, Any], context: str) -> None:
    status = _require_string(record["status"], context + ".status")
    if status not in {"known", "unknown"}:
        raise _error(context + ".status", "must be known or unknown")
    dimensions = _require_unique_strings(record["dimensions"], context + ".dimensions")
    if any(item not in LINEAGE_DIMENSIONS for item in dimensions):
        raise _error(context + ".dimensions", "contains an unsupported lineage dimension")
    _require_unique_strings(record["depends_on"], context + ".depends_on")
    _require_unique_strings(record["basis_span_keys"], context + ".basis_span_keys")
    _require_unique_strings(record["assertion_keys"], context + ".assertion_keys")
    note = _require_string(record["note"], context + ".note")
    if status == "unknown" and "unknown" not in note.lower():
        raise _error(context + ".note", "unknown lineage must be stated explicitly")


def _validate_assertion(record: dict[str, Any], context: str) -> None:
    _require_key(record["proposition_key"], context + ".proposition_key")
    actor = _require_dict(record["actor"], context + ".actor")
    _require_exact_fields(actor, {"id", "kind"}, context + ".actor")
    _require_string(actor["id"], context + ".actor.id")
    if _require_string(actor["kind"], context + ".actor.kind") not in ACTOR_KINDS:
        raise _error(context + ".actor.kind", "unsupported actor kind")
    if _require_string(record["stance"], context + ".stance") not in STANCES:
        raise _error(context + ".stance", "unsupported assertion stance")
    span_keys = _require_unique_strings(record["span_keys"], context + ".span_keys")
    if not span_keys:
        raise _error(context + ".span_keys", "must name at least one exact source span")
    _require_key(record["lineage_key"], context + ".lineage_key")
    _require_timestamp(record["asserted_at"], context + ".asserted_at")


def _validate_relation(record: dict[str, Any], context: str) -> None:
    relation_type = _require_string(record["relation_type"], context + ".relation_type")
    if relation_type not in RELATION_TYPES:
        raise _error(context + ".relation_type", "unsupported evidence relation")
    _require_key(record["from_ref"], context + ".from_ref")
    _require_key(record["to_ref"], context + ".to_ref")
    span_keys = _require_unique_strings(record["basis_span_keys"], context + ".basis_span_keys")
    if not span_keys:
        raise _error(context + ".basis_span_keys", "must name at least one exact source span")
    _require_string(record["note"], context + ".note")


def _validate_family(record: dict[str, Any], context: str) -> None:
    _require_string(record["title"], context + ".title")
    _require_string(record["question"], context + ".question")
    for field in ("proposition_keys", "assertion_keys", "relation_keys"):
        values = _require_unique_strings(record[field], context + "." + field)
        if not values:
            raise _error(context + "." + field, "must not be empty")


def _validate_evaluation(record: dict[str, Any], context: str) -> None:
    _require_key(record["claim_family_key"], context + ".claim_family_key")
    _require_string(record["policy_id"], context + ".policy_id")
    _require_string(record["frontier"], context + ".frontier")
    _require_string(record["label"], context + ".label")
    if not _require_unique_strings(record["reason_codes"], context + ".reason_codes"):
        raise _error(context + ".reason_codes", "must name at least one policy reason")


def _validate_cycles(lineages: dict[str, dict[str, Any]]) -> None:
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(key: str) -> None:
        marker = state.get(key, 0)
        if marker == 1:
            start = stack.index(key)
            cycle = " -> ".join(stack[start:] + [key])
            raise DossierValidationError(f"lineage dependence cycle: {cycle}")
        if marker == 2:
            return
        state[key] = 1
        stack.append(key)
        for dependency in lineages[key]["depends_on"]:
            visit(dependency)
        stack.pop()
        state[key] = 2

    for key in lineages:
        visit(key)


def _require_refs(values: Iterable[str], allowed: dict[str, dict[str, Any]], context: str) -> None:
    for value in values:
        if value not in allowed:
            raise _error(context, f"unknown reference {value!r}")


def validate_dossier(dossier: dict[str, Any]) -> None:
    """Validate strict shape, content identity, spans, closure, and dependence."""
    root = _require_dict(dossier, "dossier")
    _scan_forbidden_fields(root)
    _require_exact_fields(root, ROOT_FIELDS, "dossier")
    if root["format"] != DOSSIER_FORMAT:
        raise _error("dossier.format", f"must be {DOSSIER_FORMAT!r}")
    _require_string(root["title"], "dossier.title")
    _require_string(root["question"], "dossier.question")
    _require_string(root["scope"], "dossier.scope")
    if _require_string(root["stage"], "dossier.stage") not in {"fixture", "draft", "reviewed"}:
        raise _error("dossier.stage", "must be fixture, draft, or reviewed")
    _require_visibility(root["visibility"], "dossier.visibility")

    collections: dict[str, dict[str, dict[str, Any]]] = {}
    global_keys: dict[str, str] = {}
    global_ids: dict[str, str] = {}
    for collection in COLLECTIONS:
        records = _require_list(root[collection], f"dossier.{collection}")
        indexed: dict[str, dict[str, Any]] = {}
        for index, raw_record in enumerate(records):
            context = f"dossier.{collection}[{index}]"
            record = _require_dict(raw_record, context)
            _require_exact_fields(record, RECORD_FIELDS[collection], context)
            key = _require_key(record["key"], context + ".key")
            if key in global_keys:
                raise _error(context + ".key", f"duplicate key also used by {global_keys[key]}")
            identifier = _require_string(record["id"], context + ".id")
            if identifier in global_ids:
                raise _error(
                    context + ".id", f"duplicate stable ID also used by {global_ids[identifier]}"
                )
            expected_id = record_id(collection, record)
            if identifier != expected_id:
                raise _error(context + ".id", f"does not match content address {expected_id}")
            _require_visibility(record["visibility"], context + ".visibility")
            indexed[key] = record
            global_keys[key] = context
            global_ids[identifier] = context
        collections[collection] = indexed

    validators = {
        "source_works": _validate_source_work,
        "editions": _validate_edition,
        "propositions": _validate_proposition,
        "lineages": _validate_lineage,
        "assertions": _validate_assertion,
        "evidence_relations": _validate_relation,
        "claim_families": _validate_family,
        "evaluations": _validate_evaluation,
    }
    for collection, validator in validators.items():
        for key, record in collections[collection].items():
            validator(record, f"dossier.{collection}.{key}")
    for key, record in collections["spans"].items():
        _validate_span(record, collections["editions"], f"dossier.spans.{key}")

    source_works = collections["source_works"]
    editions = collections["editions"]
    spans = collections["spans"]
    propositions = collections["propositions"]
    lineages = collections["lineages"]
    assertions = collections["assertions"]
    relations = collections["evidence_relations"]
    families = collections["claim_families"]
    all_records = {key: record for group in collections.values() for key, record in group.items()}

    for key, record in editions.items():
        _require_refs([record["work_key"]], source_works, f"edition {key}.work_key")
    for key, record in assertions.items():
        _require_refs([record["proposition_key"]], propositions, f"assertion {key}.proposition_key")
        _require_refs(record["span_keys"], spans, f"assertion {key}.span_keys")
        _require_refs([record["lineage_key"]], lineages, f"assertion {key}.lineage_key")
    for key, record in lineages.items():
        _require_refs(record["depends_on"], lineages, f"lineage {key}.depends_on")
        _require_refs(record["basis_span_keys"], spans, f"lineage {key}.basis_span_keys")
        _require_refs(record["assertion_keys"], assertions, f"lineage {key}.assertion_keys")
        for assertion_key in record["assertion_keys"]:
            if assertions[assertion_key]["lineage_key"] != key:
                raise _error(
                    f"lineage {key}.assertion_keys",
                    f"assertion {assertion_key!r} points to another lineage",
                )
    for key, record in assertions.items():
        if key not in lineages[record["lineage_key"]]["assertion_keys"]:
            raise _error(f"assertion {key}.lineage_key", "lineage does not list this assertion")
    for key, record in relations.items():
        _require_refs([record["from_ref"], record["to_ref"]], all_records, f"relation {key}")
        _require_refs(record["basis_span_keys"], spans, f"relation {key}.basis_span_keys")
        relation_type = record["relation_type"]
        if relation_type in {"support", "rebuttal", "qualification", "undercutting"}:
            if record["from_ref"] not in spans | assertions or record["to_ref"] not in (
                propositions | assertions
            ):
                raise _error(
                    f"relation {key}",
                    f"{relation_type} requires a span/assertion source and "
                    "proposition/assertion target",
                )
        elif relation_type in {"replication", "failed-replication"}:
            if record["from_ref"] not in assertions or record["to_ref"] not in assertions:
                raise _error(f"relation {key}", f"{relation_type} endpoints must be assertions")
        elif record["from_ref"] not in lineages or record["to_ref"] not in lineages:
            raise _error(f"relation {key}", "dependence endpoints must both be lineages")
    for key, record in families.items():
        _require_refs(record["proposition_keys"], propositions, f"family {key}.proposition_keys")
        _require_refs(record["assertion_keys"], assertions, f"family {key}.assertion_keys")
        _require_refs(record["relation_keys"], relations, f"family {key}.relation_keys")
    for key, record in collections["evaluations"].items():
        _require_refs([record["claim_family_key"]], families, f"evaluation {key}.claim_family_key")

    _validate_cycles(lineages)
    expected_dossier_id = dossier_id(root)
    if root["dossier_id"] != expected_dossier_id:
        raise _error("dossier.dossier_id", f"does not match content address {expected_dossier_id}")


def public_dossier(dossier: dict[str, Any]) -> dict[str, Any]:
    """Filter private records before producing the public content address."""
    validate_dossier(dossier)
    if dossier["visibility"] != "public":
        raise DossierValidationError("private dossier root cannot produce a public projection")
    projected = {
        key: copy.deepcopy(value)
        for key, value in dossier.items()
        if key not in COLLECTIONS and key != "dossier_id"
    }
    projected["visibility"] = "public"
    for collection in COLLECTIONS:
        projected[collection] = [
            copy.deepcopy(record)
            for record in dossier[collection]
            if record["visibility"] == "public"
        ]
    projected["dossier_id"] = dossier_id(projected)
    try:
        validate_dossier(projected)
    except DossierValidationError as exc:
        raise DossierValidationError(
            f"public projection is not referentially closed: {exc}"
        ) from exc
    return projected


def independence_summary(dossier: dict[str, Any], assertion_keys: Iterable[str]) -> dict[str, Any]:
    """Collapse known dependencies to roots and give unknown lineage no credit."""
    validate_dossier(dossier)
    assertions = {record["key"]: record for record in dossier["assertions"]}
    lineages = {record["key"]: record for record in dossier["lineages"]}
    requested = list(assertion_keys)
    _require_refs(requested, assertions, "independence_summary.assertion_keys")
    roots: set[str] = set()
    unknown: set[str] = set()

    def resolve(lineage_key: str) -> tuple[set[str], set[str]]:
        lineage = lineages[lineage_key]
        if lineage["status"] == "unknown":
            return set(), {lineage_key}
        if not lineage["depends_on"]:
            return {lineage_key}, set()
        known_roots: set[str] = set()
        unknown_roots: set[str] = set()
        for dependency in lineage["depends_on"]:
            dependency_roots, dependency_unknown = resolve(dependency)
            known_roots.update(dependency_roots)
            unknown_roots.update(dependency_unknown)
        return known_roots, unknown_roots

    for assertion_key in requested:
        known_roots, unknown_roots = resolve(assertions[assertion_key]["lineage_key"])
        roots.update(known_roots)
        unknown.update(unknown_roots)
    return {
        "assertion_keys": requested,
        "independent_lineage_count": len(roots),
        "independent_lineage_roots": sorted(roots),
        "unknown_lineage_count": len(unknown),
        "unknown_lineages": sorted(unknown),
    }


@dataclass(frozen=True)
class DossierProjection:
    """One disclosure-safe identity rendered through human and agent adapters."""

    data: dict[str, Any]

    def __post_init__(self) -> None:
        validate_dossier(self.data)
        if self.data["visibility"] != "public" or any(
            record["visibility"] != "public"
            for collection in COLLECTIONS
            for record in self.data[collection]
        ):
            raise DossierValidationError(
                "DossierProjection requires a disclosure-safe public dossier"
            )
        object.__setattr__(self, "data", copy.deepcopy(self.data))

    @classmethod
    def from_dossier(cls, dossier: dict[str, Any]) -> DossierProjection:
        return cls(public_dossier(dossier))

    @property
    def id(self) -> str:
        return self.data["dossier_id"]

    def json_text(self) -> str:
        return json.dumps(self.data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"

    def markdown(self) -> str:
        lines = [
            f"# {self.data['title']}",
            "",
            f"**Dossier:** `{self.id}`",
            "",
            f"**Question:** {self.data['question']}",
            "",
            f"**Scope:** {self.data['scope']}",
            "",
            "## Source works",
            "",
        ]
        lines.extend(
            f"- **{record['title']}** — `{record['id']}`" for record in self.data["source_works"]
        )
        lines += ["", "## Propositions", ""]
        lines.extend(
            f"- {record['text']} — `{record['id']}`" for record in self.data["propositions"]
        )
        lines += ["", "## Policy-relative evaluations", ""]
        lines.extend(
            f"- `{record['policy_id']}`: {record['label']} — `{record['id']}`"
            for record in self.data["evaluations"]
        )
        return "\n".join(lines).rstrip() + "\n"

    def html(self) -> str:
        sources = "".join(
            f"<li><strong>{html.escape(record['title'])}</strong> "
            f"<code>{html.escape(record['id'])}</code></li>"
            for record in self.data["source_works"]
        )
        propositions = "".join(
            f"<li>{html.escape(record['text'])} <code>{html.escape(record['id'])}</code></li>"
            for record in self.data["propositions"]
        )
        return (
            f'<article data-dossier-id="{html.escape(self.id)}">'
            f"<h1>{html.escape(self.data['title'])}</h1>"
            f"<p><strong>Dossier:</strong> <code>{html.escape(self.id)}</code></p>"
            f"<p><strong>Question:</strong> {html.escape(self.data['question'])}</p>"
            f"<p><strong>Scope:</strong> {html.escape(self.data['scope'])}</p>"
            f"<h2>Source works</h2><ul>{sources}</ul>"
            f"<h2>Propositions</h2><ul>{propositions}</ul>"
            "</article>"
        )

    def api_envelope(self) -> dict[str, Any]:
        return {"dossier_id": self.id, "data": copy.deepcopy(self.data)}

    def mcp_resource(self) -> dict[str, Any]:
        return {
            "uri": "epistemedia://dossier/" + quote(self.id, safe=""),
            "mimeType": "application/json",
            "text": self.json_text(),
            "_meta": {"dossier_id": self.id},
        }

    def cli_text(self) -> str:
        return self.json_text()
