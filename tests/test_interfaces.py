from __future__ import annotations

import asyncio
import base64
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote

from epistemedia.cli import main
from epistemedia.core import (
    PROTOCOL_VERSION,
    PublicCatalog,
    audit_public,
    build_public,
    stable_id,
    topic_projection,
    validate_repository,
)
from epistemedia.server import Gateway, Request, tool_definitions


ROOT = Path(__file__).resolve().parents[1]


def test_repo_receipt_command_does_not_overwrite_cli_dispatch(tmp_path: Path) -> None:
    result = main(
        [
            "--root",
            str(tmp_path),
            "repo",
            "receipt",
            "EM-0008",
            "--run",
            "local-test",
            "--command",
            "make check",
        ]
    )
    assert result == 0
    receipts = list((tmp_path / "runs" / "proposals").glob("*.json"))
    assert len(receipts) == 1
    receipt = json.loads(receipts[0].read_text())
    assert receipt["kind"] == "run-receipt"
    assert receipt["task_id"] == "EM-0008"
    assert receipt["run_id"] == "local-test"
    assert receipt["command"] == "make check"


def test_repository_is_valid() -> None:
    assert validate_repository(ROOT) == []


def test_catalog_is_deterministic() -> None:
    first = PublicCatalog.build(ROOT)
    second = PublicCatalog.build(ROOT)
    assert first.catalog_id == second.catalog_id
    assert first.frontier == second.frontier
    assert [obj.id for obj in first.objects] == [obj.id for obj in second.objects]


