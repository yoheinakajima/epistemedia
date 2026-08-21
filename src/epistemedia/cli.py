from __future__ import annotations

import argparse
import http.server
import json
import os
import socketserver
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .core import (
    DEFAULT_API_URL,
    DEFAULT_BASE_URL,
    DEFAULT_MCP_URL,
    VERSION,
    PublicCatalog,
    audit_public,
    build_public,
    discover_root,
    validate_repository,
)
from .server import Gateway


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="epistemedia", description="Knowledge that can show its work.")
    root.add_argument("--version", action="version", version=f"epistemedia {VERSION}")
    root.add_argument("--root", type=Path, help="Repository root; inferred for local commands")
    sub = root.add_subparsers(dest="command", required=True)

    sub.add_parser("orient", help="Print the bounded agent orientation and current repository state")
    sub.add_parser("validate", help="Validate accepted repository inputs")

    build = sub.add_parser("build", help="Compile all public human and agent interfaces")
    build.add_argument("--output", type=Path, default=Path("generated/public"))
    build.add_argument("--base-url", default=DEFAULT_BASE_URL)
    build.add_argument("--api-url", default=DEFAULT_API_URL)
    build.add_argument("--mcp-url", default=DEFAULT_MCP_URL)

    audit = sub.add_parser("audit", help="Audit a compiled PublicProjection")
    audit.add_argument("--public", type=Path, default=Path("generated/public"))

    serve = sub.add_parser("serve", help="Serve compiled static output")
    serve.add_argument("--public", type=Path, default=Path("generated/public"))
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)

    api = sub.add_parser("api-serve", help="Serve API and MCP through an ASGI server")
    api.add_argument("--host", default="127.0.0.1")
    api.add_argument("--port", type=int, default=8080)

    search = sub.add_parser("search", help="Search a local realm or the public remote API")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=20)
    search.add_argument("--remote", action="store_true")
    search.add_argument("--api", default=DEFAULT_API_URL)

    get = sub.add_parser("get", help="Get an exact object")
    get.add_argument("id")
    get.add_argument("--remote", action="store_true")
    get.add_argument("--api", default=DEFAULT_API_URL)

    project = sub.add_parser("project", help="Compile or retrieve a topic projection")
    project.add_argument("slug")
    project.add_argument("--lens", default="encyclopedia")
    project.add_argument("--remote", action="store_true")
    project.add_argument("--api", default=DEFAULT_API_URL)

    repo = sub.add_parser("repo", help="Repository-native agent operations")
    repo_sub = repo.add_subparsers(dest="repo_command", required=True)
    repo_sub.add_parser("next", help="Show the best currently discoverable task contracts")
    claim = repo_sub.add_parser("claim", help="Create an append-only local task-claim proposal")
    claim.add_argument("task_id")
    claim.add_argument("--agent", required=True)
    receipt = repo_sub.add_parser("receipt", help="Record a local append-only run receipt proposal")
    receipt.add_argument("task_id")
    receipt.add_argument("--run", required=True)
    receipt.add_argument("--command", dest="run_command", required=True)

    mcp = sub.add_parser("mcp", help="MCP utilities")
    mcp_sub = mcp.add_subparsers(dest="mcp_command", required=True)
    mcp_sub.add_parser("serve", help="Run a newline-delimited stdio MCP adapter")
    mcp_sub.add_parser("discover", help="Print server discovery metadata")

    return root


def resolve_root(args: argparse.Namespace, required: bool = True) -> Path | None:
    if args.root:
        return args.root.resolve()
    try:
        return discover_root()
    except FileNotFoundError:
        if required:
            raise
        return None


