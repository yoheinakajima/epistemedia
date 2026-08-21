from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

VERSION = "0.2.0"
PROTOCOL_VERSION = "2026-07-28"
DEFAULT_BASE_URL = "https://epistemedia.org"
DEFAULT_API_URL = "https://api.epistemedia.org/v1"
DEFAULT_MCP_URL = "https://mcp.epistemedia.org/mcp"

LENSES: dict[str, str] = {
    "encyclopedia": "A coherent general overview with explicit provenance and disagreement.",
    "evidence-first": "Primary evidence and derivation are foregrounded before narrative.",
    "skeptical": "Only strongly supported, independently grounded conclusions are foregrounded.",
    "frontier": "Open questions, disputes, missing evidence, and speculative work are foregrounded.",
    "historical": "The state visible at a selected accepted evidence frontier.",
    "pedagogical": "A prerequisite-aware explanation for learning and exploration.",
    "source-only": "Source objects and exact passages without generated synthesis.",
}

TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".toml",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".css",
    ".html",
    ".xml",
    ".csv",
    ".sql",
    ".sh",
}

IGNORED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "generated",
    "dist",
    "build",
}

PUBLIC_ROOTS = {
    "README.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "LICENSE",
    "constitution",
    "policies",
    "schemas",
    "docs",
    "tasks",
    "governance",
    "research",
    "releases",
    "src",
    "tests",
    ".github",
    "catalog",
    "pyproject.toml",
    "Makefile",
    "Dockerfile",
    "compose.yaml",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical_json(value).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def stable_id(kind: str, value: Any) -> str:
    return f"em:{kind}:sha256:{digest(value)}"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_value(root: Path, *args: str, default: str = "unknown") -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return default


def title_from_path(path: str) -> str:
    name = Path(path).stem.replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", name).strip().title() or path


def first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def first_paragraph(text: str, limit: int = 320) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
    for paragraph in paragraphs:
        if paragraph and not paragraph.startswith("#") and not paragraph.startswith("|"):
            return paragraph[:limit]
    return ""


def safe_slug(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "item"


def is_public_source(root: Path, path: Path) -> bool:
    rel = path.relative_to(root)
    if not rel.parts:
        return False
    if any(part in IGNORED_PARTS or part.startswith(".") and part != ".github" for part in rel.parts):
        return False
    first = rel.parts[0]
    return first in PUBLIC_ROOTS and path.suffix.lower() in TEXT_SUFFIXES or str(rel) in PUBLIC_ROOTS


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


@dataclass(frozen=True)
class PublicObject:
    id: str
    kind: str
    path: str
    title: str
    media_type: str
    content_digest: str
    text: str
    summary: str
    visibility: str = "public"
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self, include_text: bool = True) -> dict[str, Any]:
        value: dict[str, Any] = {
            "id": self.id,
            "kind": self.kind,
            "path": self.path,
            "title": self.title,
            "media_type": self.media_type,
            "content_digest": self.content_digest,
            "summary": self.summary,
            "visibility": self.visibility,
            "metadata": self.metadata,
        }
        if include_text:
            value["text"] = self.text
        return value


@dataclass(frozen=True)
class Topic:
    slug: str
    title: str
    description: str
    include: tuple[str, ...]
    tags: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.title,
            "description": self.description,
            "include": list(self.include),
            "tags": list(self.tags),
        }


