# ruff: noqa: E501
"""Public, non-admitting research protocol for cold-start coding agents."""

from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import html
import ipaddress
import json
import re
import socket
from typing import Any
from urllib.parse import urlsplit

PROTOCOL_FORMAT = "epistemedia-agent-research-protocol-v0.2"
BRIEF_FORMAT = "epistemedia-case-research-brief-v0.1"
PROPOSAL_FORMAT = "epistemedia-research-proposal-v0.2"
VALIDATION_FORMAT = "epistemedia-research-proposal-validation-v0.2"
MAX_BUNDLE_BYTES = 524_288
MAX_TEXT = 20_000
MAX_ITEMS = 500
MAX_SOURCES = 20
MAX_SPANS_PER_SOURCE = 100
MAX_QUOTE_CHARACTERS = 1_000
MAX_UNKNOWN_LICENSE_QUOTE_CHARACTERS = 320
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    re.compile(r"\b(?:sk-proj-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,})\b"),
    re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    re.compile(r"(?<![A-Za-z0-9:])/(?:Users|home|private|root)/"),
    re.compile(r"(?:^|[\s'\"`])[A-Za-z]:\\Users\\"),
)
PLACEHOLDER_PATTERN = re.compile(r"\b(?:REPLACE|YOUR QUESTION|YYYY-MM-DD)\b")
PUBLIC_TEXT_PATTERNS = (
    re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    re.compile(r"(?<![A-Za-z0-9])/(?:tmp|var|opt|etc)/"),
    re.compile(r"(?:^|[\s'\"`])(?:\.\.[/\\])+"),
    re.compile(r"(?:^|[\s'\"`])[A-Za-z]:\\"),
    re.compile(
        r"(?i)\b(?:chain[- ]of[- ]thought|private reasoning|hidden reasoning|"
        r"system prompt|developer message)\b"
    ),
)

PROPOSAL_FIELDS = {
    "format",
    "status",
    "question",
    "cutoff",
    "scope",
    "results",
    "calculations",
    "dependencies",
    "retrieval_attempts",
    "sources",
    "counterevidence",
    "negative_results",
    "limitations",
    "unresolved",
    "search_notes",
    "lineage",
    "runtime",
    "license",
}
SCOPE_FIELDS = {"included", "excluded", "comparison_target"}
RESULT_FIELDS = {
    "result_id",
    "proposition",
    "reported_value",
    "scope",
    "source_ids",
    "exact_span_ids",
    "interpretation",
    "warrant",
    "uncertainty",
    "calculation_ids",
    "calculation_status",
    "dependency_ids",
    "claim_atoms",
}
CLAIM_ATOM_FIELDS = {
    "atom_id",
    "text",
    "kind",
    "status",
    "source_ids",
    "exact_span_ids",
}
REPORTED_VALUE_FIELDS = {"numerator", "denominator", "rate", "comparison"}
RESULT_SCOPE_FIELDS = {
    "models_or_agents",
    "dataset_or_population",
    "tool_and_retrieval_path",
    "time",
    "metric_scope",
}
SOURCE_FIELDS = {
    "source_id",
    "url",
    "title",
    "creators_or_org",
    "date",
    "identifier",
    "edition",
    "retrieval_status",
    "media_type",
    "license",
    "exact_spans",
}
SOURCE_LICENSE_FIELDS = {"status", "identifier", "basis_span_id"}
SPAN_FIELDS = {"span_id", "locator", "quote", "supports"}
COUNTER_FIELDS = {
    "claim",
    "evidence",
    "source_ids",
    "exact_span_ids",
    "qualification",
}
NEGATIVE_FIELDS = {
    "result",
    "kind",
    "scope",
    "source_ids",
    "exact_span_ids",
    "retrieval_attempt_ids",
    "disposition",
}
LINEAGE_FIELDS = {
    "prompt_sha256",
    "run_identity",
    "provider_model_identity",
    "retrieval_environment",
    "shared_dependencies",
}
RUNTIME_FIELDS = {"started_at", "completed_at", "agent", "toolchain"}
LICENSE_FIELDS = {"bundle", "source_material"}
CALCULATION_FIELDS = {
    "calculation_id",
    "equation",
    "inputs",
    "output",
    "uncertainty",
    "depends_on",
}
CALCULATION_INPUT_FIELDS = {
    "input_id",
    "name",
    "value",
    "origin",
    "source_id",
    "span_id",
    "json_pointer",
}
CALCULATION_DEPENDENCY_FIELDS = {"calculation_id", "input_id", "consumed_output"}
DEPENDENCY_FIELDS = {
    "dependency_id",
    "kind",
    "description",
    "source_ids",
    "exact_span_ids",
}
RETRIEVAL_ATTEMPT_FIELDS = {
    "attempt_id",
    "source_id",
    "url",
    "attempted_at",
    "transport",
    "outcome",
    "failure_code",
    "artifact_sha256",
}

CLAIM_ATOM_KINDS = {"finding", "date", "comparison", "metadata", "process", "boundary"}
CLAIM_ATOM_STATUSES = {"supported", "qualified", "hypothesis", "unresolved"}
SOURCE_LICENSE_STATUSES = {"known", "unknown", "unassessed"}
RETRIEVAL_TRANSPORTS = {"https", "http"}
RETRIEVAL_OUTCOMES = {"retrieved", "blocked", "not-found", "timeout", "failed"}
RETRIEVAL_FAILURE_CODES = {
    "none",
    "http-403",
    "http-404",
    "timeout",
    "dns-failure",
    "tls-failure",
    "robots-blocked",
    "access-denied",
    "unknown-failure",
}


def _digest(value: Any) -> str:
    material = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(material).hexdigest()


def parse_utc_timestamp(value: Any, path: str, errors: list[str]) -> dt.datetime | None:
    """Parse one canonical UTC timestamp without accepting contributor clock aliases."""
    if not isinstance(value, str) or re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value
    ) is None:
        errors.append(f"{path} must use canonical UTC YYYY-MM-DDTHH:MM:SSZ")
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{path} is not a valid timestamp")
        return None
    return parsed


def submission_status(base_url: str) -> dict[str, Any]:
    return {
        "format": "epistemedia-research-submission-status-v0.2",
        "hosted_submission_available": False,
        "github_submission_available": True,
        "queue_status": "github-draft-pr-pilot",
        "intended_authority": "EM-0038",
        "github_pilot_authority": "EM-0041",
        "public_mcp_mode": "read-only",
        "proposal_credit": "zero until independent source, span, derivation, and lineage review",
        "next_step": (
            "Prepare and validate a portable proposal bundle, then follow the autonomous "
            "GitHub draft-PR submission guide. Stop after submission; do not review or merge it."
        ),
        "submission_guide": f"{base_url.rstrip('/')}/agents/submit/",
        "status_url": f"{base_url.rstrip('/')}/agents/submission-status.json",
    }


