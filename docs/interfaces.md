# Human and Agent Interface Contract

Epistemedia does not maintain separate editorial truths for people, API clients, MCP agents, and local tools. Each interface adapts one disclosure-safe catalog and projection manifest.

## Public surfaces

| Interface | Purpose |
| --- | --- |
| Human HTML | Accessible exploration, lens switching, source and manifest inspection |
| Clean Markdown | Compact deterministic representation for agents and text-first readers |
| `llms.txt` | Curated orientation and selective retrieval map |
| JSON / JSON-LD | Structured catalog, object, projection, and manifest exchange |
| REST API | Free bounded reads and content negotiation |
| MCP | Read-only resources and tools for agent clients |
| CLI | Local-first sovereign realm operations plus optional remote reads |
| Bundles | Offline import, verification, self-hosting, replay, and federation |

## Equivalence invariant

For a selected realm, frontier, disclosure policy, epistemic policy, lens, and audience, all interfaces must expose the same:

- catalog and projection identity;
- accepted commit and event frontier;
- source object set;
- policy identifiers;
- compiler version;
- material status and limitations.

Representations may differ in layout and affordance. They may not silently differ in underlying evidence or evaluation.

## Human pages

A topic page should show the realm, frontier, epistemic policy, disclosure policy, lens, compiler, and compile time. Readers can inspect exact source objects, strongest challenges, independent lineages, derivations, before/after frontiers, and alternate policies.

HTML must remain useful without JavaScript. Interactive graph and lens controls are progressive enhancement.

## Markdown and `llms.txt`

Important HTML pages have deterministic Markdown twins. Root and path-scoped `llms.txt` files remain concise and route agents to deeper context instead of forcing one giant prompt. An optional `llms-full.txt` is a convenience snapshot rather than a required integration surface.

## API

Anonymous public reads are free within declared resource limits. Public knowledge is not paywalled, and complete snapshots remain downloadable for local operation. Expensive inference and unbounded projection compilation are separate resource concerns.

Every API response carries or links to catalog, frontier, accepted commit, policy, compiler, and manifest metadata.

Write endpoints, when introduced, create proposal or contribution objects. They do not directly mutate accepted truth, policy, or page state.

## MCP

The anonymous knowledge server is read-only. Typical resources include topics, objects, projections, policies, frontiers, tasks, and releases. Typical tools include search, exact object retrieval, trace, lens comparison, gap discovery, task discovery, and non-admitting bundle validation.

An authenticated contribution server may later create task claims, proposals, evidence objects, and run receipts. Its tools still cannot admit their own output.

## CLI

The CLI defaults to the user’s local realm. `--remote` explicitly selects the public service. Remote read commands do not require a local clone; local build, governance, and realm mutation commands require an explicit repository.

## Discovery

`/.well-known/epistemedia.json` identifies the realm, public catalog, accepted frontier, repository, API, OpenAPI, MCP, `llms.txt`, supported representations, protocol version, and release feeds. It is an Epistemedia project convention rather than an externally standardized well-known URI.

## Cross-interface tests

CI must test:

- catalog/frontier identity across HTML, Markdown, API, MCP, and CLI;
- deterministic rebuilds;
- deployment URL independence of canonical catalog identity;
- exact object and source trace equivalence;
- public disclosure noninterference;
- content negotiation and error behavior;
- MCP protocol and Origin handling;
- offline snapshot usability;
- stale generated-state detection.
