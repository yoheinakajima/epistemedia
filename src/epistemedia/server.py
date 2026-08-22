from __future__ import annotations

import asyncio
import base64
import binascii
import json
import math
import os
import time
from collections import OrderedDict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

from .core import (
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
from .featured import FEATURE_VIEWS, FeaturedDossier, load_featured_dossier

DEFAULT_MAX_BODY_BYTES = 1_048_576
DEFAULT_MAX_QUERY_BYTES = 8_192
DEFAULT_MAX_RESPONSE_BYTES = 8_388_608
DEFAULT_RATE_LIMIT_PER_MINUTE = 120
DEFAULT_REQUEST_TIMEOUT_SECONDS = 15.0
DEFAULT_ALLOWED_ORIGINS = (
    "https://epistemedia.org",
    "https://www.epistemedia.org",
    "http://localhost",
    "http://127.0.0.1",
)
MCP_PROTOCOL_META = "io.modelcontextprotocol/protocolVersion"
MCP_CAPABILITIES_META = "io.modelcontextprotocol/clientCapabilities"
MCP_SERVER_INFO_META = "io.modelcontextprotocol/serverInfo"
MCP_SERVER_INFO = {
    "name": "com.epistemedia/knowledge",
    "title": "Epistemedia Knowledge",
    "version": VERSION,
}


class MCPRequestError(ValueError):
    def __init__(self, status: int, code: int, message: str, data: Any = None) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.data = data


@dataclass
class Request:
    method: str
    path: str
    query: dict[str, list[str]]
    headers: dict[str, str]
    body: bytes


class Gateway:
    """Dependency-free ASGI gateway over one disclosure-safe PublicCatalog."""

    def __init__(
        self,
        root: Path | None = None,
        *,
        max_body_bytes: int | None = None,
        max_query_bytes: int | None = None,
        max_response_bytes: int | None = None,
        rate_limit_per_minute: int | None = None,
        request_timeout_seconds: float | None = None,
        allowed_origins: tuple[str, ...] | None = None,
    ) -> None:
        configured = os.environ.get("EPISTEMEDIA_ROOT")
        self.root = Path(configured).resolve() if configured else (root or discover_root())
        self.max_body_bytes = max_body_bytes or env_int(
            "EPISTEMEDIA_MAX_BODY_BYTES", DEFAULT_MAX_BODY_BYTES
        )
        self.max_query_bytes = max_query_bytes or env_int(
            "EPISTEMEDIA_MAX_QUERY_BYTES", DEFAULT_MAX_QUERY_BYTES
        )
        self.max_response_bytes = max_response_bytes or env_int(
            "EPISTEMEDIA_MAX_RESPONSE_BYTES", DEFAULT_MAX_RESPONSE_BYTES
        )
        self.rate_limit_per_minute = rate_limit_per_minute or env_int(
            "EPISTEMEDIA_RATE_LIMIT_PER_MINUTE", DEFAULT_RATE_LIMIT_PER_MINUTE
        )
        self.request_timeout_seconds = request_timeout_seconds or env_float(
            "EPISTEMEDIA_REQUEST_TIMEOUT_SECONDS", DEFAULT_REQUEST_TIMEOUT_SECONDS
        )
        configured_origins = os.environ.get("EPISTEMEDIA_ALLOWED_ORIGINS")
        self.allowed_origins = allowed_origins or (
            tuple(item.strip() for item in configured_origins.split(",") if item.strip())
            if configured_origins is not None
            else DEFAULT_ALLOWED_ORIGINS
        )
        self._catalog: PublicCatalog | None = None
        self._fingerprint: tuple[str, int] | None = None
        self._rate_buckets: OrderedDict[str, deque[float]] = OrderedDict()

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

    def featured(self) -> FeaturedDossier | None:
        return load_featured_dossier(self.root)

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await send({"type": "http.response.start", "status": 404, "headers": []})
            await send({"type": "http.response.body", "body": b""})
            return
        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        method = scope.get("method", "GET").upper()
        path = scope.get("path", "/")
        query_string = scope.get("query_string", b"")

        # MCP requires Origin validation before the server consumes a potentially hostile body.
        if path == "/mcp" and not origin_allowed(headers.get("origin"), self.allowed_origins):
            await self.send_response(
                send,
                path,
                403,
                {},
                self.rpc_error(None, -32003, "Origin is not allowed"),
            )
            return

        client = scope.get("client") or ("unknown", 0)
        allowed, retry_after = self.check_rate_limit(str(client[0]))
        if not allowed:
            payload = (
                self.rpc_error(
                    None,
                    -32000,
                    "Rate limit exceeded",
                    {"retryAfterSeconds": retry_after},
                )
                if path == "/mcp"
                else {"error": "rate_limited", "retry_after_seconds": retry_after}
            )
            await self.send_response(
                send,
                path,
                429,
                {"retry-after": str(retry_after)},
                payload,
            )
            return
        if len(query_string) > self.max_query_bytes:
            payload = (
                self.rpc_error(None, -32600, "Query string exceeds configured size limit")
                if path == "/mcp"
                else {"error": "query_too_large", "limit_bytes": self.max_query_bytes}
            )
            await self.send_response(
                send,
                path,
                414,
                {},
                payload,
            )
            return
        content_length = headers.get("content-length")
        if content_length:
            try:
                declared_length = int(content_length)
            except ValueError:
                payload = (
                    self.rpc_error(None, -32600, "Invalid Content-Length")
                    if path == "/mcp"
                    else {"error": "invalid_content_length"}
                )
                await self.send_response(
                    send, path, 400, {}, payload
                )
                return
            if declared_length < 0 or declared_length > self.max_body_bytes:
                await self.send_response(
                    send,
                    path,
                    413,
                    {},
                    self.request_too_large(path),
                )
                return

        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                continue
            body.extend(message.get("body", b""))
            if len(body) > self.max_body_bytes:
                await self.send_response(
                    send,
                    path,
                    413,
                    {},
                    self.request_too_large(path),
                )
                return
            if not message.get("more_body", False):
                break
        try:
            query = parse_qs(query_string.decode("utf-8"))
        except UnicodeDecodeError:
            await self.send_response(
                send, path, 400, {}, {"error": "invalid_query_encoding"}
            )
            return
        request = Request(method, path, query, headers, bytes(body))
        try:
            status, response_headers, payload = await asyncio.wait_for(
                asyncio.to_thread(self.dispatch, request),
                timeout=self.request_timeout_seconds,
            )
        except TimeoutError:
            status, response_headers, payload = (
                504,
                {},
                self.rpc_error(
                    None,
                    -32603,
                    "Request exceeded configured timeout",
                    {"limitSeconds": self.request_timeout_seconds},
                )
                if path == "/mcp"
                else {
                    "error": "request_timeout",
                    "limit_seconds": self.request_timeout_seconds,
                },
            )
        except Exception:
            status, response_headers, payload = (
                500,
                {},
                self.rpc_error(None, -32603, "Internal error")
                if path == "/mcp"
                else {"error": "internal_error"},
            )
        await self.send_response(send, path, status, response_headers, payload)

    async def send_response(
        self,
        send: Any,
        path: str,
        status: int,
        response_headers: dict[str, str],
        payload: Any,
    ) -> None:
        encoded = payload if isinstance(payload, bytes) else json.dumps(
            payload, ensure_ascii=False, sort_keys=True
        ).encode("utf-8")
        if len(encoded) > self.max_response_bytes:
            status = 500
            payload = (
                self.rpc_error(None, -32603, "Response exceeds configured size limit")
                if path == "/mcp"
                else {"error": "response_too_large", "limit_bytes": self.max_response_bytes}
            )
            encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
            response_headers = {}
        catalog = self.catalog()
        default_headers = {
            "content-type": "application/json; charset=utf-8",
            "cache-control": "public, max-age=60",
            "ratelimit-policy": f"{self.rate_limit_per_minute};w=60",
            "x-epistemedia-catalog": catalog.catalog_id,
            "x-epistemedia-frontier": catalog.frontier,
            "x-epistemedia-commit": catalog.commit,
            "x-epistemedia-compiler": f"epistemedia/{VERSION}",
        }
        if path != "/mcp":
            default_headers["access-control-allow-origin"] = "*"
        default_headers.update(response_headers)
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [(k.encode("latin-1"), v.encode("latin-1")) for k, v in default_headers.items()],
        })
        await send({"type": "http.response.body", "body": encoded})

    def request_too_large(self, path: str) -> dict[str, Any]:
        if path == "/mcp":
            return self.rpc_error(
                None,
                -32600,
                "Request body exceeds configured size limit",
                {"limitBytes": self.max_body_bytes},
            )
        return {"error": "request_too_large", "limit_bytes": self.max_body_bytes}

    def check_rate_limit(self, client: str) -> tuple[bool, int]:
        now = time.monotonic()
        bucket = self._rate_buckets.pop(client, deque())
        while bucket and now - bucket[0] >= 60:
            bucket.popleft()
        if len(bucket) >= self.rate_limit_per_minute:
            self._rate_buckets[client] = bucket
            return False, max(1, math.ceil(60 - (now - bucket[0])))
        bucket.append(now)
        self._rate_buckets[client] = bucket
        while len(self._rate_buckets) > 4096:
            self._rate_buckets.popitem(last=False)
        return True, 0

    def dispatch(self, request: Request) -> tuple[int, dict[str, str], Any]:
        if request.path == "/mcp":
            return self.handle_mcp(request)
        if request.method == "OPTIONS":
            return 204, {
                "access-control-allow-methods": "GET, OPTIONS",
                "access-control-allow-headers": "content-type",
            }, b""
        if request.path in ("/healthz", "/v1/healthz"):
            return 200, {}, envelope(self.catalog(), {"ok": True, "version": VERSION})
        if request.path in ("/openapi.json", "/v1/openapi.json"):
            return 200, {}, openapi_document()
        if request.path.startswith("/v1/") or request.path == "/v1":
            return self.handle_api(request)
        return 404, {}, api_error(
            self.catalog(),
            "not_found",
            "Use /v1, /openapi.json, or /mcp.",
        )

    def handle_api(self, request: Request) -> tuple[int, dict[str, str], Any]:
        catalog = self.catalog()
        if request.method != "GET":
            return 405, {}, api_error(catalog, "method_not_allowed")
        path = request.path.rstrip("/") or "/v1"
        if path == "/v1":
            return 200, {}, envelope(catalog, {
                "name": "Epistemedia Public API",
                "version": VERSION,
                "status": "/v1/status",
                "search": "/v1/search?q=...",
                "dossiers": "/v1/dossiers",
                "topics": "/v1/topics",
                "openapi": "/openapi.json",
                "mcp": "/mcp",
            })
        if path == "/v1/status":
            featured = self.featured()
            return 200, {}, envelope(catalog, {
                "version": VERSION,
                "protocol_version": PROTOCOL_VERSION,
                "object_count": len(catalog.objects),
                "topic_count": len(catalog.topics),
                "dossier_count": 1 if featured is not None else 0,
                "featured_dossier": featured.slug if featured is not None else None,
                "generated_at": catalog.generated_at,
            })
        if path == "/v1/search":
            query = first(request.query, "q", "")
            limit = clamp_int(first(request.query, "limit", "20"), 1, 100, 20)
            return 200, {}, envelope(catalog, {"query": query, "results": catalog.search(query, limit)})
        if path == "/v1/dossiers":
            featured = self.featured()
            summaries = [featured.summary(catalog)] if featured is not None else []
            return 200, {}, envelope(catalog, summaries)
        if path.startswith("/v1/dossiers/"):
            slug = unquote(path[len("/v1/dossiers/"):])
            featured = self.featured()
            if featured is None or slug != featured.slug:
                return 404, {}, api_error(catalog, "not_found", f"Unknown dossier: {slug}")
            policy = first(request.query, "policy", featured.default_view)
            if policy not in FEATURE_VIEWS:
                return 400, {}, api_error(
                    catalog,
                    "invalid_policy",
                    allowed=list(FEATURE_VIEWS),
                )
            return 200, {}, featured.envelope(catalog, policy)
        if path == "/v1/topics":
            return 200, {}, envelope(catalog, [topic.as_dict() for topic in catalog.topics])
        if path.startswith("/v1/topics/"):
            slug = unquote(path[len("/v1/topics/"):])
            topic = catalog.topic_map().get(slug)
            if not topic:
                return 404, {}, api_error(catalog, "not_found", f"Unknown topic: {slug}")
            lens = first(request.query, "lens", "encyclopedia")
            if lens not in LENSES:
                return 400, {}, api_error(
                    catalog,
                    "invalid_lens",
                    allowed=sorted(LENSES),
                )
            return 200, {}, envelope(catalog, topic_projection(catalog, topic, lens, DEFAULT_BASE_URL))
        if path.startswith("/v1/objects/"):
            object_id = unquote(path[len("/v1/objects/"):])
            obj = catalog.object_map().get(object_id)
            if not obj:
                return 404, {}, api_error(
                    catalog,
                    "not_found",
                    f"Unknown object: {object_id}",
                )
            return 200, {}, envelope(catalog, obj.as_dict())
        if path.startswith("/v1/claims/") and path.endswith("/trace"):
            object_id = unquote(path[len("/v1/claims/"):-len("/trace")].rstrip("/"))
            obj = catalog.object_map().get(object_id)
            if not obj:
                return 404, {}, api_error(
                    catalog,
                    "not_found",
                    f"Unknown claim or object: {object_id}",
                )
            return 200, {}, envelope(catalog, {
                "subject": obj.as_dict(include_text=False),
                "accepted_source": {"repository_path": obj.path, "content_digest": obj.content_digest},
                "frontier": catalog.frontier,
                "policies": catalog.policies,
                "limitations": ["This repository-object trace is not evidence that the source content is true."],
            })
        return 404, {}, api_error(catalog, "not_found", path)

    def handle_mcp(self, request: Request) -> tuple[int, dict[str, str], Any]:
        origin = request.headers.get("origin")
        if not origin_allowed(origin, self.allowed_origins):
            return 403, {}, self.rpc_error(None, -32003, "Origin is not allowed")
        cors_headers = mcp_cors_headers(origin)
        if request.method == "OPTIONS":
            return 204, {
                **cors_headers,
                "access-control-allow-methods": "POST, OPTIONS",
                "access-control-allow-headers": (
                    "accept,content-type,mcp-protocol-version,mcp-method,mcp-name,origin"
                ),
            }, b""
        if request.method != "POST":
            return 405, {
                **cors_headers,
                "allow": "POST, OPTIONS",
            }, self.rpc_error(None, -32600, "MCP endpoint accepts POST only")
        try:
            message = json.loads(request.body or b"{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return 400, cors_headers, self.rpc_error(None, -32700, "Parse error")
        if (
            isinstance(message, dict)
            and message.get("jsonrpc") == "2.0"
            and message.get("method") == "notifications/cancelled"
        ):
            return 404, cors_headers, self.rpc_error(
                message.get("id"),
                -32601,
                "Method not found",
                {"method": "notifications/cancelled", "transport": "streamable-http"},
            )
        try:
            request_id, method, params = self.validate_mcp_request(message, request.headers)
            result = self.mcp_method(method, params)
            if isinstance(result, dict):
                result = self.decorate_mcp_result(result)
        except MCPRequestError as exc:
            return exc.status, cors_headers, self.rpc_error(
                request_id if "request_id" in locals() else message.get("id") if isinstance(message, dict) else None,
                exc.code,
                str(exc),
                exc.data,
            )
        except KeyError as exc:
            return 404, cors_headers, self.rpc_error(
                request_id, -32004, "Not found", {"id": exc.args[0] if exc.args else ""}
            )
        except ValueError as exc:
            return 400, cors_headers, self.rpc_error(request_id, -32602, str(exc))
        return 200, {
            **cors_headers,
            "mcp-protocol-version": PROTOCOL_VERSION,
            "cache-control": "public, max-age=60",
        }, {"jsonrpc": "2.0", "id": request_id, "result": result}

    def validate_mcp_request(
        self,
        message: Any,
        headers: dict[str, str] | None = None,
    ) -> tuple[Any, str, dict[str, Any]]:
        request_id = message.get("id") if isinstance(message, dict) else None
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            raise MCPRequestError(400, -32600, "Invalid Request")
        if "id" not in message or (
            isinstance(message["id"], bool)
            or not isinstance(message["id"], (str, int))
        ):
            raise MCPRequestError(400, -32600, "Invalid Request id")
        method = message.get("method")
        if not isinstance(method, str) or not method:
            raise MCPRequestError(400, -32600, "Invalid Request method")
        params = message.get("params", {})
        if not isinstance(params, dict):
            raise MCPRequestError(400, -32602, "Params must be an object")
        meta = params.get("_meta")
        if not isinstance(meta, dict):
            raise MCPRequestError(400, -32600, "Request params must include _meta")
        requested_version = meta.get(MCP_PROTOCOL_META)

        if headers is not None:
            self.validate_mcp_http_headers(headers, method, params, requested_version)
        if requested_version != PROTOCOL_VERSION:
            raise MCPRequestError(
                400,
                -32022,
                "Unsupported protocol version",
                {"supported": [PROTOCOL_VERSION], "requested": requested_version},
            )
        capabilities = meta.get(MCP_CAPABILITIES_META)
        if not isinstance(capabilities, dict):
            raise MCPRequestError(
                400,
                -32600,
                "Request _meta must include client capabilities",
            )
        return request_id, method, params

    def decorate_mcp_result(self, result: dict[str, Any]) -> dict[str, Any]:
        decorated = dict(result)
        decorated.setdefault("resultType", "complete")
        result_meta = dict(decorated.get("_meta") or {})
        result_meta.setdefault(MCP_SERVER_INFO_META, MCP_SERVER_INFO)
        decorated["_meta"] = result_meta
        identity_fields = {
            "catalog_id",
            "frontier",
            "commit",
            "policies",
            "compiler",
            "content_digest",
        }
        identity_material = {
            key: value for key, value in decorated.items() if key not in identity_fields
        }
        identity = envelope(self.catalog(), identity_material)
        identity.pop("data")
        decorated.update(identity)
        return decorated

    def validate_mcp_http_headers(
        self,
        headers: dict[str, str],
        method: str,
        params: dict[str, Any],
        requested_version: Any,
    ) -> None:
        content_type = headers.get("content-type", "").split(";", 1)[0].strip().lower()
        accepted = {
            part.split(";", 1)[0].strip().lower()
            for part in headers.get("accept", "").split(",")
            if part.strip()
        }
        if content_type != "application/json":
            raise header_mismatch("Content-Type must be application/json")
        if not {"application/json", "text/event-stream"}.issubset(accepted):
            raise header_mismatch(
                "Accept must include application/json and text/event-stream"
            )
        if (
            not isinstance(requested_version, str)
            or not headers.get("mcp-protocol-version")
            or headers.get("mcp-protocol-version") != requested_version
        ):
            raise header_mismatch(
                "MCP-Protocol-Version header does not match request _meta"
            )
        if headers.get("mcp-method") != method:
            raise header_mismatch("Mcp-Method header does not match request method")

        expected_name: Any = None
        name_required = method in {"tools/call", "resources/read", "prompts/get"}
        if method == "tools/call":
            expected_name = params.get("name")
        elif method == "resources/read":
            expected_name = params.get("uri")
        elif method == "prompts/get":
            expected_name = params.get("name")
        if name_required:
            if not isinstance(expected_name, str) or not expected_name:
                raise header_mismatch("Mcp-Name source field is missing from request params")
            try:
                header_name = decode_mcp_header(headers.get("mcp-name"))
            except ValueError as exc:
                raise header_mismatch(str(exc)) from exc
            if header_name != expected_name:
                raise header_mismatch("Mcp-Name header does not match request params")
        elif "mcp-name" in headers:
            raise header_mismatch("Mcp-Name is not valid for this request")

    def mcp_method(self, method: str, params: dict[str, Any]) -> Any:
        catalog = self.catalog()
        if method == "server/discover":
            return {
                "resultType": "complete",
                "supportedVersions": [PROTOCOL_VERSION],
                "capabilities": {"tools": {"listChanged": False}, "resources": {"listChanged": False}},
                "_meta": {MCP_SERVER_INFO_META: MCP_SERVER_INFO},
                "instructions": "Read-only access to disclosure-safe projections. Preserve catalog, frontier, policy, and source metadata in downstream use.",
                "descriptor": mcp_descriptor(DEFAULT_MCP_URL),
                "ttlMs": 60000,
                "cacheScope": "public",
            }
        if method == "notifications/cancelled":
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
            featured = self.featured()
            if featured is not None:
                resources += [
                    {
                        "uri": f"epistemedia://dossier/{featured.slug}/{view}",
                        "name": f"{featured.slug}-{view}",
                        "title": f"{featured.dossier['title']} — {view}",
                        "description": featured.dossier["scope"],
                        "mimeType": "application/json",
                    }
                    for view in FEATURE_VIEWS
                ]
            return {"resultType": "complete", "ttlMs": 60000, "cacheScope": "public", "resources": resources}
        if method == "resources/read":
            uri = params.get("uri", "")
            if not isinstance(uri, str) or not uri:
                raise ValueError("resources/read requires a non-empty uri")
            data = self.read_resource(uri)
            return {
                "resultType": "complete",
                "ttlMs": 60000,
                "cacheScope": "public",
                "contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(envelope(catalog, data), indent=2, sort_keys=True)}],
            }
        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            if not isinstance(name, str) or not name:
                raise ValueError("tools/call requires a non-empty name")
            if not isinstance(arguments, dict):
                raise ValueError("tools/call arguments must be an object")
            data = self.call_tool(name, arguments)
            return {
                "resultType": "complete",
                "content": [{"type": "text", "text": json.dumps(envelope(catalog, data), indent=2, sort_keys=True)}],
                "structuredContent": envelope(catalog, data),
                "isError": False,
            }
        raise MCPRequestError(
            404,
            -32601,
            "Method not found",
            {"method": method},
        )

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
        if uri.startswith("epistemedia://dossier/"):
            remainder = uri[len("epistemedia://dossier/"):]
            try:
                slug, view = remainder.rsplit("/", 1)
            except ValueError as exc:
                raise KeyError(uri) from exc
            featured = self.featured()
            if featured is None or slug != featured.slug or view not in FEATURE_VIEWS:
                raise KeyError(uri)
            return featured.projection(view)
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
        if name == "get_dossier":
            slug = str(arguments.get("slug", ""))
            policy = str(arguments.get("policy", "encyclopedia"))
            featured = self.featured()
            if featured is None or slug != featured.slug:
                raise KeyError(slug)
            if policy not in FEATURE_VIEWS:
                raise ValueError(f"Unknown dossier policy: {policy}")
            return featured.projection(policy)
        if name == "compare_dossier_policies":
            slug = str(arguments.get("slug", ""))
            featured = self.featured()
            if featured is None or slug != featured.slug:
                raise KeyError(slug)
            return {
                "slug": featured.slug,
                "dossier_id": featured.dossier["dossier_id"],
                "views": {
                    view: featured.projection(view)
                    for view in FEATURE_VIEWS
                },
            }
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
        response: dict[str, Any] = {"jsonrpc": "2.0", "error": error}
        if isinstance(request_id, (str, int)) and not isinstance(request_id, bool):
            response["id"] = request_id
        return response


def tool_definitions() -> list[dict[str, Any]]:
    return [
        tool("search_knowledge", "Search disclosure-safe public objects.", {"query": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 100}}, ["query"]),
        tool("get_object", "Get one exact object and its source metadata.", {"id": {"type": "string"}}, ["id"]),
        tool("get_topic", "Compile one topic through a selected public lens.", {"slug": {"type": "string"}, "lens": {"type": "string", "enum": sorted(LENSES)}}, ["slug"]),
        tool(
            "get_dossier",
            "Get one accepted dossier through a named application policy.",
            {
                "slug": {"type": "string"},
                "policy": {"type": "string", "enum": list(FEATURE_VIEWS)},
            },
            ["slug"],
        ),
        tool(
            "compare_dossier_policies",
            "Compare encyclopedia and skeptical views over one accepted dossier.",
            {"slug": {"type": "string"}},
            ["slug"],
        ),
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


def api_error(
    catalog: PublicCatalog,
    error: str,
    detail: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"error": error, **extra}
    if detail is not None:
        payload["detail"] = detail
    identity = envelope(catalog, payload)
    identity.pop("data")
    return {**identity, **payload}


def env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    try:
        value = default if raw is None else int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value < 1:
        raise ValueError(f"{name} must be positive")
    return value


def env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    try:
        value = default if raw is None else float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def parse_origin(value: str) -> tuple[str, str, int | None]:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Origin is malformed") from exc
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Origin is malformed")
    return parsed.scheme, parsed.hostname.lower(), port


def origin_allowed(origin: str | None, allowed_origins: tuple[str, ...]) -> bool:
    if origin is None:
        return True
    try:
        scheme, host, port = parse_origin(origin)
    except ValueError:
        return False
    for allowed in allowed_origins:
        try:
            allowed_scheme, allowed_host, allowed_port = parse_origin(allowed)
        except ValueError:
            continue
        if (scheme, host) != (allowed_scheme, allowed_host):
            continue
        if allowed_port is not None and port == allowed_port:
            return True
        if allowed_port is None and host in {"localhost", "127.0.0.1"}:
            return True
        default_port = 443 if scheme == "https" else 80
        if allowed_port is None and port in {None, default_port}:
            return True
    return False


def mcp_cors_headers(origin: str | None) -> dict[str, str]:
    if origin is None:
        return {}
    return {
        "access-control-allow-origin": origin,
        "vary": "Origin",
    }


def header_mismatch(message: str) -> MCPRequestError:
    return MCPRequestError(400, -32020, f"Header mismatch: {message}")


def decode_mcp_header(value: str | None) -> str:
    if value is None:
        raise ValueError("Mcp-Name header is required")
    if value.startswith("=?base64?") and value.endswith("?="):
        encoded = value[len("=?base64?"):-2]
        try:
            return base64.b64decode(encoded, validate=True).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError) as exc:
            raise ValueError("Mcp-Name header has invalid Base64 encoding") from exc
    if value != value.strip() or any(ord(character) < 0x20 or ord(character) > 0x7E for character in value):
        raise ValueError("Mcp-Name header must use visible ASCII or Base64 encoding")
    if value.startswith("=?base64?") or value.endswith("?="):
        raise ValueError("Mcp-Name header uses an invalid Base64 sentinel")
    return value


app = Gateway()