def test_public_timestamp_is_the_accepted_commit_time() -> None:
    epoch = int(
        subprocess.check_output(
            ["git", "show", "-s", "--format=%ct", "HEAD"], cwd=ROOT, text=True
        ).strip()
    )
    expected = (
        datetime.fromtimestamp(epoch, timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    assert PublicCatalog.build(ROOT).generated_at == expected


def test_deployment_url_does_not_change_catalog_identity(tmp_path: Path) -> None:
    a = build_public(ROOT, tmp_path / "a", base_url="https://epistemedia.org")
    b = build_public(ROOT, tmp_path / "b", base_url="https://mirror.example")
    assert a["catalog_id"] == b["catalog_id"]
    assert a["frontier"] == b["frontier"]
    # A release manifest includes rendered files, so its own ID may change with links.
    assert (tmp_path / "a" / "catalog.json").read_text() == (tmp_path / "b" / "catalog.json").read_text()


def test_public_build_emits_every_interface(tmp_path: Path) -> None:
    public = tmp_path / "public"
    manifest = build_public(ROOT, public)
    expected = [
        "index.html",
        "index.md",
        "llms.txt",
        "llms-full.txt",
        "catalog.json",
        "search.json",
        "status.json",
        "manifest.json",
        "openapi.json",
        ".well-known/epistemedia.json",
        "mcp/server.json",
        "docs/llms.txt",
    ]
    assert all((public / path).exists() for path in expected)
    assert manifest["file_count"] > 10
    assert audit_public(ROOT, public) == []

    discovery = json.loads((public / ".well-known" / "epistemedia.json").read_text())
    assert discovery["human"] == "https://epistemedia.org"
    assert discovery["api"] == "https://api.epistemedia.org/v1"
    assert discovery["openapi"] == "https://epistemedia.org/openapi.json"
    assert discovery["mcp"] == "https://mcp.epistemedia.org/mcp"

    llms = (public / "llms.txt").read_text()
    assert "Static OpenAPI contract — hosted API not live" in llms
    assert "https://epistemedia.org/openapi.json" in llms
    assert "Static MCP descriptor — remote MCP not live" in llms
    assert "https://epistemedia.org/mcp/server.json" in llms
    assert "https://api.epistemedia.org/openapi.json" not in llms

    obj = next(obj for obj in PublicCatalog.build(ROOT).objects if obj.kind == "documentation")
    file_key = quote(obj.id, safe="")
    route_key = quote(file_key, safe="")
    docs_html = (public / "docs" / "index.html").read_text()
    docs_llms = (public / "docs" / "llms.txt").read_text()
    assert f"/objects/{route_key}/" in docs_html
    assert f"/objects/{route_key}.md" in docs_llms
    assert unquote(route_key) == file_key
    assert (public / "objects" / file_key / "index.html").exists()
    assert (public / "objects" / f"{file_key}.md").exists()
    assert '<link rel="canonical" href="https://epistemedia.org/docs/">' in docs_html

    object_html = (public / "objects" / file_key / "index.html").read_text()
    expected_canonical = f'https://epistemedia.org/objects/{route_key}/'
    assert f'<link rel="canonical" href="{expected_canonical}">' in object_html

    home_html = (public / "index.html").read_text()
    assert "overflow-wrap:anywhere;word-break:break-word" in home_html
    assert "pre code{padding:0;overflow-wrap:normal;word-break:normal}" in home_html
    assert "minmax(min(100%,260px),1fr)" in home_html
    assert "Current coverage:" in home_html
    assert "self-describing bootstrap corpus" in home_html
    assert "How We Know" in home_html

    topic = PublicCatalog.build(ROOT).topics[0]
    topic_html = (public / "topics" / topic.slug / "index.html").read_text()
    topic_markdown = (public / "topics" / topic.slug / "index.md").read_text()
    assert topic_html.count("<h1>") == 1
    assert f"<h1>{topic.title}</h1>" in topic_html
    assert topic_html.count(topic.description) == 1
    assert "Experimental lens manifests (shared inventory)" in topic_html
    assert "not yet materially different editorial products" in topic_html
    assert topic_markdown.startswith(f"# {topic.title}\n")
    assert (
        f'<link rel="canonical" href="https://epistemedia.org/topics/{topic.slug}/">'
        in topic_html
    )

    experimental_html = (
        public / "topics" / topic.slug / "skeptical" / "index.html"
    ).read_text()
    assert experimental_html.count("<h1>") == 1
    assert "Experimental lens manifest." in experimental_html
    assert "not a differentiated editorial result" in experimental_html

    status_markdown = (public / "status" / "index.md").read_text()
    assert "Canonical human site" in status_markdown
    assert status_markdown.count("not verified live") == 3
    assert "self-describing repository bootstrap" in status_markdown


def test_topic_lenses_share_source_frontier() -> None:
    catalog = PublicCatalog.build(ROOT)
    topic = catalog.topics[0]
    encyclopedia = topic_projection(catalog, topic, "encyclopedia", "https://a.example")
    skeptical = topic_projection(catalog, topic, "skeptical", "https://b.example")
    assert encyclopedia["catalog_id"] == skeptical["catalog_id"]
    assert encyclopedia["frontier"] == skeptical["frontier"]
    assert [o["id"] for o in encyclopedia["objects"]] == [o["id"] for o in skeptical["objects"]]
    assert encyclopedia["projection_id"] != skeptical["projection_id"]


def test_public_status_copy_distinguishes_live_and_target_surfaces() -> None:
    readme = (ROOT / "README.md").read_text()
    api_docs = (ROOT / "docs" / "api-mcp-cli.md").read_text()
    assert "canonical static site live at <https://epistemedia.org/>" in readme
    assert "sharing redirect and hosted API/MCP runtime" in readme
    assert "does **not** yet instantiate that claim/evidence graph" in readme
    assert "Target architecture" in readme
    assert "Public hosting at `epistemedia.org`" not in readme
    assert api_docs.count("No hosted runtime at that hostname has passed") == 2


def test_object_ids_are_content_and_path_addressed() -> None:
    catalog = PublicCatalog.build(ROOT)
    obj = catalog.objects[0]
    assert obj.id.startswith("em:")
    assert len(obj.content_digest) == 64
    assert obj.id == stable_id(obj.kind, {"path": obj.path, "content_digest": obj.content_digest, "media_type": obj.media_type})


def test_search_is_stable() -> None:
    catalog = PublicCatalog.build(ROOT)
    assert catalog.search("Epistemedia") == catalog.search("Epistemedia")


def mcp_params(**values: object) -> dict[str, object]:
    return {
        **values,
        "_meta": {
            "io.modelcontextprotocol/protocolVersion": PROTOCOL_VERSION,
            "io.modelcontextprotocol/clientInfo": {
                "name": "epistemedia-tests",
                "version": "1",
            },
            "io.modelcontextprotocol/clientCapabilities": {},
        },
    }


def mcp_request(
    method: str,
    params: dict[str, object] | None = None,
    *,
    request_id: object = 1,
    origin: str | None = "https://epistemedia.org",
) -> Request:
    body_params = params or mcp_params()
    headers = {
        "accept": "application/json, text/event-stream",
        "content-type": "application/json; charset=utf-8",
        "mcp-protocol-version": str(
            body_params.get("_meta", {}).get(
                "io.modelcontextprotocol/protocolVersion", ""
            )
        ),
        "mcp-method": method,
    }
    if origin is not None:
        headers["origin"] = origin
    if method in {"tools/call", "prompts/get"} and "name" in body_params:
        headers["mcp-name"] = str(body_params["name"])
    if method == "resources/read" and "uri" in body_params:
        headers["mcp-name"] = str(body_params["uri"])
    message = {"jsonrpc": "2.0", "method": method, "params": body_params}
    if request_id is not None:
        message["id"] = request_id
    return Request("POST", "/mcp", {}, headers, json.dumps(message).encode())


def test_api_and_mcp_expose_same_catalog() -> None:
    gateway = Gateway(ROOT)
    status, _, api = gateway.handle_api(Request("GET", "/v1/status", {}, {}, b""))
    assert status == 200
    mcp_status, _, mcp_response = gateway.handle_mcp(mcp_request("server/discover"))
    assert mcp_status == 200
    mcp = mcp_response["result"]
    assert api["catalog_id"] == gateway.catalog().catalog_id
    assert api["commit"] == gateway.catalog().commit
    assert api["policies"] == gateway.catalog().policies
    assert len(api["content_digest"]) == 64
    assert mcp["catalog_id"] == api["catalog_id"]
    assert mcp["frontier"] == api["frontier"]
    assert mcp["commit"] == api["commit"]
    assert mcp["policies"] == api["policies"]
    assert mcp["compiler"] == api["compiler"]
    assert len(mcp["content_digest"]) == 64
    assert gateway.decorate_mcp_result(mcp) == mcp
    assert mcp["supportedVersions"] == [PROTOCOL_VERSION]
    assert mcp["resultType"] == "complete"
    assert mcp["_meta"]["io.modelcontextprotocol/serverInfo"]["version"]

    error_status, _, error = gateway.handle_api(
        Request("GET", "/v1/objects/not-an-object", {}, {}, b"")
    )
    assert error_status == 404
    assert error["commit"] == gateway.catalog().commit
    assert error["policies"] == gateway.catalog().policies
    assert len(error["content_digest"]) == 64


def test_mcp_tool_result_carries_catalog_and_frontier() -> None:
    gateway = Gateway(ROOT)
    result = gateway.mcp_method("tools/call", {"name": "search_knowledge", "arguments": {"query": "governance"}})
    structured = result["structuredContent"]
    assert structured["catalog_id"] == gateway.catalog().catalog_id
    assert structured["frontier"] == gateway.catalog().frontier
    assert structured["policies"] == gateway.catalog().policies
    assert len(structured["content_digest"]) == 64
    assert result["isError"] is False

    resource = gateway.mcp_method("resources/read", {"uri": "epistemedia://status"})
    assert resource["resultType"] == "complete"
    assert resource["ttlMs"] == 60000
    assert resource["cacheScope"] == "public"


def test_mcp_rejects_unknown_protocol() -> None:
    gateway = Gateway(ROOT)
    request = mcp_request("tools/list")
    request.headers["mcp-protocol-version"] = "1900-01-01"
    message = json.loads(request.body)
    message["params"]["_meta"]["io.modelcontextprotocol/protocolVersion"] = "1900-01-01"
    request.body = json.dumps(message).encode()
    status, _, result = gateway.handle_mcp(request)
    assert status == 400
    assert result["error"]["code"] == -32022
    assert result["error"]["data"] == {
        "supported": [PROTOCOL_VERSION],
        "requested": "1900-01-01",
    }


def test_mcp_rejects_untrusted_origin() -> None:
    gateway = Gateway(ROOT)
    status, headers, result = gateway.handle_mcp(
        mcp_request("tools/list", origin="https://attacker.example")
    )
    assert status == 403
    assert "access-control-allow-origin" not in headers
    assert result["error"]["code"] == -32003

    rebinding = mcp_request("tools/list", origin="http://localhost:@attacker.example")
    assert gateway.handle_mcp(rebinding)[0] == 403


def test_mcp_accepts_controlled_production_origin() -> None:
    gateway = Gateway(ROOT)
    status, headers, result = gateway.handle_mcp(mcp_request("tools/list"))
    assert status == 200
    assert headers["access-control-allow-origin"] == "https://epistemedia.org"
    assert result["id"] == 1
    assert result["result"]["resultType"] == "complete"
    assert "io.modelcontextprotocol/serverInfo" in result["result"]["_meta"]


def test_mcp_rejects_header_body_mismatch_and_missing_name() -> None:
    gateway = Gateway(ROOT)
    request = mcp_request("tools/list")
    request.headers["mcp-method"] = "resources/list"
    status, _, result = gateway.handle_mcp(request)
    assert status == 400
    assert result["error"]["code"] == -32020

    call = mcp_request(
        "tools/call",
        mcp_params(name="search_knowledge", arguments={"query": "governance"}),
    )
    del call.headers["mcp-name"]
    status, _, result = gateway.handle_mcp(call)
    assert status == 400
    assert result["error"]["code"] == -32020


def test_mcp_accepts_base64_name_and_rejects_unknown_method() -> None:
    gateway = Gateway(ROOT)
    uri = "epistemedia://status"
    request = mcp_request("resources/read", mcp_params(uri=uri))
    request.headers["mcp-name"] = "=?base64?" + base64.b64encode(uri.encode()).decode() + "?="
    assert gateway.handle_mcp(request)[0] == 200

    status, _, result = gateway.handle_mcp(mcp_request("not/a-method"))
    assert status == 404
    assert result["error"]["code"] == -32601

    status, _, result = gateway.handle_mcp(
        mcp_request("prompts/get", mcp_params(name="not-supported"))
    )
    assert status == 404
    assert result["error"]["code"] == -32601


def test_mcp_streamable_http_rejects_get_delete_and_http_cancellation() -> None:
    gateway = Gateway(ROOT)
    for method in ("GET", "DELETE"):
        status, headers, result = gateway.handle_mcp(
            Request(method, "/mcp", {}, {"origin": "https://epistemedia.org"}, b"")
        )
        assert status == 405
        assert headers["allow"] == "POST, OPTIONS"
        assert result["error"]["code"] == -32600

    status, _, result = gateway.handle_mcp(
        mcp_request("notifications/cancelled", request_id=None)
    )
    assert status == 404
    assert result["error"]["code"] == -32601
    assert "id" not in result

    missing_id = mcp_request("tools/list", request_id=None)
    status, _, result = gateway.handle_mcp(missing_id)
    assert status == 400
    assert result["error"]["code"] == -32600
    assert "id" not in result


def test_mcp_parse_error_omits_unknown_request_id() -> None:
    gateway = Gateway(ROOT)
    request = mcp_request("tools/list")
    request.body = b"{"
    status, _, result = gateway.handle_mcp(request)
    assert status == 400
    assert result["error"]["code"] == -32700
    assert "id" not in result


def test_mcp_request_meta_is_required_for_stdio() -> None:
    gateway = Gateway(ROOT)
    request_id, method, params = gateway.validate_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": "discover",
            "method": "server/discover",
            "params": mcp_params(),
        }
    )
    assert (request_id, method) == ("discover", "server/discover")
    assert params["_meta"]["io.modelcontextprotocol/protocolVersion"] == PROTOCOL_VERSION


