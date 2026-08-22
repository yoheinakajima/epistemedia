# `prepublic-ready` branch cleanup read-back

Status: completed and externally verified on 2026-08-22 UTC.

This append-only record closes the deferred branch cleanup authorized by
[`2026-08-22-pages-bootstrap.md`](2026-08-22-pages-bootstrap.md). It records an
external repository mutation and its provider read-back; it does not change
accepted knowledge or recreate the deleted reference.

## Authorization and exact target

- accepted authorizing commit: `a6669fc5cbdb38c4ce673b2d3dced6080b5c9d30`
- authorizing pull request: `#19`
- deleted reference: `refs/heads/prepublic-ready`
- reference tip before deletion: `9cf66ef15fc842531619364529086d6061dc7aab`
- tip tree: `c3be9b724f3b15e6864c86974bd1e865eb10e007`
- promoted ancestor commit: `986e33a09658f1c0fdb0c67668681201ac0ff080`
- promoted tree: `03bc33f8dc1de76abc871bfd23cd2e2f853bc623`

The exact remote reference was deleted through GitHub's Git References API
only after the authorizing record was accepted on `main`. No administrator
bypass, force push, history rewrite, tag deletion, or commit deletion was used.

## Provider and repository read-back

Read-back completed at `2026-08-22T02:01:08Z`:

- `GET /repos/yoheinakajima/epistemedia/git/ref/heads/prepublic-ready`
  returned HTTP `404 Not Found`;
- `git ls-remote --heads origin prepublic-ready` returned no reference;
- `git fetch --all --prune` removed the stale local remote-tracking reference;
- neither GitHub nor the refreshed checkout lists `origin/prepublic-ready`;
- `main` and `origin/main` both resolved to the accepted authorizing commit
  before this follow-up candidate was created.

Both recorded commits still pass `git merge-base --is-ancestor <commit> main`.
Their recorded tree hashes also reproduce locally. The deletion therefore
removed only the obsolete branch name. Its history remains reachable from
accepted `main`, and an administrator could recreate the reference at
`9cf66ef15fc842531619364529086d6061dc7aab` if a future recovery need were
explicitly authorized.

## Limitations

- GitHub does not expose a branch-deletion timestamp through the Git References
  read endpoint after deletion; this record preserves the exact target,
  authorizing commit, and first post-deletion read-back instead.
- This cleanup is not evidence that custom-domain DNS, the hosted API or MCP
  runtime, or any release registry is active.
