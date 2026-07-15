import os
import json
import sys
from datetime import datetime

def log_info(msg):
    print(f"[*] {msg}")

def log_success(msg):
    print(f"[\033[32m+\033[0m] {msg}")

def log_error(msg):
    print(f"[\033[31m-\033[0m] {msg}", file=sys.stderr)

def load_json_file(filepath, default_val):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log_error(f"Error loading {filepath}: {e}")
    return default_val

def save_json_file(filepath, data):
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        tmp_file = filepath + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_file, filepath)
        return True
    except Exception as e:
        log_error(f"Failed to write JSON {filepath}: {e}")
        return False

def check_and_create_project_brief(project_name, config):
    vault_path = config["vault_path"]
    brief_path = os.path.join(vault_path, "01 - Projects", f"{project_name}.md")
    if os.path.exists(brief_path):
        return True
        
    template_path = os.path.join(vault_path, "99 - Templates", "Project Brief.md")
    if not os.path.exists(template_path):
        log_error(f"Project brief template not found at {template_path}")
        return False
        
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
            
        today = datetime.now().strftime("%Y-%m-%d")
        content = template.replace("{{date}}", today).replace("{{title}}", project_name)
        
        with open(brief_path, "w", encoding="utf-8") as f:
            f.write(content)
        log_success(f"Created new project brief at {brief_path}")
        return True
    except Exception as e:
        log_error(f"Failed to create project brief: {e}")
        return False

