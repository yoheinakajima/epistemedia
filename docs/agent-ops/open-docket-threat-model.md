# Open-docket contribution threat model

The GitHub pilot treats the submitted proposal, source text, links, Markdown, and branch contents as
untrusted coordination input.

| Threat | Control |
| --- | --- |
| Prompt injection in sources | Sources are data; public instructions never authorize executing source instructions. |
| Contributor code execution | Submission-only CI runs accepted-base validator code and permits exactly three queue files. |
| Credential or private-context leakage | Recursive disclosure checks reject secret-shaped values, local paths, private/system prompts, hidden reasoning, and personal data. |
| Restricted-source redistribution | Proposal spans remain quote-minimal and attributed; action traces contain digests and status, never source payloads. |
| Payload splitting | Per-field, item-count, aggregate free-text, trace-byte, source-count, span-count, per-artifact, and aggregate-retrieval bounds fail closed. |
| Server-side request forgery | Proposal URLs reject local and legacy numeric addresses; promotion retrieval resolves every host to global addresses, disables proxies and redirects, and requires the final carrier URL. |
| Markdown or HTML injection | Human projection text is escaped and collapsed; the complete JSON record uses an injection-safe dynamic fence and Unicode-escaped HTML delimiters. |
| Self-review or Sybil review | The submission branch is never merged; promotion starts on a different branch from accepted `main`, and reviewer model, run, agent, and prompt identities must differ. |
| Forged or incomplete review | Review binds proposal ID, exact bytes/digest, source PR identity, and exact source/span coverage; promotion fails closed on drift or missing coverage. |
| Path traversal or repository overwrite | The base validator rejects every path outside one direct submission directory and rejects unsupported files. |
| Spam, replay, or duplicate proposal | Proposal ID and canonical digest are stable; duplicate submission directories and accepted slugs fail closed. |
| Workflow privilege escalation | Pull-request CI has read-only contents permission, no persisted credentials, no `pull_request_target`, and no deployment environment. |
| Self-integration | A trusted post-check `workflow_run` can ask the repository-scoped review-gate App to sign only an exact accepted-base-validated five-file promotion at its receipt head. The App can write checks but cannot write contents, approve, merge, or deploy. |
| Silent admission | A valid queue keeps the required check blocking. Only an accepted-base-validated promotion with a receipt-only child creates a clearly labeled open docket after protected merge and separate deployment. |
| Replay under a new slug | Accepted proposal IDs and canonical digests are globally unique; duplicates fail closed. |
| Forged reviewer identity | Agent, run, prompt, canonical model family, toolchain, and independently retrieved artifact set are typed, bound, and compared with the submitter trace. |
| Unchecked arithmetic or dependence | Results name typed dependencies and any calculations bind equations, inputs, source spans, outputs, uncertainty, and independent review dispositions. |

The pilot is not a general anonymous intake service. GitHub supplies authentication and abuse
controls. EM-0038 separately governs any future hosted MCP queue, retention system, or write-service
credential.

The trusted App check is an activation gate, not a substitute for evidence review. No cold-start
pilot may begin until the implementation is accepted on `main`, the App installation and exact
permissions are read back, protection requires `independent-review` from App ID `4766776`, and the
workflow secret and variable are configured. The check is emitted only after the separate review
receipt is pushed and accepted-base promotion validation succeeds at that exact head.
