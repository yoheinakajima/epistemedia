# Reversible claim dossiers

Status: reversible alpha application contracts exercised by two reviewed vertical slices.

The dossier module represents enough structure to test a real **How We Know** case without promoting an early model into the Epistemic Mesh protocol. It lives in `epistemedia.dossier`, not `schemas/`, and may change incompatibly while the pilot is measured.

No dossier is accepted merely because it validates. Validation establishes shape, integrity, referential closure, and disclosure safety—not truth, evidentiary quality, licensing permission, or governance acceptance.

## Identity model

Every record has two identities:

- `key` is a short dossier-local reference used to connect records and make cycles reviewable;
- `id` is a content address over the complete record except its own `id` field.

The dossier has a content-addressed `dossier_id` over the full document except that field. Local keys are not global identifiers. Adapters expose content IDs; authors use keys only inside the dossier package.

Strict validation rejects missing fields, extra fields, duplicate keys, duplicate stable IDs, malformed content addresses, and dangling references.

## Object layers

| Collection | Application meaning |
| --- | --- |
| `source_works` | Logical identity of a paper, page, dataset, report, instrument output, or other source |
| `editions` | Exact retrieved version and bytes or canonical JSON actually examined |
| `spans` | Exact text-offset quote or JSON Pointer value plus locator and digest |
| `propositions` | Semantic statement and scope without endorsement or global status |
| `assertions` | An actor’s dated stance toward a proposition, grounded in exact spans and one explicit lineage |
| `lineages` | Known or unknown dependence state, dimensions, roots, dependencies, and member assertions |
| `evidence_relations` | Support, rebuttal, qualification, undercutting, replication, failed replication, or dependence |
| `claim_families` | A bounded question joining related propositions, assertions, and evidence relations |
| `evaluations` | A label and reason codes produced under an explicit policy and frontier |

Propositions do not contain `truth`, `confidence`, `probability`, or similarly intrinsic verdict fields. Those field names are forbidden recursively. A policy-relative evaluation is a separate record and cannot silently become a property of the proposition.

## Works, editions, and exact spans

A source work and an examined edition must remain different records. An edition stores:

- its work reference and edition label;
- retrieval time with timezone;
- media type;
- exact text or structured JSON content used by the pilot;
- SHA-256 digest and byte length.

A text span gives start and end character offsets, a human-readable locator label, the exact quote, and its SHA-256 digest. Validation rejects out-of-bounds offsets, quote mismatches, and digest mismatches.

A structured span gives a JSON Pointer, label, exact selected value, and digest over canonical JSON. The alpha model intentionally supports only content that can be checked locally and deterministically; an inaccessible URL or citation label cannot stand in for examined bytes.

License and snapshot decisions still belong to research review. The model’s ability to store content does not grant permission to commit copyrighted source material.

## Lineage and independence

Every assertion points to exactly one lineage, and that lineage must list the assertion. A lineage is either:

- `known`, with declared dependence dimensions and zero or more lineage dependencies; or
- `unknown`, with an explicit note stating that its lineage is unknown.

Dependence cycles fail validation. The reference independence summary collapses known dependent lineages to their known roots. Unknown lineages contribute to an explicit unknown count and receive zero automatic independence credit. A known lineage that ultimately depends on an unknown lineage also receives no root credit for that path.

The calculation is instrumentation for the pilot, not a universal evidence-scoring policy.

## Disclosure ordering and noninterference

`public_dossier()` validates the complete package, removes private records, recomputes the public dossier content address, and validates referential closure again. A public record that depends on a removed private record fails closed.

The source dossier ID may change when private records change. The public dossier ID and every public adapter must remain byte-for-byte unchanged when only disconnected private records change. Tests exercise this noninterference contract.

## Interface parity

`DossierProjection` begins from the disclosure-safe public dossier and exposes:

- deterministic JSON;
- Markdown;
- semantic HTML;
- an API-style envelope;
- an MCP resource;
- CLI JSON text.

Every form carries the same public `dossier_id`. After independent review, an explicit application
manifest may bind one exact dossier and review receipt into the public compiler. The compiler scans
accepted manifests in deterministic order and rejects duplicate case numbers, slugs, dossier
identities, source paths, generated routes, and MCP resource URIs. Each profile binds exact dossier
and review-receipt bytes, format, reviewer identity, reviewed head, and independence checks before
producing HTML, Markdown, static JSON, local API, MCP, and CLI representations from the same
disclosure-safe object. This makes the dossier publicly discoverable on the static site; it does
not activate the reserved hosted API/MCP runtime.

## Construction and validation

```python
from epistemedia.dossier import DossierProjection, stamp_dossier, validate_dossier

dossier = stamp_dossier(application_material_without_ids)
validate_dossier(dossier)
public_projection = DossierProjection.from_dossier(dossier)
print(public_projection.id)
```

The synthetic fixture builder and adversarial mutations are in `tests/test_dossiers.py`. The first
two real applications are selected in `catalog/dossiers/`: Case 001 preserves its legacy feature
profile, while Case 002 uses a separate agent-citation-lineage profile with different count units
and display grammar. Both remain byte-bound to their independent review receipts. Synthetic
fixtures demonstrate mechanics only and make no empirical or philosophical claims.

## Promotion boundary

This format must not be copied into `schemas/` or described as protocol v1 without a later normative task, independent evaluation, compatibility analysis, and migration plan. The pilot should first reveal which fields survive real source work, exact-span review, lineage adjudication, and two genuinely different policy evaluations.
