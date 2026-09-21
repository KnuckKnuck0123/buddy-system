# Buddy Sync Policy & Standard Operating Procedure

This document defines the canonical synchronization policy for the **Buddy System** across all agent harnesses, subagent hierarchies, and interactive sessions.

---

## 1. Core Objectives

1. **Continuous Memory Integrity**: Ensure operational rules, project statuses, technical stacks, and session logs remain perfectly synchronized with the canonical Obsidian Vault (`Buddy02 Vault`) and local agent memory (`noah_memory.json`).
2. **Multi-Harness Coherence**: Support seamless interaction across different AI frameworks (**Antigravity / Gemini CLI**, **Codex**, **OpenCode**) without state divergence or log fragmentation.
3. **Subagent Traceability**: Maintain clear parent-child lineage when subagents are spawned, ensuring subagent handoffs and task executions are attributed to their parent context.

---

## 2. Sync Triggers & Frequency Standard

### 2.1 End-of-Session Sync (Compulsory)
At the conclusion of every session turn or workspace interaction, the agent **MUST** execute:
```bash
buddy sync --conv-id <CONVERSATION_ID> --summary "<concise summary of work>" --next-steps "<next action>"
```
- **Summary**: Concise bullet points detailing what was accomplished and verified.
- **Next Steps**: Specific, actionable next steps for the next turn or subagent.

### 2.2 Subagent Delegation Policy
When a subagent is spawned:
1. **In-Flight Communication**: The subagent communicates progress via `send_message` or handoff logs.
2. **Subagent Session Sync**: If a subagent session is synced independently, it MUST include the `--parent-conv-id` and `--subagent-role` flags:
   ```bash
   buddy sync --conv-id <SUBAGENT_CONV_ID> --parent-conv-id <PARENT_CONV_ID> --subagent-role "<Role Name>" --summary "..." --next-steps "..."
   ```
3. **Parent Aggregation**: Upon receiving subagent completion notifications, the parent agent summarizes the subagent's contributions in its own final session sync.

### 2.3 Checkpoint / Mid-Session Sync
For long-running sessions or high-stakes milestones:
- Execute `buddy sync` upon completing significant code changes, refactors, or deployments.
- `buddy sync` operates **idempotently**: re-running sync for the same `conv_id` safely overwrites and updates the corresponding section in `Antigravity Journal.md` without duplicating entries.

---

## 3. Multi-Harness & Subagent Protocol

### 3.1 Harness Identification & Detection
`buddy sync` automatically detects the log source frame:
- **`GEMINI`**: Logged under `~/.gemini/*/brain/<conv_id>` (Antigravity CLI / IDE).
- **`CODEX`**: Logged under `~/.codex/sessions/**/rollout-*.jsonl`.
- **`OPENCODE`**: Logged in `opencode.db` SQLite database.

If auto-detection is ambiguous or a custom harness is used, override via:
```bash
buddy sync --conv-id <ID> --harness codex --summary "..." --next-steps "..."
```

### 3.2 State Conflict Resolution & Idempotency
- **Rules & Technical Ecosystem**: Merged as sets. Duplicate rules/tech items are automatically deduplicated (case-insensitive key normalization).
- **Active Projects**: Dictionary-merged by project name. Updating a project updates `noah_memory.json`, creates/updates the project brief (`01 - Projects/<Name>.md`), and updates the table row in `00 - Dashboards/Main Dashboard.md`.
- **Journal Entries**: Re-syncing overwrites the specific `### 🛠️ Session Archive: <conv_id>` section in `02 - Logs/Antigravity Journal.md`.

---

## 4. In-Chat Directives & Memory Extraction Syntax

During active conversation, users and agents can include explicit directives in prompts or messages. `buddy sync` scans conversation transcripts for these tags and automatically extracts them into structured memory:

| Directive Tag | Purpose | Example |
| :--- | :--- | :--- |
| `[rule]` or `[memory]` | Adds a global operational rule | `[rule] Always run tests before declaring a task finished.` |
| `[tech]` | Records a technical tool / dependency | `[tech] PyQGIS 3.34 with GDAL 3.8` |
| `[project]` | Registers/updates a project record | `[project] name: NaturalCAD, status: active, path: /Users/noahk/dev/naturalcad, next_action: Add mesh parser` |

---

## 5. Summary of Recommended CLI Commands

- **Standard End-of-Session Sync**:
  `buddy sync --conv-id <CONVERSATION_ID> --summary "<summary>" --next-steps "<next_steps>"`
- **Subagent Session Sync**:
  `buddy sync --conv-id <CONV_ID> --parent-conv-id <PARENT_ID> --subagent-role "<ROLE>" --summary "<summary>" --next-steps "<next>"`
- **Manual Project Update**:
  `buddy project "NaturalCAD" --status active --next-action "Implement UI sidecar" --path "/path/to/repo"`
- **Claim & Handoff**:
  `buddy claim "20260816-sync-policy" --owner "Gemini"`
  `buddy handoff "Completed sync policy formalization" --next "Enhance sync.py CLI args"`

---

## 6. Garbage Prevention & Signal Filtering

To keep the canonical Vault, memory files, and session logs clean and legible over time:

1. **System Prompt & Wrapper Stripping**:
   - Transcripts automatically unwrap XML elements like `<USER_REQUEST>` to preserve original human intent.
   - System metadata blocks (e.g. `<ADDITIONAL_METADATA>`, `<USER_SETTINGS_CHANGE>`, injected rule lists, rule file notifications) are automatically stripped out.

2. **File Artifact Filtering**:
   - System files, caches, and transient files (`.DS_Store`, `__pycache__`, `*.pyc`, `*.tmp`, `pruner_status.json`, `noah_memory.json`, `journal.md`, `.git/*`) are excluded from Workspace Actions.

3. **Command Noise Filtering**:
   - Trivial read-only commands (`ls`, `pwd`, `which`, `git status`) are omitted from executed command logs to prioritize meaningful shell actions.

4. **Idempotent Storage**:
   - Session archives are keyed by conversation ID. Re-running sync updates the existing session entry in place without creating duplicate journal headers.
