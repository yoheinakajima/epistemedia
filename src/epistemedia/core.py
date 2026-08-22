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
from typing import Any
from urllib.parse import quote

VERSION = "0.2.0"
PROTOCOL_VERSION = "2026-07-28"
DEFAULT_BASE_URL = "https://epistemedia.org"
DEFAULT_API_URL = "https://api.epistemedia.org/v1"
DEFAULT_MCP_URL = "https://mcp.epistemedia.org/mcp"

LENSES: dict[str, str] = {
    "encyclopedia": "The current default repository-object projection over the shared inventory.",
    "evidence-first": (
        "Experimental identifier reserved for foregrounding primary evidence; currently uses "
        "the shared inventory."
    ),
    "skeptical": (
        "Experimental identifier reserved for stronger support thresholds; currently uses the "
        "shared inventory."
    ),
    "frontier": (
        "Experimental identifier reserved for open questions and disputes; currently uses the "
        "shared inventory."
    ),
    "historical": (
        "Experimental identifier reserved for time-bounded views; currently uses the shared "
        "inventory."
    ),
    "pedagogical": (
        "Experimental identifier reserved for prerequisite-aware explanations; currently uses "
        "the shared inventory."
    ),
    "source-only": (
        "Experimental identifier reserved for exact-source views; currently uses the shared "
        "inventory."
    ),
}

