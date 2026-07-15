# Security

Buddy System is local-operator software that reads and writes project memory surfaces. Treat it accordingly.

## Current Risk Areas

- `buddy sync` mutates configured canonical files directly
- transcript parsers assume trusted local logs and local filesystem access
- configuration can point at sensitive journals, vaults, or session stores
- parser behavior may vary across provider transcript formats

## Safe Usage Guidance

- test against disposable or version-controlled memory files first
- keep backups of canonical memory surfaces
- review config paths before running sync commands
- do not expose local transcript stores or journals through unreviewed network services
- prefer a staged preview/confirm model for any public or team-shared deployment

## Reporting

If you find a bug or unsafe write-path behavior, document:

- what file or surface was touched
- what command triggered it
- what transcript/provider shape caused it
- whether the issue can corrupt or leak canonical memory

This repository does not yet claim hardened production security. It is an early open-source seed and should be treated with operator caution.
