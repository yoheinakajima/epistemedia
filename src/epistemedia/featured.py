"""Compile one reviewed dossier into disclosure-safe application policy views.

This is an application adapter, not a protocol schema. The catalog manifest selects an exact
reviewed dossier; all displayed claims, counts, spans, and source identities are derived from that
dossier rather than copied into page templates.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .dossier import independence_summary, public_dossier

if TYPE_CHECKING:
    from .core import PublicCatalog


FEATURE_FORMAT = "epistemedia-featured-dossier-v0.1"
PROJECTION_FORMAT = "epistemedia-featured-projection-v0.1"
FEATURE_MANIFEST = Path("catalog/dossiers/corrections-and-familiarity-backfire.json")
FEATURE_VIEWS = ("encyclopedia", "skeptical")
MANIFEST_FIELDS = {
    "claim_family_key",
    "counting",
    "default_view",
    "dossier_id",
    "dossier_path",
    "format",
    "number",
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
VIEW_FIELDS = {"evaluation_key", "featured_relation_keys"}
COUNTING_FIELDS = {"target_comparable_support_proposition_keys"}
SAFE_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
GIT_SHA = re.compile(r"^[a-f0-9]{40}$")


class FeaturedDossierError(ValueError):
    """Raised when accepted feature input cannot be bound to reviewed evidence."""


def _exact_fields(value: dict[str, Any], expected: set[str], context: str) -> None:
    missing = sorted(expected - value.keys())
    extra = sorted(value.keys() - expected)
    if missing:
        raise FeaturedDossierError(f"{context} missing fields: {', '.join(missing)}")
    if extra:
        raise FeaturedDossierError(f"{context} unknown fields: {', '.join(extra)}")


def _object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FeaturedDossierError(f"{context} must be an object")
    return value


def _string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FeaturedDossierError(f"{context} must be a non-empty string")
    return value


def _strings(value: Any, context: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise FeaturedDossierError(f"{context} must contain non-empty strings")
    if len(value) != len(set(value)):
        raise FeaturedDossierError(f"{context} must not contain duplicates")
    return value


def _inside(root: Path, relative: str, context: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise FeaturedDossierError(f"{context} escapes the repository root") from exc
    if not path.is_file():
        raise FeaturedDossierError(f"{context} does not exist: {relative}")
    return path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _index(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {record["key"]: record for record in records}


@dataclass(frozen=True)
class FeaturedDossier:
    """An exact accepted selection joined to its disclosure-safe dossier and review receipt."""

    root: Path
    manifest_path: Path
    manifest: dict[str, Any]
    dossier: dict[str, Any]
    receipt: dict[str, Any]

    @classmethod
    def load(
        cls,
        root: Path,
        manifest_path: Path = FEATURE_MANIFEST,
    ) -> FeaturedDossier:
        root = root.resolve()
        selected_path = _inside(root, manifest_path.as_posix(), "feature manifest")
        try:
            manifest = _object(json.loads(selected_path.read_text()), "feature manifest")
        except json.JSONDecodeError as exc:
            raise FeaturedDossierError("feature manifest is not valid JSON") from exc
        _exact_fields(manifest, MANIFEST_FIELDS, "feature manifest")
        if manifest["format"] != FEATURE_FORMAT:
            raise FeaturedDossierError(f"feature manifest format must be {FEATURE_FORMAT}")
        if manifest["status"] != "accepted":
            raise FeaturedDossierError("featured dossier must have accepted selection status")
        slug = _string(manifest["slug"], "feature manifest.slug")
        if SAFE_SLUG.fullmatch(slug) is None:
            raise FeaturedDossierError("feature manifest.slug is not URL-safe")
        number = _string(manifest["number"], "feature manifest.number")
        if not number.isdigit():
            raise FeaturedDossierError("feature manifest.number must contain digits")
        reviewed_head = _string(manifest["reviewed_head"], "feature manifest.reviewed_head")
        if GIT_SHA.fullmatch(reviewed_head) is None:
            raise FeaturedDossierError("feature manifest.reviewed_head must be a Git SHA")

        counting = _object(manifest["counting"], "feature manifest.counting")
        _exact_fields(counting, COUNTING_FIELDS, "feature manifest.counting")
        target_support = _strings(
            counting["target_comparable_support_proposition_keys"],
            "feature manifest.counting.target_comparable_support_proposition_keys",
        )
        if not target_support:
            raise FeaturedDossierError("target-comparable support set must not be empty")

        views = _object(manifest["views"], "feature manifest.views")
        if set(views) != set(FEATURE_VIEWS):
            raise FeaturedDossierError(
                "feature manifest.views must define encyclopedia and skeptical"
            )
        for view_name in FEATURE_VIEWS:
            view = _object(views[view_name], f"feature manifest.views.{view_name}")
            _exact_fields(view, VIEW_FIELDS, f"feature manifest.views.{view_name}")
            _string(view["evaluation_key"], f"feature manifest.views.{view_name}.evaluation_key")
            if not _strings(
                view["featured_relation_keys"],
                f"feature manifest.views.{view_name}.featured_relation_keys",
            ):
                raise FeaturedDossierError(f"{view_name} featured relation set must not be empty")
        if manifest["default_view"] not in FEATURE_VIEWS:
            raise FeaturedDossierError("feature manifest.default_view is unsupported")
        if views["encyclopedia"] == views["skeptical"]:
            raise FeaturedDossierError("featured policy views must differ materially")

        dossier_path = _inside(
            root,
            _string(manifest["dossier_path"], "feature manifest.dossier_path"),
            "feature manifest.dossier_path",
        )
        receipt_path = _inside(
            root,
            _string(
                manifest["review_receipt_path"],
                "feature manifest.review_receipt_path",
            ),
            "feature manifest.review_receipt_path",
        )
        receipt_digest = _string(
            manifest["review_receipt_sha256"],
            "feature manifest.review_receipt_sha256",
        )
        if SHA256.fullmatch(receipt_digest) is None:
            raise FeaturedDossierError(
                "feature manifest.review_receipt_sha256 must be a SHA-256 digest"
            )
        receipt_bytes = manifest["review_receipt_bytes"]
        if (
            not isinstance(receipt_bytes, int)
            or isinstance(receipt_bytes, bool)
            or receipt_bytes <= 0
        ):
            raise FeaturedDossierError(
                "feature manifest.review_receipt_bytes must be a positive integer"
            )
        if _sha256(receipt_path) != receipt_digest:
            raise FeaturedDossierError(
                "review receipt bytes differ from the accepted feature manifest"
            )
        if receipt_path.stat().st_size != receipt_bytes:
            raise FeaturedDossierError(
                "review receipt length differs from the accepted feature manifest"
            )
        try:
            source_dossier = _object(json.loads(dossier_path.read_text()), "selected dossier")
            receipt = _object(json.loads(receipt_path.read_text()), "review receipt")
        except json.JSONDecodeError as exc:
            raise FeaturedDossierError("selected dossier or receipt is not valid JSON") from exc
        try:
            dossier = public_dossier(source_dossier)
        except ValueError as exc:
            raise FeaturedDossierError("selected dossier fails strict public validation") from exc
        if dossier["dossier_id"] != manifest["dossier_id"]:
            raise FeaturedDossierError("selected public dossier identity differs from manifest")

        if receipt.get("decision") != "pass":
            raise FeaturedDossierError("selected dossier lacks an independent pass receipt")
        receipt_format = _string(
            manifest["review_receipt_format"],
            "feature manifest.review_receipt_format",
        )
        if receipt.get("format") != receipt_format:
            raise FeaturedDossierError("review receipt format differs from feature manifest")
        reviewer = _object(receipt.get("reviewer"), "review receipt.reviewer")
        reviewer_id = _string(manifest["reviewer_id"], "feature manifest.reviewer_id")
        if reviewer.get("id") != reviewer_id:
            raise FeaturedDossierError("review receipt reviewer differs from feature manifest")
        if reviewer.get("fresh_clone") is not True:
            raise FeaturedDossierError("review receipt must attest a fresh independent clone")
        if reviewer.get("independent_retrieval") is not True:
            raise FeaturedDossierError("review receipt must attest independent retrieval")
        if reviewer.get("authoring_agent_artifacts_used") is not False:
            raise FeaturedDossierError(
                "review receipt must reject authoring-agent artifacts"
            )
        repository = _object(receipt.get("repository"), "review receipt.repository")
        if repository.get("reviewed_head") != reviewed_head:
            raise FeaturedDossierError("review receipt head differs from feature manifest")
        if repository.get("dossier_id") != dossier["dossier_id"]:
            raise FeaturedDossierError(
                "review receipt dossier identity differs from selected dossier"
            )
        candidate_files = repository.get("candidate_files")
        if not isinstance(candidate_files, list):
            raise FeaturedDossierError("review receipt candidate file list is missing")
        dossier_rel = dossier_path.relative_to(root).as_posix()
        dossier_receipts = [item for item in candidate_files if item.get("path") == dossier_rel]
        if len(dossier_receipts) != 1:
            raise FeaturedDossierError("review receipt does not bind the selected dossier path")
        dossier_receipt = _object(dossier_receipts[0], "review receipt dossier file")
        if dossier_receipt.get("sha256") != _sha256(dossier_path):
            raise FeaturedDossierError("selected dossier bytes differ from independent review")
        if dossier_receipt.get("bytes") != dossier_path.stat().st_size:
            raise FeaturedDossierError("selected dossier length differs from independent review")

        family_key = _string(manifest["claim_family_key"], "feature manifest.claim_family_key")
        target_key = _string(
            manifest["target_proposition_key"], "feature manifest.target_proposition_key"
        )
        families = _index(dossier["claim_families"])
        propositions = _index(dossier["propositions"])
        evaluations = _index(dossier["evaluations"])
        relations = _index(dossier["evidence_relations"])
        if family_key not in families:
            raise FeaturedDossierError("selected claim family is not present in dossier")
        family = families[family_key]
        if target_key not in propositions or target_key not in family["proposition_keys"]:
            raise FeaturedDossierError("target proposition is not in the selected claim family")
        for proposition_key in target_support:
            if (
                proposition_key not in propositions
                or proposition_key not in family["proposition_keys"]
            ):
                raise FeaturedDossierError(
                    f"target-comparable support proposition is not in family: {proposition_key}"
                )
        evaluation_keys: set[str] = set()
        for view_name in FEATURE_VIEWS:
            view = views[view_name]
            evaluation_key = view["evaluation_key"]
            evaluation = evaluations.get(evaluation_key)
            if not evaluation or evaluation["claim_family_key"] != family_key:
                raise FeaturedDossierError(f"{view_name} evaluation is not in selected family")
            if evaluation["policy_id"] != f"em:application-policy:{view_name}-v0.1":
                raise FeaturedDossierError(f"{view_name} evaluation policy identity is unexpected")
            evaluation_keys.add(evaluation_key)
            for relation_key in view["featured_relation_keys"]:
                if relation_key not in relations or relation_key not in family["relation_keys"]:
                    raise FeaturedDossierError(
                        f"{view_name} relation is not in selected family: {relation_key}"
                    )
        if len(evaluation_keys) != len(FEATURE_VIEWS):
            raise FeaturedDossierError("featured policy views must use different evaluations")

        return cls(root, selected_path, manifest, dossier, receipt)

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

    def derived_counts(self) -> dict[str, Any]:
        indexes = self.indexes()
        assertions = indexes["assertions"]
        lineages = indexes["lineages"]
        target_support = set(
            self.manifest["counting"]["target_comparable_support_proposition_keys"]
        )

        def assertion_keys(relation_type: str) -> list[str]:
            return sorted(
                {
                    relation["from_ref"]
                    for relation in self.dossier["evidence_relations"]
                    if relation["relation_type"] == relation_type
                    and relation["from_ref"] in assertions
                }
            )

        support_keys = assertion_keys("support")
        counter_keys = assertion_keys("rebuttal")
        review_keys = sorted(
            key
            for key in support_keys
            if "data" not in lineages[assertions[key]["lineage_key"]]["dimensions"]
        )
        comparable_keys = sorted(
            key for key in support_keys if assertions[key]["proposition_key"] in target_support
        )
        support = independence_summary(self.dossier, support_keys)
        comparable = independence_summary(self.dossier, comparable_keys)
        counter = independence_summary(self.dossier, counter_keys)
        return {
            "apparent_support_assertion_count": len(support_keys),
            "apparent_support_assertion_keys": support_keys,
            "known_support_data_root_count": support["independent_lineage_count"],
            "known_support_data_root_keys": support["independent_lineage_roots"],
            "unresolved_support_data_root_count": support["unknown_lineage_count"],
            "unresolved_support_data_root_keys": support["unknown_lineages"],
            "target_comparable_support_data_root_count": comparable[
                "independent_lineage_count"
            ],
            "target_comparable_support_data_root_keys": comparable[
                "independent_lineage_roots"
            ],
            "target_comparable_unresolved_data_root_count": comparable[
                "unknown_lineage_count"
            ],
            "target_comparable_unresolved_data_root_keys": comparable["unknown_lineages"],
            "review_report_assertion_count": len(review_keys),
            "review_report_assertion_keys": review_keys,
            "counter_assertion_count": len(counter_keys),
            "counter_assertion_keys": counter_keys,
            "counter_data_root_count": counter["independent_lineage_count"],
            "counter_data_root_keys": counter["independent_lineage_roots"],
            "counting_unit": (
                "One participant-data lineage per publication-defined data series. Experiments "
                "within one publication are collapsed; author, method, material, and research-"
                "program overlap remain disclosed separately."
            ),
            "derivation_rule": (
                "Raw support and counter assertions are unique assertion endpoints of modeled "
                "support and rebuttal relations. Lineage roots are recomputed from declared "
                "participant-data dependencies; unknown roots receive no automatic credit."
            ),
        }

    def span_trace(self, span_key: str) -> dict[str, Any]:
        indexes = self.indexes()
        span = indexes["spans"][span_key]
        edition = indexes["editions"][span["edition_key"]]
        work = indexes["source_works"][edition["work_key"]]
        edition_summary = {
            key: value
            for key, value in edition.items()
            if key not in {"content", "visibility"}
        }
        work_summary = {key: value for key, value in work.items() if key != "visibility"}
        return {
            "span": {key: value for key, value in span.items() if key != "visibility"},
            "edition": edition_summary,
            "source_work": work_summary,
        }

    def relation_trace(self, relation_key: str) -> dict[str, Any]:
        indexes = self.indexes()
        relation = indexes["evidence_relations"][relation_key]
        from_ref = relation["from_ref"]
        assertion = indexes["assertions"].get(from_ref)
        lineage = indexes["lineages"].get(from_ref)
        statement = relation["note"]
        if assertion:
            proposition = indexes["propositions"][assertion["proposition_key"]]
            lineage = indexes["lineages"][assertion["lineage_key"]]
            span_keys = [*assertion["span_keys"], *relation["basis_span_keys"]]
        else:
            proposition = None
            span_keys = [from_ref, *relation["basis_span_keys"]]
        span_keys = list(dict.fromkeys(key for key in span_keys if key in indexes["spans"]))
        target = None
        for collection in ("propositions", "assertions", "lineages", "spans"):
            if relation["to_ref"] in indexes[collection]:
                target = {
                    "collection": collection,
                    "record": indexes[collection][relation["to_ref"]],
                }
                break
        return {
            "relation": relation,
            "relation_label": relation["relation_type"].replace("-", " "),
            "statement": statement,
            "proposition": proposition,
            "assertion": assertion,
            "lineage": lineage,
            "target": target,
            "sources": [self.span_trace(key) for key in span_keys],
        }

    def projection(self, view: str) -> dict[str, Any]:
        if view not in FEATURE_VIEWS:
            raise FeaturedDossierError(f"unknown dossier policy view: {view}")
        indexes = self.indexes()
        family = indexes["claim_families"][self.manifest["claim_family_key"]]
        evaluation = indexes["evaluations"][self.manifest["views"][view]["evaluation_key"]]
        unknown_lineages = [
            lineage for lineage in self.dossier["lineages"] if lineage["status"] == "unknown"
        ]
        dependence_relations = [
            relation
            for relation in self.dossier["evidence_relations"]
            if relation["relation_type"] == "dependence"
        ]
        reviewer = _object(self.receipt.get("reviewer"), "review receipt.reviewer")
        repository = _object(self.receipt.get("repository"), "review receipt.repository")
        candidate_files = repository.get("candidate_files", [])
        sources = self.receipt.get("sources", [])
        spans = self.receipt.get("spans", [])
        limitations = self.receipt.get("limitations", [])
        return {
            "format": PROJECTION_FORMAT,
            "slug": self.slug,
            "number": self.manifest["number"],
            "selection_status": self.manifest["status"],
            "selection_note": self.manifest["selection_note"],
            "selection_manifest": self.manifest_path.relative_to(self.root).as_posix(),
            "selection_manifest_sha256": _sha256(self.manifest_path),
            "dossier_id": self.dossier["dossier_id"],
            "title": self.dossier["title"],
            "question": self.dossier["question"],
            "scope": self.dossier["scope"],
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
            "counts": self.derived_counts(),
            "featured_relations": [
                self.relation_trace(key)
                for key in self.manifest["views"][view]["featured_relation_keys"]
            ],
            "unresolved_lineages": unknown_lineages,
            "dependence_relations": dependence_relations,
            "source_work_count": len(self.dossier["source_works"]),
            "edition_count": len(self.dossier["editions"]),
            "span_count": len(self.dossier["spans"]),
            "source_works": self.dossier["source_works"],
            "review": {
                "decision": self.receipt["decision"],
                "reviewer_id": reviewer.get("id", "unknown"),
                "fresh_clone": reviewer.get("fresh_clone") is True,
                "independent_retrieval": reviewer.get("independent_retrieval") is True,
                "authoring_agent_artifacts_used": (
                    reviewer.get("authoring_agent_artifacts_used") is True
                ),
                "reviewed_head": self.manifest["reviewed_head"],
                "reviewed_base": repository.get("reviewed_base", "unknown"),
                "reviewed_tree": repository.get("reviewed_tree", "unknown"),
                "diff_sha256": repository.get("diff_sha256", "unknown"),
                "receipt_path": self.manifest["review_receipt_path"],
                "receipt_sha256": _sha256(
                    self.root / self.manifest["review_receipt_path"]
                ),
                "completed_at": self.receipt.get("completed_at", "unknown"),
                "candidate_file_count": (
                    len(candidate_files) if isinstance(candidate_files, list) else 0
                ),
                "source_receipt_count": len(sources) if isinstance(sources, list) else 0,
                "span_record_count": len(spans) if isinstance(spans, list) else 0,
                "checked_scope": [
                    "Exact candidate bytes, dossier identity, and Git binding",
                    "Primary artifacts, public data workbooks, and exact source spans",
                    "Lineage topology, count derivation, target baselines, and limitations",
                    "License treatment, deterministic rebuild, and full repository check",
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
        """Return the sanitized public review view bound to the default projection."""

        from .core import envelope

        projection = self.projection(self.default_view)
        return envelope(
            catalog,
            {
                "format": "epistemedia-public-review-receipt-v0.1",
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
            "content_digest": projection["content_digest"],
        }


def load_featured_dossier(root: Path, *, required: bool = False) -> FeaturedDossier | None:
    path = root.resolve() / FEATURE_MANIFEST
    if not path.exists():
        if required:
            raise FeaturedDossierError(f"missing accepted feature manifest: {FEATURE_MANIFEST}")
        return None
    return FeaturedDossier.load(root)


def _extent_text(source: dict[str, Any]) -> str:
    extent = source["span"]["extent"]
    if extent["type"] == "quote":
        return extent["text"]
    return json.dumps(extent["value"], ensure_ascii=False, sort_keys=True)


def projection_markdown(envelope: dict[str, Any]) -> str:
    data = envelope["data"]
    counts = data["counts"]
    lines = [
        f"# {data['title']}",
        "",
        f"**How We Know case {data['number']} · {data['view']['id'].title()} policy**",
        "",
        f"> {data['view']['label']}",
        "",
        f"**Question:** {data['question']}",
        "",
        f"**Scope:** {data['scope']}",
        "",
        "## The lineage count",
        "",
        (
            f"- Apparent support assertions: **{counts['apparent_support_assertion_count']}**"
        ),
        f"- Known supporting participant-data roots: **{counts['known_support_data_root_count']}**",
        (
            "- Target-comparable supporting roots: "
            f"**{counts['target_comparable_support_data_root_count']} known + "
            f"{counts['target_comparable_unresolved_data_root_count']} unresolved**"
        ),
        f"- Counterevidence assertions: **{counts['counter_assertion_count']}**",
        f"- Counterevidence participant-data roots: **{counts['counter_data_root_count']}**",
        "",
        counts["counting_unit"],
        "",
        "## Evidence record",
        "",
    ]
    for index, item in enumerate(data["featured_relations"], start=1):
        lines += [
            f"### {index}. {item['relation_label'].title()}",
            "",
            item["statement"],
            "",
            f"Relation: `{item['relation']['id']}`",
            "",
            "Exact accepted source spans:",
            "",
        ]
        for source in item["sources"]:
            work = source["source_work"]
            span = source["span"]
            edition = source["edition"]
            lines += [
                f"- **{work['title']}** — {span['locator']['label']}",
                f"  - Exact extent: “{_extent_text(source)}”",
                f"  - Edition: `{edition['id']}`",
                f"  - Span: `{span['id']}`",
                f"  - Source: {work['canonical_uri']}",
                f"  - License treatment: {work['license']}",
            ]
        lines.append("")
    lines += [
        "## What remains unresolved",
        "",
    ]
    for lineage in data["unresolved_lineages"]:
        lines.append(f"- {lineage['note']} — `{lineage['id']}`")
    lines += [
        "",
        "## Reproducibility receipt",
        "",
        f"- Dossier: `{data['dossier_id']}`",
        f"- Catalog: `{envelope['catalog_id']}`",
        f"- Frontier: `{envelope['frontier']}`",
        f"- Accepted commit: `{envelope['commit']}`",
        f"- View policy: `{data['view']['policy_id']}`",
        f"- Epistemic policy: `{envelope['policies']['epistemic']}`",
        f"- Disclosure policy: `{envelope['policies']['disclosure']}`",
        f"- Compiler: `{envelope['compiler']}`",
        f"- Content digest: `{envelope['content_digest']}`",
        f"- Independent review receipt: `{data['review']['receipt_path']}`",
    ]
    return "\n".join(lines).rstrip() + "\n"


def _source_xray(item: dict[str, Any], index: int) -> str:
    sources = []
    for source_index, source in enumerate(item["sources"], start=1):
        work = source["source_work"]
        edition = source["edition"]
        span = source["span"]
        sources.append(
            '<article class="xray-source">'
            f'<p class="xray-index">Source {index}.{source_index}</p>'
            f'<h4><a href="{html.escape(work["canonical_uri"])}">'
            f'{html.escape(work["title"])}</a></h4>'
            f'<p class="source-locator">{html.escape(span["locator"]["label"])}</p>'
            f'<blockquote>{html.escape(_extent_text(source))}</blockquote>'
            '<dl class="xray-meta">'
            f'<div><dt>Edition</dt><dd><code>{html.escape(edition["id"])}</code></dd></div>'
            f'<div><dt>Span</dt><dd><code>{html.escape(span["id"])}</code></dd></div>'
            f'<div><dt>Digest</dt><dd><code>{html.escape(span["digest"])}</code></dd></div>'
            f'<div><dt>License</dt><dd>{html.escape(work["license"])}</dd></div>'
            '</dl></article>'
        )
    count = len(sources)
    return (
        '<details class="source-xray">'
        f'<summary>Inspect {count} exact source span{"s" if count != 1 else ""}</summary>'
        f'<div class="xray-grid">{"".join(sources)}</div></details>'
    )


def _policy_switch(data: dict[str, Any], base_url: str) -> str:
    links = []
    for view in FEATURE_VIEWS:
        current = view == data["view"]["id"]
        current_class = " current" if current else ""
        current_attribute = ' aria-current="page"' if current else ""
        links.append(
            f'<a href="{html.escape(base_url)}/how-we-know/{html.escape(data["slug"])}/'
            f'{view}/" class="policy-tab{current_class}"{current_attribute}>'
            f'{view.title()}</a>'
        )
    return '<nav class="policy-switch" aria-label="Evidence policy">' + "".join(links) + "</nav>"


def evidence_tally(data: dict[str, Any], base_url: str) -> str:
    counts = data["counts"]
    unresolved_href = (
        f'{html.escape(base_url)}/how-we-know/{html.escape(data["slug"])}/'
        "#unresolved-lineage"
    )
    return (
        '<div class="evidence-tally" aria-label="Evidence lineage summary">'
        '<div class="tally-cell"><strong>'
        f'{counts["apparent_support_assertion_count"]}</strong>'
        '<span>apparent support assertions</span></div>'
        '<span class="tally-arrow" aria-hidden="true">→</span>'
        f'<a class="tally-cell tally-emphasis" href="{unresolved_href}" '
        'aria-label="Open the four known and one unresolved supporting evidence roots"><strong>'
        f'{counts["target_comparable_support_data_root_count"]} + '
        f'{counts["target_comparable_unresolved_data_root_count"]}?</strong>'
        '<span>target-comparable support roots</span></a>'
        '<div class="tally-cell tally-counter"><strong>'
        f'{counts["counter_data_root_count"]}</strong>'
        '<span>counterevidence data roots</span></div>'
        '</div>'
    )


def feature_home_html(envelope: dict[str, Any], base_url: str) -> str:
    data = envelope["data"]
    review_url = (
        f'{html.escape(base_url)}/how-we-know/{html.escape(data["slug"])}/review/'
    )
    return (
        '<section class="case-hero home-case" aria-labelledby="featured-case-title">'
        '<div class="case-rule"><span>How We Know</span>'
        f'<span>Case {html.escape(data["number"])}</span>'
        f'<a class="case-rule-link" href="{review_url}">Review receipt</a></div>'
        '<div class="case-grid"><div class="case-copy">'
        '<p class="eyebrow">Truth, evidence, knowledge, and information</p>'
        f'<h1 id="featured-case-title">{html.escape(data["title"])}</h1>'
        f'<p class="finding">{html.escape(data["view"]["label"])}</p>'
        f'{_policy_switch(data, base_url)}'
        '<p class="case-actions">'
        f'<a class="primary-action" href="{html.escape(base_url)}/how-we-know/'
        f'{html.escape(data["slug"])}/">Open the evidence docket</a>'
        f'<a href="{html.escape(base_url)}/how-we-know/{html.escape(data["slug"])}/index.md">'
        'Read as Markdown</a></p></div>'
        f'<aside class="case-docket">{evidence_tally(data, base_url)}'
        '<p class="docket-note">Raw mentions are not independent evidence. Open the case to '
        'inspect the exact editions, spans, shared programs, failed replication, and unresolved '
        '2007 participant-data lineage behind the count.</p>'
        f'<p class="docket-meta">{data["source_work_count"]} works · '
        f'{data["span_count"]} exact spans · dossier {html.escape(data["number"])}</p>'
        '</aside></div></section>'
    )


def feature_page_html(envelope: dict[str, Any], base_url: str) -> str:
    data = envelope["data"]
    review_url = (
        f'{html.escape(base_url)}/how-we-know/{html.escape(data["slug"])}/review/'
    )
    evidence = []
    for index, item in enumerate(data["featured_relations"], start=1):
        relation_note = (
            ""
            if item["relation"]["note"] == item["statement"]
            else f'<p class="relation-note">{html.escape(item["relation"]["note"])}</p>'
        )
        evidence.append(
            '<article class="evidence-sentence">'
            '<div class="evidence-marker">'
            f'<span>{index:02d}</span><strong>{html.escape(item["relation_label"])}</strong>'
            '</div><div class="evidence-body">'
            f'<p class="material-sentence">{html.escape(item["statement"])}</p>'
            f'{relation_note}'
            f'{_source_xray(item, index)}</div></article>'
        )
    unresolved = "".join(
        '<li><strong>Unresolved lineage.</strong> '
        f'{html.escape(lineage["note"])} <code>{html.escape(lineage["id"])}</code></li>'
        for lineage in data["unresolved_lineages"]
    )
    reason_codes = "".join(
        f'<li>{html.escape(reason.replace("-", " "))}</li>'
        for reason in data["view"]["reason_codes"]
    )
    sources = "".join(
        '<li><a href="'
        f'{html.escape(work["canonical_uri"])}">{html.escape(work["title"])}</a>'
        f'<span>{html.escape(", ".join(work["creators"]))}</span></li>'
        for work in data["source_works"]
    )
    return (
        '<article class="dossier-page">'
        '<section class="case-hero dossier-hero">'
        '<div class="case-rule"><span>How We Know</span>'
        f'<span>Case {html.escape(data["number"])}</span>'
        f'<span>{html.escape(data["view"]["id"])} policy</span>'
        f'<a class="case-rule-link" href="{review_url}">Review receipt</a></div>'
        '<div class="dossier-lead">'
        f'<p class="eyebrow">{html.escape(data["claim_family"]["title"])}</p>'
        f'<h1>{html.escape(data["title"])}</h1>'
        f'<p class="finding">{html.escape(data["view"]["label"])}</p>'
        f'{_policy_switch(data, base_url)}'
        '<p class="representation-links">This exact view: '
        f'<a href="{html.escape(base_url)}/how-we-know/{html.escape(data["slug"])}/'
        f'{html.escape(data["view"]["id"])}/index.md">Markdown</a> · '
        f'<a href="{html.escape(base_url)}/how-we-know/{html.escape(data["slug"])}/'
        f'{html.escape(data["view"]["id"])}/index.json">JSON</a></p>'
        '</div></section>'
        '<section class="lineage-ledger" aria-labelledby="lineage-title">'
        '<div class="section-head"><div><p class="eyebrow">The stranger test</p>'
        '<h2 id="lineage-title">Many mentions, fewer evidence roots</h2></div></div>'
        f'{evidence_tally(data, base_url)}'
        f'<p>{html.escape(data["counts"]["counting_unit"])}</p>'
        '<p class="scope-note"><strong>Scope:</strong>'
        f'<span>{html.escape(data["scope"])}</span></p></section>'
        '<section aria-labelledby="evidence-record-title">'
        '<div class="section-head"><div><p class="eyebrow">Sentence x-ray</p>'
        '<h2 id="evidence-record-title">Read the evaluated record</h2></div>'
        f'<p class="meta">{len(evidence)} policy-selected relations · '
        f'{data["span_count"]} spans in full dossier</p></div>'
        f'<div class="evidence-record">{"".join(evidence)}</div></section>'
        '<section id="unresolved-lineage" class="uncertainty-panel" '
        'aria-labelledby="uncertainty-title">'
        '<div><p class="eyebrow">Kept visible</p><h2 id="uncertainty-title">What remains '
        'unresolved</h2><ul>'
        f'{unresolved}</ul></div><div><p class="eyebrow">Policy reasons</p><ul>{reason_codes}'
        '</ul></div></section>'
        '<details class="source-register"><summary>Open the complete '
        f'{data["source_work_count"]}-work source register'
        f'</summary><ol>{sources}</ol></details></article>'
    )


def feature_index_html(envelope: dict[str, Any], base_url: str) -> str:
    """Render the realm index without cloning the homepage hero."""

    data = envelope["data"]
    featured = data["featured"]
    case_url = f'{html.escape(base_url)}/how-we-know/{html.escape(featured["slug"])}/'
    counts = featured["counts"]
    return (
        '<section class="hero hero-compact realm-intro">'
        '<p class="eyebrow">Evidence dossiers</p><h1>How We Know</h1>'
        f'<p class="dek">{html.escape(data["scope"])}</p></section>'
        '<section class="case-index" aria-labelledby="published-cases-title">'
        '<div class="section-head"><div><p class="eyebrow">Published record</p>'
        '<h2 id="published-cases-title">One admitted case</h2></div>'
        '<p class="meta">No second case yet</p></div>'
        '<article class="case-index-row"><p class="case-index-number">Case '
        f'{html.escape(featured["number"])}</p><div class="case-index-copy">'
        f'<h3><a href="{case_url}">{html.escape(featured["title"])}</a></h3>'
        f'<p class="case-index-verdict">{html.escape(featured["evaluation"])}</p>'
        '<p class="case-index-counts">'
        f'<strong>{counts["apparent_support_assertion_count"]}</strong> apparent assertions '
        '<span aria-hidden="true">→</span> '
        f'<strong>{counts["target_comparable_support_data_root_count"]} + '
        f'{counts["target_comparable_unresolved_data_root_count"]}?</strong> supporting roots · '
        f'<strong>{counts["counter_data_root_count"]}</strong> counter roots</p></div>'
        f'<a class="primary-action" href="{case_url}">Open case</a></article>'
        '<p class="empty-case-note"><strong>The series starts here.</strong> A second dossier '
        'will appear only after its evidence packet and independent review are accepted.</p>'
        '</section>'
    )


def review_receipt_markdown(envelope: dict[str, Any]) -> str:
    data = envelope["data"]
    review = data["review"]
    lines = [
        f"# Review receipt — How We Know Case {data['number']}",
        "",
        f"**Decision:** `{review['decision']}`",
        "",
        f"- Reviewer: `{review['reviewer_id']}`",
        f"- Reviewed head: `{review['reviewed_head']}`",
        f"- Reviewed tree: `{review['reviewed_tree']}`",
        f"- Dossier: `{data['dossier_id']}`",
        f"- Receipt SHA-256: `{review['receipt_sha256']}`",
        f"- Completed: `{review['completed_at']}`",
        "",
        "## Independence conditions",
        "",
        f"- Fresh independent clone: **{str(review['fresh_clone']).lower()}**",
        f"- Independent retrieval: **{str(review['independent_retrieval']).lower()}**",
        "- Authoring-agent artifacts used: "
        f"**{str(review['authoring_agent_artifacts_used']).lower()}**",
        "",
        "## Checked scope",
        "",
        *[f"- {item}" for item in review["checked_scope"]],
        "",
        f"The receipt binds {review['candidate_file_count']} candidate files, "
        f"{review['source_receipt_count']} source receipts, and "
        f"{review['span_record_count']} span records.",
        "",
        "## Limitations",
        "",
        *[f"- {item}" for item in review["limitations"]],
        "",
        "## Projection identity",
        "",
        f"- Catalog: `{envelope['catalog_id']}`",
        f"- Frontier: `{envelope['frontier']}`",
        f"- Accepted commit: `{envelope['commit']}`",
        f"- Compiler: `{envelope['compiler']}`",
        f"- Content digest: `{envelope['content_digest']}`",
    ]
    return "\n".join(lines).rstrip() + "\n"


def review_receipt_html(envelope: dict[str, Any], base_url: str) -> str:
    data = envelope["data"]
    review = data["review"]
    case_url = f'{html.escape(base_url)}/how-we-know/{html.escape(data["slug"])}/'
    raw_url = (
        "https://github.com/yoheinakajima/epistemedia/blob/"
        f'{html.escape(envelope["commit"])}/{html.escape(review["receipt_path"])}'
    )
    checked = "".join(f"<li>{html.escape(item)}</li>" for item in review["checked_scope"])
    limitations = "".join(
        f"<li>{html.escape(item)}</li>" for item in review["limitations"]
    )
    independence = (
        '<div><dt>Fresh clone</dt><dd>Yes</dd></div>'
        '<div><dt>Independent retrieval</dt><dd>Yes</dd></div>'
        '<div><dt>Authoring artifacts used</dt><dd>No</dd></div>'
    )
    return (
        '<article class="review-page"><section class="hero hero-compact review-hero">'
        '<p class="eyebrow">How We Know · Independent audit</p>'
        f'<h1>Review receipt for Case {html.escape(data["number"])}</h1>'
        '<p class="dek">This is the public, disclosure-safe view of the exact receipt that '
        'admitted the dossier—not a self-awarded badge.</p>'
        f'<p><a href="{case_url}">← Return to the evidence docket</a></p></section>'
        '<section class="review-decision" aria-labelledby="review-decision-title">'
        '<div><p class="eyebrow">Decision</p><h2 id="review-decision-title">Pass</h2>'
        f'<p>Reviewer <code>{html.escape(review["reviewer_id"])}</code> completed the audit '
        f'on <time>{html.escape(review["completed_at"])}</time>.</p></div>'
        '<span class="review-stamp">Exact-head pass</span></section>'
        '<section class="review-grid" aria-label="Review identity">'
        f'<dl>{independence}</dl><dl>'
        '<div><dt>Reviewed head</dt><dd><code>'
        f'{html.escape(review["reviewed_head"])}</code></dd></div>'
        '<div><dt>Reviewed tree</dt><dd><code>'
        f'{html.escape(review["reviewed_tree"])}</code></dd></div>'
        '<div><dt>Receipt digest</dt><dd><code>'
        f'{html.escape(review["receipt_sha256"])}</code></dd></div>'
        '</dl></section>'
        '<section class="review-scope" aria-labelledby="review-scope-title">'
        '<div><p class="eyebrow">What was checked</p><h2 id="review-scope-title">Bounded scope</h2>'
        f'<ul>{checked}</ul><p class="meta">{review["candidate_file_count"]} candidate files · '
        f'{review["source_receipt_count"]} source receipts · '
        f'{review["span_record_count"]} span records</p></div>'
        '<div><p class="eyebrow">What this does not prove</p><h2>Limitations</h2>'
        f'<ul>{limitations}</ul></div></section>'
        f'<p class="raw-receipt-link"><a href="{raw_url}">Inspect the byte-bound JSON receipt '
        'in the accepted repository</a></p></article>'
    )
