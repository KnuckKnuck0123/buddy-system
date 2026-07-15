import os
import re
import sys
import json
import sqlite3
import subprocess
from datetime import datetime
from .memory import (
    load_json_file,
    save_json_file,
    check_and_create_project_brief,
    update_dashboard_table,
    update_project_index
)

def log_info(msg):
    print(f"[*] {msg}")

def log_success(msg):
    print(f"[\033[32m+\033[0m] {msg}")

def log_error(msg):
    print(f"[\033[31m-\033[0m] {msg}", file=sys.stderr)

def get_latest_conv(config):
    convs = []
    
    # 1. Scan configured Gemini-compatible brain directories
    for brain_dir in config["brain_dirs"]:
        if not os.path.exists(brain_dir):
            continue
        for name in os.listdir(brain_dir):
            path = os.path.join(brain_dir, name)
            if os.path.isdir(path) and name != "tempmediaStorage":
                log_dir = os.path.join(path, ".system_generated", "logs")
                mtime = os.path.getmtime(path)
                for file_check in ["transcript.jsonl", "transcript_full.jsonl"]:
                    fp = os.path.join(log_dir, file_check)
                    if os.path.exists(fp):
                        mtime = max(mtime, os.path.getmtime(fp))
                        break
                convs.append((name, mtime, path, "gemini"))
                
    # 2. Scan Codex sessions recursively
    codex_root = config["codex_sessions_root"]
    if os.path.exists(codex_root):
        for root, dirs, files in os.walk(codex_root):
            for file in files:
                if file.endswith(".jsonl") and "rollout-" in file:
                    fp = os.path.join(root, file)
                    mtime = os.path.getmtime(fp)
                    match = re.search(r"rollout-.*-([a-fA-F0-9-]+)\.jsonl", file)
                    if match:
                        conv_id = match.group(1)
                        convs.append((conv_id, mtime, fp, "codex"))

    # 3. Scan OpenCode sessions
    opencode_db = config["opencode_db"]
    if os.path.exists(opencode_db):
        try:
            result = subprocess.run(
                ["opencode", "session", "list", "--format", "json"],
                capture_output=True,
                text=True,
                check=True,
            )
            for session in json.loads(result.stdout):
                convs.append((session["id"], session.get("updated", 0) / 1000, session["id"], "opencode"))
        except Exception:
            pass
                        
    if not convs:
        return None, None, None
        
    convs.sort(key=lambda x: x[1], reverse=True)
    return convs[0][0], convs[0][2], convs[0][3]

def find_conv_by_id(conv_id, config):
    # Try configured Gemini-compatible brain directories
    for brain_dir in config["brain_dirs"]:
        test_path = os.path.join(brain_dir, conv_id)
        if os.path.exists(test_path):
            return test_path, "gemini"
            
    # Try Codex rollouts
    codex_root = config["codex_sessions_root"]
    if os.path.exists(codex_root):
        for root, dirs, files in os.walk(codex_root):
            for file in files:
                if file.endswith(".jsonl") and conv_id in file:
                    return os.path.join(root, file), "codex"

    if conv_id.startswith("ses_"):
        return conv_id, "opencode"
                    
    return None, None

def scaffold_journal(journal_file):
    if os.path.exists(journal_file):
        return
    log_info(f"Scaffolding work journal at {journal_file}...")
    header = """# Buddy System Work Journal
*An evergreen chronological log of coordination activity, tool development, and workspace changes.*

---

## Operations Archive

"""
    try:
        os.makedirs(os.path.dirname(journal_file), exist_ok=True)
        with open(journal_file, "w", encoding="utf-8") as f:
            f.write(header)
    except Exception as e:
        log_error(f"Error scaffolding journal: {e}")