def protocol_document(base_url: str) -> dict[str, Any]:
    base = base_url.rstrip("/")
    return {
        "format": PROTOCOL_FORMAT,
        "purpose": (
            "Research one contestable question while keeping sources, exact passages, "
            "derivations, dependence, uncertainty, and negative results inspectable."
        ),
        "read_order": [
            f"{base}/llms.txt",
            f"{base}/agents/research-protocol.md",
            f"{base}/how-we-know/",
            f"{base}/explore/",
            "the selected case research-brief.md, when one exists",
        ],
        "steps": [
            "Restate the question, cutoff, included scope, excluded scope, and comparison target.",
            "Prefer primary public editions; record exact URL, edition, access state, and license.",
            "For every proposal source, add a retrieve-source action-trace event with the exact public URL and independently computed artifact SHA-256; do not copy source payloads into the trace.",
            "Decompose each result into typed claim atoms, including every material proposition, reported value, model, population, retrieval path, date, metric, and comparison literal; every required literal must be supported or qualified by quote-minimal exact spans and explicit locators, while unsupported process explanations remain separate hypotheses with no evidence credit.",
            "Represent every calculated result with its equation, source-bound inputs, output, uncertainty, and calculation dependencies; attach typed source, data, method, material, and derivation dependencies to each result.",
            "Record counterevidence, negative results, unresolved items, and inaccessible carriers.",
            "Collapse shared prompt, runtime, retrieval, source, data, method, and derivation lineages; never count runs as independent by default.",
            "Prepare the proposal bundle and run fail-closed validation before any handoff.",
        ],
        "required_output_format": PROPOSAL_FORMAT,
        "validation": {
            "cli": "epistemedia research validate proposal.json",
            "mcp_tool": "validate_research_proposal",
            "static_template": f"{base}/agents/proposal-template.json",
            "maximum_bytes": MAX_BUNDLE_BYTES,
        },
        "boundaries": [
            "A proposal is untrusted intake, not knowledge and not an independent evidence root.",
            "Validation checks structure and internal closure; it does not verify truth.",
            "The public API and MCP cannot submit, admit, merge, publish, or mutate accepted state.",
            "The GitHub draft-PR pilot is coordination only; its submitted branch is never merged directly.",
            "A future authenticated MCP queue still requires separate EM-0038 governance.",
        ],
        "submission": submission_status(base),
    }


def protocol_markdown(base_url: str) -> str:
    doc = protocol_document(base_url)
    lines = [
        "# Run an Epistemedia evidence test",
        "",
        doc["purpose"],
        "",
        "## Give this to your coding agent",
        "",
        "> Read this protocol and the relevant case brief. Research my question using public "
        "primary sources. Return one validated `epistemedia-research-proposal-v0.2` JSON "
        "bundle. Keep counterevidence and failed retrievals. If asked to submit, follow the "
        "separate GitHub draft-PR guide and stop before review or merge.",
        "",
        "## Procedure",
        "",
        *[f"{index}. {step}" for index, step in enumerate(doc["steps"], 1)],
        "",
        "## Validate locally",
        "",
        "```sh",
        'epistemedia research prepare --question "YOUR QUESTION" --output proposal.json',
        "epistemedia research validate proposal.json",
        "```",
        "",
        "The prepare command creates a draft scaffold. Validation fails until required sources, "
        "spans, lineage, negative-result, runtime, and license fields are complete.",
        "",
        "## Submission boundary",
        "",
        doc["submission"]["next_step"],
        "",
        f"Current GitHub draft-PR submission: **{str(doc['submission']['github_submission_available']).lower()}**. Hosted MCP submission: **false**.",
        "",
        "## Machine representations",
        "",
        f"- [Protocol JSON]({base_url.rstrip('/')}/agents/research-protocol.json)",
        f"- [Proposal template]({base_url.rstrip('/')}/agents/proposal-template.json)",
        f"- [Submission status]({base_url.rstrip('/')}/agents/submission-status.json)",
        f"- [Autonomous submission guide]({base_url.rstrip('/')}/agents/submit/)",
        "",
    ]
    return "\n".join(lines)


