# ruff: noqa: E501
"""Strict multi-case application adapters for the How We Know library.

The legacy Case 001 adapter remains in :mod:`epistemedia.featured`.  This module adds the
Case 002 agent-lineage profile and a deterministic registry without promoting either reversible
application format into a normative schema.
"""

from __future__ import annotations

import html
import json
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .dossier import public_dossier
from .featured import (
    FEATURE_FORMAT,
    FEATURE_MANIFEST,
    FEATURE_VIEWS,
    GIT_SHA,
    SAFE_SLUG,
    SHA256,
    FeaturedDossier,
    FeaturedDossierError,
    _exact_fields,
    _index,
    _inside,
    _object,
    _sha256,
    _string,
    _strings,
)

if TYPE_CHECKING:
    from .core import PublicCatalog


AGENT_LINEAGE_FORMAT = "epistemedia-agent-lineage-feature-v0.1"
AGENT_LINEAGE_PROFILE = "agent-citation-lineage-v0.1"
AGENT_PROJECTION_FORMAT = "epistemedia-agent-lineage-projection-v0.1"
BOUNDED_PROPOSITION_FORMAT = "epistemedia-bounded-proposition-feature-v0.1"
BOUNDED_PROPOSITION_PROFILE = "bounded-proposition-v0.1"
BOUNDED_PROJECTION_FORMAT = "epistemedia-bounded-proposition-projection-v0.1"
MANIFEST_DIRECTORY = Path("catalog/dossiers")
AGENT_MANIFEST_FIELDS = {
    "claim_family_key",
    "default_view",
    "dossier_bytes",
    "dossier_id",
    "dossier_path",
    "dossier_sha256",
    "format",
    "number",
    "profile",
    "review_receipt_bytes",
    "review_receipt_format",
    "review_receipt_path",
    "review_receipt_sha256",
    "reviewed_head",
    "reviewer_id",
    "selection_note",
    "slug",
    "status",
    "target_proposition_key",
    "views",
}
AGENT_VIEW_FIELDS = {"evaluation_key", "featured_relation_keys"}
BOUNDED_MANIFEST_FIELDS = {
    "claim_family_key",
    "count_cards",
    "default_view",
    "dependence_warning",
    "dossier_bytes",
    "dossier_id",
    "dossier_path",
    "dossier_sha256",
    "format",
    "lexicon",
    "number",
    "practical_readings",
    "profile",
    "public_scope",
    "review_receipt_bytes",
    "review_receipt_format",
    "review_receipt_path",
    "review_receipt_sha256",
    "reviewed_head",
    "reviewed_tree",
    "reviewer_id",
    "selection_note",
    "slug",
    "status",
    "target_proposition_key",
    "task_id",
    "views",
    "warrant_warning",
}
BOUNDED_COUNT_CARD_FIELDS = {"anchor", "key", "label", "members", "note"}
BOUNDED_COUNT_MEMBER_FIELDS = {
    "basis_span_key",
    "collection",
    "item_key",
    "label",
    "object_key",
}
BOUNDED_PRACTICAL_FIELDS = {"basis_relation_keys", "qualifier", "text"}
BOUNDED_LEXICON_FIELDS = {"definition", "term"}
AUDIT_WORK_KEY = "work-em0026-audit-instrument"
AUDIT_EDITION_KEY = "edition-em0026-audit-projection"
COUNT_SPAN_KEYS = {
    "counts": "span-audit-counts",
    "dispositions": "span-audit-dispositions",
    "unresolved": "span-audit-unresolved",
    "inaccessible": "span-audit-inaccessible",
    "unsupported": "span-audit-unsupported",
    "rejected": "span-audit-rejected",
}
COUNT_RECEIPT_KEYS = {
    "captured_reports": "captured_reports",
    "citation_occurrences": "citation_occurrences",
    "cited_url_strings": "cited_urls",
    "resolving_url_roots": "resolving_url_roots",
    "source_work_roots": "source_work_roots",
    "examined_edition_roots": "examined_edition_roots",
    "accepted_exact_span_roots": "accepted_exact_span_roots",
    "candidate_warrant_roots": "candidate_warrant_roots",
    "independently_confirmed_warrant_roots": "independently_confirmed_warrant_roots",
    "pending_warrant_groups": "pending_warrant_groups",
    "independently_rejected_claim_occurrences": (
        "independently_rejected_claim_occurrences"
    ),
    "inaccessible_citations": "inaccessible_citations",
    "unresolved_citations": "unresolved_citations",
    "unsupported_or_force_raised_claims": "unsupported_or_force_raised_claims",
}
AGENT_LEXICON = (
    {
        "term": "Citation occurrence",
        "definition": "One report-level use of a citation, before repeated URLs are collapsed.",
    },
    {
        "term": "URL root",
        "definition": "One distinct cited URL string; resolution does not prove claim support.",
    },
    {
        "term": "Source work",
        "definition": "One logical paper, dataset, repository, or audit instrument across editions.",
    },
    {
        "term": "Candidate warrant root",
        "definition": (
            "One source-method-data proposition that survived bounded semantic review, while "
            "residual independence remains unresolved."
        ),
    },
    {
        "term": "No credit",
        "definition": (
            "The item remains visible but does not support the stronger claim because its carrier, "
            "span, semantics, or lineage did not close."
        ),
    },
)
AGENT_PRACTICAL_READINGS = {
    "encyclopedia": {
        "text": (
            "Use a polished cited report as a map into sources, not as a vote count. Check URL "
            "resolution and sentence-level support separately."
        ),
        "qualifier": (
            "This bounded 2026 packet does not estimate current or universal agent reliability."
        ),
    },
    "skeptical": {
        "text": (
            "Do not infer independent corroboration from eight agreeing reports: 34 citation "
            "occurrences remain unresolved, 20 claims lost credit, and no warrant root was "
            "independently confirmed."
        ),
        "qualifier": (
            "The packet is a lineage audit, not a vendor ranking or a representative product test."
        ),
    },
}
AGENT_LEDGER_SECTIONS = (
    ("reports", "Captured reports", "reports"),
    ("citation-occurrences", "Citation occurrences", "citation_occurrences"),
    ("cited-urls", "Distinct cited URL strings", "cited_urls"),
    ("resolving-urls", "Resolving URL roots", "resolving_urls"),
    ("source-works", "Source works", "source_works"),
    ("examined-editions", "Examined editions", "editions"),
    ("accepted-spans", "Accepted exact span roots", "exact_spans"),
    ("candidate-warrants", "Candidate warrant roots", "candidate_warrants"),
    ("confirmed-warrants", "Independently confirmed warrant roots", "confirmed_warrants"),
    ("pending-warrants", "Pending warrant groups", "pending_warrants"),
    ("unresolved-citations", "Unresolved citation occurrences", "unresolved_citations"),
    ("unsupported-claims", "Unsupported or force-raised claims", "unsupported_claims"),
    ("rejected-claims", "Independently rejected claims", "rejected_claims"),
    ("inaccessible-citations", "Inaccessible carriers", "inaccessible_citations"),
)

# Editorial framing is part of the application projection, not the accepted dossier.
# Each line below restates already-reviewed boundaries in a human-first order while
# leaving the dossier, receipt, policy, count, and source objects byte-identical.
CASE_EDITORIAL = {
    "agent-citation-lineage": {
        "failure_mode": "False independence",
        "claim": "Eight research agents agreed, so the answer looked independently corroborated.",
        "why": (
            "A cited report can look rigorous while its runs, links, and source claims still "
            "share one capture program. Counting echoes as witnesses is a direct failure mode "
            "for agent-generated research."
        ),
        "story": [
            {
                "label": "What looked persuasive",
                "title": "Eight polished reports",
                "text": "The same frozen question produced eight separately captured, citation-rich answers.",
            },
            {
                "label": "What the audit collapsed",
                "title": "Thirty URLs became eleven works",
                "text": "Repeated links and editions were grouped, and run multiplicity received zero automatic independence credit.",
            },
            {
                "label": "What remains",
                "title": "Seven candidates, none confirmed",
                "text": "Thirty-four citation occurrences remain unresolved; the seven warrant candidates still require independent rooting.",
            },
        ],
    },
    "gpt-4-bar-exam-percentile": {
        "failure_mode": "Missing comparison class",
        "claim": "GPT-4 scored around the 90th percentile on the bar exam.",
        "why": (
            "A score can be historical fact while its headline rank changes with the people, "
            "administration, cutoff, and interpolation used for comparison. The missing noun "
            "after “percentile” changes what the number means."
        ),
        "story": [
            {
                "label": "What is documented",
                "title": "One historical simulated score",
                "text": "The report, paper, repository, and supplement describe manifestations of one bounded model run.",
            },
            {
                "label": "What moves",
                "title": "The percentile",
                "text": "Official administration charts and modeled populations place the same score differently.",
            },
            {
                "label": "What to carry forward",
                "title": "Score plus comparator",
                "text": "State the administration and comparison population; do not turn the rank into general legal competence.",
            },
        ],
    },
    "mehrabian-7-38-55": {
        "failure_mode": "Scope inflation",
        "claim": "Only 7% of communication is verbal; 93% is nonverbal.",
        "why": (
            "A memorable formula escaped two narrow experiments about inconsistent feelings "
            "and attitudes, then circulated as a universal law. The missing experimental scope "
            "is the difference between history and advice."
        ),
        "story": [
            {
                "label": "What was tested",
                "title": "Two separate pairings",
                "text": "One participant group compared words with tone; another compared face with tone.",
            },
            {
                "label": "What was proposed",
                "title": "A cross-study formula",
                "text": "The three weights were assembled across studies; no original experiment tested all three channels together.",
            },
            {
                "label": "What was inflated",
                "title": "A universal 93% slogan",
                "text": "Later circulation documents popularity, not scientific truth, and the exact origin of the .07 coefficient remains unresolved.",
            },
        ],
    },
}


