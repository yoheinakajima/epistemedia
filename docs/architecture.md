# Epistemedia Architecture

## System thesis

Epistemedia is not an autonomous wiki whose canonical object is a page. Its canonical substrate is an append-only, provenance-preserving epistemic history. Pages and agent responses are reproducible projections over that history.

```text
content-addressed source artifacts
             +
append-only epistemic event logs
             +
versioned ontologies and policies
             │
             ▼
    deterministic graph replay
             │
             ▼
 disclosure-safe PublicProjection
             │
             ▼
 policy-relative evaluation
             │
             ▼
      projection compiler
 ┌────────┬──────────┬──────┬─────┬────────┐
 HTML   Markdown    JSON    API   MCP      CLI
```

## Canonical object layers

The protocol separates objects that conventional fact graphs often collapse:

| Object | Meaning |
| --- | --- |
| Source work | A logical paper, site, dataset, conversation, instrument output, or other source identity |
| Edition or snapshot | The exact version and immutable bytes actually examined |
| Source span | Exact passage, table, region, row, frame, or timestamp |
| Observation | What an actor or instrument detected in a source span or the world |
| Proposition | Semantic content independent of endorsement |
| Assertion | An actor’s act of asserting, denying, predicting, questioning, or hypothesizing a proposition |
| Evidence relation | Support, rebuttal, qualification, undercutting, replication, dependence, or failed replication |
| Method or derivation | Procedure, inputs, code, model, prompt, parameters, and transformations |
| Evaluation | A policy-relative assessment over an explicit frontier and disclosure boundary |
| Projection | A page, dossier, graph, API result, or task compiled from evaluated state |
| Governance record | A proposal, evaluator result, canary, promotion, rejection, quarantine, or fork |

A proposition is n-ary and may include predicate, arguments, scope, valid time, modality, polarity, quantities, units, conditions, and terminology context. RDF/JSON-LD triples are useful exchange views but are not the only canonical semantic form.

## Time model

Core records distinguish:

- **valid time:** when a represented condition applies in the world;
- **observed time:** when an actor or instrument encountered it;
- **recorded time:** when a realm accepted it into history.

Capture, publication, derivation, import, evaluation, and compilation times are additional event metadata.

## Storage model

1. **Artifact store:** immutable bytes and structured packages, addressed by digest.
2. **Event log:** authoritative append-only mutations.
3. **Graph projection:** deterministic semantic and epistemic relations.
4. **Evaluation materialization:** policy outputs with reason codes and vectors, never global truth fields.
5. **Search indexes:** disposable derived acceleration structures.
6. **Reader projections:** disposable pages, dossiers, Markdown, API, MCP, and CLI output.
7. **Reactive behaviors:** research, revalidation, contradiction search, import, and governance automation.

## Evaluation

Truth-like status is computed as:

```text
Evaluate(
  claim family,
  accepted event frontier,
  ontology alignments,
  epistemic policy,
  disclosure boundary,
  audience or task
)
```

An evaluation may report direct and indirect support lineages, challenges, qualifiers, method validity, scope match, temporal relevance, source custody, replication, dependencies, unresolved defeaters, uncertainty, status, and reason codes.

Different policies may produce different statuses from the same accepted history. The system preserves both without corrupting the underlying claims.

## Evidence independence

Agent count is not evidence independence. The mesh tracks dependence across source, data, experiment, apparatus, method, model family, retrieval corpus, prompt family, prior conclusions seen, and social exposure. Unknown dependence does not receive automatic independence credit.

## Federation

A sovereign **realm** owns its constitution, event log, schemas, ontologies, alignments, policies, trusted roots, subscriptions, imports, exports, disclosure, and resource allocation.

A federation exchange follows:

```text
produce content-addressed bundle
→ attest origin
→ verify envelope and dependencies
→ check schema, license, safety, and disclosure
→ quarantine
→ evaluate under local import policy
→ accept, partially accept, map, defer, or reject
→ append a local import receipt
```

A signature establishes origin and integrity. It does not establish truth or local acceptance. Ontology mappings are themselves versioned, sourced, contestable propositions.

## Public projection ordering

The safe order is:

```text
canonical replay
→ disclosure eligibility
→ field policy
→ referential closure
→ sanitized PublicProjection
→ public epistemic evaluation
→ selection and ranking
→ narrative generation
→ rendering
→ noninterference audit
```

Evaluating with private evidence and merely hiding the private citation leaks information through status, ranking, wording, and topology. All public interfaces consume the same sanitized projection.

## Deployment identity

Catalog and frontier identities exclude deployment URLs and timestamps. A local node, GitHub Pages mirror, and `epistemedia.com` may expose different links while representing the same accepted catalog. Rendered release manifests include deployment-specific files and therefore identify the exact published representation separately.