def test_stdio_mcp_serves_modern_discovery() -> None:
    message = {
        "jsonrpc": "2.0",
        "id": "discover",
        "method": "server/discover",
        "params": mcp_params(),
    }
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "epistemedia",
            "--root",
            str(ROOT),
            "mcp",
            "serve",
        ],
        cwd=ROOT,
        input=json.dumps(message) + "\n",
        text=True,
        capture_output=True,
        check=True,
    )
    response = json.loads(completed.stdout)
    assert response["id"] == "discover"
    assert response["result"]["supportedVersions"] == [PROTOCOL_VERSION]
    assert response["result"]["resultType"] == "complete"


def test_stdio_mcp_parse_error_does_not_reuse_a_prior_request_id() -> None:
    message = {
        "jsonrpc": "2.0",
        "id": "first",
        "method": "server/discover",
        "params": mcp_params(),
    }
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "epistemedia",
            "--root",
            str(ROOT),
            "mcp",
            "serve",
        ],
        cwd=ROOT,
        input=json.dumps(message) + "\n{\n",
        text=True,
        capture_output=True,
        check=True,
    )
    responses = [json.loads(line) for line in completed.stdout.splitlines()]
    assert responses[0]["id"] == "first"
    assert responses[1]["error"]["code"] == -32700
    assert "id" not in responses[1]