SITE_CSS = """
:root{
  color-scheme:light;
  --paper:#f3f0e6;
  --paper-raised:#fffdf6;
  --paper-deep:#e9e4d5;
  --ink:#171a15;
  --muted:#5e6259;
  --forest:#274c3a;
  --forest-deep:#163426;
  --amber:#a96512;
  --amber-wash:#f5e4bd;
  --rule:#c9c4b5;
  --code:#e8e4d8;
  --serif:ui-serif,Georgia,Cambria,"Times New Roman",serif;
  --sans:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  --space-1:.35rem;
  --space-2:.65rem;
  --space-3:1rem;
  --space-4:1.5rem;
  --space-5:2.25rem;
  --space-6:3.25rem;
  --measure:72ch;
  --page:1180px;
}
*{box-sizing:border-box}
html{background:var(--paper);scroll-padding-top:1rem}
body{
  margin:0;
  border-top:4px solid;
  border-image:linear-gradient(90deg,var(--forest) 0 78%,var(--amber) 78% 100%) 1;
  background:
    linear-gradient(90deg,rgba(39,76,58,.025) 1px,transparent 1px) 0 0/24px 24px,
    var(--paper);
  color:var(--ink);
  font:16px/1.58 var(--sans);
  text-rendering:optimizeLegibility;
}
a{color:var(--forest-deep);text-decoration-thickness:1px;text-underline-offset:3px}
a:hover{text-decoration-thickness:2px}
a:focus-visible,summary:focus-visible{
  outline:3px solid var(--amber);
  outline-offset:4px;
  border-radius:1px;
}
.skip-link{
  position:fixed;
  z-index:10;
  top:.5rem;
  left:.75rem;
  transform:translateY(-180%);
  background:var(--ink);
  color:var(--paper-raised);
  padding:.55rem .8rem;
}
.skip-link:focus{transform:none}
.site-header,main,.site-footer{
  width:min(100% - 2.5rem,var(--page));
  margin-inline:auto;
}
.site-header{
  min-height:62px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:var(--space-3);
  border-bottom:1px solid var(--rule);
}
.brand{
  display:inline-flex;
  align-items:center;
  gap:.55rem;
  color:var(--ink);
  font-weight:760;
  letter-spacing:-.015em;
  text-decoration:none;
}
.brand-mark{
  display:inline-grid;
  place-items:center;
  width:1.85rem;
  height:1.85rem;
  border:1px solid var(--forest);
  background:var(--forest);
  color:var(--paper-raised);
  font:700 .75rem/1 var(--mono);
  letter-spacing:-.08em;
}
nav{display:flex;align-items:center;gap:1.1rem}
nav a{
  color:var(--ink);
  font-size:.82rem;
  font-weight:720;
  letter-spacing:.055em;
  text-decoration:none;
  text-transform:uppercase;
}
nav a:hover{text-decoration:underline}
main{padding-block:0 var(--space-6)}
.site-footer{
  display:grid;
  grid-template-columns:1fr auto;
  gap:var(--space-4);
  padding-block:var(--space-4);
  border-top:1px solid var(--rule);
  color:var(--muted);
  font-size:.83rem;
}
.site-footer p{margin:0}
p,li,blockquote{max-width:var(--measure)}
h1,h2,h3,h4,h5,h6{
  margin:0 0 .55em;
  color:var(--ink);
  font-family:var(--serif);
  line-height:1.04;
  text-wrap:balance;
}
h1{max-width:18ch;font-size:clamp(2.45rem,6vw,5.25rem);letter-spacing:-.045em}
h2{font-size:clamp(1.55rem,2.3vw,2.15rem);letter-spacing:-.025em}
h3{font-size:1.28rem}
h4{font-size:1.08rem}
.hero{padding:var(--space-5) 0 var(--space-4);border-bottom:1px solid var(--rule)}
.hero-home{padding-top:clamp(2.25rem,5vw,4rem)}
.hero-home h1{max-width:14ch}
.hero-compact{padding-bottom:var(--space-3)}
.dek{margin:.35rem 0 var(--space-3);max-width:760px;color:var(--muted);font-size:1.16rem}
.eyebrow,.meta,.docket-number{
  margin:0 0 .65rem;
  color:var(--muted);
  font:700 .72rem/1.35 var(--mono);
  letter-spacing:.085em;
  text-transform:uppercase;
}
.docket-number{color:var(--forest)}
.scope-note{
  display:grid;
  grid-template-columns:auto 1fr;
  gap:.7rem;
  max-width:900px;
  margin:var(--space-3) 0 0;
  padding:.8rem 0 .8rem var(--space-3);
  border-left:4px solid var(--amber);
  background:linear-gradient(90deg,var(--amber-wash),transparent 88%);
}
.scope-note strong{font:700 .72rem/1.55 var(--mono);letter-spacing:.055em;text-transform:uppercase}
section+section{margin-top:var(--space-5)}
.section-head{
  display:flex;
  align-items:end;
  justify-content:space-between;
  gap:var(--space-3);
  margin-bottom:var(--space-3);
  border-bottom:1px solid var(--ink);
}
.section-head h2{margin-bottom:.45rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,245px),1fr));gap:.75rem}
.card{
  position:relative;
  display:flex;
  min-width:0;
  min-height:190px;
  flex-direction:column;
  padding:1rem;
  border:1px solid var(--rule);
  border-top:3px solid var(--forest);
  border-radius:2px;
  background:rgba(255,253,246,.78);
}
.card h2{font-size:1.28rem;line-height:1.08}
.card>p:not(.card-meta):not(.docket-number){margin:.2rem 0 var(--space-3);color:var(--muted)}
.card-meta{
  display:flex;
  flex-wrap:wrap;
  gap:.35rem .75rem;
  margin:auto 0 0;
  padding-top:.7rem;
  border-top:1px solid var(--rule);
  color:var(--muted);
  font:650 .68rem/1.35 var(--mono);
  letter-spacing:.025em;
}
.card:focus-within{outline:3px solid var(--amber);outline-offset:2px}
.lens-status{
  border:1px solid var(--rule);
  border-left:4px solid var(--amber);
  background:var(--paper-raised);
  padding:.85rem 1rem;
  margin:var(--space-4) 0;
}
.lens-status summary{cursor:pointer;font-weight:760}
.lens-status p:last-child{margin-bottom:0}
.projection-receipt{
  margin-top:var(--space-5);
  border:1px solid var(--ink);
  border-top:5px solid var(--forest);
  background:var(--paper-raised);
  box-shadow:6px 6px 0 var(--paper-deep);
}
.receipt-head{
  display:flex;
  align-items:start;
  justify-content:space-between;
  gap:var(--space-3);
  padding:1rem;
  border-bottom:1px solid var(--rule);
}
.receipt-head h2{margin:0;font-size:1.45rem}
.stamp{
  flex:0 0 auto;
  padding:.35rem .5rem;
  border:2px solid var(--forest);
  color:var(--forest-deep);
  font:750 .65rem/1.2 var(--mono);
  letter-spacing:.08em;
  text-transform:uppercase;
}
.receipt-grid{display:grid;margin:0}
.receipt-grid>div{
  display:grid;
  grid-template-columns:minmax(110px,.22fr) 1fr;
  gap:var(--space-3);
  padding:.7rem 1rem;
  border-top:1px solid var(--rule);
}
.receipt-grid>div:first-child{border-top:0}
.receipt-grid dt{color:var(--muted);font:700 .7rem/1.5 var(--mono);letter-spacing:.06em;text-transform:uppercase}
.receipt-grid dd{min-width:0;margin:0}
.object-facts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.5rem 1rem;margin:var(--space-3) 0 0}
.object-facts>div{min-width:0;padding:.55rem 0;border-top:1px solid var(--rule)}
.object-facts dt{color:var(--muted);font:700 .68rem/1.5 var(--mono);letter-spacing:.05em;text-transform:uppercase}
.object-facts dd{margin:.2rem 0 0;overflow-wrap:anywhere;word-break:break-word}
.source-document{padding-top:var(--space-4)}
.source-document>h2{padding-bottom:.45rem;border-bottom:1px solid var(--ink)}
.status-list{border-top:1px solid var(--ink)}
.status-row{display:grid;grid-template-columns:150px 1fr auto;gap:var(--space-3);align-items:start;padding:.8rem 0;border-bottom:1px solid var(--rule)}
.status-name{font-weight:750}
.status-value{min-width:0;overflow-wrap:anywhere;word-break:break-word}
.status-label{font:750 .66rem/1.3 var(--mono);letter-spacing:.06em;text-transform:uppercase}
.status-live{color:var(--forest-deep)}
.status-reserved{color:#704406}
code,pre{background:var(--code);font-family:var(--mono)}
code{padding:.1rem .28rem;border-radius:2px;overflow-wrap:anywhere;word-break:break-word}
pre{max-width:100%;padding:1rem;overflow:auto;border:1px solid var(--rule);border-radius:2px}
pre code{padding:0;overflow-wrap:normal;word-break:normal}
blockquote{margin-left:0;padding:.35rem 0 .35rem 1rem;border-left:4px solid var(--amber);color:var(--muted)}
.manifest{border-top:1px solid var(--rule);margin-top:var(--space-5);padding-top:var(--space-3)}
@media (max-width:640px){
  .site-header,main,.site-footer{width:min(100% - 2rem,var(--page))}
  .site-header{min-height:58px;gap:.65rem}
  .brand{font-size:.9rem}
  .brand-mark{width:1.65rem;height:1.65rem}
  nav{gap:.7rem}
  nav a{font-size:.68rem}
  .hero{padding:1.8rem 0 1.2rem}
  .hero-home{padding-top:2.2rem}
  .scope-note{grid-template-columns:1fr;gap:.15rem}
  .section-head{align-items:start;flex-direction:column;gap:0}
  .card{min-height:0}
  .receipt-head{align-items:stretch;flex-direction:column}
  .stamp{align-self:start}
  .receipt-grid>div{grid-template-columns:1fr;gap:.2rem}
  .object-facts{grid-template-columns:1fr}
  .status-row{grid-template-columns:1fr;gap:.2rem}
  .status-label{justify-self:start}
  .site-footer{grid-template-columns:1fr}
}
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
""".strip()

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


