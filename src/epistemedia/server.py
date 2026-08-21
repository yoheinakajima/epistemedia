from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote

from .core import (
    DEFAULT_API_URL,
    DEFAULT_BASE_URL,
    DEFAULT_MCP_URL,
    LENSES,
    PROTOCOL_VERSION,
    VERSION,
    PublicCatalog,
    discover_root,
    envelope,
    mcp_descriptor,
    openapi_document,
    topic_projection,
)


@dataclass
class Request:
    method: str
    path: str
    query: dict[str, list[str]]
    headers: dict[str, str]
    body: bytes


class Gateway:
    """Dependency-free ASGI gateway over one disclosure-safe PublicCatalog."""

    def __init__(self, root: Path | None = None) -> None:
        configured = os.environ.get("EPISTEMEDIA_ROOT")
        self.root = Path(configured).resolve() if configured else (root or discover_root())
        self._catalog: PublicCatalog | None = None
        self._fingerprint: tuple[str, int] | None = None

    def catalog(self) -> PublicCatalog:
        # Reload when Git HEAD or the topics manifest changes. Production deployments normally
        # pin one immutable commit, while local development remains responsive.
        head = "unknown"
        git_head = self.root / ".git" / "HEAD"
        if git_head.exists():
            head = git_head.read_text(errors="ignore").strip()
        topics = self.root / "catalog" / "topics.json"
        mtime = topics.stat().st_mtime_ns if topics.exists() else 0
        fingerprint = (head, mtime)
        if self._catalog is None or fingerprint != self._fingerprint:
            self._catalog = PublicCatalog.build(self.root)
            self._fingerprint = fingerprint
        return self._catalog

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await send({"type": "http.response.start", "status": 404, "headers": []})
            await send({"type": "http.response.body", "body": b""})
            return
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                continue
            body.extend(message.get("body", b""))
            if not message.get("more_body", False):
                break
        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        request = Request(
            method=scope.get("method", "GET").upper(),
            path=scope.get("path", "/"),
            query=parse_qs(scope.get("query_string", b"").decode("utf-8")),
            headers=headers,
            body=bytes(body),
        )
        status, response_headers, payload = self.dispatch(request)
        encoded = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        default_headers = {
            "content-type": "application/json; charset=utf-8",
            "cache-control": "public, max-age=60",
            "access-control-allow-origin": "*",
            "x-epistemedia-catalog": self.catalog().catalog_id,
            "x-epistemedia-frontier": self.catalog().frontier,
        }
        default_headers.update(response_headers)
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [(k.encode("latin-1"), v.encode("latin-1")) for k, v in default_headers.items()],
        })
        await send({"type": "http.response.body", "body": encoded})

    def dispatch(self, request: Request) -> tuple[int, dict[str, str], Any]:
        if request.method == "OPTIONS":
            return 204, {
                "access-control-allow-methods": "GET, POST, OPTIONS",
                "access-control-allow-headers": "content-type,mcp-protocol-version,origin",
            }, b""
        if request.path in ("/healthz", "/v1/healthz"):
            return 200, {}, {"ok": True, "version": VERSION}
        if request.path in ("/openapi.json", "/v1/openapi.json"):
            return 200, {}, openapi_document()
        if request.path == "/mcp":
            return self.handle_mcp(request)
        if request.path.startswith("/v1/") or request.path == "/v1":
            return self.handle_api(request)
        return 404, {}, {"error": "not_found", "detail": "Use /v1, /openapi.json, or /mcp."}

    def handle_api(self, request: Request) -> tuple[int, dict[str, str], Any]:
        catalog = self.catalog()
        if request.method != "GET":
            return 405, {}, {"error": "method_not_allowed"}
        path = request.path.rstrip("/") or "/v1"
        if path == "/v1":
            return 200, {}, envelope(catalog, {
                "name": "Epistemedia Public API",
                "version": VERSION,
                "status": "/v1/status",
                "search": "/v1/search?q=...",
                "topics": "/v1/topics",
                "openapi": "/openapi.json",
                "mcp": "/mcp",
            })
        if path == "/v1/status":
            return 200, {}, envelope(catalog, {
                "version": VERSION,
                "protocol_version": PROTOCOL_VERSION,
                "object_count": len(catalog.objects),
                "topic_count": len(catalog.topics),
                "generated_at": catalog.generated_at,
            })
        if path == "/v1/search":
            query = first(request.query, "q", "")
            limit = clamp_int(first(request.query, "limit", "20"), 1, 100, 20)
            return 200, {}, envelope(catalog, {"query": query, "results": catalog.search(query, limit)})
        if path == "/v1/topics":
            return 200, {}, envelope(catalog, [topic.as_dict() for topic in catalog.topics])
        if path.startswith("/v1/topics/"):
            slug = unquote(path[len("/v1/topics/"):])
            topic = catalog.topic_map().get(slug)
            if not topic:
                return 404, {}, {"error": "not_found", "detail": f"Unknown topic: {slug}"}
            lens = first(request.query, "lens", "encyclopedia")
            if lens not in LENSES:
                return 400, {}, {"error": "invalid_lens", "allowed": sorted(LENSES)}
            return 200, {}, envelope(catalog, topic_projection(catalog, topic, lens, DEFAULT_BASE_URL))
        if path.startswith("/v1/objects/"):
            object_id = unquote(path[len("/v1/objects/"):])
            obj = catalog.object_map().get(object_id)
            if not obj:
                return 404, {}, {"error": "not_found", "detail": f"Unknown object: {object_id}"}
            return 200, {}, envelope(catalog, obj.as_dict())
        if path.startswith("/v1/claims/") and path.endswith("/trace"):
            object_id = unquote(path[len("/v1/claims/"):-len("/trace")].rstrip("/"))
            obj = catalog.object_map().get(object_id)
            if not obj:
                return 404, {}, {"error": "not_found", "detail": f"Unknown claim or object: {object_id}"}
            return 200, {}, envelope(catalog, {
                "subject": obj.as_dict(include_text=False),
                "accepted_source": {"repository_path": obj.path, "content_digest": obj.content_digest},
                "frontier": catalog.frontier,
                "policies": catalog.policies,
                "limitations": ["This repository-object trace is not evidence that the source content is true."],
            })
        return 404, {}, {"error": "not_found", "detail": path}

    def handle_mcp(self, request: Request) -> tuple[int, dict[str, str], Any]:
        if request.method != "POST":
            return 405, {}, self.rpc_error(None, -32600, "MCP requires POST")
        origin = request.headers.get("origin")
        allowed_origins = {
            "https://epistemedia.com",
            "https://www.epistemedia.com",
            "http://localhost",
            "http://127.0.0.1",
        }
        if origin and not any(origin == allowed or origin.startswith(allowed + ":") for allowed in allowed_origins):
            return 403, {}, self.rpc_error(None, -32003, "Origin is not allowed")
        try:
            message = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            return 400, {}, self.rpc_error(None, -32700, "Parse error")
        if not isinstance(message, dict):
            return 400, {}, self.rpc_error(None, -32600, "Invalid Request")
        request_id = message.get("id")
        method = message.get("method")
        params = message.get("params") or {}
        if method != "server/discover":
            version = request.headers.get("mcp-protocol-version") or params.get("protocolVersion")
            if version != PROTOCOL_VERSION:
                return 400, {}, self.rpc_error(
                    request_id,
                    -32001,
                    "UnsupportedProtocolVersion",
                    {"supported": [PROTOCOL_VERSION], "received": version},
                )
        try:
            result = self.mcp_method(method, params)
        except KeyError as exc:
            return 404, {}, self.rpc_error(request_id, -32004, "Not found", {"id": str(exc)})
        except ValueError as exc:
            return 400, {}, self.rpc_error(request_id, -32602, str(exc))
        if result is None and request_id is None:
            return 202, {"mcp-protocol-version": PROTOCOL_VERSION}, b""
        return 200, {
            "mcp-protocol-version": PROTOCOL_VERSION,
            "cache-control": "public, max-age=60",
        }, {"jsonrpc": "2.0", "id": request_id, "result": result}

    def mcp_method(self, method: str, params: dict[str, Any]) -> Any:
        catalog = self.catalog()
        if method == "server/discover":
            return {
                "protocolVersion": PROTOCOL_VERSION,
                "serverInfo": {"name": "com.epistemedia/knowledge", "title": "Epistemedia Knowledge", "version": VERSION},
                "capabilities": {"tools": {"listChanged": False}, "resources": {"listChanged": False}},
                "instructions": "Read-only access to disclosure-safe projections. Preserve catalog, frontier, policy, and source metadata in downstream use.",
                "descriptor": mcp_descriptor(DEFAULT_MCP_URL),
            }
        if method in ("notifications/initialized", "notifications/cancelled"):
            return None
        if method == "tools/list":
            return {
                "resultType": "complete",
                "ttlMs": 60000,
                "cacheScope": "public",
                "tools": tool_definitions(),
            }
        if method == "resources/list":
            resources = [
                {
                    "uri": f"epistemedia://topic/{topic.slug}",
                    "name": topic.slug,
                    "title": topic.title,
                    "description": topic.description,
                    "mimeType": "application/json",
                }
                for topic in catalog.topics
            ]
            resources += [
                {
                    "uri": f"epistemedia://object/{obj.id}",
                    "name": obj.id,
                    "title": obj.title,
                    "description": obj.summary,
                    "mimeType": "application/json",
                }
                for obj in catalog.objects
            ]
            return {"resultType": "complete", "ttlMs": 60000, "cacheScope": "public", "resources": resources}
        if method == "resources/read":
            uri = params.get("uri", "")
            data = self.read_resource(uri)
            return {
                "resultType": "complete",
                "contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(envelope(catalog, data), indent=2, sort_keys=True)}],
            }
        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            data = self.call_tool(name, arguments)
            return {
                "resultType": "complete",
                "content": [{"type": "text", "text": json.dumps(envelope(catalog, data), indent=2, sort_keys=True)}],
                "structuredContent": envelope(catalog, data),
                "isError": False,
            }
        raise ValueError(f"Method not found: {method}")

    def read_resource(self, uri: str) -> Any:
        catalog = self.catalog()
        if uri.startswith("epistemedia://topic/"):
            slug = uri.split("/", 3)[-1]
            topic = catalog.topic_map().get(slug)
            if not topic:
                raise KeyError(slug)
            return topic_projection(catalog, topic, "encyclopedia", DEFAULT_BASE_URL)
        if uri.startswith("epistemedia://object/"):
            object_id = uri[len("epistemedia://object/"):]
            obj = catalog.object_map().get(object_id)
            if not obj:
                raise KeyError(object_id)
            return obj.as_dict()
        if uri == "epistemedia://status":
            return catalog.public_dict()
        raise KeyError(uri)

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        catalog = self.catalog()
        if name == "search_knowledge":
            return {"query": arguments.get("query", ""), "results": catalog.search(str(arguments.get("query", "")), clamp_int(arguments.get("limit", 20), 1, 100, 20))}
        if name == "get_object":
            object_id = str(arguments.get("id", ""))
            obj = catalog.object_map().get(object_id)
            if not obj:
                raise KeyError(object_id)
            return obj.as_dict()
        if name == "get_topic":
            slug = str(arguments.get("slug", ""))
            lens = str(arguments.get("lens", "encyclopedia"))
            topic = catalog.topic_map().get(slug)
            if not topic:
                raise KeyError(slug)
            if lens not in LENSES:
                raise ValueError(f"Unknown lens: {lens}")
            return topic_projection(catalog, topic, lens, DEFAULT_BASE_URL)
        if name == "trace_claim":
            object_id = str(arguments.get("id", ""))
            obj = catalog.object_map().get(object_id)
            if not obj:
                raise KeyError(object_id)
            return {
                "subject": obj.as_dict(include_text=False),
                "source": {"repository_path": obj.path, "content_digest": obj.content_digest},
                "frontier": catalog.frontier,
                "policies": catalog.policies,
            }
        if name == "compare_lenses":
            slug = str(arguments.get("slug", ""))
            topic = catalog.topic_map().get(slug)
            if not topic:
                raise KeyError(slug)
            requested = arguments.get("lenses") or ["encyclopedia", "skeptical", "frontier"]
            unknown = [lens for lens in requested if lens not in LENSES]
            if unknown:
                raise ValueError("Unknown lenses: " + ", ".join(unknown))
            return {lens: topic_projection(catalog, topic, lens, DEFAULT_BASE_URL) for lens in requested}
        if name == "get_next_contribution":
            tasks = [obj.as_dict(include_text=False) for obj in catalog.objects if obj.kind == "task"]
            return {"tasks": tasks[:20], "rule": "Read the immutable task contract and AGENTS.md before claiming work."}
        if name == "validate_bundle":
            bundle = arguments.get("bundle")
            if not isinstance(bundle, dict):
                raise ValueError("bundle must be an object")
            required = ["schema", "objects", "manifest"]
            missing = [key for key in required if key not in bundle]
            return {"valid": not missing, "missing": missing, "note": "Structural validation only; this does not admit or endorse the bundle."}
        raise ValueError(f"Unknown tool: {name}")

    @staticmethod
    def rpc_error(request_id: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
        error: dict[str, Any] = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return {"jsonrpc": "2.0", "id": request_id, "error": error}


def tool_definitions() -> list[dict[str, Any]]:
    return [
        tool("search_knowledge", "Search disclosure-safe public objects.", {"query": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 100}}, ["query"]),
        tool("get_object", "Get one exact object and its source metadata.", {"id": {"type": "string"}}, ["id"]),
        tool("get_topic", "Compile one topic through a selected public lens.", {"slug": {"type": "string"}, "lens": {"type": "string", "enum": sorted(LENSES)}}, ["slug"]),
        tool("trace_claim", "Trace a repository claim/object to its accepted source and frontier.", {"id": {"type": "string"}}, ["id"]),
        tool("compare_lenses", "Compare policy-explicit projections without collapsing them.", {"slug": {"type": "string"}, "lenses": {"type": "array", "items": {"type": "string", "enum": sorted(LENSES)}}}, ["slug"]),
        tool("get_next_contribution", "List public task contracts suitable for an agent to inspect.", {}, []),
        tool("validate_bundle", "Perform non-admitting structural validation of a contribution bundle.", {"bundle": {"type": "object"}}, ["bundle"]),
    ]


def tool(name: str, description: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "title": name.replace("_", " ").title(),
        "description": description,
        "inputSchema": {"type": "object", "properties": properties, "required": required, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
    }


def first(query: dict[str, list[str]], key: str, default: str) -> str:
    values = query.get(key)
    return values[0] if values else default


def clamp_int(value: Any, minimum: int, maximum: int, default: int) -> int:
    try:
        return max(minimum, min(maximum, int(value)))
    except (TypeError, ValueError):
        return default


app = Gateway()