def update_dashboard_table(project_name, status, next_action, config):
    vault_path = config["vault_path"]
    dashboard_path = os.path.join(vault_path, "00 - Dashboards", "Main Dashboard.md")
    if not os.path.exists(dashboard_path):
        log_error(f"Main Dashboard not found at {dashboard_path}")
        return False
        
    try:
        with open(dashboard_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        table_start = -1
        table_end = -1
        for i, line in enumerate(lines):
            if "| Track | State | Next meaningful artifact |" in line:
                table_start = i
                break
                
        if table_start == -1:
            log_error("Could not find projects table in Main Dashboard.")
            return False
            
        for i in range(table_start + 1, len(lines)):
            if not lines[i].strip().startswith("|"):
                table_end = i
                break
        if table_end == -1:
            table_end = len(lines)
            
        table_lines = lines[table_start:table_end]
        rows = table_lines[2:]
        
        updated_rows = []
        project_found = False
        
        for row in rows:
            if not row.strip():
                continue
            parts = [p.strip() for p in row.split("|")[1:-1]]
            if not parts:
                continue
                
            clean_proj_name = parts[0].replace("[[", "").replace("]]", "").split("/")[-1].split("|")[0]
            if clean_proj_name.lower() == project_name.lower():
                proj_cell = parts[0]
                if not proj_cell.startswith("[["):
                    proj_cell = f"[[01 - Projects/{project_name}|{project_name}]]"
                parts[0] = proj_cell
                parts[1] = status
                if next_action:
                    parts[2] = next_action
                project_found = True
                
            updated_rows.append(f"| {' | '.join(parts)} |")
            
        if not project_found:
            proj_cell = f"[[01 - Projects/{project_name}|{project_name}]]"
            new_row = f"| {proj_cell} | {status} | {next_action or 'N/A'} |"
            updated_rows.append(new_row)
            
        new_lines = lines[:table_start + 2] + [r + "\n" for r in updated_rows] + lines[table_end:]
        
        with open(dashboard_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        log_success(f"Updated projects matrix in Main Dashboard.md")
        return True
    except Exception as e:
        log_error(f"Failed to update Main Dashboard matrix: {e}")
        return False

def update_project_index(project_name, config, active=True):
    vault_path = config["vault_path"]
    index_path = os.path.join(vault_path, "01 - Projects", "_Index.md")
    if not os.path.exists(index_path):
        return False
        
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        proj_link = f"[[{project_name}]]"
        if proj_link in content:
            return True
            
        section = "## Active" if active else "## Other"
        if section not in content:
            return False
            
        parts = content.split(section)
        lines = parts[1].split("\n")
        
        insert_idx = -1
        for idx, line in enumerate(lines):
            if line.strip().startswith("##") or (idx > 0 and line.strip() == "" and idx < len(lines) - 1 and lines[idx+1].strip().startswith("##")):
                insert_idx = idx
                break
        if insert_idx == -1:
            for idx, line in enumerate(lines):
                if line.strip() == "":
                    insert_idx = idx
                    break
        if insert_idx == -1:
            insert_idx = len(lines)
            
        lines.insert(insert_idx, f"- [[{project_name}]]")
        parts[1] = "\n".join(lines)
        
        new_content = section.join(parts)
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        log_success(f"Added project link to {index_path}")
        return True
    except Exception as e:
        log_error(f"Failed to update project index: {e}")
        return False

def manage_project(name, status, next_action, path, features, config):
    memory_file = config["memory_file"]
    memory_data = load_json_file(memory_file, {"last_updated": "", "active_projects": {}, "technical_additions": [], "operational_rules": []})
    
    if "active_projects" not in memory_data:
        memory_data["active_projects"] = {}
        
    proj_info = memory_data["active_projects"].get(name, {})
    proj_info["status"] = status
    if path:
        proj_info["path"] = path
    if features:
        proj_info["features"] = [f.strip() for f in features.split(",")]
        
    memory_data["active_projects"][name] = proj_info
    memory_data["last_updated"] = datetime.now().isoformat()
    
    save_json_file(memory_file, memory_data)
    log_success(f"Project '{name}' updated in noah_memory.json.")
    
    check_and_create_project_brief(name, config)
    update_dashboard_table(name, status, next_action, config)
    update_project_index(name, config, active=(status.lower() not in ["stalled", "complete"]))

def manage_rule(action, text, config):
    memory_file = config["memory_file"]
    memory_data = load_json_file(memory_file, {"last_updated": "", "active_projects": {}, "technical_additions": [], "operational_rules": []})
    
    rules = memory_data.get("operational_rules", [])
    if action == "add":
        if not text:
            log_error("Rule text required for add action.")
            return
        if text not in rules:
            rules.append(text)
            log_success(f"Added rule: {text}")
    elif action == "rm":
        if not text:
            log_error("Rule text required for rm action.")
            return
        matching = [r for r in rules if text.lower() in r.lower()]
        if not matching:
            log_error(f"Rule matching '{text}' not found.")
            return
        if len(matching) > 1:
            log_info("Multiple matching rules found, please be more specific:")
            for m in matching:
                print(f"  - {m}")
            return
        rules.remove(matching[0])
        log_success(f"Removed rule: {matching[0]}")
    elif action == "list":
        for idx, r in enumerate(rules, 1):
            print(f"  {idx:02d}. {r}")
        return
        
    memory_data["operational_rules"] = rules
    memory_data["last_updated"] = datetime.now().isoformat()
    save_json_file(memory_file, memory_data)

def manage_tech(action, text, config):
    memory_file = config["memory_file"]
    memory_data = load_json_file(memory_file, {"last_updated": "", "active_projects": {}, "technical_additions": [], "operational_rules": []})
    
    tech = memory_data.get("technical_additions", [])
    if action == "add":
        if not text:
            log_error("Tech item required for add action.")
            return
        if text not in tech:
            tech.append(text)
            log_success(f"Added technical addition: {text}")
    elif action == "rm":
        if not text:
            log_error("Tech item required for rm action.")
            return
        matching = [t for t in tech if text.lower() in t.lower()]
        if not matching:
            log_error(f"Tech matching '{text}' not found.")
            return
        if len(matching) > 1:
            log_info("Multiple matching tech items found, please be more specific:")
            for m in matching:
                print(f"  - {m}")
            return
        tech.remove(matching[0])
        log_success(f"Removed tech addition: {matching[0]}")
    elif action == "list":
        print(", ".join(tech))
        return
        
    memory_data["technical_additions"] = sorted(tech)
    memory_data["last_updated"] = datetime.now().isoformat()
    save_json_file(memory_file, memory_data)
