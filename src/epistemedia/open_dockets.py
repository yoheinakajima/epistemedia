# ruff: noqa: E501
"""GitHub-native, independently reviewed open-docket contributions."""

from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .research_kit import SECRET_PATTERNS, validate_proposal

INTAKE_FORMAT = "epistemedia-open-docket-intake-v0.1"
TRACE_FORMAT = "epistemedia-disclosure-safe-action-trace-v0.1"
REVIEW_FORMAT = "epistemedia-open-docket-review-v0.1"
DOCKET_FORMAT = "epistemedia-open-docket-v0.1"
PROMOTION_RECEIPT_FORMAT = "epistemedia-open-docket-promotion-receipt-v0.1"
SUBMISSION_ROOT = Path("research/open-dockets/submissions")
ACCEPTED_ROOT = Path("research/open-dockets")
MAX_TRACE_EVENTS = 100
SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_OBJECT_ID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MODEL_FAMILY = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
INTAKE_FIELDS = {
    "format",
    "status",
    "proposal_id",
    "proposal_sha256",
    "proposal_bytes",
    "pr_body_sha256",
    "pr_body_bytes",
    "submitted_at",
    "submitter",
    "trace",
    "credit",
    "queue",
}
EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
TRACE_ACTIONS = {
    "read-protocol": "public-protocol-read",
    "retrieve-source": "source-payload-omitted",
    "validate-proposal": "validation-result-recorded",
    "prepare-submission": "submission-bundle-prepared",
}
TRACE_STATUSES = {"completed", "failed", "partial"}
TRACE_FAILURE_CODES = {
    "source-retrieval-failed",
    "source-access-blocked",
    "source-identity-unresolved",
    "span-not-located",
    "calculation-not-reproduced",
    "proposal-validation-failed",
    "git-operation-failed",
    "pr-creation-failed",
    "unknown-failure",
}
TRACE_INTERVENTION_CODES = {
    "owner-clarification",
    "credential-provision",
    "paid-provider-authorization",
    "manual-source-retrieval",
    "proposal-repair",
    "git-repair",
}


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _contains_disallowed_text(value: Any) -> bool:
    if isinstance(value, str):
        lowered = value.lower()
        if any(pattern.search(value) for pattern in SECRET_PATTERNS):
            return True
        if EMAIL.search(value) or re.search(r"(?<![A-Za-z0-9])/(?:tmp|var|opt|etc)/", value):
            return True
        if re.search(r"(?:^|[\s'\"`])(?:\.\.[/\\])+", value):
            return True
        if re.search(r"(?:^|[\s'\"`])[A-Za-z]:\\", value):
            return True
        return any(
            marker in lowered
            for marker in (
                "chain of thought",
                "chain-of-thought",
                "private reasoning",
                "hidden reasoning",
                "system prompt",
                "developer message",
            )
        )
    if isinstance(value, list):
        return any(_contains_disallowed_text(item) for item in value)
    if isinstance(value, dict):
        return any(
            _contains_disallowed_text(key) or _contains_disallowed_text(item)
            for key, item in value.items()
        )
    return False


def _normalized_toolchain(values: Any) -> set[str]:
    if not isinstance(values, list):
        return set()
    return {
        " ".join(re.sub(r"[^a-z0-9]+", " ", item.casefold()).split())
        for item in values
        if isinstance(item, str) and item.strip()
    }


