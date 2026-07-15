# Operating Doctrine

Buddy System works only if the coordination protocol stays real.

## Minimum Protocol

Before substantive work:

- read the shared board
- check for overlapping claims
- claim a narrow task

During work:

- stay inside the claimed surface
- avoid broad rewrites while other harnesses are active
- update shared state only through known canonical paths

When stopping or switching:

- append a handoff
- record what changed
- record what was verified
- record the next step
- sync back to canonical memory when the bridge is available

## Source Of Truth Rules

- the shared vault or shared memory layer is canonical
- harness-local memory is helpful but non-canonical
- operator surfaces may render, compare, and stage actions
- operator surfaces must not silently fork reality

## Good Coordination Looks Like

- different harnesses have distinct lanes
- active claims are visible
- handoffs are short and current
- the operator can see what changed and who touched what
- the system can survive interruption

## Failure Modes

- everyone edits the same files without claims
- multiple agents silently maintain different truths
- UI polish advances faster than memory discipline
- provider differences are hidden until they cause errors
- writes happen without preview, confirmation, or traceability

## Required Behaviors

- be readable by a human under pressure
- be cheap enough to use every day
- be explicit enough to recover after interruptions
- be flexible enough for different harness personalities and strengths