def _positive_integer(value: Any, context: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise FeaturedDossierError(f"{context} must be a positive integer")
    return value


def _audit_value(indexes: dict[str, dict[str, dict[str, Any]]], key: str) -> Any:
    span = indexes["spans"].get(key)
    if span is None:
        raise FeaturedDossierError(f"Case 002 lacks required audit span: {key}")
    extent = _object(span.get("extent"), f"{key}.extent")
    if extent.get("type") != "json-value" or "value" not in extent:
        raise FeaturedDossierError(f"{key} must carry a JSON value")
    return extent["value"]


def _citation_occurrence_id(span_occurrence_id: str) -> str:
    if ":" not in span_occurrence_id:
        raise FeaturedDossierError(
            f"malformed citation span occurrence identity: {span_occurrence_id}"
        )
    return span_occurrence_id.rsplit(":", 1)[0]


@dataclass(frozen=True)
class AgentLineageDossier:
    """The strict, reversible Case 002 adapter over one reviewed public dossier."""

    root: Path
    manifest_path: Path
    manifest: dict[str, Any]
    dossier: dict[str, Any]
    receipt: dict[str, Any]

    @classmethod
    def load(cls, root: Path, manifest_path: Path) -> AgentLineageDossier:
        root = root.resolve()
        selected_path = _inside(root, manifest_path.as_posix(), "Case 002 manifest")
        try:
            manifest = _object(json.loads(selected_path.read_text()), "Case 002 manifest")
        except json.JSONDecodeError as exc:
            raise FeaturedDossierError("Case 002 manifest is not valid JSON") from exc
        _exact_fields(manifest, AGENT_MANIFEST_FIELDS, "Case 002 manifest")
        if manifest["format"] != AGENT_LINEAGE_FORMAT:
            raise FeaturedDossierError("unsupported Case 002 manifest format")
        if manifest["profile"] != AGENT_LINEAGE_PROFILE:
            raise FeaturedDossierError("unsupported Case 002 projection profile")
        if manifest["status"] != "accepted":
            raise FeaturedDossierError("Case 002 selection status must be accepted")
        slug = _string(manifest["slug"], "Case 002 manifest.slug")
        if SAFE_SLUG.fullmatch(slug) is None:
            raise FeaturedDossierError("Case 002 manifest.slug is not URL-safe")
        number = _string(manifest["number"], "Case 002 manifest.number")
        if not number.isdigit():
            raise FeaturedDossierError("Case 002 manifest.number must contain digits")
        reviewed_head = _string(manifest["reviewed_head"], "Case 002 reviewed_head")
        if GIT_SHA.fullmatch(reviewed_head) is None:
            raise FeaturedDossierError("Case 002 reviewed_head must be a Git SHA")
        default_view = _string(manifest["default_view"], "Case 002 default_view")
        if default_view not in FEATURE_VIEWS:
            raise FeaturedDossierError("Case 002 default view is unsupported")

        views = _object(manifest["views"], "Case 002 manifest.views")
        if set(views) != set(FEATURE_VIEWS):
            raise FeaturedDossierError("Case 002 must define encyclopedia and skeptical views")
        for view_name in FEATURE_VIEWS:
            view = _object(views[view_name], f"Case 002 views.{view_name}")
            _exact_fields(view, AGENT_VIEW_FIELDS, f"Case 002 views.{view_name}")
            _string(view["evaluation_key"], f"Case 002 {view_name} evaluation")
            if not _strings(
                view["featured_relation_keys"],
                f"Case 002 {view_name} featured relations",
            ):
                raise FeaturedDossierError(f"Case 002 {view_name} relations are empty")
        if views["encyclopedia"] == views["skeptical"]:
            raise FeaturedDossierError("Case 002 views must differ materially")

        dossier_path = _inside(
            root,
            _string(manifest["dossier_path"], "Case 002 dossier_path"),
            "Case 002 dossier_path",
        )
        receipt_path = _inside(
            root,
            _string(manifest["review_receipt_path"], "Case 002 review_receipt_path"),
            "Case 002 review_receipt_path",
        )
        for label, path, digest_key, bytes_key in (
            ("dossier", dossier_path, "dossier_sha256", "dossier_bytes"),
            (
                "review receipt",
                receipt_path,
                "review_receipt_sha256",
                "review_receipt_bytes",
            ),
        ):
            expected_digest = _string(manifest[digest_key], f"Case 002 {digest_key}")
            if SHA256.fullmatch(expected_digest) is None:
                raise FeaturedDossierError(f"Case 002 {digest_key} is not SHA-256")
            expected_bytes = _positive_integer(
                manifest[bytes_key], f"Case 002 {bytes_key}"
            )
            if _sha256(path) != expected_digest or path.stat().st_size != expected_bytes:
                raise FeaturedDossierError(
                    f"Case 002 {label} bytes differ from the accepted manifest"
                )
        try:
            source_dossier = _object(json.loads(dossier_path.read_text()), "Case 002 dossier")
            receipt = _object(json.loads(receipt_path.read_text()), "Case 002 receipt")
        except json.JSONDecodeError as exc:
            raise FeaturedDossierError("Case 002 dossier or receipt is invalid JSON") from exc
        try:
            dossier = public_dossier(source_dossier)
        except ValueError as exc:
            raise FeaturedDossierError("Case 002 dossier fails public validation") from exc
        if dossier["dossier_id"] != manifest["dossier_id"]:
            raise FeaturedDossierError("Case 002 dossier identity differs from manifest")

        if receipt.get("schema") != manifest["review_receipt_format"]:
            raise FeaturedDossierError("Case 002 receipt format differs from manifest")
        if receipt.get("decision") != "pass":
            raise FeaturedDossierError("Case 002 lacks an independent pass receipt")
        if receipt.get("reviewer") != manifest["reviewer_id"]:
            raise FeaturedDossierError("Case 002 reviewer differs from manifest")
        if not isinstance(receipt.get("independence_statement"), str):
            raise FeaturedDossierError("Case 002 receipt lacks an independence statement")
        repository = _object(receipt.get("repository"), "Case 002 receipt.repository")
        if repository.get("reviewed_author_head") != reviewed_head:
            raise FeaturedDossierError("Case 002 reviewed head differs from manifest")
        candidate = _object(
            receipt.get("candidate_dossier"), "Case 002 receipt.candidate_dossier"
        )
        expected_candidate = {
            "path": dossier_path.relative_to(root).as_posix(),
            "id": dossier["dossier_id"],
            "sha256": manifest["dossier_sha256"],
            "bytes": manifest["dossier_bytes"],
        }
        if any(candidate.get(key) != value for key, value in expected_candidate.items()):
            raise FeaturedDossierError("Case 002 receipt does not bind exact dossier bytes")
        packet = _object(
            receipt.get("accepted_em0026_packet"), "Case 002 accepted packet receipt"
        )
        if packet.get("result") != "byte-identical":
            raise FeaturedDossierError("Case 002 accepted research packet drifted")
        source_review = _object(
            receipt.get("source_identity_review"), "Case 002 source review"
        )
        semantic_review = _object(
            receipt.get("semantic_review"), "Case 002 semantic review"
        )
        if source_review.get("result") != "pass":
            raise FeaturedDossierError("Case 002 source identity review did not pass")
        if semantic_review.get("sentence_to_span_work_edition_license_retrieval_closure") != "pass":
            raise FeaturedDossierError("Case 002 sentence-to-source closure did not pass")
        if semantic_review.get("material_span_containment_mismatches") != 0:
            raise FeaturedDossierError("Case 002 retains material span mismatches")
        if semantic_review.get("supplement_sentence_gaps_remaining") != 0:
            raise FeaturedDossierError("Case 002 retains supplement sentence gaps")
        if semantic_review.get("candidate_warrant_independently_confirmed_count") != 0:
            raise FeaturedDossierError("Case 002 receipt unexpectedly confirms warrant roots")

        indexes = {
            name: _index(dossier[name])
            for name in (
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
        }
        family_key = _string(manifest["claim_family_key"], "Case 002 claim family")
        target_key = _string(manifest["target_proposition_key"], "Case 002 target")
        family = indexes["claim_families"].get(family_key)
        if family is None or target_key not in family["proposition_keys"]:
            raise FeaturedDossierError("Case 002 target is outside its claim family")
        for view_name in FEATURE_VIEWS:
            view = views[view_name]
            evaluation = indexes["evaluations"].get(view["evaluation_key"])
            if evaluation is None or evaluation["claim_family_key"] != family_key:
                raise FeaturedDossierError(f"Case 002 {view_name} evaluation is invalid")
            if evaluation["policy_id"] != f"em:application-policy:{view_name}-v0.1":
                raise FeaturedDossierError(f"Case 002 {view_name} policy is unexpected")
            for relation_key in view["featured_relation_keys"]:
                if relation_key not in indexes["evidence_relations"]:
                    raise FeaturedDossierError(
                        f"Case 002 featured relation is missing: {relation_key}"
                    )

        loaded = cls(root, selected_path, manifest, dossier, receipt)
        reproduced = _object(receipt.get("reproduced_counts"), "Case 002 receipt counts")
        counts = loaded.derived_counts()
        for local_key, receipt_key in COUNT_RECEIPT_KEYS.items():
            if counts[local_key] != reproduced.get(receipt_key):
                raise FeaturedDossierError(
                    f"Case 002 derived count differs from review receipt: {local_key}"
                )
        return loaded

    @property
    def slug(self) -> str:
        return self.manifest["slug"]

    @property
    def default_view(self) -> str:
        return self.manifest["default_view"]

    def indexes(self) -> dict[str, dict[str, dict[str, Any]]]:
        return {
            name: _index(self.dossier[name])
            for name in (
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
        }

    def span_trace(self, span_key: str) -> dict[str, Any]:
        indexes = self.indexes()
        span = indexes["spans"][span_key]
        edition = indexes["editions"][span["edition_key"]]
        work = indexes["source_works"][edition["work_key"]]
        content = _object(edition.get("content"), f"edition {edition['key']} content")
        return {
            "span": {key: value for key, value in span.items() if key != "visibility"},
            "edition": {
                key: value
                for key, value in edition.items()
                if key not in {"content", "visibility"}
            },
            "source_work": {
                key: value for key, value in work.items() if key != "visibility"
            },
            "retrieval": content.get("readback_receipts", []),
            "license_treatment": content.get("license_treatment", work.get("license")),
        }

    def relation_trace(self, relation_key: str) -> dict[str, Any]:
        indexes = self.indexes()
        relation = indexes["evidence_relations"][relation_key]
        from_ref = relation["from_ref"]
        assertion = indexes["assertions"].get(from_ref)
        lineage = indexes["lineages"].get(from_ref)
        proposition = None
        span_keys: list[str] = []
        if assertion is not None:
            proposition = indexes["propositions"][assertion["proposition_key"]]
            lineage = indexes["lineages"][assertion["lineage_key"]]
            span_keys.extend(assertion["span_keys"])
        elif lineage is not None:
            span_keys.extend(lineage.get("basis_span_keys", []))
        span_keys.extend(relation.get("basis_span_keys", []))
        unique_span_keys = list(
            dict.fromkeys(key for key in span_keys if key in indexes["spans"])
        )
        if not unique_span_keys:
            raise FeaturedDossierError(
                f"Case 002 material relation lacks exact source spans: {relation_key}"
            )
        return {
            "relation": relation,
            "relation_label": relation["relation_type"].replace("-", " "),
            "statement": relation["note"],
            "proposition": proposition,
            "assertion": assertion,
            "lineage": lineage,
            "sources": [self.span_trace(key) for key in unique_span_keys],
        }

    def _citation_ledgers(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        indexes = self.indexes()
        citations: dict[str, dict[str, Any]] = {}
        urls: dict[str, dict[str, Any]] = {}
        for edition in self.dossier["editions"]:
            if edition["key"] == AUDIT_EDITION_KEY:
                continue
            work = indexes["source_works"][edition["work_key"]]
            content = _object(edition["content"], f"edition {edition['key']} content")
            for receipt in content.get("readback_receipts", []):
                requested_url = _string(receipt.get("requested_url"), "requested URL")
                entry = urls.setdefault(
                    requested_url,
                    {
                        "key": requested_url,
                        "title": requested_url,
                        "status": "inaccessible",
                        "source_work_keys": [],
                        "edition_keys": [],
                        "resolved_urls": [],
                    },
                )
                entry["source_work_keys"].append(work["key"])
                entry["edition_keys"].append(edition["key"])
                if isinstance(receipt.get("resolved_url"), str):
                    entry["resolved_urls"].append(receipt["resolved_url"])
                if receipt.get("retrieval_status") == "retrieved":
                    entry["status"] = "retrieved"
            for excerpt in content.get("excerpts", []):
                for occurrence_id in excerpt.get("occurrence_ids", []):
                    citation_id = _citation_occurrence_id(occurrence_id)
                    entry = citations.setdefault(
                        citation_id,
                        {
                            "key": citation_id,
                            "title": citation_id,
                            "status": "matched-exact-span",
                            "source_work_keys": [],
                            "edition_keys": [],
                            "span_occurrence_ids": [],
                        },
                    )
                    entry["source_work_keys"].append(work["key"])
                    entry["edition_keys"].append(edition["key"])
                    entry["span_occurrence_ids"].append(occurrence_id)

        unresolved = _audit_value(indexes, COUNT_SPAN_KEYS["unresolved"])
        if not isinstance(unresolved, list):
            raise FeaturedDossierError("Case 002 unresolved citation ledger must be a list")
        for record in unresolved:
            item = _object(record, "Case 002 unresolved citation")
            citation_id = _string(item.get("citation_occurrence_id"), "citation occurrence")
            entry = citations.setdefault(
                citation_id,
                {
                    "key": citation_id,
                    "title": citation_id,
                    "status": "unresolved",
                    "source_work_keys": [],
                    "edition_keys": [],
                    "span_occurrence_ids": [],
                },
            )
            entry["status"] = "unresolved"
            for key, singular in (
                ("source_work_keys", "source_work_id"),
                ("edition_keys", "edition_id"),
                ("span_occurrence_ids", "span_occurrence_ids"),
            ):
                value = item.get(singular)
                if isinstance(value, list):
                    entry[key].extend(value)
                elif isinstance(value, str):
                    entry[key].append(value)
            entry["requested_url"] = item.get("requested_url")
            entry["license"] = item.get("license")
            entry["license_treatment"] = item.get("license_treatment")

        for collection in (citations, urls):
            for entry in collection.values():
                for key in (
                    "source_work_keys",
                    "edition_keys",
                    "span_occurrence_ids",
                    "resolved_urls",
                ):
                    if key in entry:
                        entry[key] = sorted(set(entry[key]))
        for entry in citations.values():
            entry.update(
                {
                    "object_type": "citation_occurrence",
                    "object_key": entry["key"],
                    "object": {"id": entry["key"], "status": entry["status"]},
                }
            )
        for entry in urls.values():
            entry.update(
                {
                    "object_type": "cited_url",
                    "object_key": entry["key"],
                    "object": {"id": entry["key"], "status": entry["status"]},
                }
            )
        return (
            [citations[key] for key in sorted(citations)],
            [urls[key] for key in sorted(urls)],
        )

    def count_ledgers(self) -> dict[str, list[dict[str, Any]]]:
        indexes = self.indexes()
        citation_occurrences, cited_urls = self._citation_ledgers()
        reports = []
        for index in range(1, 9):
            trace = self.span_trace(f"span-audit-report-{index}")
            value = trace["span"]["extent"]["value"]
            reports.append(
                {
                    "key": value["run_id"],
                    "title": value["run_id"],
                    "status": value["status"],
                    "requested_model_profile": value["requested_model_profile"],
                    "prompt_sha256": value["prompt_sha256"],
                    "source": trace,
                    "object_type": "captured_report",
                    "object_key": value["run_id"],
                    "object": {"id": value["run_id"], "status": value["status"]},
                }
            )
        source_works = [
            {
                "key": work["key"],
                "title": work["title"],
                "status": "examined-source-work",
                "canonical_uri": work["canonical_uri"],
                "license": work["license"],
                "id": work["id"],
                "object_type": "source_work",
                "object_key": work["key"],
                "object": work,
            }
            for work in self.dossier["source_works"]
            if work["key"] != AUDIT_WORK_KEY
        ]
        editions = [
            {
                "key": edition["key"],
                "title": edition["edition_label"],
                "status": "examined-edition",
                "id": edition["id"],
                "digest": edition["content_digest"],
                "bytes": edition["content_length"],
                "source_work_key": edition["work_key"],
                "object_type": "edition",
                "object_key": edition["key"],
                "object": edition,
            }
            for edition in self.dossier["editions"]
            if edition["key"] != AUDIT_EDITION_KEY
        ]
        exact_spans = [
            {
                "key": span["key"],
                "title": span["locator"]["label"],
                "status": "matched-exact-span",
                "id": span["id"],
                "digest": span["digest"],
                "edition_key": span["edition_key"],
                "object_type": "span",
                "object_key": span["key"],
                "object": span,
            }
            for span in self.dossier["spans"]
            if not span["key"].startswith(("span-audit", "span-supplement"))
        ]
        candidate_relations = [
            relation
            for relation in self.dossier["evidence_relations"]
            if relation["relation_type"] == "support"
            and relation["from_ref"] in indexes["assertions"]
            and relation["from_ref"] != "assertion-derived-counts"
        ]
        candidates = []
        for relation in candidate_relations:
            trace = self.relation_trace(relation["key"])
            candidates.append(
                {
                    **trace,
                    "object_type": "evidence_relation",
                    "object_key": relation["key"],
                    "object": relation,
                }
            )
        pending_relations = [
            relation
            for relation in self.dossier["evidence_relations"]
            if relation["relation_type"] == "qualification"
        ]
        pending = []
        for relation in pending_relations:
            trace = self.relation_trace(relation["key"])
            pending.append(
                {
                    **trace,
                    "object_type": "evidence_relation",
                    "object_key": relation["key"],
                    "object": relation,
                }
            )

        def audit_list(name: str) -> list[Any]:
            value = _audit_value(indexes, COUNT_SPAN_KEYS[name])
            if not isinstance(value, list):
                raise FeaturedDossierError(f"Case 002 {name} ledger must be a list")
            return value

        def citation_gap(raw: Any, status: str) -> dict[str, Any]:
            item = _object(raw, f"Case 002 {status} citation")
            identity = _string(
                item.get("citation_occurrence_id"),
                f"Case 002 {status} citation identity",
            )
            return {
                **item,
                "key": identity,
                "title": str(item.get("raw_title", identity)),
                "status": status,
                "object_type": "citation_occurrence",
                "object_key": identity,
                "object": {"id": identity, "status": status},
            }

        unresolved = [citation_gap(item, "unresolved") for item in audit_list("unresolved")]
        inaccessible = [
            citation_gap(item, "inaccessible") for item in audit_list("inaccessible")
        ]
        unsupported = [
            {
                "key": item,
                "title": item,
                "status": "no-credit",
                "object_type": "claim_occurrence",
                "object_key": item,
                "object": {"id": item, "status": "no-credit"},
            }
            for item in audit_list("unsupported")
        ]
        rejected = [
            {
                "key": item,
                "title": item,
                "status": "independently-rejected",
                "object_type": "claim_occurrence",
                "object_key": item,
                "object": {"id": item, "status": "independently-rejected"},
            }
            for item in audit_list("rejected")
        ]
        return {
            "reports": reports,
            "citation_occurrences": citation_occurrences,
            "cited_urls": cited_urls,
            "resolving_urls": [item for item in cited_urls if item["status"] == "retrieved"],
            "source_works": sorted(source_works, key=lambda item: item["key"]),
            "editions": sorted(editions, key=lambda item: item["key"]),
            "exact_spans": sorted(exact_spans, key=lambda item: item["key"]),
            "candidate_warrants": sorted(
                candidates, key=lambda item: item["relation"]["key"]
            ),
            "confirmed_warrants": [],
            "pending_warrants": sorted(
                pending, key=lambda item: item["relation"]["key"]
            ),
            "unresolved_citations": sorted(
                unresolved, key=lambda item: item["citation_occurrence_id"]
            ),
            "unsupported_claims": unsupported,
            "rejected_claims": rejected,
            "inaccessible_citations": sorted(
                inaccessible, key=lambda item: item["citation_occurrence_id"]
            ),
        }

    def derived_counts(self) -> dict[str, int]:
        ledgers = self.count_ledgers()
        return {
            "captured_reports": len(ledgers["reports"]),
            "citation_occurrences": len(ledgers["citation_occurrences"]),
            "cited_url_strings": len(ledgers["cited_urls"]),
            "resolving_url_roots": len(ledgers["resolving_urls"]),
            "source_work_roots": len(ledgers["source_works"]),
            "examined_edition_roots": len(ledgers["editions"]),
            "accepted_exact_span_roots": len(ledgers["exact_spans"]),
            "candidate_warrant_roots": len(ledgers["candidate_warrants"]),
            "independently_confirmed_warrant_roots": len(
                ledgers["confirmed_warrants"]
            ),
            "pending_warrant_groups": len(ledgers["pending_warrants"]),
            "independently_rejected_claim_occurrences": len(
                ledgers["rejected_claims"]
            ),
            "inaccessible_citations": len(ledgers["inaccessible_citations"]),
            "unresolved_citations": len(ledgers["unresolved_citations"]),
            "unsupported_or_force_raised_claims": len(ledgers["unsupported_claims"]),
        }

    def projection(self, view: str) -> dict[str, Any]:
        if view not in FEATURE_VIEWS:
            raise FeaturedDossierError(f"unknown dossier policy view: {view}")
        indexes = self.indexes()
        family = indexes["claim_families"][self.manifest["claim_family_key"]]
        evaluation = indexes["evaluations"][self.manifest["views"][view]["evaluation_key"]]
        ledgers = self.count_ledgers()
        counts = self.derived_counts()
        featured_relations = [
            self.relation_trace(key)
            for key in self.manifest["views"][view]["featured_relation_keys"]
        ]
        practical = AGENT_PRACTICAL_READINGS[view]
        repository = _object(self.receipt["repository"], "Case 002 receipt.repository")
        limitations = self.receipt.get("limitations", [])
        display_title = self.dossier["title"].removeprefix(
            f"Case {self.manifest['number']}: "
        )
        return {
            "format": AGENT_PROJECTION_FORMAT,
            "profile": AGENT_LINEAGE_PROFILE,
            "slug": self.slug,
            "number": self.manifest["number"],
            "selection_status": self.manifest["status"],
            "selection_note": self.manifest["selection_note"],
            "selection_manifest": self.manifest_path.relative_to(self.root).as_posix(),
            "selection_manifest_sha256": _sha256(self.manifest_path),
            "dossier_id": self.dossier["dossier_id"],
            "title": display_title,
            "question": self.dossier["question"],
            "scope": self.dossier["scope"],
            "editorial": CASE_EDITORIAL[self.slug],
            "claim_family": family,
            "target_proposition": indexes["propositions"][
                self.manifest["target_proposition_key"]
            ],
            "view": {
                "id": view,
                "policy_id": evaluation["policy_id"],
                "evaluation_id": evaluation["id"],
                "label": evaluation["label"],
                "reason_codes": evaluation["reason_codes"],
            },
            "counts": counts,
            "count_cards": [
                {
                    "key": "captured_reports",
                    "ledger_key": "reports",
                    "value": counts["captured_reports"],
                    "label": "captured reports",
                    "anchor": "reports",
                    "note": "Observations from one frozen capture program",
                },
                {
                    "key": "cited_url_strings",
                    "ledger_key": "cited_urls",
                    "value": counts["cited_url_strings"],
                    "label": "distinct URL strings",
                    "anchor": "cited-urls",
                    "note": "A resolving link is not sentence support",
                },
                {
                    "key": "source_work_roots",
                    "ledger_key": "source_works",
                    "value": counts["source_work_roots"],
                    "label": "source works",
                    "anchor": "source-works",
                    "note": "Logical works after edition collapse",
                },
                {
                    "key": "candidate_warrant_roots",
                    "ledger_key": "candidate_warrants",
                    "value": counts["candidate_warrant_roots"],
                    "label": "candidate warrants",
                    "anchor": "candidate-warrants",
                    "note": "Scoped candidates, not independent programs",
                },
                {
                    "key": "unresolved_citations",
                    "ledger_key": "unresolved_citations",
                    "value": counts["unresolved_citations"],
                    "label": "unresolved citations",
                    "anchor": "unresolved-citations",
                    "note": "Visible and assigned no credit",
                },
            ],
            "count_ledgers": ledgers,
            "ledger_sections": [
                {"anchor": anchor, "title": title, "key": key}
                for anchor, title, key in AGENT_LEDGER_SECTIONS
            ],
            "lexicon": list(AGENT_LEXICON),
            "practical_reading": {
                **practical,
                "basis_relation_keys": [
                    item["relation"]["key"] for item in featured_relations
                ],
            },
            "featured_relations": featured_relations,
            "dependence_warning": indexes["lineages"][
                "lineage-capture-dependence-unknown"
            ]["note"],
            "warrant_warning": indexes["lineages"][
                "lineage-source-dependence-unknown"
            ]["note"],
            "source_work_count": counts["source_work_roots"],
            "edition_count": counts["examined_edition_roots"],
            "span_count": counts["accepted_exact_span_roots"],
            "source_works": ledgers["source_works"],
            "review": {
                "decision": self.receipt["decision"],
                "reviewer_id": self.receipt["reviewer"],
                "independence_statement": self.receipt["independence_statement"],
                "fresh_clone": True,
                "independent_retrieval": True,
                "authoring_agent_artifacts_used": False,
                "reviewed_head": self.manifest["reviewed_head"],
                "reviewed_base": repository.get("reviewed_base", "unknown"),
                "reviewed_tree": repository.get("reviewed_author_tree", "unknown"),
                "receipt_path": self.manifest["review_receipt_path"],
                "receipt_sha256": _sha256(
                    self.root / self.manifest["review_receipt_path"]
                ),
                "completed_at": self.receipt.get("completed_at", "unknown"),
                "checked_scope": [
                    "Exact dossier, supplement, Git, and accepted-packet bytes",
                    "Fourteen public-edition identities and all material source spans",
                    "Count grammar, no-credit dispositions, and dependence dimensions",
                    "Policy divergence, disclosure audit, deterministic build, and protection",
                ],
                "limitations": (
                    limitations
                    if isinstance(limitations, list)
                    and all(isinstance(item, str) for item in limitations)
                    else []
                ),
            },
            "dossier": self.dossier,
        }

    def envelope(self, catalog: PublicCatalog, view: str) -> dict[str, Any]:
        from .core import envelope

        return envelope(catalog, self.projection(view))

    def review_envelope(self, catalog: PublicCatalog) -> dict[str, Any]:
        from .core import envelope

        projection = self.projection(self.default_view)
        return envelope(
            catalog,
            {
                "format": "epistemedia-public-review-receipt-v0.1",
                "profile": AGENT_LINEAGE_PROFILE,
                "slug": projection["slug"],
                "number": projection["number"],
                "title": projection["title"],
                "dossier_id": projection["dossier_id"],
                "review": projection["review"],
            },
        )

    def summary(self, catalog: PublicCatalog) -> dict[str, Any]:
        projection = self.envelope(catalog, self.default_view)
        data = projection["data"]
        return {
            "slug": self.slug,
            "number": data["number"],
            "title": data["title"],
            "question": data["question"],
            "scope": data["scope"],
            "dossier_id": data["dossier_id"],
            "default_view": self.default_view,
            "views": list(FEATURE_VIEWS),
            "evaluation": data["view"]["label"],
            "counts": data["counts"],
            "count_cards": data["count_cards"],
            "content_digest": projection["content_digest"],
        }


@dataclass(frozen=True)
class BoundedPropositionDossier(AgentLineageDossier):
    """A strict generic adapter over one reviewed bounded-proposition dossier."""

    @classmethod
    def load(cls, root: Path, manifest_path: Path) -> BoundedPropositionDossier:
        root = root.resolve()
        selected_path = _inside(root, manifest_path.as_posix(), "bounded manifest")
        try:
            manifest = _object(
                json.loads(selected_path.read_text()), "bounded manifest"
            )
        except json.JSONDecodeError as exc:
            raise FeaturedDossierError("bounded manifest is not valid JSON") from exc
        _exact_fields(manifest, BOUNDED_MANIFEST_FIELDS, "bounded manifest")
        if manifest["format"] != BOUNDED_PROPOSITION_FORMAT:
            raise FeaturedDossierError("unsupported bounded manifest format")
        if manifest["profile"] != BOUNDED_PROPOSITION_PROFILE:
            raise FeaturedDossierError("unsupported bounded projection profile")
        if manifest["status"] != "accepted":
            raise FeaturedDossierError("bounded selection status must be accepted")
        slug = _string(manifest["slug"], "bounded manifest.slug")
        if SAFE_SLUG.fullmatch(slug) is None:
            raise FeaturedDossierError("bounded manifest.slug is not URL-safe")
        number = _string(manifest["number"], "bounded manifest.number")
        if not number.isdigit():
            raise FeaturedDossierError("bounded manifest.number must contain digits")
        default_view = _string(manifest["default_view"], "bounded default_view")
        if default_view not in FEATURE_VIEWS:
            raise FeaturedDossierError("bounded default view is unsupported")
        reviewed_head = _string(manifest["reviewed_head"], "bounded reviewed_head")
        reviewed_tree = _string(manifest["reviewed_tree"], "bounded reviewed_tree")
        if GIT_SHA.fullmatch(reviewed_head) is None or GIT_SHA.fullmatch(
            reviewed_tree
        ) is None:
            raise FeaturedDossierError("bounded reviewed Git identity is malformed")
        _string(manifest["public_scope"], "bounded public_scope")
        _string(manifest["selection_note"], "bounded selection_note")
        _string(manifest["dependence_warning"], "bounded dependence_warning")
        _string(manifest["warrant_warning"], "bounded warrant_warning")

        views = _object(manifest["views"], "bounded manifest.views")
        if set(views) != set(FEATURE_VIEWS):
            raise FeaturedDossierError(
                "bounded manifest must define encyclopedia and skeptical views"
            )
        for view_name in FEATURE_VIEWS:
            view = _object(views[view_name], f"bounded views.{view_name}")
            _exact_fields(view, AGENT_VIEW_FIELDS, f"bounded views.{view_name}")
            _string(view["evaluation_key"], f"bounded {view_name} evaluation")
            if not _strings(
                view["featured_relation_keys"],
                f"bounded {view_name} featured relations",
            ):
                raise FeaturedDossierError(
                    f"bounded {view_name} featured relations are empty"
                )
        if views["encyclopedia"] == views["skeptical"]:
            raise FeaturedDossierError("bounded views must differ materially")

        dossier_path = _inside(
            root,
            _string(manifest["dossier_path"], "bounded dossier_path"),
            "bounded dossier_path",
        )
        receipt_path = _inside(
            root,
            _string(manifest["review_receipt_path"], "bounded receipt_path"),
            "bounded receipt_path",
        )
        for label, path, digest_key, bytes_key in (
            ("dossier", dossier_path, "dossier_sha256", "dossier_bytes"),
            (
                "review receipt",
                receipt_path,
                "review_receipt_sha256",
                "review_receipt_bytes",
            ),
        ):
            expected_digest = _string(
                manifest[digest_key], f"bounded {digest_key}"
            )
            if SHA256.fullmatch(expected_digest) is None:
                raise FeaturedDossierError(f"bounded {digest_key} is not SHA-256")
            expected_bytes = _positive_integer(
                manifest[bytes_key], f"bounded {bytes_key}"
            )
            if _sha256(path) != expected_digest or path.stat().st_size != expected_bytes:
                raise FeaturedDossierError(
                    f"bounded {label} bytes differ from the accepted manifest"
                )
        try:
            source_dossier = _object(
                json.loads(dossier_path.read_text()), "bounded dossier"
            )
            receipt = _object(json.loads(receipt_path.read_text()), "bounded receipt")
        except json.JSONDecodeError as exc:
            raise FeaturedDossierError(
                "bounded dossier or receipt is invalid JSON"
            ) from exc
        try:
            dossier = public_dossier(source_dossier)
        except ValueError as exc:
            raise FeaturedDossierError(
                "bounded dossier fails public validation"
            ) from exc
        if dossier["dossier_id"] != manifest["dossier_id"]:
            raise FeaturedDossierError(
                "bounded dossier identity differs from manifest"
            )

        if receipt.get("format") != manifest["review_receipt_format"]:
            raise FeaturedDossierError(
                "bounded review format differs from manifest"
            )
        if receipt.get("decision") != "pass" or receipt.get("complete") is not True:
            raise FeaturedDossierError(
                "bounded dossier lacks a complete independent pass"
            )
        if receipt.get("task_id") != manifest["task_id"]:
            raise FeaturedDossierError("bounded review task differs from manifest")
        reviewer = _object(receipt.get("reviewer"), "bounded receipt.reviewer")
        if reviewer.get("id") != manifest["reviewer_id"]:
            raise FeaturedDossierError("bounded reviewer differs from manifest")
        if reviewer.get("fresh_clone") is not True:
            raise FeaturedDossierError("bounded review did not use a fresh clone")
        if manifest["task_id"] == "EM-0034":
            if reviewer.get("independent") is not True:
                raise FeaturedDossierError("bounded reviewer is not independent")
            if reviewer.get("authored_candidate") is not False:
                raise FeaturedDossierError(
                    "bounded reviewer authorship boundary is not closed"
                )
        elif manifest["task_id"] == "EM-0035":
            if reviewer.get("reviewer_was_author") is not False:
                raise FeaturedDossierError("bounded reviewer was the author")
            if reviewer.get("authoring_notes_used_as_evidence") is not False:
                raise FeaturedDossierError(
                    "bounded review used authoring notes as evidence"
                )
        else:
            raise FeaturedDossierError("unsupported bounded review task")
        git_state = _object(receipt.get("git_state"), "bounded receipt.git_state")
        for key in (
            "fresh_clone",
            "pre_review_clean",
            "post_review_clean",
            "unchanged_during_review",
        ):
            if git_state.get(key) is not True:
                raise FeaturedDossierError(
                    f"bounded receipt Git predicate did not pass: {key}"
                )

        reviewed = receipt.get("reviewed")
        if isinstance(reviewed, dict):
            bound_head = reviewed.get("head")
            bound_tree = reviewed.get("tree")
            candidate = _object(reviewed.get("dossier"), "bounded reviewed.dossier")
        else:
            repository = _object(
                receipt.get("repository"), "bounded receipt.repository"
            )
            bound_head = repository.get("reviewed_author_head")
            bound_tree = repository.get("reviewed_author_tree")
            bindings = _object(receipt.get("bindings"), "bounded receipt.bindings")
            candidate = _object(
                bindings.get("candidate_dossier"),
                "bounded receipt candidate_dossier",
            )
        if bound_head != reviewed_head or bound_tree != reviewed_tree:
            raise FeaturedDossierError(
                "bounded reviewed Git identity differs from manifest"
            )
        expected_candidate = {
            "path": dossier_path.relative_to(root).as_posix(),
            "sha256": manifest["dossier_sha256"],
            "bytes": manifest["dossier_bytes"],
        }
        for key, value in expected_candidate.items():
            if candidate.get(key) != value:
                raise FeaturedDossierError(
                    f"bounded review does not bind dossier {key}"
                )
        candidate_identity = candidate.get(
            "dossier_id", candidate.get("id")
        )
        if candidate_identity != dossier["dossier_id"]:
            raise FeaturedDossierError(
                "bounded review does not bind dossier identity"
            )

        indexes = {
            name: _index(dossier[name])
            for name in (
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
        }
        family_key = _string(
            manifest["claim_family_key"], "bounded claim_family_key"
        )
        target_key = _string(
            manifest["target_proposition_key"], "bounded target_proposition_key"
        )
        family = indexes["claim_families"].get(family_key)
        if family is None or target_key not in family["proposition_keys"]:
            raise FeaturedDossierError(
                "bounded target is outside its claim family"
            )
        for view_name in FEATURE_VIEWS:
            view = views[view_name]
            evaluation = indexes["evaluations"].get(view["evaluation_key"])
            if evaluation is None or evaluation["claim_family_key"] != family_key:
                raise FeaturedDossierError(
                    f"bounded {view_name} evaluation is invalid"
                )
            if evaluation["policy_id"] != f"epistemedia-{view_name}-v1":
                raise FeaturedDossierError(
                    f"bounded {view_name} policy is unexpected"
                )
            for relation_key in view["featured_relation_keys"]:
                if relation_key not in indexes["evidence_relations"]:
                    raise FeaturedDossierError(
                        f"bounded featured relation is missing: {relation_key}"
                    )

        cards = manifest["count_cards"]
        if not isinstance(cards, list) or not cards:
            raise FeaturedDossierError("bounded count_cards must be a non-empty list")
        card_keys: set[str] = set()
        anchors: set[str] = set()
        for card_index, raw_card in enumerate(cards):
            card = _object(raw_card, f"bounded count_cards[{card_index}]")
            _exact_fields(
                card, BOUNDED_COUNT_CARD_FIELDS, f"bounded count_cards[{card_index}]"
            )
            card_key = _string(card["key"], "bounded count card key")
            anchor = _string(card["anchor"], "bounded count card anchor")
            _string(card["label"], "bounded count card label")
            _string(card["note"], "bounded count card note")
            if card_key in card_keys or anchor in anchors:
                raise FeaturedDossierError(
                    "bounded count cards contain duplicate keys or anchors"
                )
            card_keys.add(card_key)
            anchors.add(anchor)
            members = card["members"]
            if not isinstance(members, list) or not members:
                raise FeaturedDossierError(
                    f"bounded count card has no members: {card_key}"
                )
            member_keys: set[str] = set()
            for member_index, raw_member in enumerate(members):
                member = _object(
                    raw_member,
                    f"bounded {card_key}.members[{member_index}]",
                )
                _exact_fields(
                    member,
                    BOUNDED_COUNT_MEMBER_FIELDS,
                    f"bounded {card_key}.members[{member_index}]",
                )
                item_key = _string(member["item_key"], "bounded count item_key")
                collection = _string(
                    member["collection"], "bounded count collection"
                )
                object_key = _string(
                    member["object_key"], "bounded count object_key"
                )
                _string(member["label"], "bounded count member label")
                if item_key in member_keys:
                    raise FeaturedDossierError(
                        f"bounded count card has duplicate member: {item_key}"
                    )
                member_keys.add(item_key)
                if collection not in indexes or object_key not in indexes[collection]:
                    raise FeaturedDossierError(
                        f"bounded count member is not in dossier: {collection}.{object_key}"
                    )
                basis_span_key = member["basis_span_key"]
                if basis_span_key is not None:
                    basis_span_key = _string(
                        basis_span_key, "bounded count basis_span_key"
                    )
                    if basis_span_key not in indexes["spans"]:
                        raise FeaturedDossierError(
                            f"bounded count basis span is missing: {basis_span_key}"
                        )
                    source = indexes[collection][object_key]
                    source_spans = source.get(
                        "basis_span_keys", source.get("span_keys", [])
                    )
                    if basis_span_key not in source_spans:
                        raise FeaturedDossierError(
                            f"bounded count basis span is outside member: {item_key}"
                        )

        practical_readings = _object(
            manifest["practical_readings"], "bounded practical_readings"
        )
        if set(practical_readings) != set(FEATURE_VIEWS):
            raise FeaturedDossierError(
                "bounded practical readings must cover both views"
            )
        for view_name in FEATURE_VIEWS:
            practical = _object(
                practical_readings[view_name],
                f"bounded practical_readings.{view_name}",
            )
            _exact_fields(
                practical,
                BOUNDED_PRACTICAL_FIELDS,
                f"bounded practical_readings.{view_name}",
            )
            _string(practical["text"], "bounded practical text")
            _string(practical["qualifier"], "bounded practical qualifier")
            for relation_key in _strings(
                practical["basis_relation_keys"],
                "bounded practical basis_relation_keys",
            ):
                if relation_key not in indexes["evidence_relations"]:
                    raise FeaturedDossierError(
                        f"bounded practical relation is missing: {relation_key}"
                    )
        lexicon = manifest["lexicon"]
        if not isinstance(lexicon, list) or len(lexicon) < 3:
            raise FeaturedDossierError("bounded lexicon must have at least three terms")
        for item_index, raw_item in enumerate(lexicon):
            item = _object(raw_item, f"bounded lexicon[{item_index}]")
            _exact_fields(
                item, BOUNDED_LEXICON_FIELDS, f"bounded lexicon[{item_index}]"
            )
            _string(item["term"], "bounded lexicon term")
            _string(item["definition"], "bounded lexicon definition")

        return cls(root, selected_path, manifest, dossier, receipt)

    def relation_trace(self, relation_key: str) -> dict[str, Any]:
        """Close a bounded relation over its proposition, lineage, and calculations."""
        indexes = self.indexes()
        relation = indexes["evidence_relations"][relation_key]
        proposition = indexes["propositions"].get(relation["to_ref"])
        assertion = next(
            (
                item
                for item in indexes["assertions"].values()
                if proposition is not None
                and item["proposition_key"] == proposition["key"]
            ),
            None,
        )
        if assertion is None:
            assertion = indexes["assertions"].get(relation["from_ref"])
            if assertion is not None:
                proposition = indexes["propositions"][assertion["proposition_key"]]
        lineage = (
            indexes["lineages"].get(assertion["lineage_key"])
            if assertion is not None
            else indexes["lineages"].get(relation["from_ref"])
        )
        if proposition is None or assertion is None or lineage is None:
            raise FeaturedDossierError(
                f"bounded material relation lacks proposition closure: {relation_key}"
            )

        dependencies = sorted(
            (
                item
                for item in indexes["evidence_relations"].values()
                if item["relation_type"] == "dependence"
                and lineage["key"] in {item["from_ref"], item["to_ref"]}
            ),
            key=lambda item: item["key"],
        )
        calculation_traces = []
        for candidate_assertion in sorted(
            indexes["assertions"].values(), key=lambda item: item["key"]
        ):
            candidate_key = candidate_assertion["proposition_key"]
            if (
                candidate_assertion["lineage_key"] != lineage["key"]
                or not candidate_key.startswith("derive-")
            ):
                continue
            candidate_proposition = indexes["propositions"][candidate_key]
            candidate_relations = sorted(
                (
                    item
                    for item in indexes["evidence_relations"].values()
                    if item["to_ref"] == candidate_key
                    and item["relation_type"] == "support"
                ),
                key=lambda item: item["key"],
            )
            for candidate_relation in candidate_relations:
                calculation_sources = [
                    self.span_trace(key)
                    for key in dict.fromkeys(
                        candidate_assertion["span_keys"]
                        + candidate_relation.get("basis_span_keys", [])
                    )
                    if key in indexes["spans"]
                ]
                calculation_traces.append(
                    {
                        "relation": candidate_relation,
                        "proposition": candidate_proposition,
                        "assertion": candidate_assertion,
                        "sources": calculation_sources,
                    }
                )

        span_keys = list(assertion["span_keys"])
        span_keys.extend(relation.get("basis_span_keys", []))
        for dependency in dependencies:
            span_keys.extend(dependency.get("basis_span_keys", []))
        unique_span_keys = list(
            dict.fromkeys(key for key in span_keys if key in indexes["spans"])
        )
        if not unique_span_keys:
            raise FeaturedDossierError(
                f"bounded material relation lacks exact source spans: {relation_key}"
            )
        return {
            "relation": relation,
            "relation_label": relation["relation_type"].replace("-", " "),
            "statement": proposition["text"],
            "proposition": proposition,
            "assertion": assertion,
            "lineage": lineage,
            "dependencies": dependencies,
            "calculations": calculation_traces,
            "sources": [self.span_trace(key) for key in unique_span_keys],
        }

    def count_ledgers(self) -> dict[str, list[dict[str, Any]]]:
        indexes = self.indexes()
        ledgers: dict[str, list[dict[str, Any]]] = {}
        for card in self.manifest["count_cards"]:
            entries = []
            for member in card["members"]:
                obj = indexes[member["collection"]][member["object_key"]]
                entry = {
                    "key": member["item_key"],
                    "title": member["label"],
                    "object_type": member["collection"],
                    "object_key": member["object_key"],
                    "object": obj,
                }
                basis_span_key = member["basis_span_key"]
                if basis_span_key is not None:
                    entry["basis"] = self.span_trace(basis_span_key)
                entries.append(entry)
            ledgers[card["key"]] = entries
        return ledgers

    def derived_counts(self) -> dict[str, int]:
        return {
            key: len(entries) for key, entries in self.count_ledgers().items()
        }

    def projection(self, view: str) -> dict[str, Any]:
        if view not in FEATURE_VIEWS:
            raise FeaturedDossierError(f"unknown dossier policy view: {view}")
        indexes = self.indexes()
        family = indexes["claim_families"][self.manifest["claim_family_key"]]
        evaluation = indexes["evaluations"][
            self.manifest["views"][view]["evaluation_key"]
        ]
        ledgers = self.count_ledgers()
        counts = self.derived_counts()
        count_cards = [
            {
                "key": card["key"],
                "ledger_key": card["key"],
                "value": counts[card["key"]],
                "label": card["label"],
                "anchor": card["anchor"],
                "note": card["note"],
            }
            for card in self.manifest["count_cards"]
        ]
        featured_relations = [
            self.relation_trace(key)
            for key in self.manifest["views"][view]["featured_relation_keys"]
        ]
        practical = self.manifest["practical_readings"][view]
        reviewer = _object(self.receipt["reviewer"], "bounded reviewer")
        reviewed = self.receipt.get("reviewed")
        if isinstance(reviewed, dict):
            reviewed_base = reviewed.get("base", "unknown")
        else:
            repository = _object(
                self.receipt.get("repository"), "bounded receipt.repository"
            )
            reviewed_base = repository.get("reviewed_base", "unknown")
        limitations = self.receipt.get("limitations", [])
        display_title = self.dossier["title"].removeprefix(
            f"Case {self.manifest['number']}: "
        )
        return {
            "format": BOUNDED_PROJECTION_FORMAT,
            "profile": BOUNDED_PROPOSITION_PROFILE,
            "slug": self.slug,
            "number": self.manifest["number"],
            "selection_status": self.manifest["status"],
            "selection_note": self.manifest["selection_note"],
            "selection_manifest": self.manifest_path.relative_to(self.root).as_posix(),
            "selection_manifest_sha256": _sha256(self.manifest_path),
            "dossier_id": self.dossier["dossier_id"],
            "title": display_title,
            "question": self.dossier["question"],
            "scope": self.manifest["public_scope"],
            "editorial": CASE_EDITORIAL[self.slug],
            "research_scope": self.dossier["scope"],
            "claim_family": family,
            "target_proposition": indexes["propositions"][
                self.manifest["target_proposition_key"]
            ],
            "view": {
                "id": view,
                "policy_id": evaluation["policy_id"],
                "evaluation_id": evaluation["id"],
                "label": evaluation["label"],
                "reason_codes": evaluation["reason_codes"],
            },
            "counts": counts,
            "count_cards": count_cards,
            "count_ledgers": ledgers,
            "ledger_sections": [
                {
                    "anchor": card["anchor"],
                    "key": card["key"],
                    "title": card["label"].title(),
                }
                for card in self.manifest["count_cards"]
            ],
            "lexicon": self.manifest["lexicon"],
            "practical_reading": practical,
            "featured_relations": featured_relations,
            "dependence_warning": self.manifest["dependence_warning"],
            "warrant_warning": self.manifest["warrant_warning"],
            "source_work_count": len(indexes["source_works"]),
            "edition_count": len(indexes["editions"]),
            "span_count": len(indexes["spans"]),
            "source_works": sorted(
                indexes["source_works"].values(), key=lambda item: item["key"]
            ),
            "review": {
                "decision": self.receipt["decision"],
                "reviewer_id": reviewer["id"],
                "independence_statement": (
                    "A separate Codex review agent used a fresh clone, did not author "
                    "the candidate, and checked exact source, calculation, lineage, "
                    "receipt, repository, and deterministic-build closure. The review "
                    "did not decide that the bounded scientific claim is universally true."
                ),
                "fresh_clone": True,
                "reviewed_head": self.manifest["reviewed_head"],
                "reviewed_base": reviewed_base,
                "reviewed_tree": self.manifest["reviewed_tree"],
                "receipt_path": self.manifest["review_receipt_path"],
                "receipt_sha256": _sha256(
                    self.root / self.manifest["review_receipt_path"]
                ),
                "completed_at": self.receipt.get("completed_at", "unknown"),
                "checked_scope": [
                    "Exact accepted packet, dossier, and review-receipt bytes",
                    "Source, edition, span, calculation, and license closure",
                    "Count grammar, unresolved items, and typed dependence edges",
                    "Policy divergence, adversarial validation, and deterministic build",
                ],
                "limitations": (
                    limitations
                    if isinstance(limitations, list)
                    and all(isinstance(item, str) for item in limitations)
                    else []
                ),
            },
            "dossier": self.dossier,
        }

    def review_envelope(self, catalog: PublicCatalog) -> dict[str, Any]:
        from .core import envelope

        projection = self.projection(self.default_view)
        return envelope(
            catalog,
            {
                "format": "epistemedia-public-review-receipt-v0.1",
                "profile": BOUNDED_PROPOSITION_PROFILE,
                "slug": projection["slug"],
                "number": projection["number"],
                "title": projection["title"],
                "dossier_id": projection["dossier_id"],
                "review": projection["review"],
            },
        )


AcceptedDossier = FeaturedDossier | AgentLineageDossier | BoundedPropositionDossier


@dataclass(frozen=True)
class FeaturedDossierLibrary:
    root: Path
    dossiers: tuple[AcceptedDossier, ...]
    lead_slug: str

    @property
    def lead(self) -> AcceptedDossier:
        return self.get(self.lead_slug)

    def get(self, slug: str) -> AcceptedDossier:
        for dossier in self.dossiers:
            if dossier.slug == slug:
                return dossier
        raise KeyError(slug)

    def summaries(self, catalog: PublicCatalog) -> list[dict[str, Any]]:
        return [dossier.summary(catalog) for dossier in self.dossiers]


def load_featured_library(
    root: Path, *, required: bool = False
) -> FeaturedDossierLibrary | None:
    root = root.resolve()
    directory = root / MANIFEST_DIRECTORY
    manifest_paths = (
        sorted(path.relative_to(root) for path in directory.glob("*.json"))
        if directory.exists()
        else []
    )
    if not manifest_paths:
        if required:
            raise FeaturedDossierError("no accepted dossier manifests are configured")
        return None
    dossiers: list[AcceptedDossier] = []
    for manifest_path in manifest_paths:
        try:
            header = _object(
                json.loads((root / manifest_path).read_text()),
                f"dossier manifest {manifest_path}",
            )
        except json.JSONDecodeError as exc:
            raise FeaturedDossierError(
                f"dossier manifest is invalid JSON: {manifest_path}"
            ) from exc
        manifest_format = header.get("format")
        if manifest_format == FEATURE_FORMAT:
            dossiers.append(FeaturedDossier.load(root, manifest_path))
        elif manifest_format == AGENT_LINEAGE_FORMAT:
            dossiers.append(AgentLineageDossier.load(root, manifest_path))
        elif manifest_format == BOUNDED_PROPOSITION_FORMAT:
            dossiers.append(BoundedPropositionDossier.load(root, manifest_path))
        else:
            raise FeaturedDossierError(
                f"unsupported dossier manifest format at {manifest_path}: {manifest_format}"
            )
    dossiers.sort(key=lambda dossier: (int(dossier.manifest["number"]), dossier.slug))

    uniqueness: dict[str, set[str]] = {
        "dossier number": set(),
        "dossier slug": set(),
        "dossier identity": set(),
        "dossier path": set(),
        "receipt path": set(),
        "generated route": set(),
        "MCP URI": set(),
    }
    for dossier in dossiers:
        values = {
            "dossier number": dossier.manifest["number"],
            "dossier slug": dossier.slug,
            "dossier identity": dossier.dossier["dossier_id"],
            "dossier path": dossier.manifest["dossier_path"],
            "receipt path": dossier.manifest["review_receipt_path"],
        }
        routes = {
            f"/how-we-know/{dossier.slug}/",
            f"/how-we-know/{dossier.slug}/review/",
            *(f"/how-we-know/{dossier.slug}/{view}/" for view in FEATURE_VIEWS),
        }
        uris = {
            f"epistemedia://dossier/{dossier.slug}/{view}" for view in FEATURE_VIEWS
        }
        for context, value in values.items():
            if value in uniqueness[context]:
                raise FeaturedDossierError(f"duplicate accepted {context}: {value}")
            uniqueness[context].add(value)
        for route in routes:
            if route in uniqueness["generated route"]:
                raise FeaturedDossierError(f"duplicate accepted dossier route: {route}")
            uniqueness["generated route"].add(route)
        for uri in uris:
            if uri in uniqueness["MCP URI"]:
                raise FeaturedDossierError(f"duplicate accepted dossier MCP URI: {uri}")
            uniqueness["MCP URI"].add(uri)

    legacy_slug = None
    for dossier in dossiers:
        if dossier.manifest_path.relative_to(root) == FEATURE_MANIFEST:
            legacy_slug = dossier.slug
            break
    if legacy_slug is None:
        raise FeaturedDossierError("the explicit Case 001 lead manifest is missing")
    return FeaturedDossierLibrary(root, tuple(dossiers), legacy_slug)


def _display_item(item: dict[str, Any]) -> tuple[str, str]:
    relation = item.get("relation")
    if isinstance(relation, dict):
        return str(relation.get("key", "relation")), str(item.get("statement", ""))
    key = str(item.get("key", item.get("citation_occurrence_id", "item")))
    title = str(item.get("title", item.get("raw_title", key)))
    status = item.get("status", item.get("resolution_status"))
    return key, f"{title}{f' — {status}' if status else ''}"


def agent_projection_markdown(document: dict[str, Any]) -> str:
    data = document["data"]
    editorial = data["editorial"]
    lines = [
        f"# Case {data['number']} — {data['title']}",
        "",
        f"**Failure mode:** {editorial['failure_mode']}",
        "",
        f"**The claim:** {editorial['claim']}",
        "",
        f"**Why care:** {editorial['why']}",
        "",
        f"**{data['view']['id'].title()} finding:** {data['view']['label']}",
        "",
        f"**Practical reading:** {data['practical_reading']['text']}",
        "",
        data["practical_reading"]["qualifier"],
        "",
        "## How the claim changes under inspection",
        "",
    ]
    for index, step in enumerate(editorial["story"], 1):
        lines.extend(
            [
                f"### {index:02d} — {step['title']}",
                "",
                f"**{step['label']}:** {step['text']}",
                "",
            ]
        )
    lines.extend(
        [
        "## Run this research with your agent",
        "",
        "Open [`research-brief.md`](research-brief.md) for this case and the "
        "[common protocol](/agents/research-protocol.md). A prepared proposal is untrusted "
        "intake with zero evidential credit; hosted submission is not available yet.",
        "",
        "## Evidence accounting",
        "",
        ]
    )
    for card in data["count_cards"]:
        lines.append(
            f"- [{card['value']} {card['label']}](#{card['anchor']}): {card['note']}"
        )
    lines.extend(
        [
            "",
            f"**Dependence warning:** {data['dependence_warning']}",
            "",
            "## What the selected record says",
            "",
        ]
    )
    for item in data["featured_relations"]:
        lines.append(f"### {item['relation_label'].title()}")
        lines.append("")
        lines.append(item["statement"])
        lines.append("")
        lines.append(f"- Relation: `{item['relation']['key']}` · `{item['relation']['id']}`")
        if isinstance(item.get("proposition"), dict):
            lines.append(
                f"- Proposition: `{item['proposition']['key']}` · `{item['proposition']['id']}`"
            )
        if isinstance(item.get("assertion"), dict):
            lines.append(
                f"- Assertion: `{item['assertion']['key']}` · `{item['assertion']['id']}`"
            )
        if isinstance(item.get("lineage"), dict):
            lines.append(
                f"- Lineage: `{item['lineage']['key']}` · `{item['lineage']['id']}`"
            )
        for dependency in item.get("dependencies", []):
            lines.append(
                f"- Dependence: `{dependency['key']}` · `{dependency['id']}` · "
                f"`{dependency['from_ref']}` → `{dependency['to_ref']}`"
            )
        lines.append("")
        for source in item["sources"]:
            span = source["span"]
            edition = source["edition"]
            work = source["source_work"]
            lines.extend(
                [
                    f"- Source: [{work['title']}]({work['canonical_uri']})",
                    f"- Work: `{work['id']}`",
                    f"- Edition: `{edition['id']}` · `{edition['content_digest']}`",
                    f"- Span: `{span['id']}` · `{span['digest']}`",
                    f"- Locator: {span['locator']['label']}",
                    f"- License: {work['license']} · {source['license_treatment']}",
                    "",
                ]
            )
        for calculation in item.get("calculations", []):
            lines.extend(
                [
                    f"#### Calculation · `{calculation['relation']['key']}`",
                    "",
                    calculation["proposition"]["text"],
                    "",
                    f"- Proposition: `{calculation['proposition']['id']}`",
                    f"- Assertion: `{calculation['assertion']['id']}`",
                ]
            )
            for source in calculation["sources"]:
                span = source["span"]
                edition = source["edition"]
                work = source["source_work"]
                lines.extend(
                    [
                        f"- Input/source: `{span['key']}` · `{span['digest']}`",
                        f"  - Work: `{work['id']}` · {work['license']}",
                        f"  - Edition: `{edition['id']}` · `{edition['content_digest']}`",
                        f"  - Locator: {span['locator']['label']}",
                    ]
                )
                if span["key"].startswith("span-calculation-"):
                    lines.extend(
                        [
                            "",
                            "```json",
                            json.dumps(
                                span["extent"].get("value"), indent=2, sort_keys=True
                            ),
                            "```",
                        ]
                    )
            lines.append("")
    lines.extend(["## Complete count ledgers", ""])
    for section in data["ledger_sections"]:
        key = section["key"]
        title = section["title"]
        items = data["count_ledgers"][key]
        lines.extend([f"### {title} ({len(items)})", ""])
        for item in items:
            identity, label = _display_item(item)
            lines.append(f"- `{identity}` — {label}")
            obj = item.get("object")
            if isinstance(obj, dict):
                lines.append(
                    f"  - {item.get('object_type', 'object')}: "
                    f"`{item.get('object_key', 'unknown')}` · `{obj.get('id', 'unknown')}`"
                )
                if obj.get("status") is not None:
                    lines.append(f"  - Status: {obj['status']}")
                if obj.get("dimensions"):
                    lines.append(
                        "  - Dependence dimensions: "
                        + ", ".join(f"`{value}`" for value in obj["dimensions"])
                    )
            basis = item.get("basis")
            if isinstance(basis, dict):
                lines.extend(
                    [
                        f"  - Basis span: `{basis['span']['id']}` · `{basis['span']['digest']}`",
                        f"  - Basis edition: `{basis['edition']['id']}` · `{basis['edition']['content_digest']}`",
                        f"  - Basis work: `{basis['source_work']['id']}` · {basis['source_work']['license']}",
                    ]
                )
        lines.append("")
    lines.extend(
        [
            "## Reproducibility identity",
            "",
            f"- Dossier: `{data['dossier_id']}`",
            f"- Review receipt: `{data['review']['receipt_sha256']}`",
            f"- Catalog: `{document['catalog_id']}`",
            f"- Frontier: `{document['frontier']}`",
            f"- Accepted commit: `{document['commit']}`",
            f"- Content digest: `{document['content_digest']}`",
            "",
        ]
    )
    return "\n".join(lines)


def _source_extent(source: dict[str, Any]) -> str:
    extent = source["span"]["extent"]
    value = extent.get("quote", extent.get("value"))
    if isinstance(value, dict) and isinstance(value.get("quote"), str):
        return value["quote"]
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, sort_keys=True)
    return str(value)


def _source_token(source: dict[str, Any]) -> tuple[str, str]:
    return str(source["span"]["id"]), str(source["span"]["digest"])


def _source_register(
    relations: list[dict[str, Any]],
) -> tuple[dict[tuple[str, str], str], str]:
    source_ids: dict[tuple[str, str], str] = {}
    records: list[dict[str, Any]] = []
    uses: dict[tuple[str, str], list[int]] = {}
    for relation_index, item in enumerate(relations, 1):
        sources = list(item["sources"])
        for calculation in item.get("calculations", []):
            sources.extend(calculation["sources"])
        for source in sources:
            token = _source_token(source)
            uses.setdefault(token, []).append(relation_index)
            if token in source_ids:
                continue
            source_id = f"exact-source-{len(records) + 1:02d}"
            source_ids[token] = source_id
            records.append(source)

    cards = []
    for source in records:
        token = _source_token(source)
        source_id = source_ids[token]
        span = source["span"]
        edition = source["edition"]
        work = source["source_work"]
        retrieval = source.get("retrieval") or []
        retrieval_text = " · ".join(
            f"{record.get('retrieval_status', 'not-recorded')} {record.get('requested_url', '')}"
            for record in retrieval
        ) or "Repository audit span; no external retrieval record"
        relation_uses = ", ".join(f"{index:02d}" for index in sorted(set(uses[token])))
        cards.append(
            f'<article class="source-card" id="{source_id}">'
            f'<p class="source-use">Used by evidence statement {html.escape(relation_uses)}</p>'
            f"<h4>{html.escape(work['title'])}</h4>"
            f"<p>{html.escape(span['locator']['label'])}</p>"
            f"<blockquote>{html.escape(_source_extent(source))}</blockquote>"
            '<details class="technical-disclosure"><summary>Exact source identity</summary>'
            '<dl class="receipt-grid compact">'
            f"<div><dt>Work</dt><dd><a href=\"{html.escape(work['canonical_uri'])}\">{html.escape(work['id'])}</a></dd></div>"
            f"<div><dt>Edition</dt><dd>{html.escape(edition['id'])}</dd></div>"
            f"<div><dt>Edition digest</dt><dd>{html.escape(edition['content_digest'])}</dd></div>"
            f"<div><dt>Span</dt><dd>{html.escape(span['id'])}</dd></div>"
            f"<div><dt>Span digest</dt><dd>{html.escape(span['digest'])}</dd></div>"
            f"<div><dt>Retrieval</dt><dd>{html.escape(retrieval_text)}</dd></div>"
            f"<div><dt>License</dt><dd>{html.escape(str(work['license']))} · {html.escape(str(source['license_treatment']))}</dd></div>"
            "</dl></details></article>"
        )
    register = (
        '<details class="source-register human-source-register">'
        f"<summary>{len(records)} exact passages · repeated display spans collapsed</summary>"
        '<p class="source-register-note">This human register shows each exact accepted span once. '
        "The JSON, Markdown, relations, and ledgers retain every occurrence.</p>"
        + "".join(cards)
        + "</details>"
    )
    return source_ids, register


def _agent_source_xray(
    item: dict[str, Any], index: int, source_ids: dict[tuple[str, str], str]
) -> str:
    source_links = "".join(
        f'<a href="#{html.escape(source_ids[_source_token(source)])}">'
        f"{html.escape(source['source_work']['title'])} · "
        f"{html.escape(source['span']['locator']['label'])}</a>"
        for source in item["sources"]
    )
    identity_rows = []
    for label, value in (
        ("Relation", item.get("relation")),
        ("Proposition", item.get("proposition")),
        ("Assertion", item.get("assertion")),
        ("Lineage", item.get("lineage")),
    ):
        if not isinstance(value, dict):
            continue
        identity_rows.append(
            f"<div><dt>{label}</dt><dd><code>{html.escape(str(value.get('key', 'unknown')))}</code> "
            f"<code>{html.escape(str(value.get('id', 'unknown')))}</code></dd></div>"
        )
    dependency_html = "".join(
        '<li class="ledger-entry"><code>'
        f"{html.escape(dependency['key'])}</code><span>"
        f"{html.escape(dependency['from_ref'])} → {html.escape(dependency['to_ref'])}"
        f"<small>{html.escape(dependency['id'])}</small>"
        f"<small>{html.escape(dependency['note'])}</small></span></li>"
        for dependency in item.get("dependencies", [])
    )
    calculation_html = "".join(
        _calculation_html(calculation) for calculation in item.get("calculations", [])
    )
    return (
        '<article class="evidence-brief">'
        f'<div class="evidence-marker"><span>{index:02d}</span>{html.escape(item["relation_label"])}</div>'
        '<div class="evidence-brief-copy">'
        f'<p class="material-sentence">{html.escape(item["statement"])}</p>'
        f'<div class="source-jump-list">{source_links}</div>'
        '<details class="technical-disclosure relation-trace"><summary>Trace this statement</summary>'
        f'<dl class="receipt-grid compact">{"".join(identity_rows)}</dl>'
        + (
            '<h4>Typed dependence</h4><ol class="ledger-list">'
            + dependency_html
            + "</ol>"
            if dependency_html
            else ""
        )
        + calculation_html
        + "</details></div></article>"
    )


def _calculation_html(calculation: dict[str, Any]) -> str:
    source_rows = []
    calculation_record = None
    for source in calculation["sources"]:
        span = source["span"]
        edition = source["edition"]
        work = source["source_work"]
        source_rows.append(
            '<li class="ledger-entry"><code>'
            f"{html.escape(span['key'])}</code><span>{html.escape(span['locator']['label'])}"
            f"<small>{html.escape(span['id'])} · {html.escape(span['digest'])}</small>"
            f"<small>{html.escape(edition['id'])} · {html.escape(edition['content_digest'])}</small>"
            f"<small>{html.escape(work['id'])} · {html.escape(str(work['license']))} · "
            f"{html.escape(str(source['license_treatment']))}</small></span></li>"
        )
        if span["key"].startswith("span-calculation-"):
            calculation_record = span["extent"].get("value")
    record_html = ""
    if calculation_record is not None:
        record_html = (
            '<pre class="calculation-record"><code>'
            + html.escape(json.dumps(calculation_record, indent=2, sort_keys=True))
            + "</code></pre>"
        )
    return (
        '<details class="technical-disclosure calculation-disclosure">'
        f"<summary>Calculation · {html.escape(calculation['proposition']['text'])}</summary>"
        '<dl class="receipt-grid compact">'
        f"<div><dt>Relation</dt><dd><code>{html.escape(calculation['relation']['key'])}</code> "
        f"<code>{html.escape(calculation['relation']['id'])}</code></dd></div>"
        f"<div><dt>Proposition</dt><dd><code>{html.escape(calculation['proposition']['id'])}</code></dd></div>"
        f"<div><dt>Assertion</dt><dd><code>{html.escape(calculation['assertion']['id'])}</code></dd></div>"
        "</dl>"
        + record_html
        + f'<ol class="ledger-list">{"".join(source_rows)}</ol>'
        + "</details>"
    )


def _ledger_html(key: str, title: str, items: list[dict[str, Any]]) -> str:
    rows = []
    for item in items:
        identity, label = _display_item(item)
        obj = item.get("object") if isinstance(item.get("object"), dict) else None
        object_type = item.get("object_type")
        object_key = item.get("object_key")
        if (
            obj is None
            or not isinstance(object_type, str)
            or not object_type
            or not isinstance(object_key, str)
            or not object_key
            or not isinstance(obj.get("id"), str)
            or not obj["id"]
        ):
            raise FeaturedDossierError(
                f"human ledger member lacks typed identity: {key}.{identity}"
            )
        provenance_rows = [
            f"<div><dt>Member</dt><dd><code>{html.escape(identity)}</code></dd></div>",
            f"<div><dt>Object type</dt><dd>{html.escape(object_type.replace('_', ' '))}</dd></div>",
            f"<div><dt>Object key</dt><dd><code>{html.escape(object_key)}</code></dd></div>",
            f"<div><dt>Object ID</dt><dd><code>{html.escape(obj['id'])}</code></dd></div>",
        ]
        if obj.get("status") is not None:
            provenance_rows.append(
                f"<div><dt>Status</dt><dd>{html.escape(str(obj['status']))}</dd></div>"
            )
        if obj.get("dimensions"):
            provenance_rows.append(
                "<div><dt>Dependence</dt><dd>"
                + html.escape(", ".join(str(value) for value in obj["dimensions"]))
                + "</dd></div>"
            )
        basis = item.get("basis")
        if isinstance(basis, dict):
            provenance_rows.extend(
                [
                    f"<div><dt>Basis span</dt><dd><code>{html.escape(basis['span']['id'])}</code> "
                    f"<code>{html.escape(basis['span']['digest'])}</code></dd></div>",
                    f"<div><dt>Basis edition</dt><dd><code>{html.escape(basis['edition']['id'])}</code> "
                    f"<code>{html.escape(basis['edition']['content_digest'])}</code></dd></div>",
                    f"<div><dt>Basis work</dt><dd><code>{html.escape(basis['source_work']['id'])}</code> · "
                    f"{html.escape(str(basis['source_work']['license']))}</dd></div>",
                ]
            )
        rows.append(
            '<li class="ledger-entry"><span class="ledger-human-label">'
            f"{html.escape(label)}</span>"
            '<details class="technical-disclosure ledger-provenance">'
            "<summary>Technical identity</summary>"
            f'<dl class="receipt-grid compact">{"".join(provenance_rows)}</dl>'
            "</details></li>"
        )
    return (
        f'<details class="source-xray ledger-group" id="{html.escape(key)}">'
        f"<summary>{len(items)} · {html.escape(title)}</summary>"
        f'<ol class="ledger-list">{"".join(rows)}</ol></details>'
    )


def agent_page_html(document: dict[str, Any], base_url: str) -> str:
    data = document["data"]
    view = data["view"]["id"]
    policy_link_parts = []
    for policy in FEATURE_VIEWS:
        current = ' aria-current="page"' if policy == view else ""
        policy_link_parts.append(
            f'<a href="{html.escape(base_url)}/how-we-know/'
            f'{html.escape(data["slug"])}/{policy}/"{current}>{policy.title()}</a>'
        )
    policy_links = "".join(policy_link_parts)
    cards = "".join(
        '<a class="tally-cell" '
        f'href="#{html.escape(card["anchor"])}"><strong>{card["value"]}</strong>'
        f'<span>{html.escape(card["label"])}</span><small>{html.escape(card["note"])}</small></a>'
        for card in data["count_cards"]
    )
    source_ids, source_register = _source_register(data["featured_relations"])
    relation_html = "".join(
        _agent_source_xray(item, index, source_ids)
        for index, item in enumerate(data["featured_relations"], 1)
    )
    primary_ledger_keys = {card["ledger_key"] for card in data["count_cards"]}
    primary_sections = [
        section for section in data["ledger_sections"] if section["key"] in primary_ledger_keys
    ]
    audit_sections = [
        section for section in data["ledger_sections"] if section["key"] not in primary_ledger_keys
    ]
    ledgers = "".join(
        _ledger_html(
            section["anchor"],
            section["title"],
            data["count_ledgers"][section["key"]],
        )
        for section in primary_sections
    )
    audit_ledgers = "".join(
        _ledger_html(
            section["anchor"],
            section["title"],
            data["count_ledgers"][section["key"]],
        )
        for section in audit_sections
    )
    audit_html = (
        '<details class="full-audit-ledgers"><summary>Open the full technical ledger '
        f"· {len(audit_sections)} additional groups</summary>{audit_ledgers}</details>"
        if audit_sections
        else ""
    )
    lexicon = "".join(
        f"<div><dt>{html.escape(item['term'])}</dt><dd>{html.escape(item['definition'])}</dd></div>"
        for item in data["lexicon"]
    )
    editorial = data["editorial"]
    story = "".join(
        '<article class="evidence-map-step">'
        f'<p class="eyebrow">{index:02d} · {html.escape(step["label"])}</p>'
        f'<h3>{html.escape(step["title"])}</h3>'
        f'<p>{html.escape(step["text"])}</p></article>'
        for index, step in enumerate(editorial["story"], 1)
    )
    return f"""
<article class="dossier-page structured-case {html.escape(data['profile'])}">
  <header class="dossier-lead">
    <div class="case-rule"><span>How We Know · Case {html.escape(data['number'])}</span><span>{html.escape(editorial['failure_mode'])}</span></div>
    <h1>{html.escape(data['title'])}</h1>
    <p class="case-claim"><strong>The claim:</strong> {html.escape(editorial['claim'])}</p>
    <p class="dek"><strong>Why care:</strong> {html.escape(editorial['why'])}</p>
    <nav class="policy-switch" aria-label="Evidence policy">{policy_links}</nav>
  </header>
  <section class="case-finding" aria-labelledby="finding-title">
    <div><p class="eyebrow" id="finding-title">{html.escape(view)} finding</p>
    <p class="verdict-copy">{html.escape(data['view']['label'])}</p></div>
    <div><p class="eyebrow">If you use this claim</p><p>{html.escape(data['practical_reading']['text'])}</p></div>
    <p class="muted">{html.escape(data['practical_reading']['qualifier'])}</p>
  </section>
  <p class="scope-note"><strong>Boundary</strong><span>{html.escape(data['scope'])}</span></p>
  <section aria-labelledby="evidence-map-title">
    <p class="eyebrow">The evidence map</p>
    <h2 id="evidence-map-title">How the familiar claim changes under inspection</h2>
    <div class="evidence-map">{story}</div>
  </section>
  <section aria-labelledby="accounting-title">
    <p class="eyebrow">Lineage accounting</p>
    <h2 id="accounting-title">{html.escape(data.get('accounting_heading', 'The units count different things'))}</h2>
    <div class="evidence-tally agent-tally">{cards}</div>
    <p class="qualification"><strong>Shared capture:</strong> {html.escape(data['dependence_warning'])}</p>
    <p class="qualification"><strong>Warrant boundary:</strong> {html.escape(data['warrant_warning'])}</p>
  </section>
  <aside class="agent-research-cue" aria-labelledby="agent-research-title">
    <div><p class="eyebrow">Run the test yourself</p><h2 id="agent-research-title">Give this case to your coding agent</h2>
    <p>The public brief supplies the question, comparison target, source and span rules, dependence policy, negative-result policy, and output format.</p></div>
    <p><a class="primary-action" href="{html.escape(base_url)}/how-we-know/{html.escape(data['slug'])}/research-brief.md">Open the agent brief</a><br><a href="{html.escape(base_url)}/agents/research-protocol.md">Read the common protocol</a></p>
  </aside>
  <section aria-labelledby="record-title">
    <p class="eyebrow">Sentence x-ray</p>
    <h2 id="record-title">What the selected record actually supports</h2>
    <p>Read the statement first. Its exact work, edition, span, retrieval, digest, and license chain—plus dependence and calculations—remain one disclosure away.</p>
    {relation_html}
    {source_register}
  </section>
  <section aria-labelledby="ledger-title">
    <p class="eyebrow">Verify every number</p>
    <h2 id="ledger-title">Complete count ledgers</h2>
    <p>Every displayed total is a view over these typed members; no total is maintained as marketing copy.</p>
    {ledgers}
    {audit_html}
  </section>
  <section aria-labelledby="lexicon-title">
    <p class="eyebrow">Five-line lexicon</p>
    <h2 id="lexicon-title">The units are different on purpose</h2>
    <dl class="lexicon-list">{lexicon}</dl>
  </section>
  <footer class="case-actions">
    <a href="{html.escape(base_url)}/how-we-know/{html.escape(data['slug'])}/index.md">Read as Markdown</a>
    <a href="{html.escape(base_url)}/how-we-know/{html.escape(data['slug'])}/review/">Review receipt</a>
    <a href="{html.escape(base_url)}/how-we-know/{html.escape(data['slug'])}/share-card.svg">Share card</a>
    <a href="{html.escape(base_url)}/how-we-know/{html.escape(data['slug'])}/research-brief.md">Agent research brief</a>
  </footer>
</article>
""".strip()


def agent_share_card_svg(document: dict[str, Any], base_url: str) -> str:
    data = document["data"]
    counts = data["counts"]
    title_lines = textwrap.wrap(data["title"], width=39)[:2]
    title = "".join(
        f'<tspan x="70" dy="{0 if index == 0 else 54}">{html.escape(line)}</tspan>'
        for index, line in enumerate(title_lines)
    )
    canonical = f"{base_url}/how-we-know/{data['slug']}/{data['view']['id']}/"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-labelledby="title desc">
<title id="title">Case {html.escape(data['number'])}: {html.escape(data['title'])}</title>
<desc id="desc">Eight captured reports collapse into thirty URL strings, eleven works, seven candidate warrants, and zero independently confirmed warrant roots.</desc>
<rect width="1200" height="630" fill="#f4efe3"/><rect x="0" y="0" width="18" height="630" fill="#163f31"/><rect x="18" y="0" width="9" height="630" fill="#d96f19"/>
<text x="70" y="72" font-family="ui-monospace,monospace" font-size="24" fill="#163f31">EPISTEMEDIA · HOW WE KNOW · CASE {html.escape(data['number'])}</text>
<text x="70" y="145" font-family="Georgia,serif" font-weight="700" font-size="48" fill="#171a16">{title}</text>
<g font-family="ui-sans-serif,sans-serif" fill="#171a16">
<text x="80" y="330" font-size="72" font-weight="800">{counts['captured_reports']}</text><text x="80" y="365" font-size="21">reports</text>
<text x="300" y="330" font-size="72" font-weight="800">{counts['cited_url_strings']}</text><text x="300" y="365" font-size="21">URL strings</text>
<text x="540" y="330" font-size="72" font-weight="800">{counts['source_work_roots']}</text><text x="540" y="365" font-size="21">source works</text>
<text x="770" y="330" font-size="72" font-weight="800">{counts['candidate_warrant_roots']}</text><text x="770" y="365" font-size="21">candidate warrants</text>
<text x="1010" y="330" font-size="72" font-weight="800" fill="#b65012">0</text><text x="1010" y="365" font-size="21">confirmed</text>
</g>
<text x="70" y="450" font-family="Georgia,serif" font-size="30" fill="#171a16">Eight answers are observations—not eight independent witnesses.</text>
<text x="70" y="505" font-family="ui-sans-serif,sans-serif" font-size="22" fill="#4e554d">{counts['unresolved_citations']} citations unresolved · {counts['unsupported_or_force_raised_claims']} claims receive no credit</text>
<text x="70" y="565" font-family="ui-monospace,monospace" font-size="15" fill="#4e554d">{html.escape(data['dossier_id'])}</text>
<metadata>{html.escape(json.dumps({'canonical': canonical, 'catalog_id': document['catalog_id'], 'frontier': document['frontier'], 'commit': document['commit'], 'content_digest': document['content_digest']}, sort_keys=True))}</metadata>
</svg>
"""


def bounded_share_card_svg(document: dict[str, Any], base_url: str) -> str:
    data = document["data"]
    title_lines = textwrap.wrap(data["title"], width=39)[:2]
    title = "".join(
        f'<tspan x="70" dy="{0 if index == 0 else 54}">{html.escape(line)}</tspan>'
        for index, line in enumerate(title_lines)
    )
    cards = data["count_cards"][:4]
    card_width = 270
    card_markup = []
    for index, card in enumerate(cards):
        x = 70 + index * card_width
        label_lines = textwrap.wrap(card["label"], width=22)[:3]
        label_markup = "".join(
            f'<tspan x="{x}" dy="{0 if line_index == 0 else 22}">'
            f"{html.escape(line)}</tspan>"
            for line_index, line in enumerate(label_lines)
        )
        card_markup.append(
            f'<text x="{x}" y="345" font-size="72" font-weight="800">'
            f'{card["value"]}</text><text x="{x}" y="382" font-size="18">'
            f"{label_markup}</text>"
        )
    finding = textwrap.shorten(data["view"]["label"], width=86, placeholder="…")
    canonical = f"{base_url}/how-we-know/{data['slug']}/{data['view']['id']}/"
    description = " · ".join(
        f"{card['value']} {card['label']}" for card in cards
    )
    metadata = {
        "canonical": canonical,
        "catalog_id": document["catalog_id"],
        "frontier": document["frontier"],
        "commit": document["commit"],
        "dossier_id": data["dossier_id"],
        "content_digest": document["content_digest"],
    }
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-labelledby="title desc">
<title id="title">Case {html.escape(data['number'])}: {html.escape(data['title'])}</title>
<desc id="desc">{html.escape(description)}</desc>
<rect width="1200" height="630" fill="#f4efe3"/><rect x="0" y="0" width="18" height="630" fill="#163f31"/><rect x="18" y="0" width="9" height="630" fill="#d96f19"/>
<text x="70" y="72" font-family="ui-monospace,monospace" font-size="24" fill="#163f31">EPISTEMEDIA · HOW WE KNOW · CASE {html.escape(data['number'])}</text>
<text x="70" y="145" font-family="Georgia,serif" font-weight="700" font-size="48" fill="#171a16">{title}</text>
<g font-family="ui-sans-serif,sans-serif" fill="#171a16">{''.join(card_markup)}</g>
<text x="70" y="470" font-family="Georgia,serif" font-size="29" fill="#171a16">{html.escape(finding)}</text>
<text x="70" y="525" font-family="ui-sans-serif,sans-serif" font-size="21" fill="#4e554d">Open the ledgers. Inspect the passages. Keep the unresolved record visible.</text>
<text x="70" y="575" font-family="ui-monospace,monospace" font-size="15" fill="#4e554d">{html.escape(data['dossier_id'])}</text>
<metadata>{html.escape(json.dumps(metadata, sort_keys=True))}</metadata>
</svg>
"""


def agent_review_markdown(document: dict[str, Any]) -> str:
    data = document["data"]
    review = data["review"]
    lines = [
        f"# Review receipt — Case {data['number']}",
        "",
        f"**Decision:** {review['decision']}",
        "",
        review["independence_statement"],
        "",
        f"- Technical reviewer ID: `{review['reviewer_id']}`",
        f"- Reviewed author head: `{review['reviewed_head']}`",
        f"- Dossier: `{data['dossier_id']}`",
        f"- Receipt SHA-256: `{review['receipt_sha256']}`",
        f"- Completed: `{review['completed_at']}`",
        "",
        "## Checked scope",
        "",
        *[f"- {item}" for item in review["checked_scope"]],
        "",
        "## Limitations",
        "",
        *[f"- {item}" for item in review["limitations"]],
        "",
        "This review checked the bounded evidence packet and its derivation. It did not decide "
        "whether every empirical proposition is universally or currently true.",
        "",
    ]
    return "\n".join(lines)


def agent_review_html(document: dict[str, Any], base_url: str) -> str:
    data = document["data"]
    review = data["review"]
    checked = "".join(f"<li>{html.escape(item)}</li>" for item in review["checked_scope"])
    limitations = "".join(
        f"<li>{html.escape(item)}</li>" for item in review["limitations"]
    )
    return f"""
<article class="review-sheet">
  <header class="dossier-lead"><p class="eyebrow">How We Know · Case {html.escape(data['number'])}</p><h1>Independent review receipt</h1><p class="dek">{html.escape(data['title'])}</p></header>
  <section class="verdict-panel"><p class="eyebrow">Decision</p><p class="verdict-copy">{html.escape(review['decision'])}</p><p>{html.escape(review['independence_statement'])}</p></section>
  <section><h2>Review identity</h2><dl class="receipt-grid"><div><dt>Technical reviewer ID</dt><dd>{html.escape(review['reviewer_id'])}</dd></div><div><dt>Reviewed author head</dt><dd>{html.escape(review['reviewed_head'])}</dd></div><div><dt>Dossier</dt><dd>{html.escape(data['dossier_id'])}</dd></div><div><dt>Receipt SHA-256</dt><dd>{html.escape(review['receipt_sha256'])}</dd></div><div><dt>Completed</dt><dd>{html.escape(review['completed_at'])}</dd></div></dl></section>
  <section><h2>What was checked</h2><ul>{checked}</ul></section>
  <section><h2>What this did not decide</h2><ul>{limitations}</ul><p>This review checked the bounded packet and derivation. It did not decide whether every empirical proposition is universally or currently true.</p></section>
  <p><a href="{html.escape(base_url)}/how-we-know/{html.escape(data['slug'])}/">Return to Case {html.escape(data['number'])}</a></p>
</article>
""".strip()


def library_index_markdown(document: dict[str, Any], base_url: str) -> str:
    lines = [
        "# How We Know",
        "",
        "Evidence files that keep claims, sources, exact passages, dependence, uncertainty, and policy-relative readings inspectable.",
        "",
    ]
    for item in document["data"]["dossiers"]:
        lines.extend(
            [
                f"## Case {item['number']} — {item['title']}",
                "",
                item["evaluation"],
                "",
                f"[Open case]({base_url}/how-we-know/{item['slug']}/) · "
                f"[Skeptical]({base_url}/how-we-know/{item['slug']}/skeptical/) · "
                f"[Review]({base_url}/how-we-know/{item['slug']}/review/)",
                "",
            ]
        )
    return "\n".join(lines)


def library_index_html(document: dict[str, Any], base_url: str) -> str:
    cards = []
    for item in document["data"]["dossiers"]:
        if item["number"] == "001":
            accounting = "10 apparent support assertions · 4 target-comparable roots · 1 unresolved lineage · 12 counter roots"
        else:
            accounting = " · ".join(
                f"{card['value']} {card['label']}" for card in item["count_cards"]
            )
        cards.append(
            '<article class="docket-card library-case">'
            f'<p class="eyebrow">Case {html.escape(item["number"])}</p>'
            f'<h2><a href="{html.escape(base_url)}/how-we-know/{html.escape(item["slug"])}/">{html.escape(item["title"])}</a></h2>'
            f'<p>{html.escape(item["question"])}</p>'
            f'<p class="qualification">{html.escape(item["evaluation"])}</p>'
            f'<p class="meta-line">{html.escape(accounting)}</p>'
            f'<p><a href="{html.escape(base_url)}/how-we-know/{html.escape(item["slug"])}/">Brief</a> · <a href="{html.escape(base_url)}/how-we-know/{html.escape(item["slug"])}/skeptical/">Skeptical</a> · <a href="{html.escape(base_url)}/how-we-know/{html.escape(item["slug"])}/review/">Review receipt</a></p>'
            "</article>"
        )
    return (
        '<section class="section-head"><p class="eyebrow">How We Know</p><h1>Evidence files, not finished answers</h1>'
        '<p class="dek">Each case keeps the claim, exact passages, dependence structure, unresolved record, and policy-relative reading inspectable.</p></section>'
        f'<section class="docket-grid library-grid">{"".join(cards)}</section>'
        f'<p class="qualification">{len(cards)} accepted cases. No future case is advertised as available.</p>'
    )


def case002_home_cue(summary: dict[str, Any], base_url: str) -> str:
    counts = summary["counts"]
    return f"""
<section class="library-cue" aria-labelledby="case-002-cue-title">
  <p class="eyebrow">Also in How We Know · Case {html.escape(summary['number'])}</p>
  <h2 id="case-002-cue-title">{html.escape(summary['title'])}</h2>
  <p>Eight captured reports cite 30 URL strings across 11 source works. The audit retains seven candidate warrants, 34 unresolved citation occurrences, and zero independently confirmed warrant roots.</p>
  <p class="meta-line">{counts['captured_reports']} reports · {counts['cited_url_strings']} URLs · {counts['source_work_roots']} works · {counts['candidate_warrant_roots']} candidate warrants · {counts['unresolved_citations']} unresolved</p>
  <p><a href="{html.escape(base_url)}/how-we-know/{html.escape(summary['slug'])}/">Open Case 002</a> · <a href="{html.escape(base_url)}/how-we-know/">View the case library</a></p>
</section>
""".strip()


def additional_cases_home_cue(
    summaries: list[dict[str, Any]], base_url: str
) -> str:
    if not summaries:
        return ""
    cards = []
    for summary in summaries:
        accounting = " · ".join(
            f"{card['value']} {card['label']}"
            for card in summary["count_cards"][:4]
        )
        cards.append(
            '<article class="docket-card library-case">'
            f'<p class="eyebrow">Case {html.escape(summary["number"])}</p>'
            f'<h3><a href="{html.escape(base_url)}/how-we-know/{html.escape(summary["slug"])}/">{html.escape(summary["title"])}</a></h3>'
            f'<p>{html.escape(summary["evaluation"])}</p>'
            f'<p class="meta-line">{html.escape(accounting)}</p>'
            "</article>"
        )
    return (
        '<section class="library-cue" aria-labelledby="more-cases-title">'
        '<p class="eyebrow">More evidence files</p>'
        '<h2 id="more-cases-title">The library now tests different claim shapes</h2>'
        '<div class="docket-grid library-grid">'
        + "".join(cards)
        + "</div>"
        f'<p><a href="{html.escape(base_url)}/how-we-know/">View all four cases</a></p>'
        "</section>"
    )