@dataclass
class PublicCatalog:
    root: Path
    commit: str
    frontier: str
    objects: list[PublicObject]
    topics: list[Topic]
    policies: dict[str, Any]
    catalog_id: str
    generated_at: str

    @classmethod
    def build(cls, root: Path) -> "PublicCatalog":
        root = root.resolve()
        objects: list[PublicObject] = []
        for path in sorted(root.rglob("*")):
            if not path.is_file() or not is_public_source(root, path):
                continue
            rel = path.relative_to(root).as_posix()
            text = read_text(path)
            media_type = media_type_for(path)
            content_digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            identity = {
                "path": rel,
                "content_digest": content_digest,
                "media_type": media_type,
            }
            kind = object_kind(rel)
            obj = PublicObject(
                id=stable_id(kind, identity),
                kind=kind,
                path=rel,
                title=first_heading(text, title_from_path(rel)),
                media_type=media_type,
                content_digest=content_digest,
                text=text,
                summary=first_paragraph(text),
                metadata={"source": "repository", "path": rel},
            )
            objects.append(obj)

        topics = load_topics(root, objects)
        policies = load_policies(root)
        commit = git_value(root, "rev-parse", "HEAD")
        # Frontier is accepted content, not a deploy URL or build timestamp.
        frontier_material = {
            "commit": commit,
            "objects": sorted((o.id, o.content_digest) for o in objects),
            "policies": policies,
            "topics": [topic.as_dict() for topic in topics],
        }
        frontier = stable_id("frontier", frontier_material)
        catalog_material = {
            "frontier": frontier,
            "object_ids": sorted(o.id for o in objects),
            "topic_slugs": sorted(t.slug for t in topics),
            "lens_versions": sorted(LENSES),
            "compiler": VERSION,
        }
        return cls(
            root=root,
            commit=commit,
            frontier=frontier,
            objects=objects,
            topics=topics,
            policies=policies,
            catalog_id=stable_id("catalog", catalog_material),
            generated_at=utc_now(),
        )

    def object_map(self) -> dict[str, PublicObject]:
        return {obj.id: obj for obj in self.objects}

    def topic_map(self) -> dict[str, Topic]:
        return {topic.slug: topic for topic in self.topics}

    def selected_objects(self, topic: Topic) -> list[PublicObject]:
        selected: list[PublicObject] = []
        for obj in self.objects:
            if any(path_match(obj.path, pattern) for pattern in topic.include):
                selected.append(obj)
        return selected

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        terms = [term for term in re.findall(r"[a-z0-9]+", query.lower()) if len(term) > 1]
        if not terms:
            return []
        scored: list[tuple[float, PublicObject]] = []
        for obj in self.objects:
            hay_title = obj.title.lower()
            hay_path = obj.path.lower()
            hay_text = obj.text.lower()
            score = 0.0
            for term in terms:
                score += 8.0 * hay_title.count(term)
                score += 4.0 * hay_path.count(term)
                score += min(10, hay_text.count(term))
            if score:
                scored.append((score, obj))
        scored.sort(key=lambda pair: (-pair[0], pair[1].path))
        return [
            {
                "score": score,
                "id": obj.id,
                "title": obj.title,
                "path": obj.path,
                "kind": obj.kind,
                "summary": obj.summary,
            }
            for score, obj in scored[:limit]
        ]

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": "https://epistemedia.com/schemas/public-catalog-v1.json",
            "catalog_id": self.catalog_id,
            "frontier": self.frontier,
            "commit": self.commit,
            "compiler": f"epistemedia/{VERSION}",
            "generated_at": self.generated_at,
            "object_count": len(self.objects),
            "topic_count": len(self.topics),
            "objects": [obj.as_dict(include_text=False) for obj in self.objects],
            "topics": [topic.as_dict() for topic in self.topics],
            "lenses": LENSES,
            "policies": self.policies,
        }


def media_type_for(path: Path) -> str:
    return {
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".json": "application/json",
        ".jsonl": "application/x-ndjson",
        ".yaml": "application/yaml",
        ".yml": "application/yaml",
        ".toml": "application/toml",
        ".py": "text/x-python",
        ".js": "text/javascript",
        ".ts": "text/typescript",
        ".tsx": "text/tsx",
        ".jsx": "text/jsx",
        ".css": "text/css",
        ".html": "text/html",
        ".xml": "application/xml",
        ".csv": "text/csv",
        ".sql": "text/x-sql",
        ".sh": "text/x-shellscript",
    }.get(path.suffix.lower(), "text/plain")


def object_kind(path: str) -> str:
    first = path.split("/", 1)[0]
    return {
        "constitution": "constitution",
        "policies": "policy",
        "schemas": "schema",
        "tasks": "task",
        "governance": "governance-record",
        "research": "research-note",
        "releases": "release",
        "src": "implementation",
        "tests": "test",
        "docs": "documentation",
        "catalog": "catalog-source",
        ".github": "automation",
    }.get(first, "repository-artifact")


