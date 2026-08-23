"""Build and verify the EM-0026 source, span, warrant, and dependence ledger.

Network retrieval is deliberately outside deterministic validation.  The two capture
subcommands turn already-downloaded public artifacts into byte-bound receipts.  The
default build consumes only committed receipts and raw answer artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

PACKET = Path(__file__).resolve().parent
REPO = PACKET.parents[2]
ANSWERS = PACKET / "answers-v2"
TRACES = PACKET / "traces-v2"
CONFIG = PACKET / "source-normalization-v1.json"
READBACKS = PACKET / "source-readbacks-v1.json"
SPAN_READBACKS = PACKET / "span-readbacks-v1.json"
LEDGER = PACKET / "evidence-ledger-v1.json"


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def digest_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def stable_id(prefix: str, *parts: str) -> str:
    payload = "\0".join(parts).encode()
    return f"{prefix}:sha256:{digest_bytes(payload)}"


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = value.translate(
        str.maketrans(
            {
                "“": '"',
                "”": '"',
                "‘": "'",
                "’": "'",
                "‐": "-",
                "‑": "-",
                "–": "-",
                "—": "-",
                "−": "-",
                "…": "...",
                "\u00a0": " ",
            }
        )
    )
    return " ".join(value.split()).strip()


def quote_body(value: str) -> str:
    value = normalize(value).strip()
    while len(value) >= 2 and value[0] == value[-1] == '"':
        value = value[1:-1].strip()
    return value


def ordered_fragments(quote: str, source: str) -> tuple[bool, list[str]]:
    fragments = [
        quote_body(item).strip(" .;:")
        for item in re.split(r"(?:\.{3}|\"\s*;\s*\"|\"\s*;|;\s*\")", quote)
    ]
    fragments = [item for item in fragments if len(item) >= 12]
    if len(fragments) < 2:
        return False, fragments
    cursor = 0
    for fragment in fragments:
        found = source.find(fragment, cursor)
        if found < 0:
            return False, fragments
        cursor = found + len(fragment)
    return True, fragments


def answers() -> list[tuple[str, dict[str, Any]]]:
    return [(path.stem, load(path)) for path in sorted(ANSWERS.glob("*.json"))]


def capture_readbacks(capture_root: Path, output: Path) -> None:
    config = load(CONFIG)
    raw_urls = {source["url"] for _, answer in answers() for source in answer["sources"]}
    mappings = {item["requested_url"]: item for item in config["url_mappings"]}
    if raw_urls != set(mappings):
        missing = sorted(raw_urls - set(mappings))
        extra = sorted(set(mappings) - raw_urls)
        raise SystemExit(f"URL mapping coverage drift; missing={missing}, extra={extra}")

    records = []
    for url in sorted(mappings):
        mapping = mappings[url]
        body_path = capture_root / mapping["capture_body"]
        if not body_path.is_file():
            raise SystemExit(f"capture body missing: {body_path}")
        payload = body_path.read_bytes()
        status = int(mapping["http_status"])
        usable = bool(mapping.get("usable", 200 <= status < 300))
        records.append(
            {
                "requested_url": url,
                "resolved_url": url,
                "redirect_chain": [],
                "retrieval_status": "retrieved" if usable else "inaccessible",
                "http_status": status,
                "media_type": mapping["media_type"],
                "captured_bytes": len(payload),
                "captured_sha256": digest_bytes(payload),
                "edition_id": mapping["edition_id"],
            }
        )
    document = {
        "schema": "https://epistemedia.org/research/source-readbacks-v1.json",
        "task_id": "EM-0026",
        "captured_at": config["readback_captured_at"],
        "capture_method": (
            "credential-free curl GET with redirects enabled; response bodies "
            "remained outside the repository"
        ),
        "records": records,
        "limitations": [
            "A successful HTTP read proves only that this carrier returned bytes at capture time.",
            "Wiley and OpenReview returned HTTP 403; PubMed returned HTTP 203 "
            "with a cookie-interstitial body. Alternate authoritative carriers "
            "were not substituted for their URL-level status.",
            "Mendeley landing pages returned HTTP 200, but its credential-free "
            "file API returned HTTP 401 and no supplementary file bytes were captured.",
        ],
    }
    output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")


def capture_span_readbacks(capture_root: Path, output: Path) -> None:
    config = load(CONFIG)
    editions = {item["edition_id"]: item for item in config["editions"]}
    url_map = {item["requested_url"]: item for item in config["url_mappings"]}
    readbacks = {item["requested_url"]: item for item in load(READBACKS)["records"]}
    source_texts: dict[str, tuple[str, str]] = {}
    for edition_id, edition in editions.items():
        text_path = capture_root / edition["source_text_file"]
        if not text_path.is_file():
            raise SystemExit(f"source text missing: {text_path}")
        payload = text_path.read_bytes()
        source_texts[edition_id] = (
            normalize(payload.decode(errors="replace")),
            digest_bytes(payload),
        )

    records = []
    for run_id, answer in answers():
        for source in answer["sources"]:
            mapping = url_map[source["url"]]
            edition_id = mapping["edition_id"]
            source_text, text_digest = source_texts[edition_id]
            citation_accessible = readbacks[source["url"]]["retrieval_status"] == "retrieved"
            for span in source["exact_spans"]:
                quote = quote_body(span["quote"])
                exact = bool(quote) and quote in source_text
                fragments_match, fragments = ordered_fragments(quote, source_text)
                if exact:
                    match_status = "exact-normalized-match"
                elif fragments_match:
                    match_status = "ordered-fragment-match"
                else:
                    match_status = "unresolved"
                occurrence_id = f"{run_id}:{source['source_id']}:{span['span_id']}"
                records.append(
                    {
                        "span_occurrence_id": occurrence_id,
                        "run_id": run_id,
                        "source_id": source["source_id"],
                        "span_id": span["span_id"],
                        "edition_id": edition_id,
                        "locator": span["locator"],
                        "quote_sha256": digest_bytes(span["quote"].encode()),
                        "span_root_id": stable_id(
                            "span",
                            edition_id,
                            normalize(span["locator"]),
                            normalize(span["quote"]),
                        ),
                        "match_status": match_status,
                        "citation_carrier_accessible": citation_accessible,
                        "source_text_sha256": text_digest,
                        "matched_fragments": fragments if fragments_match and not exact else [],
                    }
                )
    document = {
        "schema": "https://epistemedia.org/research/span-readbacks-v1.json",
        "task_id": "EM-0026",
        "captured_at": config["readback_captured_at"],
        "normalization": (
            "Unicode NFKC, typographic punctuation normalization, and whitespace collapse"
        ),
        "credit_rule": (
            "Only exact-normalized-match and ordered-fragment-match create exact-span "
            "roots; semantic warrant remains a separate review."
        ),
        "records": records,
        "limitations": [
            "Text extraction can reorder tables, formulas, and multi-column PDF content.",
            "An ordered-fragment match confirms each quoted fragment in sequence, "
            "not a contiguous sentence.",
            "A text match does not by itself establish that the source warrants "
            "an agent proposition.",
        ],
    }
    output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")


def build_ledger() -> dict[str, Any]:
    config = load(CONFIG)
    readback_document = load(READBACKS)
    span_document = load(SPAN_READBACKS)
    readbacks = {item["requested_url"]: item for item in readback_document["records"]}
    span_readbacks = {item["span_occurrence_id"]: item for item in span_document["records"]}
    editions = {item["edition_id"]: item for item in config["editions"]}
    works = {item["work_id"]: item for item in config["works"]}
    group_for_result = {
        occurrence: group
        for group in config["claim_groups"]
        for occurrence in group["result_occurrences"]
    }
    corrections_by_occurrence: dict[str, list[str]] = {}
    for correction in config["corrections"]:
        for occurrence in correction["raw_occurrences"]:
            corrections_by_occurrence.setdefault(occurrence, []).append(correction["correction_id"])

    report_records = []
    citation_records = []
    span_records = []
    claim_records = []
    dependence_edges = list(config["dependence_edges"])
    for group in config["claim_groups"]:
        dependence_edges.extend(
            [
                {
                    "dimension": "data",
                    "from": group["warrant_id"],
                    "to": group["data_root"],
                    "status": "declared-reviewed-lineage",
                },
                {
                    "dimension": "method",
                    "from": group["warrant_id"],
                    "to": group["method_root"],
                    "status": "declared-reviewed-lineage",
                },
                {
                    "dimension": "derivation",
                    "from": group["warrant_id"],
                    "to": group["derivation_root"],
                    "status": "declared-reviewed-lineage",
                },
            ]
        )
    seen_result_occurrences: set[str] = set()

    for run_id, answer in answers():
        answer_path = ANSWERS / f"{run_id}.json"
        trace = load(TRACES / f"{run_id}.json")
        report_records.append(
            {
                "run_id": run_id,
                "answer_path": str(answer_path.relative_to(REPO)),
                "answer_sha256": digest_bytes(answer_path.read_bytes()),
                "answer_bytes": len(answer_path.read_bytes()),
                "trace_path": str((TRACES / f"{run_id}.json").relative_to(REPO)),
                "requested_model_profile": trace["requested_model_profile"],
                "reported_model_identity": trace["reported_model_identity"],
                "prompt_sha256": trace["prompt"]["sha256"],
                "retrieval_infrastructure": trace["tool_configuration"]["reported"],
                "status": trace["status"],
            }
        )
        dependence_edges.extend(
            [
                {
                    "dimension": "model_profile",
                    "from": f"report:{run_id}",
                    "to": f"model-profile:{trace['requested_model_profile']}",
                    "status": "requested-not-independent",
                },
                {
                    "dimension": "prompt",
                    "from": f"report:{run_id}",
                    "to": f"prompt:sha256:{trace['prompt']['sha256']}",
                    "status": "shared-exact-bytes",
                },
                {
                    "dimension": "retrieval_infrastructure",
                    "from": f"report:{run_id}",
                    "to": "retrieval:codex-public-web-implementation-unknown",
                    "status": "unknown-or-shared",
                },
            ]
        )

        source_by_id = {item["source_id"]: item for item in answer["sources"]}
        span_to_source: dict[str, str] = {}
        for source in answer["sources"]:
            if source["url"] not in readbacks:
                raise SystemExit(f"missing readback for {source['url']}")
            readback = readbacks[source["url"]]
            edition = editions[readback["edition_id"]]
            occurrence_id = f"{run_id}:{source['source_id']}"
            source_span_occurrences = []
            for span in source["exact_spans"]:
                span_occurrence_id = f"{occurrence_id}:{span['span_id']}"
                if span_occurrence_id not in span_readbacks:
                    raise SystemExit(f"missing span readback for {span_occurrence_id}")
                review = span_readbacks[span_occurrence_id]
                span_to_source[span["span_id"]] = source["source_id"]
                source_span_occurrences.append(span_occurrence_id)
                span_records.append(
                    {
                        **review,
                        "requested_url": source["url"],
                        "source_work_id": edition["work_id"],
                        "quote": span["quote"],
                        "supports_declared_by_raw_answer": span["supports"],
                        "license_treatment": edition["license_treatment"],
                    }
                )
                dependence_edges.append(
                    {
                        "dimension": "exact_span",
                        "from": f"citation:{occurrence_id}",
                        "to": review["span_root_id"],
                        "status": review["match_status"],
                    }
                )
            unresolved = (
                readback["retrieval_status"] != "retrieved"
                or any(
                    span_readbacks[item]["match_status"] == "unresolved"
                    for item in source_span_occurrences
                )
                or any(
                    correction_id == "correction:mendeley-file-readback"
                    for correction_id in corrections_by_occurrence.get(occurrence_id, [])
                )
            )
            citation_records.append(
                {
                    "citation_occurrence_id": occurrence_id,
                    "run_id": run_id,
                    "raw_source_id": source["source_id"],
                    "raw_title": source["title"],
                    "requested_url": source["url"],
                    "readback": readback,
                    "source_work_id": edition["work_id"],
                    "edition_id": edition["edition_id"],
                    "span_occurrence_ids": source_span_occurrences,
                    "license": edition["license"],
                    "license_treatment": edition["license_treatment"],
                    "correction_ids": corrections_by_occurrence.get(occurrence_id, []),
                    "resolution_status": (
                        "unresolved" if unresolved else "resolved-and-span-matched"
                    ),
                }
            )
            dependence_edges.extend(
                [
                    {
                        "dimension": "requested_url",
                        "from": f"citation:{occurrence_id}",
                        "to": source["url"],
                        "status": readback["retrieval_status"],
                    },
                    {
                        "dimension": "source_work",
                        "from": f"citation:{occurrence_id}",
                        "to": edition["work_id"],
                        "status": "normalized",
                    },
                    {
                        "dimension": "edition",
                        "from": f"citation:{occurrence_id}",
                        "to": edition["edition_id"],
                        "status": "examined",
                    },
                ]
            )

        for result in answer["results"]:
            occurrence_id = f"{run_id}:{result['result_id']}"
            seen_result_occurrences.add(occurrence_id)
            group = group_for_result.get(occurrence_id)
            if group is None:
                raise SystemExit(f"unreviewed result occurrence: {occurrence_id}")
            missing_sources = sorted(set(result["source_ids"]) - set(source_by_id))
            missing_spans = sorted(set(result["exact_span_ids"]) - set(span_to_source))
            if missing_sources or missing_spans:
                raise SystemExit(
                    f"broken raw result linkage for {occurrence_id}: "
                    f"sources={missing_sources}, spans={missing_spans}"
                )
            linked_citations = [f"{run_id}:{source_id}" for source_id in result["source_ids"]]
            linked_spans = [
                f"{run_id}:{span_to_source[span_id]}:{span_id}"
                for span_id in result["exact_span_ids"]
            ]
            linked_citation_records = [
                next(
                    item
                    for item in citation_records
                    if item["citation_occurrence_id"] == citation_id
                )
                for citation_id in linked_citations
            ]
            source_unresolved = any(
                item["resolution_status"] == "unresolved"
                for item in linked_citation_records
            )
            span_unresolved = any(
                span_readbacks[span_id]["match_status"] == "unresolved" for span_id in linked_spans
            )
            correction_ids = corrections_by_occurrence.get(occurrence_id, [])
            semantic_no_credit = any(
                item["correction_id"] in correction_ids
                and item["kind"] == "semantic-warrant"
                for item in config["corrections"]
            )
            no_credit_correction = any(
                item["correction_id"] in correction_ids
                and ("no credit" in item["effect"] or "withheld" in item["effect"])
                for item in config["corrections"]
            )
            if source_unresolved or span_unresolved:
                status = "unresolved-no-warrant-credit"
            elif semantic_no_credit:
                status = "independent-review-no-credit-insufficient-span-semantics"
            elif no_credit_correction:
                status = "qualified-no-credit-for-corrected-component"
            else:
                status = "author-candidate-supported-pending-independent-review"
            claim_records.append(
                {
                    "claim_occurrence_id": occurrence_id,
                    "warrant_id": group["warrant_id"],
                    "raw_proposition": result["proposition"],
                    "canonical_proposition": group["canonical_proposition"],
                    "source_citation_occurrence_ids": linked_citations,
                    "span_occurrence_ids": linked_spans,
                    "correction_ids": correction_ids,
                    "review_status": status,
                    "warrant_dimensions": config["warrant_dimension_defaults"],
                }
            )
            for citation_id, citation_record in zip(
                linked_citations, linked_citation_records, strict=True
            ):
                dependence_edges.append(
                    {
                        "dimension": "upstream_citation",
                        "from": f"claim:{occurrence_id}",
                        "to": f"citation:{citation_id}",
                        "status": (
                            "declared-and-resolved"
                            if citation_record["resolution_status"]
                            == "resolved-and-span-matched"
                            else "declared-but-citation-unresolved"
                        ),
                    }
                )

    if seen_result_occurrences != set(group_for_result):
        raise SystemExit(
            "claim-group coverage drift; extra="
            f"{sorted(set(group_for_result) - seen_result_occurrences)}"
        )

    match_statuses = {"exact-normalized-match", "ordered-fragment-match"}
    exact_span_roots = {
        item["span_root_id"] for item in span_records if item["match_status"] in match_statuses
    }
    claims_by_warrant: dict[str, list[dict[str, Any]]] = {}
    for item in claim_records:
        claims_by_warrant.setdefault(item["warrant_id"], []).append(item)
    candidate_warrants = {
        group["warrant_id"]
        for group in config["claim_groups"]
        if group["review_status"].startswith("candidate-supported")
        and any(
            span_readbacks[span_id]["match_status"] in match_statuses
            for claim in claims_by_warrant[group["warrant_id"]]
            for span_id in claim["span_occurrence_ids"]
        )
    }
    cited_work_ids = {item["source_work_id"] for item in citation_records}
    cited_edition_ids = {item["edition_id"] for item in citation_records}
    inaccessible = [
        item for item in citation_records if item["readback"]["retrieval_status"] == "inaccessible"
    ]
    unresolved = [item for item in citation_records if item["resolution_status"] == "unresolved"]
    corrected_claims = {
        occurrence
        for correction in config["corrections"]
        if correction["kind"]
        in {
            "scope",
            "internal-source-conflict",
            "dependence",
            "edition",
            "semantic-warrant",
        }
        for occurrence in correction["raw_occurrences"]
        if occurrence in seen_result_occurrences or occurrence.endswith(":answer")
    }
    counts = {
        "captured_reports": len(report_records),
        "citation_occurrences": len(citation_records),
        "cited_urls": len({item["requested_url"] for item in citation_records}),
        "resolving_url_roots": len(
            {
                item["requested_url"]
                for item in citation_records
                if item["readback"]["retrieval_status"] == "retrieved"
            }
        ),
        "source_work_roots": len(cited_work_ids),
        "examined_edition_roots": len(cited_edition_ids),
        "raw_span_occurrences": len(span_records),
        "exact_span_roots": len(exact_span_roots),
        "raw_claim_occurrences": len(claim_records),
        "candidate_warrant_roots": len(candidate_warrants),
        "independently_confirmed_warrant_roots": 0,
        "non_resolving_citations": 0,
        "inaccessible_citations": len(inaccessible),
        "invalid_citations": 0,
        "unsupported_or_force_raised_claims": len(corrected_claims),
        "unresolved_citations": len(unresolved),
    }
    return {
        "schema": "https://epistemedia.org/research/agent-citation-evidence-ledger-v1.json",
        "task_id": "EM-0026",
        "protocol_id": "em-0026-agent-citation-trace-v2",
        "status": "research-only-author-review-complete-independent-review-required",
        "evidence_cutoff": config["review_cutoff"],
        "readback_captured_at": config["readback_captured_at"],
        "count_grammar": config["count_grammar"],
        "counts": counts,
        "reports": report_records,
        "works": [works[item] for item in sorted(cited_work_ids)],
        "editions": [editions[item] for item in sorted(cited_edition_ids)],
        "citations": citation_records,
        "spans": span_records,
        "claims": claim_records,
        "candidate_warrants": [
            {
                **{key: value for key, value in group.items() if key != "result_occurrences"},
                "independent_review_status": "pending",
            }
            for group in config["claim_groups"]
            if group["warrant_id"] in candidate_warrants
        ],
        "dependence_edges": dependence_edges,
        "corrections": config["corrections"],
        "limitations": [
            "The eight reports share exact prompt bytes, Codex runtime lineage, and "
            "unknown or shared retrieval infrastructure; they are observations, not "
            "independent evidence roots.",
            "Candidate warrant roots are author-side normalization results and remain "
            "zero independently confirmed roots until a fresh-clone reviewer repeats "
            "source and count checks.",
            "HTTP readback, text matching, and semantic warrant are separate gates.",
            "No universal claim about all agents, current products, or all web sources "
            "is authorized.",
        ],
    }


def verify() -> dict[str, Any]:
    ledger = load(LEDGER)
    rebuilt = build_ledger()
    if ledger != rebuilt:
        raise SystemExit(
            "evidence ledger is not the deterministic build of raw captures and reviews"
        )
    if ledger["counts"]["captured_reports"] != 8:
        raise SystemExit("report count drift")
    if ledger["counts"]["citation_occurrences"] != 48:
        raise SystemExit("citation occurrence count drift")
    if ledger["counts"]["raw_span_occurrences"] != 127:
        raise SystemExit("span occurrence count drift")
    if ledger["counts"]["raw_claim_occurrences"] != 52:
        raise SystemExit("claim occurrence count drift")
    required_dimensions = {
        "model_profile",
        "prompt",
        "retrieval_infrastructure",
        "requested_url",
        "source_work",
        "edition",
        "exact_span",
        "upstream_citation",
        "data",
        "method",
        "derivation",
    }
    dimensions = {item["dimension"] for item in ledger["dependence_edges"]}
    missing = required_dimensions - dimensions
    if missing:
        raise SystemExit(f"dependence dimensions missing: {sorted(missing)}")
    if ledger["counts"]["independently_confirmed_warrant_roots"] != 0:
        raise SystemExit("author packet cannot self-confirm independent warrant roots")
    citation_status = {
        f"citation:{item['citation_occurrence_id']}": item["resolution_status"]
        for item in ledger["citations"]
    }
    false_resolved_edges = [
        item
        for item in ledger["dependence_edges"]
        if item["dimension"] == "upstream_citation"
        and item["status"] == "declared-and-resolved"
        and citation_status.get(item["to"]) != "resolved-and-span-matched"
    ]
    if false_resolved_edges:
        raise SystemExit("resolved claim-to-citation edge targets an unresolved citation")
    return ledger["counts"]


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    capture_urls = subparsers.add_parser("capture-readbacks")
    capture_urls.add_argument("--capture-root", type=Path, required=True)
    capture_urls.add_argument("--output", type=Path, default=READBACKS)
    capture_spans = subparsers.add_parser("capture-spans")
    capture_spans.add_argument("--capture-root", type=Path, required=True)
    capture_spans.add_argument("--output", type=Path, default=SPAN_READBACKS)
    build = subparsers.add_parser("build")
    build.add_argument("--output", type=Path, default=LEDGER)
    subparsers.add_parser("verify")
    args = parser.parse_args()

    if args.command == "capture-readbacks":
        capture_readbacks(args.capture_root, args.output)
    elif args.command == "capture-spans":
        capture_span_readbacks(args.capture_root, args.output)
    elif args.command == "build":
        args.output.write_text(json.dumps(build_ledger(), indent=2, sort_keys=True) + "\n")
    else:
        print(json.dumps(verify(), sort_keys=True))


if __name__ == "__main__":
    main()