def accepted_commit(root: Path) -> str:
    """Return Git HEAD or a validated immutable build-time fallback."""
    value = git_value(root, "rev-parse", "HEAD", default="")
    if value:
        return value
    value = os.environ.get("EPISTEMEDIA_ACCEPTED_COMMIT", "")
    if not value:
        return "unknown"
    if re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise ValueError("accepted commit must be exactly 40 lowercase hexadecimal characters")
    return value


def accepted_timestamp(root: Path) -> str:
    """Return the accepted commit time used by reproducible public projections."""
    value = git_value(root, "show", "-s", "--format=%ct", "HEAD", default="")
    if not value:
        value = os.environ.get("SOURCE_DATE_EPOCH", "0")
    if re.fullmatch(r"0|[1-9][0-9]*", value) is None:
        raise ValueError("accepted source timestamp must be non-negative Unix epoch seconds")
    try:
        accepted = datetime.fromtimestamp(int(value), timezone.utc)
    except (OverflowError, OSError, ValueError) as exc:
        raise ValueError("accepted source timestamp is outside the supported range") from exc
    return accepted.replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def static_object_file_key(object_id: str) -> str:
    """Return a cross-platform filename for a protocol object ID."""
    return quote(object_id, safe="")


def static_object_route_key(object_id: str) -> str:
    """Encode the filename for one URL-decoding pass by a static host."""
    return quote(static_object_file_key(object_id), safe="")


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
        commit = accepted_commit(root)
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
            generated_at=accepted_timestamp(root),
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


