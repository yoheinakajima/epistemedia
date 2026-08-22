from __future__ import annotations

import asyncio
import json
import subprocess
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
from epistemedia.server import Gateway, Request


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
    assert discovery["mcp"] == "https://mcp.epistemedia.org/mcp"

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


def test_topic_lenses_share_source_frontier() -> None:
    catalog = PublicCatalog.build(ROOT)
    topic = catalog.topics[0]
    encyclopedia = topic_projection(catalog, topic, "encyclopedia", "https://a.example")
    skeptical = topic_projection(catalog, topic, "skeptical", "https://b.example")
    assert encyclopedia["catalog_id"] == skeptical["catalog_id"]
    assert encyclopedia["frontier"] == skeptical["frontier"]
    assert [o["id"] for o in encyclopedia["objects"]] == [o["id"] for o in skeptical["objects"]]
    assert encyclopedia["projection_id"] != skeptical["projection_id"]


def test_object_ids_are_content_and_path_addressed() -> None:
    catalog = PublicCatalog.build(ROOT)
    obj = catalog.objects[0]
    assert obj.id.startswith("em:")
    assert len(obj.content_digest) == 64
    assert obj.id == stable_id(obj.kind, {"path": obj.path, "content_digest": obj.content_digest, "media_type": obj.media_type})


def test_search_is_stable() -> None:
    catalog = PublicCatalog.build(ROOT)
    assert catalog.search("Epistemedia") == catalog.search("Epistemedia")


def test_api_and_mcp_expose_same_catalog() -> None:
    gateway = Gateway(ROOT)
    status, _, api = gateway.handle_api(Request("GET", "/v1/status", {}, {}, b""))
    assert status == 200
    mcp = gateway.mcp_method("server/discover", {})
    assert api["catalog_id"] == gateway.catalog().catalog_id
    assert mcp["protocolVersion"] == PROTOCOL_VERSION


def test_mcp_tool_result_carries_catalog_and_frontier() -> None:
    gateway = Gateway(ROOT)
    result = gateway.mcp_method("tools/call", {"name": "search_knowledge", "arguments": {"query": "governance"}})
    structured = result["structuredContent"]
    assert structured["catalog_id"] == gateway.catalog().catalog_id
    assert structured["frontier"] == gateway.catalog().frontier
    assert result["isError"] is False


def test_mcp_rejects_unknown_protocol() -> None:
    gateway = Gateway(ROOT)
    status, _, result = gateway.handle_mcp(
        Request(
            "POST",
            "/mcp",
            {},
            {"mcp-protocol-version": "1900-01-01"},
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}).encode(),
        )
    )
    assert status == 400
    assert result["error"]["message"] == "UnsupportedProtocolVersion"


def test_mcp_rejects_untrusted_origin() -> None:
    gateway = Gateway(ROOT)
    status, _, _ = gateway.handle_mcp(
        Request(
            "POST",
            "/mcp",
            {},
            {"origin": "https://attacker.example", "mcp-protocol-version": PROTOCOL_VERSION},
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}).encode(),
        )
    )
    assert status == 403


def test_mcp_accepts_controlled_production_origin() -> None:
    gateway = Gateway(ROOT)
    status, _, result = gateway.handle_mcp(
        Request(
            "POST",
            "/mcp",
            {},
            {"origin": "https://epistemedia.org", "mcp-protocol-version": PROTOCOL_VERSION},
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}).encode(),
        )
    )
    assert status == 200
    assert result["id"] == 1


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
