# Python package release-readiness evidence

Status: clean-install blocker corrected locally; no package or release published.

Task `EM-0015` was opened after an editable checkout and `make check` passed but
a wheel installed into a clean Python 3.11 virtual environment could not even
run `epistemedia --version`.

## Failure reproduced

The first locally built `0.2.0` artifacts were:

- wheel SHA-256: `3fe8f709c632983ac8962db3b1f33fe0bd32080302fbac607ef951c1e37c8b4b`
- source distribution SHA-256: `e3a3f243f438f802a4724de7c1e9fcde1ac9770f34e372c14707551c0fdfab00`

After a no-dependency wheel install, Python 3.11 raised an `AttributeError`
while executing the gateway's `Request` dataclass. The private implementation
module was not in `sys.modules`; checkout-level `sitecustomize.py` files had
masked that missing loader responsibility during local tests.

## Correction and regression boundary

The lazy gateway loader now registers its private module before executing it
and removes the partial module if execution fails. Both root and `src`
compatibility `sitecustomize.py` hooks are removed. An isolated subprocess test
starts outside the checkout, ignores `PYTHONPATH`, inserts only the packaged
source directory, imports the CLI, and requires the exact version output.

The corrected `0.2.0` artifacts built with `build==1.5.0` are:

- wheel SHA-256: `d38e4c71d15ec462537b8616e9821f723bb544715d4e4a3be890592d8512040e`
- source distribution SHA-256: `d07821d834760b096dbb28f2718b90471c5649361caf7179fe7481a89718cd18`

A new Python 3.11 virtual environment installed the wheel with `--no-deps`
from outside the repository. `epistemedia --version` returned
`epistemedia 0.2.0`, and an isolated `import epistemedia.server` exposed
`Gateway` successfully. The wheel metadata reports:

- name: `epistemedia`
- version: `0.2.0`
- Python: `>=3.11`
- license expression: `Apache-2.0`
- license file: `LICENSE`

The wheel contains the CLI entry point and canonical license; neither package
artifact contains a `sitecustomize` module.

## Remaining publication gates

- No release tag exists and no version has been authorized as the first public
  release.
- No GitHub Release, GHCR image, PyPI project, or MCP Registry version was
  created.
- The registry descriptor's PyPI stdio entry invokes `epistemedia mcp serve`,
  which is a local-realm command and still requires a repository through the
  current directory or `--root`. Do not publish that package entry as a
  standalone `uvx` server until a bundled disclosure-safe snapshot or a
  deliberate remote-proxy contract is accepted and tested.
- The corrected hashes are local candidate evidence, not release checksums;
  artifacts must be rebuilt from the eventual accepted release tag.
