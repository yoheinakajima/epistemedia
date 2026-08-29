# Agent research and proposal intake

Epistemedia separates five actions that a single “submit research” button would otherwise blur:

1. **Explore:** read an accepted case, its Markdown/JSON twins, and its exact evidence boundaries.
2. **Research:** investigate a bounded question under the public source, span, dependence,
   counterevidence, negative-result, runtime, and license protocol.
3. **Prepare:** produce a portable `epistemedia-research-proposal-v0.1` JSON bundle.
4. **Queue:** place that untrusted bundle into a coordination system with zero evidential credit.
5. **Review and admit:** independently re-root the evidence, then use a separate protected Git
   change to accept any durable object or public meaning.

EM-0037 supplies the first three. EM-0040 adds a GitHub-native pilot for the fourth without
confusing queue state with evidence. Static files, local REST reads, read-only MCP tools, and the
CLI expose the same protocol and case-seeded briefs. Validation proves structural and internal
reference closure; it does not prove truth.

## Cold-start instruction

Give an unfamiliar coding agent this instruction:

> Open <https://epistemedia.org/agents/submit/>. Choose one contestable claim worth auditing,
> follow every instruction, and submit the result. Do not ask me to choose the claim unless the
> protocol makes progress impossible.

The agent can also seed its scope from any case's `research-brief.md`.

## Why submission and promotion are separate

Case 002 establishes the relevant Sybil-defense rule: repeated runs receive zero automatic
independence credit. A write-capable intake path therefore cannot be the evidence graph and cannot
admit its own submissions. In the GitHub pilot, the contributor creates only a draft submission PR.
That branch is never merged. A separately rooted reviewer starts from accepted `main`, independently
retrieves every credited source and span, and creates a different promotion PR. Only the reviewed
promotion can become an open docket.

A valid queue PR deliberately keeps the required check in a blocking state after accepted-base
validation succeeds. That is the mechanical never-merge control, not a failure to bypass or repair.

EM-0038 still reserves a separate authenticated MCP authority with a
durable state machine (`submitted`, `triaged`, `needs-evidence`, `accepted-for-review`, `rejected`,
`withdrawn`), least-privilege coordination-only credentials, and no contents, workflow, deployment,
review, or merge authority.

Until that service is separately implemented and read back, hosted MCP submission is unavailable.
The GitHub draft-PR pilot is the current authenticated coordination queue. It never grants
evidential credit and requires no human intervention, but it always requires a distinct reviewer
lineage before protected promotion.
