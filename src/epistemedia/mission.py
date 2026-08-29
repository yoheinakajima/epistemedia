# ruff: noqa: E501
"""Validated public mission and reader-facing narrative projections."""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from typing import Any

MISSION_PATH = "catalog/mission.json"
MISSION_FORMAT = "epistemedia-mission-v0.3"
MISSION_VERSION = "0.3"
EXPECTED_CASES = (
    ("001", "corrections-and-familiarity-backfire"),
    ("002", "agent-citation-lineage"),
    ("003", "gpt-4-bar-exam-percentile"),
    ("004", "mehrabian-7-38-55"),
)


class MissionError(ValueError):
    """Raised when the versioned mission source is incomplete or unsafe."""


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _nonempty(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MissionError(f"{context} must be a non-empty string")
    return value.strip()


def _list(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise MissionError(f"{context} must be a non-empty list")
    return value


def _objects(value: Any, context: str, fields: set[str]) -> list[dict[str, Any]]:
    result = []
    for index, item in enumerate(_list(value, context)):
        if not isinstance(item, dict) or set(item) != fields:
            raise MissionError(f"{context}[{index}] has invalid fields")
        for key, field_value in item.items():
            _nonempty(field_value, f"{context}[{index}].{key}")
        result.append(item)
    return result


def load_mission(root: Path) -> dict[str, Any]:
    path = root.resolve() / MISSION_PATH
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MissionError(f"invalid {MISSION_PATH}: {exc}") from exc
    if not isinstance(raw, dict):
        raise MissionError("mission source must be an object")
    expected = {
        "format",
        "version",
        "title",
        "status",
        "governance_note",
        "problem",
        "building",
        "consequences",
        "case_map_note",
        "cases",
        "principles",
        "not_this",
        "direction",
        "participation",
        "current_state",
    }
    if set(raw) != expected:
        raise MissionError("mission source fields do not match v0.3")
    if raw["format"] != MISSION_FORMAT or raw["version"] != MISSION_VERSION:
        raise MissionError("unsupported mission version")
    for key in ("title", "status", "governance_note", "case_map_note"):
        _nonempty(raw[key], key)
    for key in ("problem", "building", "direction"):
        for index, value in enumerate(_list(raw[key], key)):
            _nonempty(value, f"{key}[{index}]")
    _objects(raw["consequences"], "consequences", {"title", "text"})
    _objects(raw["principles"], "principles", {"title", "text"})
    _objects(raw["not_this"], "not_this", {"title", "text"})
    cases = _objects(
        raw["cases"],
        "cases",
        {
            "number",
            "slug",
            "failure_mode",
            "familiar_claim",
            "bounded_finding",
            "defining_count",
            "unresolved_boundary",
        },
    )
    if tuple((item["number"], item["slug"]) for item in cases) != EXPECTED_CASES:
        raise MissionError("mission case map must bind exactly Cases 001-004")
    participation = _objects(
        raw["participation"],
        "participation",
        {"commitment", "title", "text", "href"},
    )
    for item in participation:
        href = item["href"]
        if not (
            href.startswith("/")
            or href == "https://github.com/yoheinakajima/epistemedia"
        ):
            raise MissionError("mission participation link is outside the public scope")
    state = raw["current_state"]
    state_fields = {
        "summary",
        "repository_open",
        "compiler_running",
        "governance_open",
        "four_case_library_live_after_deployment_readback",
        "cold_start_research_kit_live_after_deployment_readback",
        "hosted_api_live",
        "hosted_mcp_live",
        "authenticated_submission_queue_live",
        "second_realm_live",
        "note",
    }
    if not isinstance(state, dict) or set(state) != state_fields:
        raise MissionError("current_state fields do not match v0.3")
    _nonempty(state["summary"], "current_state.summary")
    _nonempty(state["note"], "current_state.note")
    for key in state_fields - {"summary", "note"}:
        if not isinstance(state[key], bool):
            raise MissionError(f"current_state.{key} must be boolean")
    if any(
        state[key]
        for key in (
            "hosted_api_live",
            "hosted_mcp_live",
            "authenticated_submission_queue_live",
            "second_realm_live",
        )
    ):
        raise MissionError("future public services must fail closed in mission v0.3")
    source_bytes = path.read_bytes()
    result = dict(raw)
    result["mission_id"] = "em:mission:sha256:" + hashlib.sha256(
        _canonical(raw)
    ).hexdigest()
    result["source"] = {
        "path": MISSION_PATH,
        "sha256": hashlib.sha256(source_bytes).hexdigest(),
        "bytes": len(source_bytes),
    }
    return result


def bind_case_summaries(
    mission: dict[str, Any], summaries: list[dict[str, Any]]
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    summary_by_slug = {item["slug"]: item for item in summaries}
    if len(summary_by_slug) != len(summaries):
        raise MissionError("case summaries contain a duplicate slug")
    if set(summary_by_slug) != {item["slug"] for item in mission["cases"]}:
        raise MissionError("mission case map and accepted case library differ")
    result = []
    for framing in mission["cases"]:
        summary = summary_by_slug[framing["slug"]]
        if summary["number"] != framing["number"]:
            raise MissionError("mission case number differs from accepted library")
        result.append((framing, summary))
    return result


def _href(base_url: str, href: str) -> str:
    if href.startswith("/"):
        return base_url.rstrip("/") + href
    return href


def mission_markdown(mission: dict[str, Any], base_url: str) -> str:
    lines = [
        f"# {mission['title']}",
        "",
        f"*Epistemedia mission, v{mission['version']}.*",
        "",
        f"> {mission['governance_note']}",
        "",
        "## The problem",
        "",
        *mission["problem"],
        "",
        "## What we are building",
        "",
        *mission["building"],
        "",
    ]
    for item in mission["consequences"]:
        lines.extend([f"### {item['title']}", "", item["text"], ""])
    lines.extend(["## It already works", "", mission["case_map_note"], ""])
    for item in mission["cases"]:
        lines.extend(
            [
                f"### Case {item['number']} — {item['failure_mode']}",
                "",
                f"**Familiar claim:** {item['familiar_claim']}",
                "",
                item["bounded_finding"],
                "",
                f"**Defining count:** {item['defining_count']}",
                "",
                f"**Open boundary:** {item['unresolved_boundary']}",
                "",
                f"[Open the case]({base_url}/how-we-know/{item['slug']}/)",
                "",
            ]
        )
    lines.extend(["## What we believe", ""])
    for item in mission["principles"]:
        lines.append(f"- **{item['title']}.** {item['text']}")
    lines.extend(["", "## What this is not", ""])
    for item in mission["not_this"]:
        lines.append(f"- **{item['title']}.** {item['text']}")
    lines.extend(["", "## Where this goes", "", *mission["direction"], ""])
    lines.extend(["## How to participate", ""])
    for item in mission["participation"]:
        lines.append(
            f"- **{item['commitment']} — [{item['title']}]({_href(base_url, item['href'])}).** {item['text']}"
        )
    state = mission["current_state"]
    lines.extend(
        [
            "",
            "## Where we actually are",
            "",
            f"**{state['summary']}**",
            "",
            state["note"],
            "",
            f"Mission ID: `{mission['mission_id']}`  ",
            f"Source: `{mission['source']['path']}`  ",
            f"Source SHA-256: `{mission['source']['sha256']}`",
            "",
            f"[Take the reader check]({base_url}/about/reader-check/)",
            "",
        ]
    )
    return "\n".join(lines)


def _cards(items: list[dict[str, Any]], class_name: str) -> str:
    return "".join(
        f'<article class="{class_name}"><h3>{html.escape(item["title"])}</h3>'
        f'<p>{html.escape(item["text"])}</p></article>'
        for item in items
    )


def failure_map_html(
    mission: dict[str, Any], summaries: list[dict[str, Any]], base_url: str
) -> str:
    cards = []
    for framing, summary in bind_case_summaries(mission, summaries):
        cards.append(
            '<article class="failure-card">'
            f'<p class="case-stamp">Case {html.escape(framing["number"])}'
            f'<span>{html.escape(framing["failure_mode"])}</span></p>'
            f'<h3><a href="{html.escape(base_url)}/how-we-know/{html.escape(framing["slug"])}/">{html.escape(framing["familiar_claim"])}</a></h3>'
            f'<p class="failure-finding">{html.escape(framing["bounded_finding"])}</p>'
            f'<p class="failure-count">{html.escape(framing["defining_count"])}</p>'
            f'<p class="failure-boundary"><strong>Still open</strong>{html.escape(framing["unresolved_boundary"])}</p>'
            f'<p class="failure-links"><a href="{html.escape(base_url)}/how-we-know/{html.escape(summary["slug"])}/">Brief</a> · '
            f'<a href="{html.escape(base_url)}/how-we-know/{html.escape(summary["slug"])}/skeptical/">Skeptical</a> · '
            f'<a href="{html.escape(base_url)}/how-we-know/{html.escape(summary["slug"])}/review/">Review</a></p>'
            "</article>"
        )
    return (
        '<section class="failure-map" aria-labelledby="failure-map-title">'
        '<div class="section-head"><div><p class="eyebrow">Four cases · four failure modes</p>'
        '<h2 id="failure-map-title">Unit tests for how knowledge goes wrong</h2></div>'
        f'<p class="meta">{html.escape(mission["case_map_note"])}</p></div>'
        f'<div class="failure-grid">{"".join(cards)}</div>'
        f'<p class="section-link"><a href="{html.escape(base_url)}/how-we-know/">View all four cases</a></p></section>'
    )


def method_html(base_url: str) -> str:
    steps = (
        ("01", "Trace sources", "Pin the edition and exact passage behind each claim."),
        ("02", "Collapse echoes", "Follow lineage so ten repetitions of one root still count as one root."),
        ("03", "Apply a named policy", "Compile a reading whose rules, limits, and alternative lens remain visible."),
    )
    body = "".join(
        f'<li><span>{number}</span><div><h3>{title}</h3><p>{text}</p></div></li>'
        for number, title, text in steps
    )
    return (
        '<section class="method-strip" aria-labelledby="method-title">'
        '<p class="eyebrow">How Epistemedia reads a claim</p>'
        '<h2 id="method-title">From assertion to inspectable reading</h2>'
        f'<ol>{body}</ol><p><a href="{html.escape(base_url)}/about/">Read the mission</a></p></section>'
    )


def mission_bridge_html(mission: dict[str, Any], base_url: str) -> str:
    return f"""
<section class="mission-bridge" aria-labelledby="mission-bridge-title">
  <p class="eyebrow">Why this exists</p>
  <h2 id="mission-bridge-title">Claims arrive without their history.</h2>
  <p>AI made confident assertions nearly free. Epistemedia makes the source trail, dependence, unresolved record, and policy behind a reading inspectable.</p>
  <p class="mission-contrast"><span>Not a finished answer.</span><span>A case file that can show its work.</span></p>
  <p><a class="primary-action" href="{html.escape(base_url)}/about/">Read mission v{html.escape(mission['version'])}</a></p>
</section>
""".strip()


def participation_html(mission: dict[str, Any], base_url: str) -> str:
    cards = "".join(
        '<article class="participation-card">'
        f'<p class="eyebrow">{html.escape(item["commitment"])}</p>'
        f'<h3><a href="{html.escape(_href(base_url, item["href"]))}">{html.escape(item["title"])}</a></h3>'
        f'<p>{html.escape(item["text"])}</p></article>'
        for item in mission["participation"][:3]
    )
    return (
        '<section aria-labelledby="participate-title"><div class="section-head"><div>'
        '<p class="eyebrow">Participate</p><h2 id="participate-title">Inspect, test, contribute</h2>'
        '</div><p class="meta">A proposal is not accepted knowledge.</p></div>'
        f'<div class="participation-grid">{cards}</div></section>'
    )


def about_html(
    mission: dict[str, Any], summaries: list[dict[str, Any]], base_url: str
) -> str:
    problem = "".join(f"<p>{html.escape(item)}</p>" for item in mission["problem"])
    building = "".join(f"<p>{html.escape(item)}</p>" for item in mission["building"])
    principles = _cards(mission["principles"], "principle-card")
    not_this = _cards(mission["not_this"], "not-card")
    direction = "".join(f"<p>{html.escape(item)}</p>" for item in mission["direction"])
    participation = "".join(
        '<article class="participation-card">'
        f'<p class="eyebrow">{html.escape(item["commitment"])}</p>'
        f'<h3><a href="{html.escape(_href(base_url, item["href"]))}">{html.escape(item["title"])}</a></h3>'
        f'<p>{html.escape(item["text"])}</p></article>'
        for item in mission["participation"]
    )
    state = mission["current_state"]
    return f"""
<article class="mission-page">
  <header class="mission-hero">
    <p class="eyebrow">Mission · Version {html.escape(mission['version'])}</p>
    <h1>{html.escape(mission['title'])}</h1>
    <p class="dek">{html.escape(mission['governance_note'])}</p>
    <p class="mission-id"><code>{html.escape(mission['mission_id'])}</code></p>
  </header>
  <section class="mission-problem" aria-labelledby="problem-title"><p class="eyebrow">The problem</p><h2 id="problem-title">Confidence is cheap. History is missing.</h2>{problem}</section>
  <section aria-labelledby="building-title"><p class="eyebrow">What we are building</p><h2 id="building-title">Store the process, then compile the reading</h2>{building}<div class="consequence-grid">{_cards(mission['consequences'], 'principle-card')}</div></section>
  {failure_map_html(mission, summaries, base_url)}
  <section aria-labelledby="beliefs-title"><p class="eyebrow">What we believe</p><h2 id="beliefs-title">Seven operating principles</h2><div class="principle-grid">{principles}</div></section>
  <section aria-labelledby="not-title"><p class="eyebrow">What this is not</p><h2 id="not-title">A shared record, not one stamped truth</h2><div class="not-grid">{not_this}</div></section>
  <section class="mission-direction" aria-labelledby="direction-title"><p class="eyebrow">Where this goes</p><h2 id="direction-title">Agents should inspect lineage before they assert</h2>{direction}</section>
  <section aria-labelledby="about-participate-title"><p class="eyebrow">How to participate</p><h2 id="about-participate-title">Start by trying to break the record</h2><div class="participation-grid">{participation}</div></section>
  <section class="current-state" aria-labelledby="state-title"><p class="eyebrow">Where we actually are</p><h2 id="state-title">{html.escape(state['summary'])}</h2><p>{html.escape(state['note'])}</p><p><a href="{html.escape(base_url)}/about/reader-check/">Take the five-question reader check</a></p></section>
</article>
""".strip()


def how_we_know_markdown(
    mission: dict[str, Any], summaries: list[dict[str, Any]], base_url: str
) -> str:
    lines = [
        "# How We Know",
        "",
        "Four unit tests for how knowledge can fail. Each evidence file keeps claims, exact passages, dependence, uncertainty, and policy-relative readings inspectable.",
        "",
        f"> {mission['case_map_note']}",
        "",
    ]
    for framing, summary in bind_case_summaries(mission, summaries):
        lines.extend(
            [
                f"## Case {framing['number']} — {framing['failure_mode']}",
                "",
                f"**Familiar claim:** {framing['familiar_claim']}",
                "",
                f"**Bounded finding:** {framing['bounded_finding']}",
                "",
                f"**Defining count:** {framing['defining_count']}",
                "",
                f"**Still open:** {framing['unresolved_boundary']}",
                "",
                f"[Brief]({base_url}/how-we-know/{summary['slug']}/) · "
                f"[Skeptical]({base_url}/how-we-know/{summary['slug']}/skeptical/) · "
                f"[Review]({base_url}/how-we-know/{summary['slug']}/review/)",
                "",
            ]
        )
    return "\n".join(lines)


def how_we_know_html(
    mission: dict[str, Any], summaries: list[dict[str, Any]], base_url: str
) -> str:
    return (
        '<section class="section-head library-intro"><div><p class="eyebrow">How We Know</p>'
        '<h1>Four unit tests for how knowledge fails</h1>'
        '<p class="dek">Each case starts with a familiar claim, then exposes the source trail, dependence structure, unresolved record, and policy-relative reading.</p></div>'
        f'<p class="meta">{html.escape(mission["case_map_note"])}</p></section>'
        + failure_map_html(mission, summaries, base_url)
        + f'<p class="qualification">{len(summaries)} accepted cases. No future case is advertised as available.</p>'
    )


def reader_check_document(mission: dict[str, Any], base_url: str) -> dict[str, Any]:
    return {
        "format": "epistemedia-human-reader-check-v0.1",
        "mission_id": mission["mission_id"],
        "status": "awaiting-human-response",
        "purpose": "Test whether a first-time human reader can explain the product without inheriting project context.",
        "instructions": "Read the homepage, one case brief, its Skeptical view, and one source disclosure. Answer in your own words. Do not use an agent or model to compose the answers.",
        "questions": [
            {
                "id": "evidence-unit",
                "question": "What does Epistemedia count instead of simply counting paper titles or repeated citations?",
                "success_signal": "The reader identifies bounded evidence or lineage roots and the declared counting rule.",
            },
            {
                "id": "run-independence",
                "question": "Why do eight agent reports not automatically count as eight independent evidence roots?",
                "success_signal": "The reader identifies shared prompt, capture, source, method, or derivation lineage.",
            },
            {
                "id": "lens-difference",
                "question": "What can change between the Brief and Skeptical readings, and what must remain shared?",
                "success_signal": "The reader distinguishes a named policy reading from the common accepted record.",
            },
            {
                "id": "current-limit",
                "question": "Name one important thing Epistemedia does not currently provide or claim.",
                "success_signal": "The reader names a real boundary such as no hosted API/MCP queue, no global truth stamp, or no second realm.",
            },
            {
                "id": "inspect-source",
                "question": "Where would you go to inspect the exact source passage behind a displayed relation?",
                "success_signal": "The reader points to the case docket or sentence/source disclosure rather than trusting the summary alone.",
            },
        ],
        "recording_boundary": "A result exists only after an actual human returns retained answers. Automated route, browser, and model checks do not satisfy this instrument.",
        "routes": {
            "home": base_url + "/",
            "cases": base_url + "/how-we-know/",
            "mission": base_url + "/about/",
        },
    }


def reader_check_markdown(document: dict[str, Any]) -> str:
    lines = [
        "# First-reader check",
        "",
        f"**Status:** {document['status']}",
        "",
        document["purpose"],
        "",
        f"> {document['instructions']}",
        "",
    ]
    for index, item in enumerate(document["questions"], start=1):
        lines.extend(
            [
                f"## {index}. {item['question']}",
                "",
                "Your answer:",
                "",
                "---",
                "",
            ]
        )
    lines.extend(["## Recording boundary", "", document["recording_boundary"], ""])
    return "\n".join(lines)


def reader_check_html(document: dict[str, Any], base_url: str) -> str:
    questions = "".join(
        '<li class="reader-question">'
        f'<h2>{html.escape(item["question"])}</h2>'
        '<p class="answer-line">Answer in your own words</p></li>'
        for item in document["questions"]
    )
    return f"""
<article class="reader-check">
  <header class="hero hero-compact"><p class="eyebrow">Real-reader instrument · Pending</p><h1>Can a first-time reader explain Epistemedia?</h1><p class="dek">{html.escape(document['purpose'])}</p></header>
  <section class="reader-instructions"><h2>Before you answer</h2><p>{html.escape(document['instructions'])}</p><p><a href="{html.escape(base_url)}/">Homepage</a> · <a href="{html.escape(base_url)}/how-we-know/">Case library</a> · <a href="{html.escape(base_url)}/about/">Mission</a></p></section>
  <ol class="reader-questions">{questions}</ol>
  <section class="reader-boundary"><h2>What counts as a result</h2><p>{html.escape(document['recording_boundary'])}</p></section>
</article>
""".strip()