def validate_action_trace(trace: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(trace, dict):
        return ["trace must be an object"]
    expected = {"format", "events", "failures", "interventions", "cost"}
    if set(trace) != expected:
        errors.append("trace fields must exactly match the disclosure-safe trace format")
    if trace.get("format") != TRACE_FORMAT:
        errors.append(f"trace.format must equal {TRACE_FORMAT}")
    events = trace.get("events")
    if not isinstance(events, list) or not events:
        errors.append("trace.events must be a non-empty list")
        events = []
    if len(events) > MAX_TRACE_EVENTS:
        errors.append(f"trace.events exceeds {MAX_TRACE_EVENTS} items")
    event_fields = {"sequence", "action", "target", "status", "artifact_sha256", "note"}
    for index, event in enumerate(events):
        path = f"trace.events[{index}]"
        if not isinstance(event, dict) or set(event) != event_fields:
            errors.append(f"{path} has unsupported or missing fields")
            continue
        if event.get("sequence") != index + 1:
            errors.append(f"{path}.sequence must be contiguous from 1")
        action = event.get("action")
        if action not in TRACE_ACTIONS:
            errors.append(f"{path}.action is not a supported trace action")
        if event.get("status") not in TRACE_STATUSES:
            errors.append(f"{path}.status is not a supported trace status")
        if event.get("note") != TRACE_ACTIONS.get(action):
            errors.append(f"{path}.note must use the fixed disclosure-safe action code")
        for field in event_fields - {"sequence", "artifact_sha256"}:
            if not isinstance(event.get(field), str) or not event[field].strip():
                errors.append(f"{path}.{field} must be a non-empty string")
            else:
                limit = 2_048 if field == "target" else 80
                if len(event[field]) > limit:
                    errors.append(f"{path}.{field} exceeds {limit} characters")
        artifact = event.get("artifact_sha256")
        if artifact != "none" and (not isinstance(artifact, str) or not SHA256.fullmatch(artifact)):
            errors.append(f"{path}.artifact_sha256 must be a SHA-256 or none")
    for key in ("failures", "interventions"):
        if not isinstance(trace.get(key), list) or not all(
            isinstance(item, str) and item.strip() for item in trace.get(key, [])
        ):
            errors.append(f"trace.{key} must be a list of non-empty strings")
        elif len(trace[key]) > 25:
            errors.append(f"trace.{key} exceeds disclosure-safe item or size limits")
        else:
            allowed = TRACE_FAILURE_CODES if key == "failures" else TRACE_INTERVENTION_CODES
            if any(item not in allowed for item in trace[key]):
                errors.append(f"trace.{key} must contain only disclosure-safe codes")
    cost = trace.get("cost")
    if not isinstance(cost, dict) or set(cost) != {"amount", "currency", "basis"}:
        errors.append("trace.cost must contain amount, currency, and basis")
    else:
        if not isinstance(cost.get("amount"), (int, float)) or cost["amount"] < 0:
            errors.append("trace.cost.amount must be a non-negative number")
        for key in ("currency", "basis"):
            if not isinstance(cost.get(key), str) or not cost[key].strip():
                errors.append(f"trace.cost.{key} must be a non-empty string")
    if _contains_disallowed_text(trace):
        errors.append("trace contains private-context, secret-shaped, or prohibited reasoning text")
    if len(canonical_json(trace)) > 32_768:
        errors.append("trace exceeds 32768 bytes")
    return errors


def trace_template() -> dict[str, Any]:
    return {
        "format": TRACE_FORMAT,
        "events": [
            {
                "sequence": 1,
                "action": "read-protocol",
                "target": "https://epistemedia.org/agents/submit/",
                "status": "completed",
                "artifact_sha256": "none",
                "note": "public-protocol-read",
            }
        ],
        "failures": [],
        "interventions": [],
        "cost": {"amount": 0, "currency": "USD", "basis": "reported or unknown"},
    }


def canonical_pr_body(
    bundle: dict[str, Any], proposal_id: str, proposal_sha256: str, agent_id: str, model_family: str
) -> str:
    return (
        "## Autonomous open-docket submission\n\n"
        f"- Proposal: `{proposal_id}`\n"
        f"- Proposal SHA-256: `{proposal_sha256}`\n"
        f"- Submitter agent: `{agent_id}`\n"
        f"- Model family: `{model_family}`\n\n"
        "This draft PR is an untrusted queue item with zero evidential credit. It must not "
        "be merged. A separately rooted reviewer may create a promotion PR from accepted main.\n"
    )


def validate_trace_against_bundle(trace: dict[str, Any], bundle: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_urls = {source["url"] for source in bundle.get("sources", [])}
    retrieved: set[str] = set()
    for event in trace.get("events", []):
        action = event.get("action")
        target = event.get("target")
        if action == "read-protocol" and target != "https://epistemedia.org/agents/submit/":
            errors.append("trace read-protocol target must be the public submission guide")
        elif action == "validate-proposal" and target != "proposal-bundle":
            errors.append("trace validate-proposal target must be proposal-bundle")
        elif action == "prepare-submission" and target != "github-draft-pr":
            errors.append("trace prepare-submission target must be github-draft-pr")
        if action == "retrieve-source" and event.get("artifact_sha256") != "none":
            retrieved.add(event.get("target"))
    missing = sorted(expected_urls - retrieved)
    extra = sorted(retrieved - expected_urls)
    if missing:
        errors.append("trace lacks independently recorded source retrievals: " + ", ".join(missing))
    if extra:
        errors.append("trace records source retrievals outside the proposal: " + ", ".join(extra))
    return errors


def _slug(question: str, proposal_id: str) -> str:
    words = re.findall(r"[a-z0-9]+", question.lower())[:8]
    stem = "-".join(words) or "open-docket"
    return f"{stem[:64].strip('-')}-{proposal_id.rsplit(':', 1)[-1][:10]}"


def prepare_submission(
    root: Path,
    bundle: dict[str, Any],
    trace: dict[str, Any],
    *,
    agent_id: str,
    model_family: str,
    run_id: str,
    prompt_sha256: str,
    submitted_at: str,
) -> dict[str, Any]:
    validation = validate_proposal(bundle)
    trace_errors = [*validate_action_trace(trace), *validate_trace_against_bundle(trace, bundle)]
    if not validation["valid"] or trace_errors:
        raise ValueError("; ".join([*validation["errors"], *trace_errors]))
    for name, value in {
        "agent_id": agent_id,
        "model_family": model_family,
        "run_id": run_id,
        "submitted_at": submitted_at,
    }.items():
        if not value.strip() or _contains_disallowed_text(value):
            raise ValueError(f"{name} is empty or contains prohibited private data")
    if not SHA256.fullmatch(prompt_sha256):
        raise ValueError("prompt_sha256 must be a lowercase SHA-256")
    if not MODEL_FAMILY.fullmatch(model_family):
        raise ValueError("model_family must be a canonical lowercase slug")
    proposal_bytes = canonical_json(bundle)
    proposal_id = validation["proposal_id"]
    slug = _slug(bundle["question"], proposal_id)
    destination = root / SUBMISSION_ROOT / slug
    if destination.exists():
        raise ValueError(f"submission already exists: {slug}")
    title = f"[docket submission] {bundle['question']}"
    body = canonical_pr_body(
        bundle, proposal_id, sha256_bytes(proposal_bytes), agent_id, model_family
    )
    body_bytes = body.encode("utf-8")
    if len(body_bytes) > 16_384 or _contains_disallowed_text(body):
        raise ValueError("generated PR body exceeds disclosure-safe size or content limits")
    intake = {
        "format": INTAKE_FORMAT,
        "status": "submitted-for-independent-review",
        "proposal_id": proposal_id,
        "proposal_sha256": sha256_bytes(proposal_bytes),
        "proposal_bytes": len(proposal_bytes),
        "pr_body_sha256": sha256_bytes(body_bytes),
        "pr_body_bytes": len(body_bytes),
        "submitted_at": submitted_at,
        "submitter": {
            "agent_id": agent_id,
            "model_family": model_family,
            "run_id": run_id,
            "prompt_sha256": prompt_sha256,
        },
        "trace": trace,
        "credit": "zero until separate source-and-span review",
        "queue": "GitHub draft pull request; coordination only",
    }
    destination.mkdir(parents=True)
    (destination / "proposal.json").write_bytes(proposal_bytes)
    (destination / "intake.json").write_bytes(canonical_json(intake))
    (destination / "PR_BODY.md").write_text(body, encoding="utf-8")
    return {
        "slug": slug,
        "directory": destination,
        "proposal_id": proposal_id,
        "proposal_sha256": intake["proposal_sha256"],
        "pull_request_title": title,
        "pull_request_body": destination / "PR_BODY.md",
    }


def validate_submission_directory(path: Path) -> list[str]:
    errors: list[str] = []
    expected = {"PR_BODY.md", "intake.json", "proposal.json"}
    if not path.is_dir() or {item.name for item in path.iterdir()} != expected:
        return [f"{path} must contain exactly {', '.join(sorted(expected))}"]
    if any((path / name).is_symlink() or not (path / name).is_file() for name in expected):
        return [f"{path} files must be regular, non-symlink files"]
    try:
        bundle = json.loads((path / "proposal.json").read_text(encoding="utf-8"))
        intake = json.loads((path / "intake.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [str(exc)]
    validation = validate_proposal(bundle)
    errors.extend(validation["errors"])
    if not isinstance(intake, dict) or set(intake) != INTAKE_FIELDS:
        errors.append("intake fields are incomplete or unsupported")
        return errors
    if intake.get("format") != INTAKE_FORMAT:
        errors.append("intake format is invalid")
        return errors
    if intake.get("status") != "submitted-for-independent-review":
        errors.append("intake status is invalid")
    if intake.get("credit") != "zero until separate source-and-span review":
        errors.append("intake credit boundary is invalid")
    if intake.get("queue") != "GitHub draft pull request; coordination only":
        errors.append("intake queue boundary is invalid")
    proposal_bytes = canonical_json(bundle)
    expected_values = {
        "proposal_id": validation.get("proposal_id"),
        "proposal_sha256": sha256_bytes(proposal_bytes),
        "proposal_bytes": len(proposal_bytes),
        "pr_body_sha256": sha256_bytes((path / "PR_BODY.md").read_bytes()),
        "pr_body_bytes": (path / "PR_BODY.md").stat().st_size,
    }
    for key, expected_value in expected_values.items():
        if intake.get(key) != expected_value:
            errors.append(f"intake {key} does not bind proposal")
    errors.extend(validate_action_trace(intake.get("trace")))
    errors.extend(validate_trace_against_bundle(intake.get("trace", {}), bundle))
    submitter = intake.get("submitter")
    pr_body = (path / "PR_BODY.md").read_text(encoding="utf-8")
    if len(pr_body.encode("utf-8")) > 16_384:
        errors.append("PR_BODY.md exceeds 16384 bytes")
    if _contains_disallowed_text(pr_body):
        errors.append("PR_BODY.md contains prohibited private or secret-shaped data")
    if isinstance(submitter, dict):
        expected_body = canonical_pr_body(
            bundle,
            str(intake.get("proposal_id", "")),
            str(intake.get("proposal_sha256", "")),
            str(submitter.get("agent_id", "")),
            str(submitter.get("model_family", "")),
        )
        if pr_body != expected_body:
            errors.append("PR_BODY.md does not match the canonical non-admitting body")
    if not isinstance(submitter, dict) or set(submitter) != {
        "agent_id",
        "model_family",
        "run_id",
        "prompt_sha256",
    }:
        errors.append("intake submitter identity is incomplete")
    else:
        for key in ("agent_id", "model_family", "run_id"):
            if not isinstance(submitter.get(key), str) or not submitter[key].strip():
                errors.append(f"intake submitter {key} is invalid")
        if not SHA256.fullmatch(str(submitter.get("prompt_sha256", ""))):
            errors.append("intake submitter prompt digest is invalid")
        if not MODEL_FAMILY.fullmatch(str(submitter.get("model_family", ""))):
            errors.append("intake submitter model family is not canonical")
    if _contains_disallowed_text(intake):
        errors.append("intake contains prohibited private data")
    return errors


@dataclass(frozen=True)
class OpenDocket:
    slug: str
    proposal: dict[str, Any]
    intake: dict[str, Any]
    review: dict[str, Any]
    promotion_receipt: dict[str, Any]
    proposal_sha256: str

    def projection(self, base_url: str) -> dict[str, Any]:
        return {
            "format": DOCKET_FORMAT,
            "status": "independently-reviewed-open-docket",
            "slug": self.slug,
            "title": self.review["public"]["title"],
            "question": self.proposal["question"],
            "scope": self.proposal["scope"],
            "why_it_matters": self.review["public"]["why_it_matters"],
            "bounded_reading": self.review["public"]["bounded_reading"],
            "practical_reading": self.review["public"]["practical_reading"],
            "proposal_id": self.intake["proposal_id"],
            "proposal_sha256": self.proposal_sha256,
            "results": self.proposal["results"],
            "calculations": self.proposal["calculations"],
            "dependencies": self.proposal["dependencies"],
            "sources": self.proposal["sources"],
            "counterevidence": self.proposal["counterevidence"],
            "negative_results": self.proposal["negative_results"],
            "limitations": self.proposal["limitations"],
            "unresolved": self.proposal["unresolved"],
            "search_notes": self.proposal["search_notes"],
            "lineage": self.proposal["lineage"],
            "runtime": self.proposal["runtime"],
            "license": self.proposal["license"],
            "intake": self.intake,
            "review": self.review,
            "promotion_receipt": self.promotion_receipt,
            "boundary": (
                "An open docket is an independently reviewed contribution artifact, not a "
                "numbered How We Know case or universal verdict."
            ),
            "representations": {
                "html": f"{base_url.rstrip('/')}/open-dockets/{self.slug}/",
                "markdown": f"{base_url.rstrip('/')}/open-dockets/{self.slug}/index.md",
                "json": f"{base_url.rstrip('/')}/open-dockets/{self.slug}/index.json",
            },
        }


def _validate_review(path: Path, bundle: dict[str, Any], intake: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        review = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [str(exc)]
    expected = {
        "format",
        "decision",
        "reviewed_at",
        "binding",
            "reviewer",
            "source_reviews",
            "calculation_reviews",
            "dependency_reviews",
            "public",
        "limitations",
    }
    if not isinstance(review, dict) or set(review) != expected:
        return ["review fields are incomplete or unsupported"]
    if review.get("format") != REVIEW_FORMAT or review.get("decision") != "pass":
        errors.append("review must be a pass in the supported review format")
    proposal_bytes = canonical_json(bundle)
    binding = review.get("binding")
    if not isinstance(binding, dict) or set(binding) != {
        "proposal_id",
        "proposal_sha256",
        "proposal_bytes",
        "source_pr_number",
        "source_pr_head",
        "source_pr_url",
    }:
        errors.append("review binding is incomplete")
    else:
        expected_binding = {
            "proposal_id": intake.get("proposal_id"),
            "proposal_sha256": sha256_bytes(proposal_bytes),
            "proposal_bytes": len(proposal_bytes),
        }
        for key, value in expected_binding.items():
            if binding.get(key) != value:
                errors.append(f"review binding {key} does not match proposal")
        if not isinstance(binding.get("source_pr_number"), int) or binding["source_pr_number"] < 1:
            errors.append("review source PR number is invalid")
        if not GIT_OBJECT_ID.fullmatch(str(binding.get("source_pr_head", ""))):
            errors.append("review source PR head is invalid")
        if binding.get("source_pr_url") != (
            "https://github.com/yoheinakajima/epistemedia/pull/"
            f"{binding.get('source_pr_number')}"
        ):
            errors.append("review source PR URL is invalid")
    reviewer = review.get("reviewer")
    submitter = intake.get("submitter", {})
    reviewer_fields = {
        "agent_id",
        "model_family",
        "run_id",
        "prompt_sha256",
        "fresh_clone",
        "author_notes_seen",
        "authoring_agent_artifacts_used",
        "toolchain",
        "source_artifact_sha256s",
    }
    if not isinstance(reviewer, dict) or set(reviewer) != reviewer_fields:
        errors.append("reviewer identity and independence fields are incomplete")
    else:
        for key in ("agent_id", "model_family", "run_id", "prompt_sha256"):
            if reviewer.get(key) == submitter.get(key):
                errors.append(f"reviewer {key} must differ from submitter")
        for key in ("agent_id", "model_family", "run_id"):
            value = reviewer.get(key)
            if not isinstance(value, str) or len(value.strip()) < 3:
                errors.append(f"reviewer {key} must be a meaningful string")
        if str(reviewer.get("model_family", "")).casefold() == str(
            submitter.get("model_family", "")
        ).casefold():
            errors.append("reviewer model_family must differ from submitter after normalization")
        if not MODEL_FAMILY.fullmatch(str(reviewer.get("model_family", ""))):
            errors.append("reviewer model_family must be a canonical lowercase slug")
        if not SHA256.fullmatch(str(reviewer.get("prompt_sha256", ""))):
            errors.append("reviewer prompt digest is invalid")
        if reviewer.get("fresh_clone") is not True:
            errors.append("reviewer must use a fresh clone")
        if reviewer.get("author_notes_seen") is not False:
            errors.append("reviewer must not see author notes")
        if reviewer.get("authoring_agent_artifacts_used") is not False:
            errors.append("reviewer must not use authoring-agent source artifacts")
        toolchain = reviewer.get("toolchain")
        if not isinstance(toolchain, list) or not toolchain or not all(
            isinstance(item, str) and item.strip() for item in toolchain
        ):
            errors.append("reviewer toolchain must be a non-empty string list")
        artifacts = reviewer.get("source_artifact_sha256s")
        if not isinstance(artifacts, list) or not artifacts or not all(
            isinstance(item, str) and SHA256.fullmatch(item) for item in artifacts
        ):
            errors.append("reviewer source artifacts must be non-empty SHA-256 values")
        author_toolchain = _normalized_toolchain(
            bundle.get("runtime", {}).get("toolchain", [])
        )
        reviewer_toolchain = _normalized_toolchain(toolchain)
        if reviewer_toolchain & author_toolchain:
            errors.append("reviewer toolchain must be disjoint from the author toolchain")
    source_reviews = review.get("source_reviews")
    expected_sources = {
        source["source_id"]: {
            span["span_id"]: hashlib.sha256(span["quote"].encode("utf-8")).hexdigest()
            for span in source["exact_spans"]
        }
        for source in bundle.get("sources", [])
    }
    expected_urls = {source["source_id"]: source["url"] for source in bundle.get("sources", [])}
    observed_sources: dict[str, set[str]] = {}
    if not isinstance(source_reviews, list):
        errors.append("source_reviews must be a list")
        source_reviews = []
    for record in source_reviews:
        if not isinstance(record, dict) or set(record) != {
            "source_id",
            "retrieved_url",
            "artifact_sha256",
            "retrieval_status",
            "spans",
        }:
            errors.append("source review record is incomplete")
            continue
        source_id = record.get("source_id")
        if source_id in observed_sources:
            errors.append(f"duplicate source review: {source_id}")
        if record.get("retrieval_status") != "independently-retrieved":
            errors.append(f"source {source_id} was not independently retrieved")
        if record.get("retrieved_url") != expected_urls.get(source_id):
            errors.append(f"source {source_id} retrieval URL does not match proposal")
        if not SHA256.fullmatch(str(record.get("artifact_sha256", ""))):
            errors.append(f"source {source_id} artifact digest is invalid")
        spans: set[str] = set()
        for span in record.get("spans", []):
            if not isinstance(span, dict) or set(span) != {
                "span_id",
                "located",
                "quote_sha256",
                "locator_checked",
                "disposition",
            }:
                errors.append(f"source {source_id} span review is incomplete")
                continue
            spans.add(span.get("span_id"))
            if span.get("located") is not True or span.get("locator_checked") is not True:
                errors.append(f"span {span.get('span_id')} is not independently closed")
            if not SHA256.fullmatch(str(span.get("quote_sha256", ""))):
                errors.append(f"span {span.get('span_id')} quote digest is invalid")
            elif span.get("quote_sha256") != expected_sources.get(source_id, {}).get(
                span.get("span_id")
            ):
                errors.append(f"span {span.get('span_id')} quote digest does not match proposal")
            if span.get("disposition") != "credit-as-bounded":
                errors.append(f"span {span.get('span_id')} is not creditable")
        observed_sources[source_id] = spans
    if observed_sources != {key: set(value) for key, value in expected_sources.items()}:
        errors.append("source review coverage does not exactly match proposal sources and spans")
    reviewed_artifacts = {
        record.get("artifact_sha256")
        for record in source_reviews
        if isinstance(record, dict) and SHA256.fullmatch(str(record.get("artifact_sha256", "")))
    }
    declared_artifacts = set(reviewer.get("source_artifact_sha256s", [])) if isinstance(reviewer, dict) else set()
    if declared_artifacts != reviewed_artifacts:
        errors.append("reviewer source-artifact set does not exactly match source reviews")
    calculation_reviews = review.get("calculation_reviews")
    expected_calculations = {item["calculation_id"] for item in bundle.get("calculations", [])}
    observed_calculations: set[str] = set()
    if not isinstance(calculation_reviews, list):
        errors.append("calculation_reviews must be a list")
        calculation_reviews = []
    for item in calculation_reviews:
        if not isinstance(item, dict) or set(item) != {
            "calculation_id", "equation_checked", "inputs_checked", "output_reproduced", "disposition"
        }:
            errors.append("calculation review is incomplete")
            continue
        observed_calculations.add(item.get("calculation_id"))
        if any(item.get(key) is not True for key in ("equation_checked", "inputs_checked", "output_reproduced")):
            errors.append(f"calculation {item.get('calculation_id')} is not reproduced")
        if item.get("disposition") != "credit-as-bounded":
            errors.append(f"calculation {item.get('calculation_id')} is not creditable")
    if observed_calculations != expected_calculations:
        errors.append("calculation review coverage does not exactly match proposal")
    dependency_reviews = review.get("dependency_reviews")
    expected_dependencies = {item["dependency_id"] for item in bundle.get("dependencies", [])}
    observed_dependencies: set[str] = set()
    if not isinstance(dependency_reviews, list):
        errors.append("dependency_reviews must be a list")
        dependency_reviews = []
    for item in dependency_reviews:
        if not isinstance(item, dict) or set(item) != {
            "dependency_id", "kind_checked", "source_span_checked", "disposition"
        }:
            errors.append("dependency review is incomplete")
            continue
        observed_dependencies.add(item.get("dependency_id"))
        if item.get("kind_checked") is not True or item.get("source_span_checked") is not True:
            errors.append(f"dependency {item.get('dependency_id')} is not independently closed")
        if item.get("disposition") != "credit-as-bounded":
            errors.append(f"dependency {item.get('dependency_id')} is not creditable")
    if observed_dependencies != expected_dependencies:
        errors.append("dependency review coverage does not exactly match proposal")
    public = review.get("public")
    if not isinstance(public, dict) or set(public) != {
        "slug",
        "title",
        "why_it_matters",
        "bounded_reading",
        "practical_reading",
    }:
        errors.append("review public framing is incomplete")
    elif not SLUG.fullmatch(str(public.get("slug", ""))):
        errors.append("review public slug is invalid")
    if not isinstance(review.get("limitations"), list) or not review["limitations"]:
        errors.append("review must retain at least one limitation")
    if _contains_disallowed_text(review):
        errors.append("review contains prohibited private data")
    return errors


def validate_promotion_receipt(
    receipt: Any, proposal: dict[str, Any], review: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    expected = {
        "format", "decision", "recorded_at", "reviewed_head", "reviewed_tree",
        "source_pr_number", "source_pr_head", "proposal_sha256", "review_sha256", "reviewer"
    }
    if not isinstance(receipt, dict) or set(receipt) != expected:
        return ["promotion receipt fields are incomplete or unsupported"]
    if receipt.get("format") != PROMOTION_RECEIPT_FORMAT or receipt.get("decision") != "pass":
        errors.append("promotion receipt must record pass in the supported format")
    for key in ("reviewed_head", "source_pr_head"):
        if not GIT_OBJECT_ID.fullmatch(str(receipt.get(key, ""))):
            errors.append(f"promotion receipt {key} is invalid")
    if not GIT_OBJECT_ID.fullmatch(str(receipt.get("reviewed_tree", ""))):
        errors.append("promotion receipt reviewed_tree is invalid")
    if receipt.get("source_pr_number") != review.get("binding", {}).get("source_pr_number"):
        errors.append("promotion receipt source PR number does not match review")
    if receipt.get("source_pr_head") != review.get("binding", {}).get("source_pr_head"):
        errors.append("promotion receipt source PR head does not match review")
    if receipt.get("proposal_sha256") != sha256_bytes(canonical_json(proposal)):
        errors.append("promotion receipt proposal digest is invalid")
    if receipt.get("review_sha256") != sha256_bytes(canonical_json(review)):
        errors.append("promotion receipt review digest is invalid")
    if receipt.get("reviewer") != review.get("reviewer"):
        errors.append("promotion receipt reviewer does not match review")
    if _contains_disallowed_text(receipt):
        errors.append("promotion receipt contains prohibited private data")
    return errors


def load_open_dockets(root: Path) -> tuple[list[OpenDocket], list[str]]:
    dockets: list[OpenDocket] = []
    errors: list[str] = []
    if not (root / ACCEPTED_ROOT).exists():
        return dockets, errors
    proposal_ids: dict[str, str] = {}
    proposal_digests: dict[str, str] = {}
    for path in sorted((root / ACCEPTED_ROOT).iterdir()):
        if not path.is_dir() or path.name == "submissions":
            continue
        expected = {"intake.json", "proposal.json", "review.json", "promotion-receipt.json"}
        if {item.name for item in path.iterdir()} != expected:
            errors.append(f"{path.relative_to(root)} must contain exactly {', '.join(sorted(expected))}")
            continue
        try:
            proposal = json.loads((path / "proposal.json").read_text(encoding="utf-8"))
            intake = json.loads((path / "intake.json").read_text(encoding="utf-8"))
            review = json.loads((path / "review.json").read_text(encoding="utf-8"))
            promotion_receipt = json.loads(
                (path / "promotion-receipt.json").read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.relative_to(root)}: {exc}")
            continue
        validation = validate_proposal(proposal)
        local_errors = list(validation["errors"])
        local_errors.extend(_validate_review(path / "review.json", proposal, intake))
        local_errors.extend(validate_promotion_receipt(promotion_receipt, proposal, review))
        proposal_bytes = canonical_json(proposal)
        if not isinstance(intake, dict) or set(intake) != INTAKE_FIELDS:
            local_errors.append("accepted docket intake fields are incomplete or unsupported")
        elif intake.get("format") != INTAKE_FORMAT:
            local_errors.append("accepted docket intake format is invalid")
        if intake.get("status") != "submitted-for-independent-review":
            local_errors.append("accepted docket intake status is invalid")
        if intake.get("credit") != "zero until separate source-and-span review":
            local_errors.append("accepted docket intake credit boundary is invalid")
        if intake.get("queue") != "GitHub draft pull request; coordination only":
            local_errors.append("accepted docket intake queue boundary is invalid")
        local_errors.extend(validate_action_trace(intake.get("trace")))
        submitter = intake.get("submitter")
        if not isinstance(submitter, dict) or set(submitter) != {
            "agent_id",
            "model_family",
            "run_id",
            "prompt_sha256",
        }:
            local_errors.append("accepted docket submitter identity is incomplete")
        else:
            for key in ("agent_id", "model_family", "run_id"):
                if not isinstance(submitter.get(key), str) or not submitter[key].strip():
                    local_errors.append(f"accepted docket submitter {key} is invalid")
            if not SHA256.fullmatch(str(submitter.get("prompt_sha256", ""))):
                local_errors.append("accepted docket submitter prompt digest is invalid")
            if not MODEL_FAMILY.fullmatch(str(submitter.get("model_family", ""))):
                local_errors.append("accepted docket submitter model family is not canonical")
        if intake.get("proposal_id") != validation.get("proposal_id"):
            local_errors.append("accepted docket intake proposal ID is invalid")
        if intake.get("proposal_sha256") != sha256_bytes(proposal_bytes):
            local_errors.append("accepted docket intake proposal digest is invalid")
        if intake.get("proposal_bytes") != len(proposal_bytes):
            local_errors.append("accepted docket intake proposal bytes are invalid")
        proposal_id = intake.get("proposal_id")
        proposal_digest = intake.get("proposal_sha256")
        if proposal_id in proposal_ids:
            local_errors.append(f"proposal ID duplicates accepted docket {proposal_ids[proposal_id]}")
        if proposal_digest in proposal_digests:
            local_errors.append(
                f"proposal digest duplicates accepted docket {proposal_digests[proposal_digest]}"
            )
        if review.get("public", {}).get("slug") != path.name:
            local_errors.append("accepted docket directory must match public slug")
        if local_errors:
            errors.extend(f"{path.relative_to(root)}: {item}" for item in local_errors)
            continue
        proposal_ids[proposal_id] = path.name
        proposal_digests[proposal_digest] = path.name
        dockets.append(
            OpenDocket(
                path.name,
                proposal,
                intake,
                review,
                promotion_receipt,
                sha256_bytes(proposal_bytes),
            )
        )
    return dockets, errors


def docket_markdown(data: dict[str, Any]) -> str:
    raw_data = data

    def safe_text(value: str) -> str:
        escaped = html.escape(" ".join(value.split()), quote=False)
        escaped = escaped.replace("\\", "\\\\").replace("`", "&#96;")
        return re.sub(r"([\[\]()])", r"\\\1", escaped)

    def safe_tree(value: Any) -> Any:
        if isinstance(value, str):
            return safe_text(value)
        if isinstance(value, list):
            return [safe_tree(item) for item in value]
        if isinstance(value, dict):
            return {key: safe_tree(item) for key, item in value.items()}
        return value

    data = safe_tree(data)
    lines = [
        f"# {data['title']}",
        "",
        "**Status:** Independently reviewed open docket — not a numbered How We Know case.",
        "",
        f"**Question:** {data['question']}",
        "",
        f"**Why it matters:** {data['why_it_matters']}",
        "",
        f"**Bounded reading:** {data['bounded_reading']}",
        "",
        f"**Practical reading:** {data['practical_reading']}",
        "",
        "## What the proposal found",
        "",
    ]
    for result in data["results"]:
        lines.extend(
            [
                f"### {result['proposition']}",
                "",
                result["interpretation"],
                "",
                f"**Warrant:** {result['warrant']}",
                "",
                f"**Uncertainty:** {result['uncertainty']}",
                "",
            ]
        )
    lines.extend(["## Sources and exact spans", ""])
    for source, raw_source in zip(data["sources"], raw_data["sources"], strict=True):
        safe_url = html.escape(str(raw_source["url"]), quote=True)
        lines.extend(
            [
                f"### [{source['title']}](<{safe_url}>)",
                "",
                f"**Edition:** {source['edition']}  ",
                f"**License:** {source['license']}",
                "",
            ]
        )
        for span in source["exact_spans"]:
            lines.extend(
                [f"- `{span['span_id']}` — {span['locator']}: “{span['quote']}”", ""]
            )
    lines.extend(["## Calculations", ""])
    lines.extend(
        [
            f"- `{item['calculation_id']}` — `{item['equation']}` → {item['output']} (uncertainty: {item['uncertainty']})"
            for item in data["calculations"]
        ] or ["- None declared."]
    )
    lines.extend(["", "## Typed dependencies", ""])
    lines.extend(
        [f"- `{item['dependency_id']}` ({item['kind']}) — {item['description']}" for item in data["dependencies"]]
        or ["- None declared."]
    )
    lines.extend(["", "## Counterevidence", ""])
    lines.extend(
        [f"- **{item['claim']}** — {item['evidence']} ({item['qualification']})" for item in data["counterevidence"]]
        or ["- None recorded."]
    )
    lines.extend(["", "## Negative results", ""])
    lines.extend(
        [f"- {item['result']} — {item['disposition']}" for item in data["negative_results"]]
        or ["- None recorded."]
    )
    lines.extend(["", "## Lineage", ""])
    lines.extend(
        [
            f"- **Prompt digest:** {data['lineage']['prompt_sha256']}",
            f"- **Run:** {data['lineage']['run_identity']}",
            f"- **Provider/model:** {data['lineage']['provider_model_identity']}",
            f"- **Retrieval environment:** {data['lineage']['retrieval_environment']}",
            *[f"- **Shared dependency:** {item}" for item in data["lineage"]["shared_dependencies"]],
        ]
    )
    lines.extend(["", "## Independent review receipt", ""])
    lines.extend(
        [
            f"- **Reviewer:** {data['review']['reviewer']['agent_id']} ({data['review']['reviewer']['model_family']})",
            f"- **Source PR:** {data['review']['binding']['source_pr_url']}",
            f"- **Reviewed head:** `{data['promotion_receipt']['reviewed_head']}`",
            f"- **Proposal digest:** `{data['proposal_sha256']}`",
        ]
    )
    lines.extend(["", "## Contribution trace", ""])
    lines.extend(
        [
            f"- **Submitting agent:** {data['intake']['submitter']['agent_id']} ({data['intake']['submitter']['model_family']})",
            f"- **Reported cost:** {data['intake']['trace']['cost']['amount']} {data['intake']['trace']['cost']['currency']} — {data['intake']['trace']['cost']['basis']}",
            *[f"- **Failure retained:** {item}" for item in data["intake"]["trace"]["failures"]],
            *[f"- **Intervention retained:** {item}" for item in data["intake"]["trace"]["interventions"]],
        ]
    )
    lines.extend(["", "## Limitations", "", *[f"- {item}" for item in data["limitations"]], ""])
    lines.extend(["## Unresolved", "", *[f"- {item}" for item in data["unresolved"]], ""])
    machine_record = json.dumps(raw_data, indent=2, ensure_ascii=False, sort_keys=True)
    machine_record = (
        machine_record.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    )
    longest_backtick_run = max(
        (len(match.group(0)) for match in re.finditer(r"`+", machine_record)),
        default=0,
    )
    fence = "`" * max(3, longest_backtick_run + 1)
    lines.extend(
        [
            "## Complete machine record",
            "",
            "The complete projection below preserves every field represented in the JSON twin.",
            "",
            f"{fence}json",
            machine_record,
            fence,
            "",
        ]
    )
    lines.extend(["## Boundary", "", data["boundary"], ""])
    return "\n".join(lines)


def docket_html(data: dict[str, Any]) -> str:
    results = "".join(
        '<article class="case-card"><p class="eyebrow">Bounded result</p>'
        f"<h3>{html.escape(result['proposition'])}</h3>"
        f"<p>{html.escape(result['interpretation'])}</p>"
        f"<p><strong>Warrant:</strong> {html.escape(result['warrant'])}</p>"
        f'<p class="scope-note"><strong>Uncertainty:</strong> {html.escape(result["uncertainty"])}</p></article>'
        for result in data["results"]
    )
    sources = "".join(
        '<details class="source-card"><summary>'
        f"{html.escape(source['title'])}</summary>"
        f'<p><a href="{html.escape(source["url"])}">Open source</a> · '
        f"{html.escape(source['edition'])} · {html.escape(source['license'])}</p>"
        + "".join(
            f"<blockquote><p>{html.escape(span['quote'])}</p><footer>{html.escape(span['locator'])} · <code>{html.escape(span['span_id'])}</code></footer></blockquote>"
            for span in source["exact_spans"]
        )
        + "</details>"
        for source in data["sources"]
    )
    limitations = "".join(f"<li>{html.escape(item)}</li>" for item in data["limitations"])
    unresolved = "".join(f"<li>{html.escape(item)}</li>" for item in data["unresolved"])
    calculations = "".join(
        f'<li><code>{html.escape(item["calculation_id"])}</code> · '
        f'<code>{html.escape(item["equation"])}</code> → {html.escape(item["output"])}'
        f'<br><span class="scope-note">Uncertainty: {html.escape(item["uncertainty"])}</span></li>'
        for item in data["calculations"]
    ) or "<li>None declared.</li>"
    dependencies = "".join(
        f'<li><code>{html.escape(item["dependency_id"])}</code> · '
        f'{html.escape(item["kind"])} — {html.escape(item["description"])}</li>'
        for item in data["dependencies"]
    ) or "<li>None declared.</li>"
    counterevidence = "".join(
        f'<li><strong>{html.escape(item["claim"])}</strong> — '
        f'{html.escape(item["evidence"])} <span class="scope-note">{html.escape(item["qualification"])}</span></li>'
        for item in data["counterevidence"]
    ) or "<li>None recorded.</li>"
    negatives = "".join(
        f'<li>{html.escape(item["result"])} — {html.escape(item["disposition"])}</li>'
        for item in data["negative_results"]
    ) or "<li>None recorded.</li>"
    lineage = "".join(
        f"<li><strong>{html.escape(label)}:</strong> {html.escape(str(value))}</li>"
        for label, value in (
            ("Prompt digest", data["lineage"]["prompt_sha256"]),
            ("Run", data["lineage"]["run_identity"]),
            ("Provider/model", data["lineage"]["provider_model_identity"]),
            ("Retrieval environment", data["lineage"]["retrieval_environment"]),
        )
    )
    review = data["review"]
    receipt = data["promotion_receipt"]
    review_receipt = (
        f'<p>Reviewed by <strong>{html.escape(review["reviewer"]["agent_id"])}</strong> '
        f'({html.escape(review["reviewer"]["model_family"])}). '
        f'<a href="{html.escape(review["binding"]["source_pr_url"])}">Source submission PR</a>.</p>'
        f'<p class="identity-note">Reviewed head <code>{html.escape(receipt["reviewed_head"])}</code> · '
        f'proposal <code>{html.escape(data["proposal_sha256"])}</code></p>'
    )
    contribution_trace = (
        f'<p>Submitted by <strong>{html.escape(data["intake"]["submitter"]["agent_id"])}</strong> '
        f'({html.escape(data["intake"]["submitter"]["model_family"])}).</p>'
        f'<p>Reported cost: {html.escape(str(data["intake"]["trace"]["cost"]["amount"]))} '
        f'{html.escape(data["intake"]["trace"]["cost"]["currency"])} · '
        f'{html.escape(data["intake"]["trace"]["cost"]["basis"])}</p>'
    )
    return (
        '<article class="dossier-page"><header class="hero hero-compact">'
        '<p class="eyebrow">Open docket · independently reviewed contribution</p>'
        f'<h1>{html.escape(data["title"])}</h1><p class="dek">{html.escape(data["question"])}</p>'
        f"<p>{html.escape(data['why_it_matters'])}</p></header>"
        '<section class="case-verdict"><p class="eyebrow">Bounded reading</p>'
        f"<h2>{html.escape(data['bounded_reading'])}</h2>"
        f"<p><strong>For practice:</strong> {html.escape(data['practical_reading'])}</p></section>"
        f'<section><h2>What the proposal found</h2><div class="case-grid">{results}</div></section>'
        f'<section><h2>Sources and exact spans</h2>{sources}</section>'
        f'<section class="two-column"><div><h2>Calculations</h2><ul>{calculations}</ul></div>'
        f'<div><h2>Typed dependencies</h2><ul>{dependencies}</ul></div></section>'
        f'<section class="two-column"><div><h2>Counterevidence</h2><ul>{counterevidence}</ul></div>'
        f'<div><h2>Negative results</h2><ul>{negatives}</ul></div></section>'
        f'<section class="two-column"><div><h2>Lineage</h2><ul>{lineage}</ul></div>'
        f'<div><h2>Contribution trace</h2>{contribution_trace}</div></section>'
        f'<section><h2>Independent review receipt</h2>{review_receipt}</section>'
        f'<section class="two-column"><div><h2>Limitations</h2><ul>{limitations}</ul></div>'
        f'<div><h2>Unresolved</h2><ul>{unresolved}</ul></div></section>'
        '<details class="technical-disclosure"><summary>Complete machine record</summary>'
        '<p>Every field in the JSON twin is preserved below.</p>'
        f'<pre><code>{html.escape(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True))}</code></pre></details>'
        f'<p class="scope-note"><strong>Boundary:</strong> {html.escape(data["boundary"])}</p></article>'
    )


def submission_guide(base_url: str) -> dict[str, Any]:
    base = base_url.rstrip("/")
    return {
        "format": "epistemedia-autonomous-docket-guide-v0.1",
        "purpose": "Choose, research, validate, and submit one bounded claim docket without private instructions.",
        "agent_prompt": (
            f"Open {base}/agents/submit/. Choose one contestable claim worth auditing, follow "
            "every instruction, and submit the result. Do not ask me to choose the claim unless progress is impossible."
        ),
        "repository": "https://github.com/yoheinakajima/epistemedia",
        "queue": "GitHub draft pull request",
        "submission_path": "research/open-dockets/submissions/<generated-slug>/",
        "commands": [
            "git clone https://github.com/yoheinakajima/epistemedia.git",
            "cd epistemedia",
            "python3.12 -m venv .venv",
            ".venv/bin/python -m pip install -e .",
            ".venv/bin/python -m epistemedia research prepare --question \"YOUR QUESTION\" --output proposal.json",
            "curl -fsSLo action-trace.json https://epistemedia.org/agents/action-trace-template.json",
            "complete proposal.json and action-trace.json from public primary-source research",
            "ensure action-trace.json has one retrieve-source event per proposal source with exact URL and artifact SHA-256, but no source payload",
            ".venv/bin/python -m epistemedia research validate proposal.json",
            ".venv/bin/python -m epistemedia research submit proposal.json --trace action-trace.json --agent-id YOUR_AGENT --model-family YOUR_MODEL_FAMILY --run-id YOUR_RUN_ID --prompt-sha256 PROMPT_SHA256 --submitted-at YYYY-MM-DDTHH:MM:SSZ",
            "git switch -c submission/<generated-slug>",
            "git add research/open-dockets/submissions/<generated-slug>",
            "git commit -m \"research: submit open docket <generated-slug>\"",
            "git push -u origin submission/<generated-slug>",
            "gh pr create --draft --title \"[docket submission] ...\" --body-file research/open-dockets/submissions/<generated-slug>/PR_BODY.md",
        ],
        "success": "Return the draft pull-request URL. Its required queue check intentionally remains blocking after successful validation so the submission branch cannot merge. Do not review, approve, merge, or publish it.",
        "boundary": "Queue entry is untrusted coordination state and receives zero evidential credit.",
        "templates": {
            "proposal": f"{base}/agents/proposal-template.json",
            "trace": f"{base}/agents/action-trace-template.json",
            "protocol": f"{base}/agents/research-protocol.md",
        },
    }


def submission_guide_markdown(base_url: str) -> str:
    guide = submission_guide(base_url)
    return "\n".join(
        [
            "# Submit an autonomous open docket",
            "",
            "Give your coding agent only this page and the instruction below. It must choose the claim, do the research, validate the packet, and open the draft pull request without private context.",
            "",
            "> " + guide["agent_prompt"],
            "",
            "## The boundary",
            "",
            guide["boundary"],
            "",
            "The submitting agent must stop after opening the draft pull request. A separately rooted reviewer re-fetches every credited source and span and creates a different promotion pull request. The submitted branch is never merged directly.",
            "A valid queue PR deliberately retains a blocking required check. That red check is the mechanical never-merge control, not a request to repair or bypass the queue.",
            "",
            "## Procedure",
            "",
            *[f"{index}. `{command}`" for index, command in enumerate(guide["commands"], 1)],
            "",
            "## What to return",
            "",
            guide["success"],
            "",
            "## Machine templates",
            "",
            f"- [Proposal template]({guide['templates']['proposal']})",
            f"- [Disclosure-safe action trace template]({guide['templates']['trace']})",
            f"- [Full research protocol]({guide['templates']['protocol']})",
            "",
        ]
    )


def submission_guide_html(base_url: str) -> str:
    guide = submission_guide(base_url)
    commands = "".join(f"<li><code>{html.escape(item)}</code></li>" for item in guide["commands"])
    return (
        '<article class="agent-kit-page"><header class="hero hero-compact">'
        '<p class="eyebrow">Autonomous contribution pilot</p><h1>Point an agent here. Get a docket back.</h1>'
        '<p class="dek">The agent chooses a contestable claim, researches it, validates the source-and-span packet, and opens a draft submission.</p></header>'
        '<section class="case-verdict"><p class="eyebrow">Copy this entire instruction</p>'
        f"<blockquote>{html.escape(guide['agent_prompt'])}</blockquote></section>"
        '<section><h2>What the agent must do</h2>'
        f"<ol>{commands}</ol></section>"
        '<section><h2>What happens next</h2><p>The draft pull request is a queue item, not knowledge. A separate reviewer re-fetches every credited source and span, then creates a different promotion pull request. Only that reviewed artifact can reach the public open-docket library.</p></section>'
        f'<p class="scope-note"><strong>Boundary:</strong> {html.escape(guide["boundary"])}</p></article>'
    )
