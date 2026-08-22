# Epistemedia Tasks

`tasks/contracts/` contains immutable accepted work contracts. A material change begins with a task contract or a narrowly authorized maintenance operation.

Task status transitions are append-only events or receipts; do not edit a merged contract to simulate progress. A later record may supersede an earlier contract while preserving its ID and history.

## Agent selection

```bash
python -m epistemedia repo next
```

Before claiming a task, read `AGENTS.md`, the contract, its dependencies, required evaluation, allowed paths, protected paths, acceptance predicates, and limitations.

## Current bootstrap sequence

- `EM-0001` — public interface bootstrap (completed)
- `EM-0002` — normative event envelope v0.1 (ready; governance path required)
- `EM-0003` — original production-domain activation contract (superseded by `EM-0004` after the owner corrected the domain)
- `EM-0004` — first corrected-domain activation contract (superseded by `EM-0006` after the owner selected `episte.media`)
- `EM-0005` — first protected namespace-migration contract (superseded by `EM-0007`)
- `EM-0006` — first owned-domain activation contract (superseded by `EM-0008` after selecting the canonical and sharing domains)
- `EM-0007` — first owned-domain namespace contract (superseded by `EM-0009`)
- `EM-0008` — canonical `epistemedia.org` deployment with `episte.media` sharing redirect (ready; external credentials required)
- `EM-0009` — `epistemedia.org` protected identifier-namespace migration (ready; governance path and independent evaluation required)
- `EM-0010` — deterministic local and CI generated-state contract (ready)
- `EM-0011` — canonical Apache-2.0 license text and detection (ready)
- `EM-0012` — remove the legacy root-level CI clock injection hook (blocked on `EM-0010`)
- `EM-0013` — harden public API identity and MCP 2026-07-28 transport conformance (ready)
- `EM-0014` — bound the container context and preserve accepted release identity (ready)
- `EM-0015` — make the installed wheel CLI self-contained (ready)
- `EM-0016` — correct public status and projection-shell defects (ready)
- `EM-0017` — implement the forensic-editorial public design system (ready; depends on `EM-0016`)
- `EM-0018` — implement a reversible claim-dossier model (ready; application-level, not protocol-normative)
- `EM-0019` — research the first How We Know lineage case (ready; depends on `EM-0018`)
- `EM-0020` — original first How We Know evidence-experience contract (superseded by `EM-0021` after exact-head review found its README authority incomplete)
- `EM-0021` — complete the first How We Know evidence experience with truthful compiled current-state documentation (ready; depends on `EM-0017` and `EM-0019`)
- `EM-0022` — harden Case 001 entry routes, public review trust, agent reachability, and release-identity parity (ready; depends on `EM-0021`)
- `EM-0023` — turn Case 001 into a living evidence report with a complete scoreboard ledger and deterministic share card (ready; depends on `EM-0022`)

Additional tasks should be small enough for independent verification and explicit enough that an unfamiliar agent does not need private conversational context to act safely.
