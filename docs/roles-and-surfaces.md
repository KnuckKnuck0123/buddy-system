# Roles and Surfaces

Buddy System separates roles so multiple harnesses can collaborate without collapsing into duplication.

## Roles

### Orchestrator

Owns:

- routing work
- maintaining continuity
- deciding what is active, blocked, or context
- keeping the system coherent across sessions

### Interface / Experience

Owns:

- the operator surface
- composition, layout, and interaction
- making the system legible enough to use in real time

### Domain / State

Owns:

- typed shared-state contracts
- canonical adapters and ingestion logic
- validation and source-health rules

### Runtime / Harness Control

Owns:

- launching and resuming harnesses
- session lifecycle and process state
- normalized runtime events

### Review / Security

Owns:

- architecture sanity checks
- source-of-truth integrity
- write-path safety
- visibility into coordination failures

## Surfaces

### Canonical Memory Surface

Human-readable shared memory and project context.

### Operator Surface

The live command deck where the human can:

- inspect state
- talk to harnesses
- compare providers
- route work
- review handoffs

### Mobile Edge

A lightweight remote channel for:

- quick instructions
- approvals
- redirects
- thought capture

## Example Split

- canonical memory: shared vault + sync bridge
- operator surface: TUI cockpit
- mobile edge: chat or messenger
- specialist harnesses: different providers under one roof
