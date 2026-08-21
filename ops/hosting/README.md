# Hosting Operations

`github.json` is the declarative desired state for repository visibility, features, merge policy, branch protection, Pages, packages, and domains. A privileged reconciler may compare it with GitHub and deployment-provider state, but it must not silently treat external state as canonical.

## Reconciliation

1. Load desired state from the accepted base commit.
2. Read current provider state with least-privilege credentials.
3. Produce a dry-run diff.
4. Reject changes outside the task contract.
5. Apply bounded changes.
6. Re-read provider state.
7. run production identity, TLS, redirect, API, MCP, and disclosure tests.
8. Append a run receipt containing provider object IDs, timestamps, commands/actions, before/after state, accepted commit, catalog, frontier, deployment manifest, and limitations.

Do not store domain, cloud, package, signing, or GitHub credentials in the repository. Deployment runtimes must not receive contribution or integration authority.