def test_public_gateway_exposes_only_read_only_closed_world_tools() -> None:
    source = (ROOT / "src" / "epistemedia" / "server.py").read_text()
    assert "urlopen(" not in source
    assert "httpx" not in source
    assert "requests." not in source
    tools = tool_definitions()
    assert tools
    assert all(tool["annotations"]["readOnlyHint"] is True for tool in tools)
    assert all(tool["annotations"]["destructiveHint"] is False for tool in tools)
    assert all(tool["annotations"]["openWorldHint"] is False for tool in tools)


def test_public_projection_excludes_private_tree(tmp_path: Path) -> None:
    root = tmp_path / "realm"
    root.mkdir()
    (root / "README.md").write_text("# Public\n\nPublic statement.\n")
    (root / "AGENTS.md").write_text("# Agents\n")
    (root / "pyproject.toml").write_text("[project]\nname='x'\nversion='0'\n")
    private = root / "private"
    private.mkdir()
    (private / "secret.md").write_text("PRIVATE-ONLY-EVIDENCE")
    catalog = PublicCatalog.build(root)
    serialized = json.dumps(catalog.public_dict())
    assert "PRIVATE-ONLY-EVIDENCE" not in serialized
    assert all(not obj.path.startswith("private/") for obj in catalog.objects)