def proposal_template(
    question: str, *, cutoff: str = "YYYY-MM-DD", case_slug: str | None = None
) -> dict[str, Any]:
    included = f"Seeded from accepted case: {case_slug}" if case_slug else ""
    return {
        "format": PROPOSAL_FORMAT,
        "status": "draft",
        "question": question,
        "cutoff": cutoff,
        "scope": {
            "included": included or "REPLACE with included scope",
            "excluded": "REPLACE with excluded scope",
            "comparison_target": "REPLACE with the exact comparison target",
        },
        "results": [
            {
                "result_id": "result-1",
                "proposition": "REPLACE with one bounded proposition",
                "reported_value": {
                    "numerator": "REPLACE or state not reported",
                    "denominator": "REPLACE or state not reported",
                    "rate": "REPLACE or state not reported",
                    "comparison": "REPLACE with the exact comparator",
                },
                "scope": {
                    "models_or_agents": ["REPLACE with the tested system or population"],
                    "dataset_or_population": "REPLACE with dataset or population",
                    "tool_and_retrieval_path": "REPLACE with retrieval path",
                    "time": "REPLACE with observation period",
                    "metric_scope": "REPLACE with what the metric does and does not measure",
                },
                "source_ids": ["source-1"],
                "exact_span_ids": ["span-1"],
                "interpretation": "REPLACE with a bounded interpretation",
                "warrant": "REPLACE with why the cited span supports the proposition",
                "uncertainty": "REPLACE with uncertainty and unresolved dependence",
                "calculation_ids": ["calculation-1"],
                "calculation_status": "reproduced",
                "dependency_ids": ["dependency-1"],
                "claim_atoms": [
                    {
                        "atom_id": "atom-1",
                        "text": "REPLACE with one material claim component",
                        "kind": "finding",
                        "status": "supported",
                        "source_ids": ["source-1"],
                        "exact_span_ids": ["span-1"],
                    }
                ],
            }
        ],
        "calculations": [
            {
                "calculation_id": "calculation-1",
                "equation": "REPLACE with an explicit equation or identity mapping",
                "inputs": [
                    {
                        "input_id": "input-1",
                        "name": "REPLACE with input name",
                        "value": "REPLACE with source-reported input value",
                        "origin": "source-span",
                        "source_id": "source-1",
                        "span_id": "span-1",
                        "json_pointer": "/REPLACE/with/exact/source/field",
                    }
                ],
                "output": "REPLACE with reproduced output",
                "uncertainty": "REPLACE with calculation uncertainty",
                "depends_on": [],
            }
        ],
        "dependencies": [
            {
                "dependency_id": "dependency-1",
                "kind": "source",
                "description": "REPLACE with the source, data, method, material, or derivation dependence",
                "source_ids": ["source-1"],
                "exact_span_ids": ["span-1"],
            }
        ],
        "retrieval_attempts": [
            {
                "attempt_id": "attempt-1",
                "source_id": "source-1",
                "url": "https://example.org/REPLACE-PRIMARY-SOURCE",
                "attempted_at": "REPLACE with UTC timestamp",
                "transport": "https",
                "outcome": "retrieved",
                "failure_code": "none",
                "artifact_sha256": "REPLACE with lowercase SHA-256",
            }
        ],
        "sources": [
            {
                "source_id": "source-1",
                "url": "https://example.org/REPLACE-PRIMARY-SOURCE",
                "title": "REPLACE with source title",
                "creators_or_org": "REPLACE with creators or organization",
                "date": "REPLACE with source date",
                "identifier": "REPLACE with DOI, accession, or stable identifier",
                "edition": "REPLACE with exact edition",
                "retrieval_status": "REPLACE with retrieval status",
                "media_type": "REPLACE with media type",
                "license": {
                    "status": "known",
                    "identifier": "REPLACE with SPDX identifier or exact license name",
                    "basis_span_id": "span-1",
                },
                "exact_spans": [
                    {
                        "span_id": "span-1",
                        "locator": "REPLACE with page, table, paragraph, or pointer",
                        "quote": "REPLACE with quote-minimal exact text",
                        "supports": "REPLACE with the proposition component this span supports",
                    }
                ],
            }
        ],
        "counterevidence": [
            {
                "claim": "REPLACE with challenged interpretation",
                "evidence": "REPLACE with counterevidence",
                "source_ids": ["source-1"],
                "exact_span_ids": ["span-1"],
                "qualification": "REPLACE with scope and disposition",
            }
        ],
        "negative_results": [
            {
                "result": "REPLACE with null, contrary, or failed-retrieval result",
                "kind": "no-evidence-located",
                "scope": "REPLACE with the bounded search or experiment scope",
                "source_ids": ["source-1"],
                "exact_span_ids": ["span-1"],
                "retrieval_attempt_ids": ["attempt-1"],
                "disposition": "REPLACE with retained status; do not convert absence to zero",
            }
        ],
        "limitations": ["REPLACE with a material limitation"],
        "unresolved": ["REPLACE with an unresolved item"],
        "search_notes": ["REPLACE with bounded search and retrieval notes"],
        "lineage": {
            "prompt_sha256": "unknown",
            "run_identity": "unknown",
            "provider_model_identity": "unknown",
            "retrieval_environment": "unknown",
            "shared_dependencies": ["REPLACE with shared run, source, or method dependencies"],
        },
        "runtime": {
            "started_at": "unknown",
            "completed_at": "unknown",
            "agent": "unknown",
            "toolchain": ["REPLACE with tools used"],
        },
        "license": {
            "bundle": "CC0-1.0",
            "source_material": "Each source retains its recorded license and treatment.",
        },
    }


def case_research_brief(projection: dict[str, Any], base_url: str) -> dict[str, Any]:
    slug = str(projection["slug"])
    brief = {
        "format": BRIEF_FORMAT,
        "case": {"number": projection["number"], "slug": slug, "title": projection["title"]},
        "question": projection["question"],
        "target_proposition": projection["target_proposition"],
        "scope": projection["scope"],
        "comparison_target": projection["target_proposition"].get("scope", ""),
        "requirements": {
            "source": "Prefer primary public editions and record inaccessible carriers.",
            "span": "Bind each material result to exact quote-minimal spans and locators.",
            "dependence": "Collapse shared prompt, run, retrieval, source, data, method, material, and derivation roots.",
            "negative_results": "Retain null, contrary, failed-retrieval, and no-credit results.",
            "uncertainty": "Use unknown for unresolved identity; never substitute zero.",
        },
        "accepted_case_is_context_not_evidence": True,
        "proposal_template": proposal_template(projection["question"], case_slug=slug),
        "links": {
            "case": f"{base_url.rstrip('/')}/how-we-know/{slug}/",
            "protocol": f"{base_url.rstrip('/')}/agents/research-protocol.md",
            "submission_status": f"{base_url.rstrip('/')}/agents/submission-status.json",
        },
    }
    if isinstance(projection.get("editorial"), dict):
        brief["failure_mode"] = projection["editorial"]["failure_mode"]
        brief["familiar_claim"] = projection["editorial"]["claim"]
    return brief


def case_brief_markdown(brief: dict[str, Any]) -> str:
    case = brief["case"]
    lines = [
        f"# Research brief — Case {case['number']}: {case['title']}",
        "",
        f"**Question:** {brief['question']}",
        "",
        f"**Target proposition:** {brief['target_proposition']['text']}",
        "",
        f"**Scope:** {brief['scope']}",
        "",
        "## Required closure",
        "",
        *[
            f"- **{key.replace('_', ' ').title()}:** {value}"
            for key, value in brief["requirements"].items()
        ],
        "",
        "## Boundary",
        "",
        "The accepted case is context, not evidence for a new proposal. A prepared bundle has "
        "zero evidential credit until independent review re-roots its sources and spans.",
        "",
        f"[Common protocol]({brief['links']['protocol']}) · "
        f"[Submission status]({brief['links']['submission_status']})",
        "",
    ]
    return "\n".join(lines)


def _exact_fields(value: Any, expected: set[str], path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return {}
    extra = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    if extra:
        errors.append(f"{path} has unsupported fields: {', '.join(extra)}")
    if missing:
        errors.append(f"{path} is missing fields: {', '.join(missing)}")
    return value


def _string(value: Any, path: str, errors: list[str], *, allow_unknown: bool = True) -> str:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path} must be a non-empty string")
        return ""
    if len(value) > MAX_TEXT:
        errors.append(f"{path} exceeds {MAX_TEXT} characters")
    if not allow_unknown and value == "unknown":
        errors.append(f"{path} must not be unknown")
    if any(pattern.search(value) for pattern in (*SECRET_PATTERNS, *PUBLIC_TEXT_PATTERNS)):
        errors.append(
            f"{path} contains private-path or secret-shaped data, personal data, "
            "or prohibited private context"
        )
    if PLACEHOLDER_PATTERN.search(value):
        errors.append(f"{path} still contains template placeholder text")
    return value


