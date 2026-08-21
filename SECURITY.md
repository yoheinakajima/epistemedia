# Security Policy

Epistemedia treats candidate code, repository text, imported sources, issue content, model output, and remote bundles as untrusted data. The project’s security boundary includes both conventional software integrity and epistemic integrity.

## Reporting

Use GitHub private vulnerability reporting for vulnerabilities that could expose secrets, private realm content, deployment credentials, signing material, personal data, or privileged integration paths. Do not place exploit details or private source material in a public issue.

## Supported releases

The latest tagged minor release receives security fixes. Earlier releases may receive a forward-only disabling advisory when replay or disclosure safety cannot be preserved.

## Critical invariants

- Untrusted pull-request workflows receive read-only repository access and no secrets.
- Candidate code cannot weaken and then use its own validator, policy, workflow, or promotion predicate.
- Trusted integration loads authority and policy from the accepted base commit, pins the candidate SHA, and records an immutable decision receipt.
- Public evaluation operates only on a disclosure-safe `PublicProjection`.
- Private-only changes cannot alter public wording, status, ranking, counts, topology, or recommendations unless disclosure policy explicitly permits the effect.
- Remote signatures prove origin and integrity, not competence, relevance, or truth.
- Stable identifiers and accepted append-only records are never silently repurposed.

## Threat classes

The test and governance program should cover at least:

- source prompt injection and tool-instruction laundering;
- malicious repository instructions in nested files;
- dependency and workflow supply-chain compromise;
- secrets in generated output, logs, bundles, and error messages;
- public inference from hidden evidence;
- source laundering and copied-evidence replication illusions;
- model, prompt, retrieval, and training-lineage monoculture;
- evaluator collusion and self-authorization;
- Sybil identities and contribution flooding;
- ontology poisoning and false entity equivalence;
- strategic uncertainty, confidence gaming, and Goodhart effects;
- replay ambiguity, mutable source URLs, and digest substitution;
- resource-exhaustion attacks against compilers, API, MCP, and federation imports;
- server-side request forgery and unsafe source retrieval;
- cross-origin MCP invocation and confused-deputy authorization;
- denial, deletion, or suppression of negative and minority results.

## Deployment

Production deployments must pin an accepted commit or signed release, expose the catalog/frontier/manifest identity, run as an unprivileged process, use read-only filesystems where feasible, enforce request and resource limits, and keep contribution authority separate from anonymous public reads.