def test_private_mutation_has_no_public_effect(tmp_path: Path) -> None:
    root = tmp_path / "realm"
    root.mkdir()
    (root / "README.md").write_text("# Public\n\nPublic statement.\n")
    (root / "AGENTS.md").write_text("# Agents\n")
    (root / "pyproject.toml").write_text("[project]\nname='x'\nversion='0'\n")
    private = root / "private"
    private.mkdir()
    (private / "secret.md").write_text("first")
    first = PublicCatalog.build(root)
    (private / "secret.md").write_text("second and contradictory")
    second = PublicCatalog.build(root)
    assert first.catalog_id == second.catalog_id
    assert first.frontier == second.frontier


def test_asgi_status_smoke() -> None:
    gateway = Gateway(ROOT)
    sent: list[dict] = []
    incoming = iter([
        {"type": "http.request", "body": b"", "more_body": False},
    ])

    async def receive() -> dict:
        return next(incoming)

    async def send(message: dict) -> None:
        sent.append(message)

    asyncio.run(gateway({"type": "http", "method": "GET", "path": "/v1/status", "query_string": b"", "headers": []}, receive, send))
    assert sent[0]["status"] == 200
    body = json.loads(sent[1]["body"])
    assert body["catalog_id"] == gateway.catalog().catalog_id
    assert body["commit"] == gateway.catalog().commit
    assert body["policies"] == gateway.catalog().policies
    assert len(body["content_digest"]) == 64