def update_journal_file(journal_file, conv_id, entry_text):
    scaffold_journal(journal_file)
    try:
        with open(journal_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        entry_text = entry_text.strip() + "\n"
        
        pattern = rf"(### 🛠️ Session Archive: {conv_id}\n.*?)(?=\n### 🛠️ Session Archive:|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            new_content = content[:match.start()] + entry_text + content[match.end():]
            log_info(f"Overwrote existing journal entry for {conv_id}.")
        else:
            header_marker = "## 🛠️ Operations Archive"
            if header_marker in content:
                parts = content.split(header_marker, 1)
                rest = parts[1].lstrip()
                new_content = f"{parts[0]}{header_marker}\n\n{entry_text}\n---\n\n{rest}"
                log_info(f"Prepended new journal entry for {conv_id}.")
            else:
                new_content = content + "\n\n" + entry_text + "\n---\n"
                log_info(f"Appended new journal entry for {conv_id}.")
                
        new_content = re.sub(r'\n{3,}', '\n\n', new_content)
        new_content = re.sub(r'---\n\n+---', '---\n', new_content)
        
        with open(journal_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    except Exception as e:
        log_error(f"Failed to update journal file: {e}")
        return False

def parse_gemini_transcript(transcript_path, memory_updates):
    prompts = []
    created_files = set()
    modified_files = set()
    executed_commands = set()
    session_start = None
    
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                step = json.loads(line)
                created_at = step.get("created_at")
                if not session_start and created_at:
                    session_start = created_at
                    
                step_type = step.get("type")
                source = step.get("source")
                
                if step_type == "USER_INPUT" or (source == "USER_EXPLICIT" and step.get("content")):
                    content = step.get("content", "").strip()
                    if content:
                        prompts.append(content)
                        
                        rule_match = re.search(r"\[(?:rule|memory)\]\s*(.*)", content, re.IGNORECASE)
                        if rule_match:
                            rule = rule_match.group(1).strip()
                            if rule:
                                memory_updates["operational_rules"].add(rule)
                                
                        tech_match = re.search(r"\[tech\]\s*(.*)", content, re.IGNORECASE)
                        if tech_match:
                            tech = tech_match.group(1).strip()
                            if tech:
                                memory_updates["technical_additions"].add(tech)
                                
                        project_match = re.search(r"\[project\]\s*name:\s*([^\n,]+)(?:,\s*status:\s*([^\n,]+))?(?:,\s*path:\s*([^\n,]+))?(?:,\s*next_action:\s*([^\n,]+))?", content, re.IGNORECASE)
                        if project_match:
                            p_name = project_match.group(1).strip()
                            p_status = project_match.group(2).strip() if project_match.group(2) else "active"
                            p_path = project_match.group(3).strip() if project_match.group(3) else ""
                            p_action = project_match.group(4).strip() if project_match.group(4) else ""
                            memory_updates["projects"][p_name] = {
                                "status": p_status,
                                "path": p_path,
                                "next_action": p_action
                            }
                            
                elif source == "MODEL" and step_type == "PLANNER_RESPONSE":
                    tool_calls = step.get("tool_calls", [])
                    for call in tool_calls:
                        name = call.get("name")
                        args = call.get("args", {})
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except Exception:
                                pass
                        
                        if name == "write_to_file":
                            target = args.get("TargetFile", "").strip()
                            if target:
                                created_files.add(os.path.basename(target))
                        elif name in ["replace_file_content", "multi_replace_file_content"]:
                            target = args.get("TargetFile", "").strip()
                            if target:
                                modified_files.add(os.path.basename(target))
                        elif name == "run_command":
                            cmd = args.get("CommandLine", "").strip()
                            if cmd:
                                executed_commands.add(cmd)
            except Exception:
                continue
    return session_start, prompts, created_files, modified_files, executed_commands

def parse_codex_transcript(rollout_path, memory_updates):
    prompts = []
    created_files = set()
    modified_files = set()
    executed_commands = set()
    session_start = None
    
    with open(rollout_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                timestamp = event.get("timestamp")
                if not session_start and timestamp:
                    session_start = timestamp
                    
                event_type = event.get("type")
                payload = event.get("payload", {})
                
                if event_type == "response_item" and payload.get("type") == "message" and payload.get("role") == "user":
                    content = payload.get("content", [])
                    for item in content:
                        if item.get("type") == "input_text" and item.get("text"):
                            text = item.get("text").strip()
                            prompts.append(text)
                            
                            rule_match = re.search(r"\[(?:rule|memory)\]\s*(.*)", text, re.IGNORECASE)
                            if rule_match:
                                rule = rule_match.group(1).strip()
                                if rule:
                                    memory_updates["operational_rules"].add(rule)
                                    
                            tech_match = re.search(r"\[tech\]\s*(.*)", text, re.IGNORECASE)
                            if tech_match:
                                tech = tech_match.group(1).strip()
                                if tech:
                                    memory_updates["technical_additions"].add(tech)
                                    
                            project_match = re.search(r"\[project\]\s*name:\s*([^\n,]+)(?:,\s*status:\s*([^\n,]+))?(?:,\s*path:\s*([^\n,]+))?(?:,\s*next_action:\s*([^\n,]+))?", text, re.IGNORECASE)
                            if project_match:
                                p_name = project_match.group(1).strip()
                                p_status = project_match.group(2).strip() if project_match.group(2) else "active"
                                p_path = project_match.group(3).strip() if project_match.group(3) else ""
                                p_action = project_match.group(4).strip() if project_match.group(4) else ""
                                memory_updates["projects"][p_name] = {
                                    "status": p_status,
                                    "path": p_path,
                                    "next_action": p_action
                                }
                                
                elif event_type == "response_item" and payload.get("type") == "custom_tool_call":
                    tool_name = payload.get("name")
                    tool_input = payload.get("input", "")
                    
                    if tool_name == "exec":
                        cmd_match = re.search(r'exec_command\(\{\s*cmd:\s*"(.*?)"', tool_input, re.DOTALL)
                        if not cmd_match:
                            cmd_match = re.search(r"exec_command\(\{\s*cmd:\s*'(.*?)'", tool_input, re.DOTALL)
                        if cmd_match:
                            try:
                                cmd_str = cmd_match.group(1).encode().decode('unicode-escape')
                            except Exception:
                                cmd_str = cmd_match.group(1)
                            executed_commands.add(cmd_str.strip())
                    elif tool_name == "apply_patch":
                        files_added = re.findall(r"\*\*\* Add File:\s*([^\n]+)", tool_input)
                        for fa in files_added:
                            created_files.add(os.path.basename(fa.strip()))
                        files_updated = re.findall(r"\*\*\* Update File:\s*([^\n]+)", tool_input)
                        for fu in files_updated:
                            modified_files.add(os.path.basename(fu.strip()))
            except Exception:
                continue
    return session_start, prompts, created_files, modified_files, executed_commands

def parse_opencode_transcript(session_id, opencode_db, memory_updates):
    prompts = []
    created_files = set()
    modified_files = set()
    executed_commands = set()
    session_start = None

    connection = sqlite3.connect(f"file:{opencode_db}?mode=ro", uri=True)
    rows = connection.execute(
        """
        SELECT message.data, part.data, message.time_created
        FROM message
        JOIN part ON part.message_id = message.id
        WHERE message.session_id = ?
        ORDER BY message.time_created, part.time_created, part.id
        """,
        (session_id,),
    ).fetchall()
    connection.close()

    for message_data, part_data, created in rows:
        info = json.loads(message_data)
        part = json.loads(part_data)
        if not session_start and created:
            session_start = datetime.fromtimestamp(created / 1000).isoformat()

        if info.get("role") == "user":
            if part.get("type") != "text" or not part.get("text", "").strip():
                continue
            text = part["text"].strip()
            prompts.append(text)

            rule_match = re.search(r"\[(?:rule|memory)\]\s*(.*)", text, re.IGNORECASE)
            if rule_match and rule_match.group(1).strip():
                memory_updates["operational_rules"].add(rule_match.group(1).strip())

            tech_match = re.search(r"\[tech\]\s*(.*)", text, re.IGNORECASE)
            if tech_match and tech_match.group(1).strip():
                memory_updates["technical_additions"].add(tech_match.group(1).strip())

            project_match = re.search(r"\[project\]\s*name:\s*([^\n,]+)(?:,\s*status:\s*([^\n,]+))?(?:,\s*path:\s*([^\n,]+))?(?:,\s*next_action:\s*([^\n,]+))?", text, re.IGNORECASE)
            if project_match:
                project_name = project_match.group(1).strip()
                memory_updates["projects"][project_name] = {
                    "status": project_match.group(2).strip() if project_match.group(2) else "active",
                    "path": project_match.group(3).strip() if project_match.group(3) else "",
                    "next_action": project_match.group(4).strip() if project_match.group(4) else "",
                }
            continue

        if info.get("role") != "assistant":
            continue
        if part.get("type") != "tool":
            continue
        tool_name = part.get("tool", "")
        state = part.get("state", {})
        tool_input = state.get("input", {}) if isinstance(state, dict) else {}
        if tool_name in {"bash", "shell"}:
            command = tool_input.get("command", "").strip()
            if command:
                executed_commands.add(command)
        elif tool_name in {"write", "write_file"}:
            target = tool_input.get("filePath") or tool_input.get("path") or tool_input.get("file_path")
            if target:
                created_files.add(os.path.basename(target))
        elif tool_name in {"edit", "patch", "apply_patch", "multiedit"}:
            target = tool_input.get("filePath") or tool_input.get("path") or tool_input.get("file_path")
            if target:
                modified_files.add(os.path.basename(target))

    return session_start, prompts, created_files, modified_files, executed_commands

def sync_conversation(conv_id, user_summary, next_steps, config):
    conv_type = "gemini"
    if not conv_id:
        conv_id, conv_path, conv_type = get_latest_conv(config)
        if not conv_id:
            log_error("No conversation logs found.")
            return False
        log_info(f"Auto-detected latest conversation: {conv_id} ({conv_type})")
    else:
        conv_path, conv_type = find_conv_by_id(conv_id, config)
        if not conv_path:
            log_error(f"Conversation {conv_id} not found in Gemini, Codex, or OpenCode sessions.")
            return False
            
    log_info(f"Processing logs in {conv_path}...")
    
    memory_updates = {
        "technical_additions": set(),
        "operational_rules": set(),
        "projects": {}
    }
    
    if conv_type == "gemini":
        transcript_path = None
        log_dir = os.path.join(conv_path, ".system_generated", "logs")
        for name in ["transcript.jsonl", "transcript_full.jsonl"]:
            fp = os.path.join(log_dir, name)
            if os.path.exists(fp):
                transcript_path = fp
                break
        if not transcript_path:
            log_error("Gemini transcript file not found.")
            return False
            
        session_start, prompts, created_files, modified_files, executed_commands = parse_gemini_transcript(transcript_path, memory_updates)
    elif conv_type == "codex":
        session_start, prompts, created_files, modified_files, executed_commands = parse_codex_transcript(conv_path, memory_updates)
    else:
        try:
            session_start, prompts, created_files, modified_files, executed_commands = parse_opencode_transcript(conv_path, config["opencode_db"], memory_updates)
        except Exception as error:
            log_error(f"Failed to parse OpenCode session: {error}")
            return False
        
    session_time = session_start if session_start else datetime.now().isoformat()
    
    # 1. Format Journal Entry
    journal_entry = f"### 🛠️ Session Archive: {conv_id}\n"
    journal_entry += f"* **Recorded**: `{session_time}`\n"
    journal_entry += f"* **Agent Frame**: `{conv_type.upper()}`\n"
    if user_summary:
        journal_entry += f"* **Summary**: {user_summary}\n"
    if next_steps:
        journal_entry += f"* **Next Steps**: {next_steps}\n"
        
    journal_entry += "* **User Prompts**:\n"
    for p in prompts:
        cleaned_p = p.replace("\n", " ").strip()
        if len(cleaned_p) > 120:
            cleaned_p = cleaned_p[:117] + "..."
        journal_entry += f"  > {cleaned_p}\n"
        
    if created_files or modified_files or executed_commands:
        journal_entry += "* **Workspace Actions**:\n"
        if created_files:
            journal_entry += f"  - 📂 Created: `{', '.join(sorted(created_files))}`\n"
        if modified_files:
            journal_entry += f"  - 📂 Modified: `{', '.join(sorted(modified_files))}`\n"
        if executed_commands:
            cmd_list = sorted(list(executed_commands))[:5]
            cmd_str = ", ".join([f"`{c}`" for c in cmd_list])
            if len(executed_commands) > 5:
                cmd_str += f" (+{len(executed_commands) - 5} more)"
            journal_entry += f"  - 🖥️ Executed: {cmd_str}\n"
            
    if update_journal_file(config["journal_file"], conv_id, journal_entry):
        log_success("Journal successfully updated.")
        
    # 2. Update memory JSON
    memory_file = config["memory_file"]
    memory_data = load_json_file(memory_file, {"last_updated": "", "active_projects": {}, "technical_additions": [], "operational_rules": []})
    
    existing_rules = {r.lower(): r for r in memory_data.get("operational_rules", [])}
    for r in memory_updates["operational_rules"]:
        existing_rules[r.lower()] = r
    memory_data["operational_rules"] = list(existing_rules.values())
    
    existing_tech = {t.lower(): t for t in memory_data.get("technical_additions", [])}
    for t in memory_updates["technical_additions"]:
        existing_tech[t.lower()] = t
    memory_data["technical_additions"] = list(existing_tech.values())
    
    if "active_projects" not in memory_data:
        memory_data["active_projects"] = {}
    for p_name, p_info in memory_updates["projects"].items():
        memory_data["active_projects"][p_name] = {
            "status": p_info["status"],
            "path": p_info["path"]
        }
        check_and_create_project_brief(p_name, config)
        update_dashboard_table(p_name, p_info["status"], p_info["next_action"], config)
        update_project_index(p_name, config, active=(p_info["status"].lower() not in ["stalled", "complete"]))
        
    memory_data["last_updated"] = datetime.now().isoformat()
    memory_data["technical_additions"] = sorted(list(set(memory_data["technical_additions"])))
    memory_data["operational_rules"] = list(set(memory_data["operational_rules"]))
    
    save_json_file(memory_file, memory_data)
    log_success("Memory JSON updated.")
    
    # 3. Add to processed conversations in pruner status
    status_file = config["status_file"]
    status_data = load_json_file(status_file, {"processed_conversations": []})
    if conv_id not in status_data["processed_conversations"]:
        status_data["processed_conversations"].append(conv_id)
        save_json_file(status_file, status_data)
        log_info("Registered conversation as processed in pruner state.")
        
    return True
