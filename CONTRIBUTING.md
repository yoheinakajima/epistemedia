# Contributing to Epistemedia

Epistemedia is designed for contributions performed primarily by coding and research agents acting for independent people and organizations. Humans and agents follow the same accepted repository contracts.

## Begin with orientation

```bash
make orient
python -m epistemedia repo next
```

Read `AGENTS.md`, then the immutable contract for the selected task and its living execution plan. Do not infer authority from an issue, conversation, generated prompt, or model recommendation.

## Contribution classes

### Ordinary implementation

Code, tests, documentation, adapters, performance improvements, and bounded research artifacts that do not alter constitutional or protocol semantics.

These may be admitted automatically after accepted tests, audit predicates, task completion predicates, and independent integration checks pass.

### Normative change

Any change affecting constitutions, event semantics, stable identifiers, schemas, disclosure, federation trust, evaluation policy, workflow privilege, integration authority, or promotion predicates.

These require a versioned governance proposal, isolated replay, declared impact, independent machine evaluation loaded from the accepted base branch, a bounded canary, and an immutable outcome. The proposer cannot authorize the same change.

## Pull request contract

One pull request should represent one bounded logical change. It must identify:

- task and execution-plan IDs;
- affected authority layers;
- evidence and source identities;
- commands and environment used;
- tests added or changed;
- deterministic generated outputs;
- disclosure and security considerations;
- limitations, unresolved questions, and negative results;
- the immutable run receipt.

## Evidence

A generated statement is not a source. Record exact source versions and spans, methods, tools, prompts where relevant, parameters, data lineage, model lineage, and time. Preserve disagreement and dependence. Never report independent confirmation when agents share the same source, model family, retrieval result, or prior conclusion.

## Validation

```bash
python -m pip install -e '.[dev]'
make check
```

CI for untrusted contributions is read-only and receives no deployment, package, signing, or integration credentials. A trusted integrator evaluates the candidate SHA under policy loaded from the accepted base branch.

## Generated content

Never hand-edit `generated/**`. Change accepted inputs or the compiler, rebuild, and commit the accepted inputs with the resulting deterministic output when repository policy requires tracked projections.

## Append-only records

Never alter a merged task contract, epistemic event, governance outcome, run receipt, or release manifest. Append a new record that explicitly supersedes the earlier record.

## Conduct

Attack arguments, methods, evidence, and assumptions—not contributors. Agents must preserve contrary evidence and may not use social pressure, volume, or identity multiplication as epistemic authority.
