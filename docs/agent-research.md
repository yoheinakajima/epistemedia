# Agent research and proposal intake

Epistemedia separates five actions that a single “submit research” button would otherwise blur:

1. **Explore:** read an accepted case, its Markdown/JSON twins, and its exact evidence boundaries.
2. **Research:** investigate a bounded question under the public source, span, dependence,
   counterevidence, negative-result, runtime, and license protocol.
3. **Prepare:** produce a portable `epistemedia-research-proposal-v0.1` JSON bundle.
4. **Queue:** place that untrusted bundle into a coordination system with zero evidential credit.
5. **Review and admit:** independently re-root the evidence, then use a separate protected Git
   change to accept any durable object or public meaning.

Only the first three exist in EM-0037. Static files, local REST reads, read-only MCP tools, and the
CLI all expose the same protocol and case-seeded briefs. Validation proves structural and internal
reference closure; it does not prove truth.

## Cold-start instruction

Give an unfamiliar coding agent this instruction:

> Open <https://epistemedia.org/agents/research-protocol.md>. Research my question using that
> protocol and return one validated `epistemedia-research-proposal-v0.1` JSON bundle. Preserve
> counterevidence, negative results, inaccessible sources, and shared dependencies. Do not claim
> that the bundle was submitted, reviewed, or accepted.

The agent can also seed its scope from any case's `research-brief.md`.

## Why the future queue is separate

Case 002 establishes the relevant Sybil-defense rule: repeated runs receive zero automatic
independence credit. A write-capable intake service therefore cannot be the evidence graph and
cannot admit its own submissions. EM-0038 reserves a separate authenticated MCP authority with a
durable state machine (`submitted`, `triaged`, `needs-evidence`, `accepted-for-review`, `rejected`,
`withdrawn`), least-privilege coordination-only credentials, and no contents, workflow, deployment,
review, or merge authority.

Until that service is separately implemented and read back, hosted submission is unavailable.
Prepared bundles can be retained locally or passed to a human reviewer without implying queue or
acceptance state.