def path_match(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        return path.startswith(pattern[:-3])
    if pattern.endswith("/*"):
        prefix = pattern[:-2]
        return path.startswith(prefix + "/") and "/" not in path[len(prefix) + 1 :]
    if "*" in pattern:
        regex = "^" + re.escape(pattern).replace(r"\*\*", ".*").replace(r"\*", "[^/]*") + "$"
        return bool(re.match(regex, path))
    return path == pattern or path.startswith(pattern.rstrip("/") + "/")


def load_topics(root: Path, objects: list[PublicObject]) -> list[Topic]:
    path = root / "catalog" / "topics.json"
    topics: list[Topic] = []
    if path.exists():
        try:
            raw = json.loads(path.read_text())
            for item in raw.get("topics", raw if isinstance(raw, list) else []):
                topics.append(
                    Topic(
                        slug=safe_slug(item["slug"]),
                        title=item["title"],
                        description=item.get("description", ""),
                        include=tuple(item.get("include", [])),
                        tags=tuple(item.get("tags", [])),
                    )
                )
        except Exception as exc:
            raise ValueError(f"invalid catalog/topics.json: {exc}") from exc
    if not topics:
        defaults = [
            ("project", "Epistemedia", "The public project, implementation, and operating state.", ("README.md", "docs/**", "src/**")),
            ("governance", "Governance", "Constitutional and policy machinery for autonomous contribution.", ("constitution/**", "policies/**", "governance/**")),
            ("protocol", "Epistemic Mesh Protocol", "Event, provenance, federation, and projection contracts.", ("schemas/**", "docs/**")),
            ("agents", "Agent Operations", "How agents orient, select, execute, validate, and hand off work.", ("AGENTS.md", "tasks/**", "docs/agent-ops/**")),
        ]
        topics = [Topic(slug, title, desc, include) for slug, title, desc, include in defaults]
    # Keep topics that resolve to at least one public object; deterministic order.
    result = []
    for topic in sorted(topics, key=lambda t: t.slug):
        if any(any(path_match(obj.path, p) for p in topic.include) for obj in objects):
            result.append(topic)
    return result


def load_policies(root: Path) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "epistemic": "commons-balanced-v0.1",
        "disclosure": "public-v0.1",
        "selection": "repository-public-v0.1",
        "compiler": f"epistemedia/{VERSION}",
    }
    manifest = root / "policies" / "manifest.json"
    if manifest.exists():
        try:
            defaults.update(json.loads(manifest.read_text()))
        except Exception as exc:
            raise ValueError(f"invalid policies/manifest.json: {exc}") from exc
    return defaults


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def html_shell(title: str, body: str, *, base_url: str, markdown_url: str | None = None) -> str:
    alternates = ""
    if markdown_url:
        alternates = f'<link rel="alternate" type="text/markdown" href="{html.escape(markdown_url)}">'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · Epistemedia</title>