def print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def remote_get(api: str, path: str, query: dict[str, Any] | None = None) -> Any:
    url = api.rstrip("/") + "/" + path.lstrip("/")
    if query:
        url += "?" + urllib.parse.urlencode(query)
    request = urllib.request.Request(url, headers={"accept": "application/json", "user-agent": f"epistemedia-cli/{VERSION}"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"remote API returned {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"remote API unavailable: {exc.reason}") from exc


def orient(root: Path) -> int:
    catalog = PublicCatalog.build(root)
    tasks = [obj for obj in catalog.objects if obj.kind == "task"]
    print("Epistemedia agent orientation")
    print("============================")
    print(f"Repository: {root}")
    print(f"Accepted commit: {catalog.commit}")
    print(f"Public catalog: {catalog.catalog_id}")
    print(f"Evidence frontier: {catalog.frontier}")
    print(f"Public objects: {len(catalog.objects)}")
    print(f"Topics: {len(catalog.topics)}")
    print(f"Task contracts visible: {len(tasks)}")
    print()
    print("Read order: AGENTS.md → selected task contract → execution plan → schemas/policies/tests.")
    print("Rule: propose changes through Git; do not become the source of truth or your own approver.")
    return 0


def next_tasks(root: Path) -> int:
    catalog = PublicCatalog.build(root)
    tasks = [obj for obj in catalog.objects if obj.kind == "task"]
    if not tasks:
        print("No public task contracts are currently discoverable.")
        return 0
    print_json({
        "catalog_id": catalog.catalog_id,
        "frontier": catalog.frontier,
        "tasks": [obj.as_dict(include_text=False) for obj in tasks[:20]],
        "instruction": "Read the immutable task contract and AGENTS.md before claiming work.",
    })
    return 0


def append_local_proposal(root: Path, kind: str, payload: dict[str, Any]) -> Path:
    from .core import digest, utc_now

    timestamp = utc_now()
    record = {
        "schema": f"https://epistemedia.com/schemas/{kind}-v1.json",
        "kind": kind,
        "recorded_at": timestamp,
        **payload,
    }
    record["id"] = f"em:{kind}:sha256:{digest(record)}"
    safe_time = timestamp.replace(":", "").replace("-", "")
    path = root / "runs" / "proposals" / f"{safe_time}-{record['id'].split(':')[-1][:12]}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return path


def stdio_mcp(root: Path) -> int:
    gateway = Gateway(root)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            request_id = request.get("id")
            method = request.get("method")
            params = request.get("params") or {}
            if method != "server/discover":
                version = params.get("protocolVersion")
                if version and version != gateway.mcp_method("server/discover", {})["protocolVersion"]:
                    raise ValueError(f"Unsupported protocol version: {version}")
            result = gateway.mcp_method(method, params)
            if request_id is not None:
                print(json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result}, sort_keys=True), flush=True)
        except Exception as exc:
            request_id = request.get("id") if isinstance(locals().get("request"), dict) else None
            print(json.dumps({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32000, "message": str(exc)}}, sort_keys=True), flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    command = args.command

    if command == "search" and args.remote:
        print_json(remote_get(args.api, "search", {"q": args.query, "limit": args.limit}))
        return 0
    if command == "get" and args.remote:
        print_json(remote_get(args.api, "objects/" + urllib.parse.quote(args.id, safe="")))
        return 0
    if command == "project" and args.remote:
        print_json(remote_get(args.api, "topics/" + urllib.parse.quote(args.slug, safe=""), {"lens": args.lens}))
        return 0

    root = resolve_root(args)
    assert root is not None

    if command == "orient":
        return orient(root)
    if command == "validate":
        errors = validate_repository(root)
        if errors:
            print_json({"valid": False, "errors": errors})
            return 1
        catalog = PublicCatalog.build(root)
        print_json({"valid": True, "catalog_id": catalog.catalog_id, "frontier": catalog.frontier, "objects": len(catalog.objects), "topics": len(catalog.topics)})
        return 0
    if command == "build":
        output = args.output if args.output.is_absolute() else root / args.output
        manifest = build_public(root, output, base_url=args.base_url, api_url=args.api_url, mcp_url=args.mcp_url)
        print_json(manifest)
        return 0
    if command == "audit":
        public = args.public if args.public.is_absolute() else root / args.public
        findings = audit_public(root, public)
        print_json({"ok": not findings, "findings": findings})
        return 1 if findings else 0
    if command == "serve":
        public = args.public if args.public.is_absolute() else root / args.public
        if not (public / "index.html").exists():
            build_public(root, public)
        os.chdir(public)
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.ThreadingTCPServer((args.host, args.port), handler) as server:
            print(f"Serving {public} at http://{args.host}:{args.port}")
            server.serve_forever()
        return 0
    if command == "api-serve":
        try:
            import uvicorn  # type: ignore
        except ImportError as exc:
            raise SystemExit("Install the server extra: pip install 'epistemedia[server]'") from exc
        os.environ["EPISTEMEDIA_ROOT"] = str(root)
        uvicorn.run("epistemedia.server:app", host=args.host, port=args.port, reload=False)
        return 0
    if command == "search":
        catalog = PublicCatalog.build(root)
        print_json({"catalog_id": catalog.catalog_id, "frontier": catalog.frontier, "query": args.query, "results": catalog.search(args.query, args.limit)})
        return 0
    if command == "get":
        catalog = PublicCatalog.build(root)
        obj = catalog.object_map().get(args.id)
        if not obj:
            raise SystemExit(f"unknown object: {args.id}")
        print_json({"catalog_id": catalog.catalog_id, "frontier": catalog.frontier, "data": obj.as_dict()})
        return 0
    if command == "project":
        from .core import topic_projection

        catalog = PublicCatalog.build(root)
        topic = catalog.topic_map().get(args.slug)
        if not topic:
            raise SystemExit(f"unknown topic: {args.slug}")
        print_json(topic_projection(catalog, topic, args.lens, DEFAULT_BASE_URL))
        return 0
    if command == "repo":
        if args.repo_command == "next":
            return next_tasks(root)
        if args.repo_command == "claim":
            path = append_local_proposal(root, "task-claim", {"task_id": args.task_id, "agent_id": args.agent, "status": "proposed"})
            print(path.relative_to(root))
            return 0
        if args.repo_command == "receipt":
            path = append_local_proposal(root, "run-receipt", {"task_id": args.task_id, "run_id": args.run, "command": args.run_command, "status": "reported"})
            print(path.relative_to(root))
            return 0
    if command == "mcp":
        if args.mcp_command == "serve":
            return stdio_mcp(root)
        if args.mcp_command == "discover":
            print_json(Gateway(root).mcp_method("server/discover", {}))
            return 0
    raise SystemExit(f"unhandled command: {command}")


if __name__ == "__main__":
    raise SystemExit(main())
