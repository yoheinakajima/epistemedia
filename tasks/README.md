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
- `EM-0024` — clarify why Epistemedia matters, compress first-read typography, state review-process independence honestly, and reconcile distinct-object versus topic-membership counts (ready; depends on `EM-0023`)
- `EM-0025` — preserve the conceptual vocabulary and select a bounded Case 002 editorial roadmap without beginning research or admission (ready; depends on `EM-0024`)
- `EM-0026` — research Case 002 through an eight-run public agent-citation trace pilot with exact source and warrant lineage (ready; depends on `EM-0025`)
- `EM-0027` — map primary-source readiness for GPT-4 bar percentile, Mehrabian 7–38–55, and fact-check effectiveness in parallel (ready; depends on `EM-0025`)
- `EM-0028` — make topic projections human-readable and expose deterministic object, source, and topic interlinks (ready; depends on `EM-0024`)
- `EM-0029` — construct and independently review the reversible Case 002 agent-citation-lineage dossier (ready; depends on `EM-0026`)
- `EM-0030` — admit Case 002 into a deterministic multi-case How We Know library (ready; depends on `EM-0028` and `EM-0029`)
- `EM-0031` — close EM-0027 accurately and record the four-live-case gate before broad launch and promotion (ready; depends on `EM-0027` and `EM-0030`)
- `EM-0032` — research the Case 003 GPT-4 bar-exam percentile and comparison-class lineage (ready; depends on `EM-0027` and `EM-0031`)
- `EM-0033` — research the Case 004 Mehrabian 7-38-55 proposition and derivation lineage (ready; depends on `EM-0027` and `EM-0031`)
- `EM-0034` — construct and independently review the reversible Case 003 GPT-4 bar-exam dossier (ready; depends on `EM-0032`)
- `EM-0035` — construct and independently review the reversible Case 004 Mehrabian 7-38-55 dossier (ready; depends on `EM-0033`)
- `EM-0036` — admit Cases 003 and 004 into a deterministic four-case How We Know library (ready; depends on `EM-0030`, `EM-0034`, and `EM-0035`)
- `EM-0037` — polish Cases 002–004 and publish a cold-start, non-admitting agent research kit (ready; depends on `EM-0036`)
- `EM-0038` — govern a separate authenticated MCP research-submission queue with no admission or merge authority (ready; depends on `EM-0037`; governance path required)
- `EM-0039` — publish the versioned mission, four-case narrative, reader-first navigation, and real-reader comprehension instrument without changing accepted evidence or implementing the submission queue (ready; depends on `EM-0037`)
- `EM-0040` — pilot a cold-start autonomous GitHub-native docket contribution from one public URL through independent non-author review and protected publication (ready; depends on `EM-0037` and `EM-0039`; governance path required)
- `EM-0041` — preserve the failed first docket pilot, harden provenance and sentence-level closure, and rerun the cold-start path without hand repair (ready; depends on `EM-0040`; governance path required)
- `EM-0042` — preserve the failed second docket pilot and close its selection, clock, and exact-head gaps before a third cold start (ready; depends on `EM-0041`; governance path required)
- `EM-0043` — adopt the owner-approved Register design system across every generated human surface while preserving accepted evidence and machine-readable twins (ready; depends on `EM-0039` and `EM-0042`)

Additional tasks should be small enough for independent verification and explicit enough that an unfamiliar agent does not need private conversational context to act safely.