<meta name="description" content="Knowledge that can show its work.">
<link rel="describedby" href="{html.escape(base_url)}/llms.txt">
{alternates}
<style>
:root{{--bg:#f7f5ef;--ink:#171714;--muted:#68685f;--line:#d8d5ca;--panel:#fffef9;--accent:#2f5946;--code:#efede5}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
a{{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:3px}} header,main,footer{{max-width:1120px;margin:auto;padding:1.25rem 2rem}}
header{{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--line)}} nav a{{margin-left:1rem}} h1{{font:700 clamp(2.3rem,7vw,6.7rem)/.94 ui-serif,Georgia,serif;letter-spacing:-.045em;margin:.3em 0}} h2,h3{{font-family:ui-serif,Georgia,serif}}
.hero{{padding:5rem 0 3rem}} .dek{{font-size:1.35rem;max-width:800px;color:var(--muted)}} .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1rem}} .card{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:1.2rem}} .meta{{color:var(--muted);font-size:.9rem}} code,pre{{background:var(--code)}} code{{padding:.12rem .3rem;border-radius:4px}} pre{{padding:1rem;overflow:auto;border-radius:8px}} .manifest{{border-top:1px solid var(--line);margin-top:3rem;padding-top:1rem}} footer{{color:var(--muted);font-size:.9rem;border-top:1px solid var(--line)}}
</style>
</head>
<body>
<header><strong><a href="{html.escape(base_url)}/">Epistemedia</a></strong><nav><a href="{html.escape(base_url)}/explore/">Explore</a><a href="{html.escape(base_url)}/docs/">Docs</a><a href="{html.escape(base_url)}/status/">Status</a></nav></header>
<main>{body}</main>
<footer>Knowledge that can show its work. Human and agent interfaces compile from the same public projection.</footer>
</body></html>
"""


def md_to_html(text: str) -> str:
    # Small deterministic renderer. It deliberately supports a conservative Markdown subset.
    lines = text.splitlines()
    out: list[str] = []
    in_code = False
    code: list[str] = []
    in_list = False
    for line in lines:
        if line.startswith("```"):
            if in_code:
                out.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
                code = []
                in_code = False
            else:
                if in_list:
                    out.append("</ul>")
                    in_list = False
                in_code = True
            continue
        if in_code:
            code.append(line)
            continue
        if line.startswith("### "):
            out.append(f"<h3>{inline_md(line[4:])}</h3>")
        elif line.startswith("## "):
            out.append(f"<h2>{inline_md(line[3:])}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{inline_md(line[2:])}</h1>")
        elif line.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline_md(line[2:])}</li>")
        elif not line.strip():
            if in_list:
                out.append("</ul>")
                in_list = False
        elif line.startswith("> "):
            out.append(f"<blockquote>{inline_md(line[2:])}</blockquote>")
        elif line.startswith("|"):
            out.append(f"<pre>{html.escape(line)}</pre>")
        else:
            out.append(f"<p>{inline_md(line)}</p>")
    if in_list:
        out.append("</ul>")
    if in_code:
        out.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
    return "\n".join(out)


def inline_md(value: str) -> str:
    escaped = html.escape(value)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\[([^]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', escaped)
    return escaped


def topic_projection(catalog: PublicCatalog, topic: Topic, lens: str, base_url: str) -> dict[str, Any]:
    selected = catalog.selected_objects(topic)
    manifest_material = {
        "catalog_id": catalog.catalog_id,
        "frontier": catalog.frontier,
        "topic": topic.slug,
        "lens": lens,
        "policies": catalog.policies,
        "objects": [obj.id for obj in selected],
        "compiler": VERSION,
    }
    projection_id = stable_id("projection", manifest_material)
    return {
        "projection_id": projection_id,
        "catalog_id": catalog.catalog_id,
        "frontier": catalog.frontier,
        "topic": topic.as_dict(),
        "lens": {"id": lens, "description": LENSES[lens]},
        "policies": catalog.policies,
        "compiler": f"epistemedia/{VERSION}",
        "commit": catalog.commit,
        "generated_at": catalog.generated_at,
        "base_url": base_url,
        "objects": [obj.as_dict(include_text=False) for obj in selected],
    }


def projection_markdown(projection: dict[str, Any]) -> str:
    topic = projection["topic"]
    lines = [
        f"# {topic['title']}",
        "",
        topic.get("description", ""),
        "",
        f"**Lens:** `{projection['lens']['id']}` — {projection['lens']['description']}",
        "",
        "## Included objects",
        "",
    ]
    for obj in projection["objects"]:
        lines += [
            f"### {obj['title']}",
            "",
            obj.get("summary") or f"Repository artifact `{obj['path']}`.",
            "",
            f"- Kind: `{obj['kind']}`",
            f"- Source path: `{obj['path']}`",
            f"- Object ID: `{obj['id']}`",
            f"- Content digest: `{obj['content_digest']}`",
            "",
        ]
    lines += [
        "## Projection manifest",
        "",
        f"- Projection: `{projection['projection_id']}`",
        f"- Catalog: `{projection['catalog_id']}`",
        f"- Evidence frontier: `{projection['frontier']}`",
        f"- Accepted commit: `{projection['commit']}`",
        f"- Epistemic policy: `{projection['policies']['epistemic']}`",
        f"- Disclosure policy: `{projection['policies']['disclosure']}`",
        f"- Compiler: `{projection['compiler']}`",
    ]
    return "\n".join(lines).strip() + "\n"


def build_public(
    root: Path,
    output: Path,
    *,
    base_url: str = DEFAULT_BASE_URL,
    api_url: str = DEFAULT_API_URL,
    mcp_url: str = DEFAULT_MCP_URL,
) -> dict[str, Any]:
    catalog = PublicCatalog.build(root)
    output = output.resolve()
    tmp = output.parent / (output.name + ".tmp")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)

    write_json(tmp / "catalog.json", catalog.public_dict())
    write_json(tmp / "status.json", {
        "project": "Epistemedia",
        "version": VERSION,
        "catalog_id": catalog.catalog_id,
        "frontier": catalog.frontier,
        "commit": catalog.commit,
        "generated_at": catalog.generated_at,
        "object_count": len(catalog.objects),
        "topic_count": len(catalog.topics),
        "protocol_version": PROTOCOL_VERSION,
    })
    write_json(tmp / "search.json", {
        "catalog_id": catalog.catalog_id,
        "frontier": catalog.frontier,
        "documents": [obj.as_dict(include_text=False) for obj in catalog.objects],
    })

    for obj in catalog.objects:
        key = quote(obj.id, safe="")
        write_json(tmp / "objects" / f"{key}.json", obj.as_dict())
        markdown = (
            f"# {obj.title}\n\n"
            f"- Object ID: `{obj.id}`\n"
            f"- Kind: `{obj.kind}`\n"
            f"- Repository path: `{obj.path}`\n"
            f"- Content digest: `{obj.content_digest}`\n\n"
            f"## Source content\n\n{obj.text.rstrip()}\n"
        )
        write_text(tmp / "objects" / f"{key}.md", markdown)
        body = md_to_html(markdown)
        write_text(
            tmp / "objects" / key / "index.html",
            html_shell(obj.title, body, base_url=base_url, markdown_url=f"{base_url}/objects/{key}.md"),
        )

    projection_count = 0
    topic_cards = []
    for topic in catalog.topics:
        selected = catalog.selected_objects(topic)
        topic_cards.append(
            f'<article class="card"><h2><a href="{base_url}/topics/{topic.slug}/">{html.escape(topic.title)}</a></h2>'
            f'<p>{html.escape(topic.description)}</p><p class="meta">{len(selected)} public objects · {len(LENSES)} lenses</p></article>'
        )
        for lens in LENSES:
            projection = topic_projection(catalog, topic, lens, base_url)
            projection_count += 1
            md = projection_markdown(projection)
            base = tmp / "topics" / topic.slug / lens
            write_json(base / "manifest.json", projection)
            write_text(base / "index.md", md)
            write_text(
                base / "index.html",
                html_shell(
                    f"{topic.title} — {lens}",
                    md_to_html(md),
                    base_url=base_url,
                    markdown_url=f"{base_url}/topics/{topic.slug}/{lens}/index.md",
                ),
            )
        default_projection = topic_projection(catalog, topic, "encyclopedia", base_url)
        md = projection_markdown(default_projection)
        lens_links = " ".join(
            f'<a href="{base_url}/topics/{topic.slug}/{lens}/">{html.escape(lens)}</a>'
            for lens in LENSES
        )
        body = (
            f'<section class="hero"><p class="meta">Topic projection</p><h1>{html.escape(topic.title)}</h1>'
            f'<p class="dek">{html.escape(topic.description)}</p><p>{lens_links}</p></section>'
            + md_to_html(md)
        )
        write_text(
            tmp / "topics" / topic.slug / "index.html",
            html_shell(topic.title, body, base_url=base_url, markdown_url=f"{base_url}/topics/{topic.slug}/index.md"),
        )
        write_text(tmp / "topics" / topic.slug / "index.md", md)

    home_body = (
        '<section class="hero"><p class="meta">An open knowledge network for humans and agents</p>'
        '<h1>Knowledge that can show its work.</h1>'
        '<p class="dek">Epistemedia preserves sources, claims, disagreements, policies, and derivations, then compiles reproducible views for each reader and agent.</p></section>'
        '<section><h2>Explore the first realm</h2><div class="grid">'
        + "".join(topic_cards)
        + '</div></section>'
        '<section class="manifest"><h2>This page is a projection</h2>'
        f'<p>Catalog <code>{html.escape(catalog.catalog_id)}</code><br>Frontier <code>{html.escape(catalog.frontier)}</code><br>Commit <code>{html.escape(catalog.commit)}</code></p></section>'
    )
    write_text(tmp / "index.html", html_shell("Knowledge that can show its work", home_body, base_url=base_url, markdown_url=f"{base_url}/index.md"))
    write_text(tmp / "index.md", "# Epistemedia\n\nKnowledge that can show its work.\n\n" + "\n".join(f"- [{t.title}]({base_url}/topics/{t.slug}/) — {t.description}" for t in catalog.topics) + "\n")

    explore_body = '<section class="hero"><h1>Explore</h1><p class="dek">Browse topics and the exact public objects used to compile them.</p></section><div class="grid">' + "".join(topic_cards) + '</div>'
    write_text(tmp / "explore" / "index.html", html_shell("Explore", explore_body, base_url=base_url, markdown_url=f"{base_url}/explore/index.md"))
    write_text(tmp / "explore" / "index.md", "# Explore\n\n" + "\n".join(f"- [{t.title}]({base_url}/topics/{t.slug}/)" for t in catalog.topics) + "\n")

    docs = [obj for obj in catalog.objects if obj.kind == "documentation" or obj.path in ("README.md", "AGENTS.md")]
    docs_body = '<section class="hero"><h1>Documentation</h1><p class="dek">Human guidance and machine-operable project contracts, compiled from accepted repository content.</p></section><div class="grid">' + "".join(f'<article class="card"><h2>{html.escape(o.title)}</h2><p>{html.escape(o.summary)}</p><p><a href="{base_url}/objects/{quote(o.id, safe="")}/">Read source projection</a></p></article>' for o in docs) + '</div>'
    write_text(tmp / "docs" / "index.html", html_shell("Documentation", docs_body, base_url=base_url, markdown_url=f"{base_url}/docs/index.md"))
    write_text(tmp / "docs" / "index.md", "# Documentation\n\n" + "\n".join(f"- [{o.title}]({base_url}/objects/{quote(o.id, safe='')}/) — `{o.path}`" for o in docs) + "\n")

    status_md = (
        "# Epistemedia status\n\n"
        f"- Version: `{VERSION}`\n"
        f"- Catalog: `{catalog.catalog_id}`\n"
        f"- Frontier: `{catalog.frontier}`\n"
        f"- Commit: `{catalog.commit}`\n"
        f"- Public objects: `{len(catalog.objects)}`\n"
        f"- Topics: `{len(catalog.topics)}`\n"
        f"- Projections: `{projection_count}`\n"
    )
    write_text(tmp / "status" / "index.md", status_md)
    write_text(tmp / "status" / "index.html", html_shell("Status", md_to_html(status_md), base_url=base_url, markdown_url=f"{base_url}/status/index.md"))

    llms = [
        "# Epistemedia",
        "> Knowledge that can show its work. An open, federated knowledge network for humans and agents.",
        "",
        "## Start here",
        f"- [Project overview]({base_url}/index.md)",
        f"- [Documentation]({base_url}/docs/index.md)",
        f"- [Explore topics]({base_url}/explore/index.md)",
        f"- [Current status]({base_url}/status/index.md)",
        f"- [Public catalog]({base_url}/catalog.json)",
        f"- [OpenAPI]({api_url.rsplit('/v1',1)[0]}/openapi.json)",
        f"- [MCP server]({mcp_url})",
        "",
        "## Agent operating rule",
        "Treat pages as reproducible projections, not canonical truth. Preserve source, frontier, policy, disclosure boundary, compiler, and derivation metadata in downstream work.",
    ]
    write_text(tmp / "llms.txt", "\n".join(llms) + "\n")
    write_text(tmp / "docs" / "llms.txt", "# Epistemedia documentation\n\n" + "\n".join(f"- [{o.title}]({base_url}/objects/{quote(o.id, safe='')}.md)" for o in docs) + "\n")
    write_text(tmp / "llms-full.txt", "# Epistemedia public project corpus\n\n" + "\n\n---\n\n".join(f"## {o.title}\n\nSource: `{o.path}`\n\n{o.text}" for o in catalog.objects) + "\n")

    openapi = openapi_document(base_url=base_url, api_url=api_url)
    write_json(tmp / "openapi.json", openapi)
    write_json(tmp / "api" / "openapi.json", openapi)
    write_json(tmp / ".well-known" / "epistemedia.json", {
        "schema": "https://epistemedia.com/schemas/discovery-v1.json",
        "name": "Epistemedia",
        "description": "Knowledge that can show its work.",
        "catalog_id": catalog.catalog_id,
        "frontier": catalog.frontier,
        "commit": catalog.commit,
        "human": base_url,
        "llms": f"{base_url}/llms.txt",
        "api": api_url,
        "openapi": f"{api_url.rsplit('/v1',1)[0]}/openapi.json",
        "mcp": mcp_url,
        "repository": "https://github.com/yoheinakajima/epistemedia",
        "protocol_version": PROTOCOL_VERSION,
        "representations": ["text/html", "text/markdown", "application/json", "application/ld+json"],
    })
    write_json(tmp / "mcp" / "server.json", mcp_descriptor(mcp_url))
    write_text(tmp / "robots.txt", "User-agent: *\nAllow: /\nSitemap: " + base_url + "/sitemap.xml\n")
    urls = [base_url + "/", base_url + "/docs/", base_url + "/explore/", base_url + "/status/"] + [f"{base_url}/topics/{topic.slug}/" for topic in catalog.topics]
    write_text(tmp / "sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(f"  <url><loc>{html.escape(url)}</loc></url>" for url in urls) + "\n</urlset>\n")
    write_text(tmp / ".well-known" / "security.txt", "Contact: https://github.com/yoheinakajima/epistemedia/security\nCanonical: " + base_url + "/.well-known/security.txt\n")

    inventory = []
    for path in sorted(tmp.rglob("*")):
        if path.is_file():
            rel = path.relative_to(tmp).as_posix()
            inventory.append({"path": rel, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size})
    manifest = {
        "schema": "https://epistemedia.com/schemas/release-manifest-v1.json",
        "catalog_id": catalog.catalog_id,
        "frontier": catalog.frontier,
        "commit": catalog.commit,
        "compiler": f"epistemedia/{VERSION}",
        "generated_at": catalog.generated_at,
        "base_url": base_url,
        "api_url": api_url,
        "mcp_url": mcp_url,
        "file_count": len(inventory) + 1,
        "files": inventory,
    }
    # Manifest ID intentionally excludes deployment URLs and generation time.
    manifest["manifest_id"] = stable_id("release-manifest", {
        "catalog_id": catalog.catalog_id,
        "frontier": catalog.frontier,
        "commit": catalog.commit,
        "files": [(item["path"], item["sha256"]) for item in inventory],
    })
    write_json(tmp / "manifest.json", manifest)

    if output.exists():
        shutil.rmtree(output)
    tmp.replace(output)
    return manifest


def openapi_document(*, base_url: str = DEFAULT_BASE_URL, api_url: str = DEFAULT_API_URL) -> dict[str, Any]:
    return {
        "openapi": "3.1.1",
        "info": {
            "title": "Epistemedia Public API",
            "version": VERSION,
            "description": "Free read access to disclosure-safe Epistemedia public projections.",
            "license": {"name": "Apache-2.0 and object-specific content licenses"},
        },
        "servers": [{"url": api_url}],
        "paths": {
            "/status": {"get": operation("Current public catalog status", "getStatus")},
            "/search": {"get": {**operation("Search public objects", "searchKnowledge"), "parameters": [{"name": "q", "in": "query", "required": True, "schema": {"type": "string"}}, {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20, "maximum": 100}}]}},
            "/topics": {"get": operation("List public topics", "listTopics")},
            "/topics/{slug}": {"get": {**operation("Get a topic projection", "getTopic"), "parameters": [{"name": "slug", "in": "path", "required": True, "schema": {"type": "string"}}, {"name": "lens", "in": "query", "schema": {"type": "string", "enum": sorted(LENSES), "default": "encyclopedia"}}]}},
            "/objects/{id}": {"get": {**operation("Get an exact public object", "getObject"), "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}]}},
            "/claims/{id}/trace": {"get": {**operation("Trace a claim or object to accepted sources and manifest data", "traceClaim"), "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}]}},
        },
        "components": {
            "schemas": {
                "Envelope": {
                    "type": "object",
                    "required": ["catalog_id", "frontier", "data"],
                    "properties": {
                        "catalog_id": {"type": "string"},
                        "frontier": {"type": "string"},
                        "commit": {"type": "string"},
                        "compiler": {"type": "string"},
                        "data": {},
                    },
                },
                "Error": {"type": "object", "required": ["error"], "properties": {"error": {"type": "string"}, "detail": {"type": "string"}}},
            }
        },
        "externalDocs": {"url": f"{base_url}/docs/"},
    }


def operation(summary: str, operation_id: str) -> dict[str, Any]:
    return {
        "summary": summary,
        "operationId": operation_id,
        "responses": {
            "200": {"description": "Disclosure-safe public response", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Envelope"}}}},
            "404": {"description": "Not found", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
        },
    }


def mcp_descriptor(mcp_url: str = DEFAULT_MCP_URL) -> dict[str, Any]:
    return {
        "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
        "name": "com.epistemedia/knowledge",
        "description": "Read and trace disclosure-safe Epistemedia knowledge projections.",
        "version": VERSION,
        "remotes": [{"type": "streamable-http", "url": mcp_url}],
        "repository": {"url": "https://github.com/yoheinakajima/epistemedia", "source": "github"},
    }


def validate_repository(root: Path) -> list[str]:
    errors: list[str] = []
    required = ["README.md", "AGENTS.md", "pyproject.toml"]
    for rel in required:
        if not (root / rel).exists():
            errors.append(f"missing required file: {rel}")
    try:
        catalog = PublicCatalog.build(root)
        if not catalog.objects:
            errors.append("public catalog contains no objects")
        if not catalog.topics:
            errors.append("public catalog contains no topics")
        ids = [obj.id for obj in catalog.objects]
        if len(ids) != len(set(ids)):
            errors.append("duplicate public object IDs")
        for obj in catalog.objects:
            if obj.visibility != "public":
                errors.append(f"non-public object entered PublicCatalog: {obj.path}")
            if not obj.content_digest:
                errors.append(f"object lacks content digest: {obj.path}")
    except Exception as exc:
        errors.append(str(exc))
    # Common secret patterns are hard failures in accepted text files.
    secret_patterns = [
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        re.compile(r"ghp_[A-Za-z0-9]{30,}"),
        re.compile(r"sk-[A-Za-z0-9]{30,}"),
    ]
    for path in root.rglob("*"):
        if not path.is_file() or not is_public_source(root, path):
            continue
        text = read_text(path)
        if any(pattern.search(text) for pattern in secret_patterns):
            errors.append(f"possible secret in {path.relative_to(root)}")
    return errors


def audit_public(root: Path, public: Path) -> list[str]:
    findings: list[str] = []
    catalog = PublicCatalog.build(root)
    catalog_path = public / "catalog.json"
    manifest_path = public / "manifest.json"
    if not catalog_path.exists():
        return ["missing generated catalog.json"]
    if not manifest_path.exists():
        return ["missing generated manifest.json"]
    generated = json.loads(catalog_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    if generated.get("catalog_id") != catalog.catalog_id:
        findings.append("generated catalog ID differs from current accepted inputs")
    if generated.get("frontier") != catalog.frontier:
        findings.append("generated frontier differs from current accepted inputs")
    if manifest.get("catalog_id") != catalog.catalog_id:
        findings.append("release manifest references another catalog")
    required = [
        public / "index.html",
        public / "llms.txt",
        public / "openapi.json",
        public / ".well-known" / "epistemedia.json",
        public / "mcp" / "server.json",
    ]
    for path in required:
        if not path.exists():
            findings.append(f"missing public interface: {path.relative_to(public)}")
    # Static public output must not contain obvious private path or key material.
    forbidden = ["/Users/", "C:\\Users\\", "PRIVATE KEY-----", "ghp_", "sk-"]
    for path in public.rglob("*"):
        if not path.is_file() or path.stat().st_size > 5_000_000:
            continue
        try:
            text = path.read_text(errors="ignore")
        except Exception:
            continue
        for token in forbidden:
            if token in text:
                findings.append(f"public disclosure finding in {path.relative_to(public)}: {token}")
    return sorted(set(findings))


def envelope(catalog: PublicCatalog, data: Any) -> dict[str, Any]:
    return {
        "catalog_id": catalog.catalog_id,
        "frontier": catalog.frontier,
        "commit": catalog.commit,
        "compiler": f"epistemedia/{VERSION}",
        "data": data,
    }


def discover_root(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()
    for candidate in [start, *start.parents]:
        if (candidate / "pyproject.toml").exists() and (candidate / "AGENTS.md").exists():
            return candidate
    raise FileNotFoundError("not inside an Epistemedia repository; pass --root")
