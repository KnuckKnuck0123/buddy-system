# Local Architecture Example

This document shows one example of how Buddy System can be wired on a local machine. Adapt the paths and harness list to your own setup.

---

## 🏗️ System Diagram

```mermaid
graph TD
    subgraph Agent Harnesses
        AG[Gemini-compatible Harness]
        CX[Codex CLI]
        OC[OpenCode Shell]
        CL[Operator Harness]
    end

    subgraph The Sync Bridge
        BY[Buddy CLI]
    end

    subgraph Canonical Memory (Obsidian Vault & JSON)
        MEM[noah_memory.json]
        JRN[Work Journal.md]
        
        subgraph Shared Vault
            BD[Main Dashboard.md]
            CB[Agent Coordination Board.md]
            HL[Agent Handoff Log.md]
        end
    end

    %% Read Operations
    AG -- Reads --> MEM
    CX -- Reads --> MEM
    OC -- Reads --> MEM
    CL -- Reads --> MEM
    
    %% Coordination
    AG -- Claims/Handoffs --> CB & HL
    CL -- Claims/Handoffs --> CB & HL

    %% Write/Sync Loop
    AG -- Generates Logs --> BY
    CX -- Generates Logs --> BY
    OC -- SQLite Logs --> BY
    
    BY -- Syncs & Updates --> MEM
    BY -- Syncs & Updates --> JRN
    BY -- Syncs & Updates --> BD
```

---

## Directories & Files Matrix

Here is one example of where each component can live:

| Component | Path | Purpose |
| :--- | :--- | :--- |
| **Global Memory** | `~/.config/buddy/memory.json` | Structured JSON store of active rules, tech stack details, and active project paths. |
| **Obsidian Vault** | `~/BuddyVault/` | Human-readable dashboard, project indices, logs, and coordination surfaces. |
| **Coordination Board** | `03 - Resources/Workspace/Agent Coordination Board.md` | Shared task board. Agents claim tasks here before starting edits to avoid collisions. |
| **Handoff Log** | `02 - Logs/Agent Handoff Log.md` | Chronological append-only handoff records detailing changes, verified tests, decisions, and blockers. |
| **Work Journal** | `~/.local/state/buddy/journal.md` | Evergreen markdown file logging transcript summaries, prompts, and workspace edits. |
| **Buddy Executable** | `~/.local/bin/buddy` | Global script wrapper executing the CLI codebase. |
| **CLI Codebase** | `~/Documents/GitHub/buddy-system/` | Python source code, configuration parser, and test suite. |

---

## ⚡ The Log Synchronization Pipeline

When you run `buddy sync`:

1. **Scan Directories:** The tool scans local folders to find the most recently modified transcript file:
   * **Gemini-compatible harnesses:** Looks in configured `brain_dirs` for the newest transcript file.
   * **Codex CLI:** Looks in the configured `codex_sessions_root` for `rollout-*.jsonl` files.
   * **OpenCode:** Queries the configured SQLite history database.
2. **Transcript Parsing:** It reads the transcript line-by-line:
   * Extracts user prompts, commands executed, and files created/modified.
   * Extracts tags inside prompts (e.g., `[rule] Write descriptive commit messages` or `[tech] Bun` or `[project] name: MyProject`).
3. **Reconciliation:**
   * Appends rules and tools to the configured memory JSON.
   * Formats a session summary and appends it to the configured work journal.
   * Updates the project matrix in the vault dashboard and generates project brief templates for new projects.