def html_shell(
    title: str,
    body: str,
    *,
    base_url: str,
    canonical_url: str,
    markdown_url: str | None = None,
) -> str:
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
<link rel="canonical" href="{html.escape(canonical_url)}">
<link rel="describedby" href="{html.escape(base_url)}/llms.txt">
{alternates}
<style>{SITE_CSS}</style>
</head>
<body>
<a class="skip-link" href="#content">Skip to content</a>
<header class="site-header">
  <a class="brand" href="{html.escape(base_url)}/" aria-label="Epistemedia home"><span class="brand-mark" aria-hidden="true">E/</span><span>Epistemedia</span></a>
  <nav aria-label="Primary"><a href="{html.escape(base_url)}/explore/">Explore</a><a href="{html.escape(base_url)}/docs/">Docs</a><a href="{html.escape(base_url)}/status/">Status</a></nav>
</header>
<main id="content" tabindex="-1">{body}</main>
<footer class="site-footer"><p><strong>Knowledge that can show its work.</strong><br>Human and agent interfaces compile from one public projection.</p><p><a href="https://github.com/yoheinakajima/epistemedia">Source repository</a></p></footer>
</body></html>
"""


def md_to_html(text: str, *, heading_offset: int = 0) -> str:
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
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            level = min(6, len(heading.group(1)) + heading_offset)
            out.append(f"<h{level}>{inline_md(heading.group(2))}</h{level}>")
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


def projection_markdown(
    projection: dict[str, Any], *, include_topic_intro: bool = True, include_manifest: bool = True
) -> str:
    topic = projection["topic"]
    lines = []
    if include_topic_intro:
        lines += [
            f"# {topic['title']}",
            "",
            topic.get("description", ""),
            "",
        ]
    lines += [
        f"**Lens:** `{projection['lens']['id']}` — {projection['lens']['description']}",
        "",
        "**Lens status:** Experimental manifest. Current lens policies preserve the same included-object inventory; the label does not yet indicate a materially differentiated editorial result.",
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
    if include_manifest:
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


def projection_receipt_html(
    *,
    catalog_id: str,
    frontier: str,
    commit: str,
    compiler: str,
    projection_id: str | None = None,
    epistemic_policy: str | None = None,
    disclosure_policy: str | None = None,
) -> str:
    rows = []
    if projection_id:
        rows.append(("Projection", projection_id))
    rows.extend(
        [
            ("Catalog", catalog_id),
            ("Frontier", frontier),
            ("Accepted commit", commit),
        ]
    )
    if epistemic_policy:
        rows.append(("Epistemic policy", epistemic_policy))
    if disclosure_policy:
        rows.append(("Disclosure policy", disclosure_policy))
    rows.append(("Compiler", compiler))
    rendered_rows = "".join(
        f"<div><dt>{html.escape(label)}</dt><dd><code>{html.escape(value)}</code></dd></div>"
        for label, value in rows
    )
    return (
        '<section class="projection-receipt" aria-labelledby="projection-receipt-title">'
        '<div class="receipt-head"><div><p class="eyebrow">Build receipt</p>'
        '<h2 id="projection-receipt-title">Reproduce this projection</h2></div>'
        '<span class="stamp">Reproducible projection</span></div>'
        f'<dl class="receipt-grid">{rendered_rows}</dl></section>'
    )


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
        file_key = static_object_file_key(obj.id)
        route_key = static_object_route_key(obj.id)
        write_json(tmp / "objects" / f"{file_key}.json", obj.as_dict())
        markdown = (
            f"# {obj.title}\n\n"
            f"- Object ID: `{obj.id}`\n"
            f"- Kind: `{obj.kind}`\n"
            f"- Repository path: `{obj.path}`\n"
            f"- Content digest: `{obj.content_digest}`\n\n"
            f"## Source content\n\n{obj.text.rstrip()}\n"
        )
        write_text(tmp / "objects" / f"{file_key}.md", markdown)
        summary = (
            f'<p class="dek">{html.escape(obj.summary)}</p>' if obj.summary else ""
        )
        body = (
            '<article class="object-page">'
            f'<section class="hero hero-compact"><p class="eyebrow">Repository object · {html.escape(obj.kind)}</p>'
            f'<h1>{html.escape(obj.title)}</h1>{summary}'
            '<dl class="object-facts">'
            f'<div><dt>Source path</dt><dd><code>{html.escape(obj.path)}</code></dd></div>'
            f'<div><dt>Media type</dt><dd><code>{html.escape(obj.media_type)}</code></dd></div>'
            f'<div><dt>Object ID</dt><dd><code>{html.escape(obj.id)}</code></dd></div>'
            f'<div><dt>Content digest</dt><dd><code>{html.escape(obj.content_digest)}</code></dd></div>'
            '</dl></section><section class="source-document" aria-labelledby="source-content-title">'
            '<h2 id="source-content-title">Source content</h2>'
            + md_to_html(obj.text, heading_offset=2)
            + "</section>"
            + projection_receipt_html(
                catalog_id=catalog.catalog_id,
                frontier=catalog.frontier,
                commit=catalog.commit,
                epistemic_policy=catalog.policies["epistemic"],
                disclosure_policy=catalog.policies["disclosure"],
                compiler=f"epistemedia/{VERSION}",
            )
            + "</article>"
        )
        write_text(
            tmp / "objects" / file_key / "index.html",
            html_shell(
                obj.title,
                body,
                base_url=base_url,
                canonical_url=f"{base_url}/objects/{route_key}/",
                markdown_url=f"{base_url}/objects/{route_key}.md",
            ),
        )

    projection_count = 0
    topic_cards = []
    for topic_index, topic in enumerate(catalog.topics, start=1):
        selected = catalog.selected_objects(topic)
        topic_cards.append(
            f'<article class="card docket-card"><p class="docket-number">Topic {topic_index:02d}</p>'
            f'<h2><a href="{base_url}/topics/{topic.slug}/">{html.escape(topic.title)}</a></h2>'
            f'<p>{html.escape(topic.description)}</p><p class="card-meta"><span>{len(selected)} public objects</span>'
            '<span>Encyclopedia projection</span></p></article>'
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
                    '<aside class="lens-status"><strong>Experimental lens manifest.</strong> '
                    "Current lenses preserve the same included-object inventory; this label changes "
                    "the projection manifest, not a differentiated editorial result.</aside>"
                    + md_to_html(projection_markdown(projection, include_manifest=False))
                    + projection_receipt_html(
                        projection_id=projection["projection_id"],
                        catalog_id=projection["catalog_id"],
                        frontier=projection["frontier"],
                        commit=projection["commit"],
                        epistemic_policy=projection["policies"]["epistemic"],
                        disclosure_policy=projection["policies"]["disclosure"],
                        compiler=projection["compiler"],
                    ),
                    base_url=base_url,
                    canonical_url=f"{base_url}/topics/{topic.slug}/{lens}/",
                    markdown_url=f"{base_url}/topics/{topic.slug}/{lens}/index.md",
                ),
            )
        default_projection = topic_projection(catalog, topic, "encyclopedia", base_url)
        md = projection_markdown(default_projection)
        lens_links = " ".join(
            f'<a href="{base_url}/topics/{topic.slug}/{lens}/">{html.escape(lens)}</a>'
            for lens in LENSES
            if lens != "encyclopedia"
        )
        body = (
            f'<section class="hero hero-compact"><p class="eyebrow">Current projection · encyclopedia</p><h1>{html.escape(topic.title)}</h1>'
            f'<p class="dek">{html.escape(topic.description)}</p></section>'
            '<details class="lens-status"><summary>Experimental lens manifests (shared inventory)</summary>'
            '<p>These routes currently preserve the same included-object inventory. Their labels and '
            'manifest identities differ; they are not yet materially different editorial products.</p>'
            f'<p>{lens_links}</p></details>'
            + md_to_html(
                projection_markdown(
                    default_projection,
                    include_topic_intro=False,
                    include_manifest=False,
                )
            )
            + projection_receipt_html(
                projection_id=default_projection["projection_id"],
                catalog_id=default_projection["catalog_id"],
                frontier=default_projection["frontier"],
                commit=default_projection["commit"],
                epistemic_policy=default_projection["policies"]["epistemic"],
                disclosure_policy=default_projection["policies"]["disclosure"],
                compiler=default_projection["compiler"],
            )
        )
        write_text(
            tmp / "topics" / topic.slug / "index.html",
            html_shell(
                topic.title,
                body,
                base_url=base_url,
                canonical_url=f"{base_url}/topics/{topic.slug}/",
                markdown_url=f"{base_url}/topics/{topic.slug}/index.md",
            ),
        )
        write_text(tmp / "topics" / topic.slug / "index.md", md)

    home_body = (
        '<section class="hero hero-home"><p class="eyebrow">Open knowledge · Public alpha</p>'
        '<h1>Knowledge that can show its work.</h1>'
        '<p class="dek">Epistemedia currently compiles accepted repository artifacts into reproducible human and machine-readable views. Its next public realm will test exact source-to-claim lineage.</p>'
        '<p class="scope-note"><strong>Current coverage:</strong><span>Epistemedia\'s own architecture and operations—the self-describing bootstrap corpus. The first outward-facing realm, <em>How We Know</em>, is in development.</span></p></section>'
        '<section><div class="section-head"><div><p class="eyebrow">Current index</p><h2>Explore the bootstrap corpus</h2></div>'
        f'<p class="meta">{len(catalog.topics)} topics · {len(catalog.objects)} public objects</p></div><div class="grid">'
        + "".join(topic_cards)
        + '</div></section>'
        + projection_receipt_html(
            catalog_id=catalog.catalog_id,
            frontier=catalog.frontier,
            commit=catalog.commit,
            epistemic_policy=catalog.policies["epistemic"],
            disclosure_policy=catalog.policies["disclosure"],
            compiler=f"epistemedia/{VERSION}",
        )
    )
    write_text(
        tmp / "index.html",
        html_shell(
            "Knowledge that can show its work",
            home_body,
            base_url=base_url,
            canonical_url=f"{base_url}/",
            markdown_url=f"{base_url}/index.md",
        ),
    )
    write_text(
        tmp / "index.md",
        "# Epistemedia\n\nKnowledge that can show its work.\n\n"
        "**Current coverage:** Epistemedia's own architecture and operations—the "
        "self-describing bootstrap corpus. The first outward-facing realm, *How We Know*, "
        "is in development.\n\n"
        + "\n".join(
            f"- [{t.title}]({base_url}/topics/{t.slug}/) — {t.description}"
            for t in catalog.topics
        )
        + "\n",
    )

    explore_body = (
        '<section class="hero hero-compact"><p class="eyebrow">Repository index</p><h1>Explore</h1>'
        '<p class="dek">Browse topics and the exact public objects used to compile them.</p></section>'
        '<section aria-label="Bootstrap topics"><div class="grid">'
        + "".join(topic_cards)
        + "</div></section>"
        + projection_receipt_html(
            catalog_id=catalog.catalog_id,
            frontier=catalog.frontier,
            commit=catalog.commit,
            epistemic_policy=catalog.policies["epistemic"],
            disclosure_policy=catalog.policies["disclosure"],
            compiler=f"epistemedia/{VERSION}",
        )
    )
    write_text(
        tmp / "explore" / "index.html",
        html_shell(
            "Explore",
            explore_body,
            base_url=base_url,
            canonical_url=f"{base_url}/explore/",
            markdown_url=f"{base_url}/explore/index.md",
        ),
    )
    write_text(tmp / "explore" / "index.md", "# Explore\n\n" + "\n".join(f"- [{t.title}]({base_url}/topics/{t.slug}/)" for t in catalog.topics) + "\n")

    docs = [
        obj
        for obj in catalog.objects
        if obj.kind == "documentation" or obj.path in ("README.md", "AGENTS.md")
    ]
    docs_cards = "".join(
        f'<article class="card docket-card"><p class="docket-number">Document {index:02d}</p>'
        f'<h2><a href="{base_url}/objects/{static_object_route_key(obj.id)}/">{html.escape(obj.title)}</a></h2>'
        f'<p>{html.escape(obj.summary)}</p><p class="card-meta"><span>{html.escape(obj.path)}</span></p></article>'
        for index, obj in enumerate(docs, start=1)
    )
    docs_body = (
        '<section class="hero hero-compact"><p class="eyebrow">Operating library</p><h1>Documentation</h1>'
        '<p class="dek">Human guidance and machine-operable project contracts, compiled from accepted repository content.</p></section>'
        f'<section aria-label="Project documentation"><div class="grid">{docs_cards}</div></section>'
        + projection_receipt_html(
            catalog_id=catalog.catalog_id,
            frontier=catalog.frontier,
            commit=catalog.commit,
            epistemic_policy=catalog.policies["epistemic"],
            disclosure_policy=catalog.policies["disclosure"],
            compiler=f"epistemedia/{VERSION}",
        )
    )
    write_text(
        tmp / "docs" / "index.html",
        html_shell(
            "Documentation",
            docs_body,
            base_url=base_url,
            canonical_url=f"{base_url}/docs/",
            markdown_url=f"{base_url}/docs/index.md",
        ),
    )
    write_text(tmp / "docs" / "index.md", "# Documentation\n\n" + "\n".join(f"- [{o.title}]({base_url}/objects/{static_object_route_key(o.id)}/) — `{o.path}`" for o in docs) + "\n")

    status_md = (
        "# Epistemedia status\n\n"
        "- Canonical human site: `https://epistemedia.org` — verified live with HTTPS\n"
        "- Sharing redirect: `https://episte.media` — reserved, not verified live\n"
        "- Hosted API: `https://api.epistemedia.org/v1` — reserved, not verified live\n"
        "- Hosted MCP: `https://mcp.epistemedia.org/mcp` — reserved, not verified live\n"
        "- Corpus scope: self-describing repository bootstrap; `How We Know` is in development\n"
        f"- Version: `{VERSION}`\n"
        f"- Catalog: `{catalog.catalog_id}`\n"
        f"- Frontier: `{catalog.frontier}`\n"
        f"- Commit: `{catalog.commit}`\n"
        f"- Public objects: `{len(catalog.objects)}`\n"
        f"- Topics: `{len(catalog.topics)}`\n"
        f"- Projections: `{projection_count}`\n"
    )
    write_text(tmp / "status" / "index.md", status_md)
    status_rows = "".join(
        [
            '<div class="status-row"><span class="status-name">Canonical human site</span>'
            '<span class="status-value"><code>https://epistemedia.org</code></span>'
            '<span class="status-label status-live">Verified live · HTTPS</span></div>',
            '<div class="status-row"><span class="status-name">Sharing redirect</span>'
            '<span class="status-value"><code>https://episte.media</code></span>'
            '<span class="status-label status-reserved">Reserved · unverified</span></div>',
            '<div class="status-row"><span class="status-name">Hosted API</span>'
            '<span class="status-value"><code>https://api.epistemedia.org/v1</code></span>'
            '<span class="status-label status-reserved">Reserved · unverified</span></div>',
            '<div class="status-row"><span class="status-name">Hosted MCP</span>'
            '<span class="status-value"><code>https://mcp.epistemedia.org/mcp</code></span>'
            '<span class="status-label status-reserved">Reserved · unverified</span></div>',
        ]
    )
    status_body = (
        '<section class="hero hero-compact"><p class="eyebrow">Provider read-back + build identity</p>'
        '<h1>Status</h1><p class="dek">Live means externally observed. Reserved destinations are not presented as deployed services.</p></section>'
        '<section aria-labelledby="surface-status-title"><div class="section-head"><div>'
        '<p class="eyebrow">Service boundary</p><h2 id="surface-status-title">Public surfaces</h2>'
        f'</div></div><div class="status-list">{status_rows}</div></section>'
        '<section aria-labelledby="build-summary-title"><div class="section-head"><div>'
        '<p class="eyebrow">Current compilation</p><h2 id="build-summary-title">Bootstrap corpus</h2>'
        '</div></div><dl class="object-facts">'
        f'<div><dt>Version</dt><dd><code>{VERSION}</code></dd></div>'
        f'<div><dt>Public objects</dt><dd>{len(catalog.objects)}</dd></div>'
        f'<div><dt>Topics</dt><dd>{len(catalog.topics)}</dd></div>'
        f'<div><dt>Projections</dt><dd>{projection_count}</dd></div>'
        '</dl><p class="scope-note"><strong>Current coverage:</strong><span>Self-describing repository bootstrap. <em>How We Know</em> is in development.</span></p></section>'
        + projection_receipt_html(
            catalog_id=catalog.catalog_id,
            frontier=catalog.frontier,
            commit=catalog.commit,
            epistemic_policy=catalog.policies["epistemic"],
            disclosure_policy=catalog.policies["disclosure"],
            compiler=f"epistemedia/{VERSION}",
        )
    )
    write_text(
        tmp / "status" / "index.html",
        html_shell(
            "Status",
            status_body,
            base_url=base_url,
            canonical_url=f"{base_url}/status/",
            markdown_url=f"{base_url}/status/index.md",
        ),
    )

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
        f"- [Static OpenAPI contract — hosted API not live]({base_url}/openapi.json)",
        f"- [Static MCP descriptor — remote MCP not live]({base_url}/mcp/server.json)",
        "",
        "## Agent operating rule",
        "Treat pages as reproducible projections, not canonical truth. Preserve repository path, object ID, content digest, catalog, frontier, policy, disclosure boundary, and compiler metadata in downstream work.",
    ]
    write_text(tmp / "llms.txt", "\n".join(llms) + "\n")
    write_text(tmp / "docs" / "llms.txt", "# Epistemedia documentation\n\n" + "\n".join(f"- [{o.title}]({base_url}/objects/{static_object_route_key(o.id)}.md)" for o in docs) + "\n")
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
        "openapi": f"{base_url}/openapi.json",
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
                    "required": [
                        "catalog_id",
                        "frontier",
                        "commit",
                        "policies",
                        "compiler",
                        "content_digest",
                        "data",
                    ],
                    "properties": {
                        "catalog_id": {"type": "string"},
                        "frontier": {"type": "string"},
                        "commit": {"type": "string"},
                        "policies": {"type": "object"},
                        "compiler": {"type": "string"},
                        "content_digest": {"type": "string"},
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
        "policies": catalog.policies,
        "compiler": f"epistemedia/{VERSION}",
        "content_digest": digest(data),
        "data": data,
    }


def discover_root(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()
    for candidate in [start, *start.parents]:
        if (candidate / "pyproject.toml").exists() and (candidate / "AGENTS.md").exists():
            return candidate
    raise FileNotFoundError("not inside an Epistemedia repository; pass --root")