def test_asgi_rejects_origin_before_consuming_mcp_body() -> None:
    gateway = Gateway(ROOT)
    sent: list[dict] = []
    receive_calls = 0

    async def receive() -> dict:
        nonlocal receive_calls
        receive_calls += 1
        raise AssertionError("untrusted MCP body must not be consumed")

    async def send(message: dict) -> None:
        sent.append(message)

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/mcp",
        "query_string": b"",
        "headers": [(b"origin", b"https://attacker.example")],
        "client": ("192.0.2.10", 1234),
    }
    asyncio.run(gateway(scope, receive, send))
    assert receive_calls == 0
    assert sent[0]["status"] == 403
    assert json.loads(sent[1]["body"])["error"]["code"] == -32003


def test_asgi_enforces_body_query_response_rate_and_timeout_limits() -> None:
    async def invoke(
        gateway: Gateway,
        *,
        path: str = "/v1/status",
        query: bytes = b"",
        headers: list[tuple[bytes, bytes]] | None = None,
        body: bytes = b"",
    ) -> list[dict]:
        sent: list[dict] = []
        incoming = iter(
            [{"type": "http.request", "body": body, "more_body": False}]
        )

        async def receive() -> dict:
            return next(incoming)

        async def send(message: dict) -> None:
            sent.append(message)

        await gateway(
            {
                "type": "http",
                "method": "GET" if path != "/mcp" else "POST",
                "path": path,
                "query_string": query,
                "headers": headers or [],
                "client": ("192.0.2.20", 4321),
            },
            receive,
            send,
        )
        return sent

    body_limited = Gateway(ROOT, max_body_bytes=10)
    oversized = asyncio.run(
        invoke(
            body_limited,
            path="/mcp",
            headers=[(b"content-length", b"11")],
        )
    )
    assert oversized[0]["status"] == 413

    query_limited = Gateway(ROOT, max_query_bytes=4)
    assert asyncio.run(invoke(query_limited, query=b"q=large"))[0]["status"] == 414

    response_limited = Gateway(ROOT, max_response_bytes=100)
    response = asyncio.run(invoke(response_limited))
    assert response[0]["status"] == 500
    assert json.loads(response[1]["body"])["error"] == "response_too_large"

    rate_limited = Gateway(ROOT, rate_limit_per_minute=1)
    assert asyncio.run(invoke(rate_limited))[0]["status"] == 200
    rate_response = asyncio.run(invoke(rate_limited))
    assert rate_response[0]["status"] == 429

    timeout_limited = Gateway(ROOT, request_timeout_seconds=0.001)
    original_dispatch = timeout_limited.dispatch

    def slow_dispatch(request: Request) -> tuple[int, dict[str, str], object]:
        time.sleep(0.02)
        return original_dispatch(request)

    timeout_limited.dispatch = slow_dispatch  # type: ignore[method-assign]
    timeout_response = asyncio.run(invoke(timeout_limited))
    assert timeout_response[0]["status"] == 504
    assert json.loads(timeout_response[1]["body"])["error"] == "request_timeout"