def _string_list(value: Any, path: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return []
    if len(value) > MAX_ITEMS:
        errors.append(f"{path} exceeds {MAX_ITEMS} items")
    result = []
    for index, item in enumerate(value):
        result.append(_string(item, f"{path}[{index}]", errors))
    return result


def _public_url(value: Any, path: str, errors: list[str]) -> str:
    url = _string(value, path, errors, allow_unknown=False)
    try:
        parsed = urlsplit(url)
    except ValueError:
        errors.append(f"{path} is not a valid URL")
        return url
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        errors.append(f"{path} must be a public HTTP(S) URL")
        return url
    hostname = parsed.hostname.lower()
    if hostname == "localhost" or hostname.endswith(".local"):
        errors.append(f"{path} must not target a local host")
    address = None
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        with contextlib.suppress(OSError, ValueError):
            # Reject legacy numeric spellings such as 2130706433 and 0177.0.0.1.
            address = ipaddress.ip_address(socket.inet_aton(hostname))
    if address is not None and not address.is_global:
        errors.append(f"{path} must not target a private address")
    if parsed.username or parsed.password:
        errors.append(f"{path} must not contain credentials")
    if ".." in parsed.path.split("/"):
        errors.append(f"{path} must not contain path traversal")
    return url


def validate_proposal(bundle: Any) -> dict[str, Any]:
    errors: list[str] = []
    try:
        encoded = json.dumps(bundle, ensure_ascii=False, sort_keys=True).encode("utf-8")
    except (TypeError, ValueError):
        return {
            "format": VALIDATION_FORMAT,
            "valid": False,
            "errors": ["bundle must be JSON-serializable"],
            "admitted": False,
            "submitted": False,
        }
    if len(encoded) > MAX_BUNDLE_BYTES:
        errors.append(f"bundle exceeds {MAX_BUNDLE_BYTES} bytes")
    root = _exact_fields(bundle, PROPOSAL_FIELDS, "bundle", errors)
    if root.get("format") != PROPOSAL_FORMAT:
        errors.append(f"bundle.format must equal {PROPOSAL_FORMAT}")
    if root.get("status") != "ready-for-review":
        errors.append("bundle.status must equal ready-for-review")
    _string(root.get("question"), "bundle.question", errors, allow_unknown=False)
    cutoff = _string(root.get("cutoff"), "bundle.cutoff", errors, allow_unknown=False)
    if cutoff and re.fullmatch(r"\d{4}-\d{2}-\d{2}", cutoff) is None:
        errors.append("bundle.cutoff must use YYYY-MM-DD")

    scope = _exact_fields(root.get("scope"), SCOPE_FIELDS, "bundle.scope", errors)
    for key in SCOPE_FIELDS:
        _string(scope.get(key), f"bundle.scope.{key}", errors, allow_unknown=False)

    sources = root.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("bundle.sources must be a non-empty list")
        sources = []
    elif len(sources) > MAX_SOURCES:
        errors.append(f"bundle.sources exceeds {MAX_SOURCES} items")
    source_ids: set[str] = set()
    span_to_source: dict[str, str] = {}
    for source_index, raw_source in enumerate(sources):
        path = f"bundle.sources[{source_index}]"
        source = _exact_fields(raw_source, SOURCE_FIELDS, path, errors)
        source_id = _string(
            source.get("source_id"), f"{path}.source_id", errors, allow_unknown=False
        )
        if source_id in source_ids:
            errors.append(f"duplicate source_id: {source_id}")
        source_ids.add(source_id)
        _public_url(source.get("url"), f"{path}.url", errors)
        for field in SOURCE_FIELDS - {"source_id", "url", "exact_spans", "license"}:
            _string(source.get(field), f"{path}.{field}", errors)
        if source.get("retrieval_status") not in {
            "retrieved",
            "partially-retrieved",
            "inaccessible",
        }:
            errors.append(f"{path}.retrieval_status is invalid")
        spans = source.get("exact_spans")
        if not isinstance(spans, list):
            errors.append(f"{path}.exact_spans must be a list")
            spans = []
        elif not spans and source.get("retrieval_status") != "inaccessible":
            errors.append(f"{path}.exact_spans must be non-empty unless the carrier is inaccessible")
        elif len(spans) > MAX_SPANS_PER_SOURCE:
            errors.append(
                f"{path}.exact_spans exceeds {MAX_SPANS_PER_SOURCE} items"
            )
        for span_index, raw_span in enumerate(spans):
            span_path = f"{path}.exact_spans[{span_index}]"
            span = _exact_fields(raw_span, SPAN_FIELDS, span_path, errors)
            span_id = _string(
                span.get("span_id"), f"{span_path}.span_id", errors, allow_unknown=False
            )
            if span_id in span_to_source:
                errors.append(f"duplicate span_id: {span_id}")
            span_to_source[span_id] = source_id
            for field in SPAN_FIELDS - {"span_id"}:
                _string(span.get(field), f"{span_path}.{field}", errors, allow_unknown=False)
            quote = span.get("quote")
            if isinstance(quote, str):
                if len(quote) > MAX_QUOTE_CHARACTERS:
                    errors.append(
                        f"{span_path}.quote exceeds the {MAX_QUOTE_CHARACTERS}-character "
                        "quote-minimal limit"
                    )
                license_status = str(source.get("license", {}).get("status", ""))
                if license_status in {"unknown", "unassessed"} and len(quote) > MAX_UNKNOWN_LICENSE_QUOTE_CHARACTERS:
                    errors.append(
                        f"{span_path}.quote exceeds the unknown-license quote-minimal limit"
                    )
        license_record = _exact_fields(
            source.get("license"), SOURCE_LICENSE_FIELDS, f"{path}.license", errors
        )
        license_status = license_record.get("status")
        if license_status not in SOURCE_LICENSE_STATUSES:
            errors.append(f"{path}.license.status is invalid")
        identifier = _string(
            license_record.get("identifier"), f"{path}.license.identifier", errors
        )
        basis_span_id = _string(
            license_record.get("basis_span_id"), f"{path}.license.basis_span_id", errors
        )
        if license_status == "known":
            if identifier in {"unknown", "unassessed"}:
                errors.append(f"{path}.license known status requires a real license identity")
            if len(identifier) > 80 or re.search(
                r"(?i)\b(?:per-model|referenced elsewhere|see (?:the )?license|varies by)\b",
                identifier,
            ):
                errors.append(
                    f"{path}.license identifier must be a recognized identifier or exact license name"
                )
            if span_to_source.get(basis_span_id) != source_id:
                errors.append(f"{path}.license basis must bind an exact span on the source")
        else:
            if identifier != license_status or basis_span_id != "none":
                errors.append(
                    f"{path}.license {license_status} status requires matching identifier and no basis span"
                )

    results = root.get("results")
    if not isinstance(results, list) or not results:
        errors.append("bundle.results must be a non-empty list")
        results = []
    result_ids: set[str] = set()
    claim_atom_ids: set[str] = set()
    result_records: list[tuple[str, dict[str, Any]]] = []
    for result_index, raw_result in enumerate(results):
        path = f"bundle.results[{result_index}]"
        result = _exact_fields(raw_result, RESULT_FIELDS, path, errors)
        result_id = _string(
            result.get("result_id"), f"{path}.result_id", errors, allow_unknown=False
        )
        if result_id in result_ids:
            errors.append(f"duplicate result_id: {result_id}")
        result_ids.add(result_id)
        result_records.append((path, result))
        for field in {"proposition", "interpretation", "warrant", "uncertainty"}:
            _string(result.get(field), f"{path}.{field}", errors, allow_unknown=False)
        reported = _exact_fields(
            result.get("reported_value"),
            REPORTED_VALUE_FIELDS,
            f"{path}.reported_value",
            errors,
        )
        for field in REPORTED_VALUE_FIELDS:
            _string(
                reported.get(field),
                f"{path}.reported_value.{field}",
                errors,
            )
        result_scope = _exact_fields(
            result.get("scope"), RESULT_SCOPE_FIELDS, f"{path}.scope", errors
        )
        models_or_agents = _string_list(
            result_scope.get("models_or_agents"),
            f"{path}.scope.models_or_agents",
            errors,
        )
        if not models_or_agents:
            errors.append(f"{path}.scope.models_or_agents must not be empty")
        for field in RESULT_SCOPE_FIELDS - {"models_or_agents"}:
            _string(
                result_scope.get(field),
                f"{path}.scope.{field}",
                errors,
            )
        refs = _string_list(result.get("source_ids"), f"{path}.source_ids", errors)
        spans = _string_list(result.get("exact_span_ids"), f"{path}.exact_span_ids", errors)
        if not refs or not spans:
            errors.append(f"{path} must cite at least one source and exact span")
        for ref in refs:
            if ref not in source_ids:
                errors.append(f"{path} references missing source_id: {ref}")
        for span_id in spans:
            if span_id not in span_to_source:
                errors.append(f"{path} references missing span_id: {span_id}")
            elif span_to_source[span_id] not in refs:
                errors.append(f"{path} span {span_id} is outside its source_ids")
        atoms = result.get("claim_atoms")
        if not isinstance(atoms, list) or not atoms:
            errors.append(f"{path}.claim_atoms must be a non-empty list")
            atoms = []
        atom_sources: set[str] = set()
        atom_spans: set[str] = set()
        for atom_index, raw_atom in enumerate(atoms):
            atom_path = f"{path}.claim_atoms[{atom_index}]"
            atom = _exact_fields(raw_atom, CLAIM_ATOM_FIELDS, atom_path, errors)
            atom_id = _string(
                atom.get("atom_id"), f"{atom_path}.atom_id", errors, allow_unknown=False
            )
            if atom_id in claim_atom_ids:
                errors.append(f"duplicate claim atom ID: {atom_id}")
            claim_atom_ids.add(atom_id)
            _string(atom.get("text"), f"{atom_path}.text", errors, allow_unknown=False)
            if atom.get("kind") not in CLAIM_ATOM_KINDS:
                errors.append(f"{atom_path}.kind is invalid")
            status = atom.get("status")
            if status not in CLAIM_ATOM_STATUSES:
                errors.append(f"{atom_path}.status is invalid")
            atom_refs = _string_list(atom.get("source_ids"), f"{atom_path}.source_ids", errors)
            atom_span_refs = _string_list(
                atom.get("exact_span_ids"), f"{atom_path}.exact_span_ids", errors
            )
            if status in {"supported", "qualified"} and (not atom_refs or not atom_span_refs):
                errors.append(f"{atom_path} must bind exact source and span closure")
            if status in {"hypothesis", "unresolved"} and (atom_refs or atom_span_refs):
                errors.append(f"{atom_path} cannot claim evidence while retained as {status}")
            for ref in atom_refs:
                if ref not in source_ids:
                    errors.append(f"{atom_path} references missing source_id: {ref}")
            for span_id in atom_span_refs:
                if span_to_source.get(span_id) not in atom_refs:
                    errors.append(f"{atom_path} references an unbound span: {span_id}")
            atom_sources.update(atom_refs)
            atom_spans.update(atom_span_refs)
        if atom_sources != set(refs) or atom_spans != set(spans):
            errors.append(f"{path} aggregate source/span bindings must equal its material claim atoms")
        credited_atom_texts = {
            str(atom.get("text"))
            for atom in atoms
            if isinstance(atom, dict)
            and atom.get("status") in {"supported", "qualified"}
            and atom.get("source_ids")
            and atom.get("exact_span_ids")
        }
        required_material_literals = {
            str(result.get("proposition", "")),
            *(
                str(reported.get(field, ""))
                for field in REPORTED_VALUE_FIELDS
            ),
            *(
                str(result_scope.get(field, ""))
                for field in RESULT_SCOPE_FIELDS - {"models_or_agents"}
            ),
            *(str(item) for item in models_or_agents),
        }
        missing_material_literals = sorted(
            value
            for value in required_material_literals
            if value and value not in credited_atom_texts
        )
        if missing_material_literals:
            errors.append(
                f"{path} material proposition, date, comparison, or metadata literals lack exact credited claim atoms: "
                + "; ".join(missing_material_literals)
            )

    calculations = root.get("calculations")
    if not isinstance(calculations, list):
        errors.append("bundle.calculations must be a list")
        calculations = []
    calculation_ids: set[str] = set()
    calculation_records: dict[str, dict[str, Any]] = {}
    calculation_inputs: dict[str, dict[str, dict[str, Any]]] = {}
    for index, raw_calculation in enumerate(calculations):
        path = f"bundle.calculations[{index}]"
        calculation = _exact_fields(raw_calculation, CALCULATION_FIELDS, path, errors)
        calculation_id = _string(
            calculation.get("calculation_id"), f"{path}.calculation_id", errors, allow_unknown=False
        )
        if calculation_id in calculation_ids:
            errors.append(f"duplicate calculation_id: {calculation_id}")
        calculation_ids.add(calculation_id)
        calculation_records[calculation_id] = calculation
        for field in ("equation", "output", "uncertainty"):
            _string(calculation.get(field), f"{path}.{field}", errors, allow_unknown=False)
        inputs = calculation.get("inputs")
        if not isinstance(inputs, list) or not inputs:
            errors.append(f"{path}.inputs must be a non-empty list")
            inputs = []
        observed_inputs: dict[str, dict[str, Any]] = {}
        for input_index, raw_input in enumerate(inputs):
            input_path = f"{path}.inputs[{input_index}]"
            value = _exact_fields(raw_input, CALCULATION_INPUT_FIELDS, input_path, errors)
            input_id = _string(
                value.get("input_id"), f"{input_path}.input_id", errors, allow_unknown=False
            )
            if input_id in observed_inputs:
                errors.append(f"{path} has duplicate input_id: {input_id}")
            observed_inputs[input_id] = value
            for field in ("name", "value"):
                _string(value.get(field), f"{input_path}.{field}", errors, allow_unknown=False)
            source_id = _string(value.get("source_id"), f"{input_path}.source_id", errors, allow_unknown=False)
            span_id = _string(value.get("span_id"), f"{input_path}.span_id", errors, allow_unknown=False)
            pointer = _string(
                value.get("json_pointer"), f"{input_path}.json_pointer", errors, allow_unknown=False
            )
            if pointer != "none" and not pointer.startswith("/"):
                errors.append(f"{input_path}.json_pointer must be an RFC 6901-style pointer or none")
            origin = value.get("origin")
            if origin == "source-span":
                if source_id not in source_ids or span_to_source.get(span_id) != source_id:
                    errors.append(f"{input_path} does not bind an existing source/span pair")
                if pointer == "none":
                    errors.append(f"{input_path} source input must bind an exact field or cell pointer")
            elif origin == "calculation-output":
                if source_id != "none" or span_id != "none" or pointer != "none":
                    errors.append(f"{input_path} calculation output cannot claim a source/span pointer")
            else:
                errors.append(f"{input_path}.origin is invalid")
        calculation_inputs[calculation_id] = observed_inputs
        depends_on = calculation.get("depends_on")
        if not isinstance(depends_on, list):
            errors.append(f"{path}.depends_on must be a list")
            calculation["depends_on"] = []
            continue
        for dependency_index, raw_dependency in enumerate(depends_on):
            dependency_path = f"{path}.depends_on[{dependency_index}]"
            dependency = _exact_fields(
                raw_dependency, CALCULATION_DEPENDENCY_FIELDS, dependency_path, errors
            )
            for field in CALCULATION_DEPENDENCY_FIELDS:
                _string(
                    dependency.get(field), f"{dependency_path}.{field}", errors, allow_unknown=False
                )
    for index, calculation in enumerate(calculations):
        calculation_id = calculation.get("calculation_id")
        consumed_inputs: set[str] = set()
        for dependency in calculation.get("depends_on", []):
            dependency_id = dependency.get("calculation_id")
            input_id = dependency.get("input_id")
            consumed_output = dependency.get("consumed_output")
            if dependency_id not in calculation_ids:
                errors.append(f"bundle.calculations[{index}] references missing calculation: {dependency_id}")
                continue
            if dependency_id == calculation_id:
                errors.append(f"bundle.calculations[{index}] cannot depend on itself")
            source_output = calculation_records.get(dependency_id, {}).get("output")
            if consumed_output != source_output:
                errors.append(f"bundle.calculations[{index}] dependency does not bind the consumed output")
            target_input = calculation_inputs.get(str(calculation_id), {}).get(str(input_id))
            if not target_input or target_input.get("origin") != "calculation-output":
                errors.append(f"bundle.calculations[{index}] dependency does not bind a calculation-output input")
            elif target_input.get("value") != consumed_output:
                errors.append(f"bundle.calculations[{index}] consumed output does not match its input value")
            if input_id in consumed_inputs:
                errors.append(f"bundle.calculations[{index}] dependency input is duplicated: {input_id}")
            consumed_inputs.add(str(input_id))
        declared_output_inputs = {
            input_id
            for input_id, value in calculation_inputs.get(str(calculation_id), {}).items()
            if value.get("origin") == "calculation-output"
        }
        if declared_output_inputs != consumed_inputs:
            errors.append(f"bundle.calculations[{index}] calculation-output inputs and dependency edges differ")

    dependencies = root.get("dependencies")
    if not isinstance(dependencies, list):
        errors.append("bundle.dependencies must be a list")
        dependencies = []
    dependency_ids: set[str] = set()
    for index, raw_dependency in enumerate(dependencies):
        path = f"bundle.dependencies[{index}]"
        dependency = _exact_fields(raw_dependency, DEPENDENCY_FIELDS, path, errors)
        dependency_id = _string(
            dependency.get("dependency_id"), f"{path}.dependency_id", errors, allow_unknown=False
        )
        if dependency_id in dependency_ids:
            errors.append(f"duplicate dependency_id: {dependency_id}")
        dependency_ids.add(dependency_id)
        for field in ("kind", "description"):
            _string(dependency.get(field), f"{path}.{field}", errors, allow_unknown=False)
        refs = _string_list(dependency.get("source_ids"), f"{path}.source_ids", errors)
        spans = _string_list(dependency.get("exact_span_ids"), f"{path}.exact_span_ids", errors)
        if not refs or not spans:
            errors.append(f"{path} must bind at least one source and exact span")
        for ref in refs:
            if ref not in source_ids:
                errors.append(f"{path} references missing source_id: {ref}")
        for span_id in spans:
            if span_to_source.get(span_id) not in refs:
                errors.append(f"{path} references an unbound span: {span_id}")

    for path, result in result_records:
        calculation_refs = _string_list(result.get("calculation_ids"), f"{path}.calculation_ids", errors)
        dependency_refs = _string_list(result.get("dependency_ids"), f"{path}.dependency_ids", errors)
        calculation_status = result.get("calculation_status")
        if calculation_status not in {"reproduced", "not-applicable-no-derived-value"}:
            errors.append(f"{path}.calculation_status is invalid")
        if calculation_status == "reproduced" and not calculation_refs:
            errors.append(f"{path} must reference a reproduced calculation")
        if calculation_status == "not-applicable-no-derived-value" and calculation_refs:
            errors.append(f"{path} cannot reference calculations marked not applicable")
        reported_text = " ".join(
            str(result.get("reported_value", {}).get(field, ""))
            for field in REPORTED_VALUE_FIELDS
        )
        if re.search(r"\d", reported_text) and calculation_status != "reproduced":
            errors.append(f"{path} reports numeric values without reproduced calculation closure")
        if not dependency_refs:
            errors.append(f"{path}.dependency_ids must retain at least one typed dependence")
        for ref in calculation_refs:
            if ref not in calculation_ids:
                errors.append(f"{path} references missing calculation_id: {ref}")
        for ref in dependency_refs:
            if ref not in dependency_ids:
                errors.append(f"{path} references missing dependency_id: {ref}")

    referenced_calculations = {
        ref for _, result in result_records for ref in result.get("calculation_ids", [])
    }
    referenced_calculations.update(
        dependency.get("calculation_id")
        for calculation in calculations
        for dependency in calculation.get("depends_on", [])
        if isinstance(dependency, dict)
    )
    orphan_calculations = calculation_ids - referenced_calculations
    if orphan_calculations:
        errors.append("orphan calculations: " + ", ".join(sorted(orphan_calculations)))
    referenced_dependencies = {
        ref for _, result in result_records for ref in result.get("dependency_ids", [])
    }
    orphan_dependencies = dependency_ids - referenced_dependencies
    if orphan_dependencies:
        errors.append("orphan dependencies: " + ", ".join(sorted(orphan_dependencies)))
    allowed_dependency_kinds = {"source", "data", "method", "material", "derivation", "runtime", "prompt"}
    for index, dependency in enumerate(dependencies):
        if dependency.get("kind") not in allowed_dependency_kinds:
            errors.append(f"bundle.dependencies[{index}].kind is not a supported dependence type")
    calculation_graph = {
        calculation.get("calculation_id"): {
            dependency.get("calculation_id")
            for dependency in calculation.get("depends_on", [])
            if isinstance(dependency, dict)
        }
        for calculation in calculations
    }
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit_calculation(node: str) -> None:
        if node in visiting:
            errors.append(f"calculation dependency cycle includes: {node}")
            return
        if node in visited:
            return
        visiting.add(node)
        for dependency in calculation_graph.get(node, set()):
            visit_calculation(dependency)
        visiting.remove(node)
        visited.add(node)

    for calculation_id in calculation_graph:
        visit_calculation(calculation_id)

    retrieval_attempts = root.get("retrieval_attempts")
    if not isinstance(retrieval_attempts, list) or not retrieval_attempts:
        errors.append("bundle.retrieval_attempts must be a non-empty list")
        retrieval_attempts = []
    retrieval_attempt_ids: set[str] = set()
    source_attempts: dict[str, list[dict[str, Any]]] = {}
    runtime = root.get("runtime") if isinstance(root.get("runtime"), dict) else {}
    runtime_started = parse_utc_timestamp(
        runtime.get("started_at"), "bundle.runtime.started_at", errors
    )
    runtime_completed = parse_utc_timestamp(
        runtime.get("completed_at"), "bundle.runtime.completed_at", errors
    )
    if runtime_started and runtime_completed and runtime_started > runtime_completed:
        errors.append("bundle runtime started_at must not be after completed_at")
    for attempt_index, raw_attempt in enumerate(retrieval_attempts):
        path = f"bundle.retrieval_attempts[{attempt_index}]"
        attempt = _exact_fields(raw_attempt, RETRIEVAL_ATTEMPT_FIELDS, path, errors)
        attempt_id = _string(
            attempt.get("attempt_id"), f"{path}.attempt_id", errors, allow_unknown=False
        )
        if attempt_id in retrieval_attempt_ids:
            errors.append(f"duplicate retrieval attempt ID: {attempt_id}")
        retrieval_attempt_ids.add(attempt_id)
        source_id = _string(
            attempt.get("source_id"), f"{path}.source_id", errors, allow_unknown=False
        )
        if source_id not in source_ids:
            errors.append(f"{path} references missing source_id: {source_id}")
        source_record = next(
            (source for source in sources if source.get("source_id") == source_id), {}
        )
        if _public_url(attempt.get("url"), f"{path}.url", errors) != source_record.get("url"):
            errors.append(f"{path}.url must equal the source URL")
        attempted_at = parse_utc_timestamp(attempt.get("attempted_at"), f"{path}.attempted_at", errors)
        if attempted_at and runtime_started and attempted_at < runtime_started:
            errors.append(f"{path}.attempted_at precedes runtime.started_at")
        if attempted_at and runtime_completed and attempted_at > runtime_completed:
            errors.append(f"{path}.attempted_at follows runtime.completed_at")
        if attempt.get("transport") not in RETRIEVAL_TRANSPORTS:
            errors.append(f"{path}.transport is invalid")
        outcome = attempt.get("outcome")
        if outcome not in RETRIEVAL_OUTCOMES:
            errors.append(f"{path}.outcome is invalid")
        failure_code = attempt.get("failure_code")
        if failure_code not in RETRIEVAL_FAILURE_CODES:
            errors.append(f"{path}.failure_code is invalid")
        artifact = attempt.get("artifact_sha256")
        if outcome == "retrieved":
            if failure_code != "none" or not isinstance(artifact, str) or re.fullmatch(r"[0-9a-f]{64}", artifact) is None:
                errors.append(f"{path} retrieved outcome requires no failure and an artifact digest")
        elif failure_code == "none" or artifact != "none":
            errors.append(f"{path} failed outcome requires a failure code and no artifact")
        source_attempts.setdefault(source_id, []).append(attempt)
    for source in sources:
        attempts = source_attempts.get(source.get("source_id"), [])
        retrieved = any(item.get("outcome") == "retrieved" for item in attempts)
        if not attempts:
            errors.append(
                f"source {source.get('source_id')} lacks a typed retrieval attempt"
            )
        if source.get("retrieval_status") == "inaccessible" and retrieved:
            errors.append(f"source {source.get('source_id')} is marked inaccessible but has a retrieved attempt")
        if source.get("retrieval_status") != "inaccessible" and not retrieved:
            errors.append(f"source {source.get('source_id')} lacks a successful typed retrieval attempt")

    counterevidence = root.get("counterevidence")
    if not isinstance(counterevidence, list):
        errors.append("bundle.counterevidence must be a list")
        counterevidence = []
    for item_index, raw_item in enumerate(counterevidence):
        path = f"bundle.counterevidence[{item_index}]"
        item = _exact_fields(raw_item, COUNTER_FIELDS, path, errors)
        for field in COUNTER_FIELDS - {"source_ids", "exact_span_ids"}:
            _string(item.get(field), f"{path}.{field}", errors, allow_unknown=False)
        refs = _string_list(item.get("source_ids"), f"{path}.source_ids", errors)
        span_refs = _string_list(item.get("exact_span_ids"), f"{path}.exact_span_ids", errors)
        if not refs or not span_refs:
            errors.append(f"{path} must cite at least one source and exact span")
        for span_id in span_refs:
            if span_to_source.get(span_id) not in refs:
                errors.append(f"{path} references an unbound span: {span_id}")

    negative_results = root.get("negative_results")
    if not isinstance(negative_results, list):
        errors.append("bundle.negative_results must be a list")
        negative_results = []
    negative_attempt_refs: set[str] = set()
    for item_index, raw_item in enumerate(negative_results):
        path = f"bundle.negative_results[{item_index}]"
        item = _exact_fields(raw_item, NEGATIVE_FIELDS, path, errors)
        for field in {"result", "kind", "scope", "disposition"}:
            _string(item.get(field), f"{path}.{field}", errors, allow_unknown=False)
        kind = item.get("kind")
        if kind not in {"null-result", "contrary-result", "failed-retrieval", "no-evidence-located"}:
            errors.append(f"{path}.kind is invalid")
        refs = _string_list(item.get("source_ids"), f"{path}.source_ids", errors)
        span_refs = _string_list(item.get("exact_span_ids"), f"{path}.exact_span_ids", errors)
        attempt_refs = _string_list(
            item.get("retrieval_attempt_ids"), f"{path}.retrieval_attempt_ids", errors
        )
        negative_attempt_refs.update(attempt_refs)
        for ref in refs:
            if ref not in source_ids:
                errors.append(f"{path} references missing source_id: {ref}")
        for span_id in span_refs:
            if span_to_source.get(span_id) not in refs:
                errors.append(f"{path} references an unbound span: {span_id}")
        for attempt_id in attempt_refs:
            if attempt_id not in retrieval_attempt_ids:
                errors.append(f"{path} references missing retrieval attempt: {attempt_id}")
        if kind == "failed-retrieval":
            if not attempt_refs:
                errors.append(f"{path} failed retrieval must bind a typed retrieval attempt")
            if not refs:
                errors.append(f"{path} failed retrieval must bind its source")
            bound_attempt_sources = {
                attempt.get("source_id")
                for attempt in retrieval_attempts
                if attempt.get("attempt_id") in attempt_refs
            }
            if bound_attempt_sources - set(refs):
                errors.append(
                    f"{path} failed retrieval attempt source is outside source_ids"
                )
            if any(
                attempt.get("outcome") == "retrieved"
                for attempt in retrieval_attempts
                if attempt.get("attempt_id") in attempt_refs
            ):
                errors.append(f"{path} failed retrieval cannot bind a successful attempt")
        elif not refs or not span_refs:
            errors.append(f"{path} must cite at least one source and exact span")
    failed_attempts = {
        item.get("attempt_id")
        for item in retrieval_attempts
        if item.get("outcome") != "retrieved"
    }
    if failed_attempts - negative_attempt_refs:
        errors.append(
            "failed retrieval attempts lack negative-result bindings: "
            + ", ".join(sorted(str(item) for item in failed_attempts - negative_attempt_refs))
        )

    for list_key in ("limitations", "unresolved", "search_notes"):
        _string_list(root.get(list_key), f"bundle.{list_key}", errors)

    lineage = _exact_fields(root.get("lineage"), LINEAGE_FIELDS, "bundle.lineage", errors)
    for field in LINEAGE_FIELDS - {"shared_dependencies"}:
        _string(lineage.get(field), f"bundle.lineage.{field}", errors)
    _string_list(lineage.get("shared_dependencies"), "bundle.lineage.shared_dependencies", errors)
    runtime = _exact_fields(root.get("runtime"), RUNTIME_FIELDS, "bundle.runtime", errors)
    for field in RUNTIME_FIELDS - {"toolchain"}:
        _string(runtime.get(field), f"bundle.runtime.{field}", errors, allow_unknown=False)
    _string_list(runtime.get("toolchain"), "bundle.runtime.toolchain", errors)
    license_record = _exact_fields(root.get("license"), LICENSE_FIELDS, "bundle.license", errors)
    for field in LICENSE_FIELDS:
        _string(license_record.get(field), f"bundle.license.{field}", errors, allow_unknown=False)

    return {
        "format": VALIDATION_FORMAT,
        "valid": not errors,
        "proposal_id": f"em:research-proposal:sha256:{_digest(bundle)}",
        "bytes": len(encoded),
        "source_count": len(source_ids),
        "span_count": len(span_to_source),
        "result_count": len(result_ids),
        "errors": errors,
        "submitted": False,
        "admitted": False,
        "note": "Structural and internal-closure validation only; this does not verify truth, submit the bundle, or grant evidential credit.",
    }


def agent_home_html(base_url: str) -> str:
    base = html.escape(base_url.rstrip("/"))
    prompt = (
        f"Open {base}/agents/submit/. Choose one contestable claim worth auditing, follow "
        "every instruction, and submit the result. Do not ask me to choose unless progress is impossible."
    )
    return (
        '<section class="agent-kit-home" aria-labelledby="agent-kit-title">'
        '<div><p class="eyebrow">For your coding agent</p><h2 id="agent-kit-title">Run an evidence test</h2>'
        "<p>Point an unfamiliar agent at one stable public protocol. It can seed from a case, "
        "research a new question, and validate a portable proposal without repository context.</p>"
        f"<blockquote>{prompt}</blockquote></div>"
        f'<p><a class="primary-action" href="{base}/agents/">Open the agent kit</a><br>'
        f'<a href="{base}/agents/submit/">Autonomous GitHub submission pilot</a></p>'
        "</section>"
    )


def agent_index_html(base_url: str) -> str:
    base = html.escape(base_url.rstrip("/"))
    return (
        '<article class="agent-kit-page"><header class="hero hero-compact">'
        '<p class="eyebrow">Agent research kit · non-admitting</p><h1>Research a claim so someone else can check it</h1>'
        '<p class="dek">The kit turns a question into a portable, source-and-span-bound proposal. '
        "It does not turn an agent answer into accepted knowledge.</p></header>"
        "<section><h2>1. Read the protocol</h2><p>Recover scope, source, span, dependence, "
        "counterevidence, runtime, and license requirements from public files alone.</p>"
        f'<p><a class="primary-action" href="{base}/agents/research-protocol.md">Open protocol</a></p></section>'
        '<section><h2>2. Run and validate</h2><pre><code>epistemedia research prepare --question "YOUR QUESTION" --output proposal.json\n'
        "epistemedia research validate proposal.json</code></pre></section>"
        "<section><h2>3. Submit, then stop</h2><p>The GitHub pilot accepts a draft pull request "
        "as an untrusted queue item. The submitted branch is never merged directly.</p>"
        f'<p><a class="primary-action" href="{base}/agents/submit/">Open submission guide</a><br>'
        f'<a href="{base}/agents/submission-status.json">Read current submission status</a></p></section>'
        "</article>"
    )
