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
- `EM-0006` — owned `episte.media` deployment and public services (ready; external credentials required)
- `EM-0007` — `episte.media` protected identifier-namespace migration (ready; governance path and independent evaluation required)

Additional tasks should be small enough for independent verification and explicit enough that an unfamiliar agent does not need private conversational context to act safely.
