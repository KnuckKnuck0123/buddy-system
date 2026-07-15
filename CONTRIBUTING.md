# Contributing

Buddy System is still early. Keep contributions narrow, readable, and reversible.

## Priorities

- preserve the coordination doctrine
- keep canonical memory human-readable
- avoid hidden automation that silently rewrites source-of-truth files
- make provider-specific behavior explicit instead of flattening it away

## Good First Areas

- transcript adapters for additional local harnesses
- tests for parser edge cases and failure modes
- docs and examples for different local setups
- safer staging and preview flows for writes
- protocol-level clarification, not just UI polish

## Contribution Style

- keep changes focused
- explain the coordination impact, not just the code change
- include or update tests when behavior changes
- document any new config keys or transcript assumptions
- avoid committing local caches, machine-specific paths, or secrets

## Before Opening Work

- run the test suite
- check for local-path leakage
- check for accidental cache artifacts such as `.DS_Store` and `__pycache__`
- call out any write-path risk in the PR or handoff
