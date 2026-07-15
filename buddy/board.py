import os
import re
from datetime import datetime, timedelta

def parse_yaml_like_blocks(text):
    """
    Parses a list of items of the form:
    - id: name
      field: value
      field2: value
    """
    blocks = []
    current_block = None
    lines = text.split("\n")
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- id:"):
            if current_block:
                blocks.append(current_block)
            current_block = {"id": stripped.split("- id:")[1].strip()}
        elif current_block and stripped and ":" in stripped:
            parts = stripped.split(":", 1)
            key = parts[0].strip()
            val = parts[1].strip()
            current_block[key] = val
        elif current_block and not stripped:
            # empty line ends a block
            blocks.append(current_block)
            current_block = None
            
    if current_block:
        blocks.append(current_block)
        
    return blocks

def format_block(block):
    lines = [f"- id: {block.get('id')}"]
    for k, v in block.items():
        if k == "id":
            continue
        lines.append(f"  {k}: {v}")
    return "\n".join(lines)

def load_board(board_path):
    if not os.path.exists(board_path):
        return None
    with open(board_path, "r", encoding="utf-8") as f:
        content = f.read()
    return content

def get_section_content(board_content, header):
    pattern = rf"## {header}\n(.*?)(?=\n## |\Z)"
    match = re.search(pattern, board_content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def replace_section_content(board_content, header, new_content):
    pattern = rf"(## {header}\n)(.*?)(?=\n## |\Z)"
    def repl(m):
        return f"{m.group(1)}{new_content}\n"
    new_board, count = re.subn(pattern, repl, board_content, flags=re.DOTALL)
    return new_board

def claim_task(board_path, task_id, owner, task=None, scope=None, hours=4):
    board_content = load_board(board_path)
    if not board_content:
        print(f"[!] Board file not found at {board_path}")
        return False
        
    active_str = get_section_content(board_content, "Active Claims")
    queue_str = get_section_content(board_content, "Queue")
    
    active_blocks = parse_yaml_like_blocks(active_str)
    queue_blocks = parse_yaml_like_blocks(queue_str)
    
    # Check if already claimed
    for block in active_blocks:
        if block["id"] == task_id:
            print(f"[*] Task '{task_id}' is already claimed by {block.get('owner')}.")
            return False
            
    # Find in queue
    target_block = None
    for block in queue_blocks:
        if block["id"] == task_id:
            target_block = block
            queue_blocks.remove(block)
            break
            
    now = datetime.now()
    started_str = now.strftime("%Y-%m-%d %H:%M Local")
    stale_str = (now + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M Local")
    today_date = now.strftime("%Y-%m-%d")
    
    if target_block:
        target_block["owner"] = owner
        target_block["status"] = "claimed"
        target_block["started"] = started_str
        target_block["stale_after"] = stale_str
        target_block["handoff"] = f"[[02 - Logs/Agent Handoff Log#{today_date}]]"
        if task:
            target_block["task"] = task
        if scope:
            target_block["scope"] = scope
    else:
        if not task:
            task = f"Task claimed by {owner}"
        target_block = {
            "id": task_id,
            "owner": owner,
            "status": "claimed",
            "task": task,
            "scope": scope or "unspecified",
            "started": started_str,
            "stale_after": stale_str,
            "handoff": f"[[02 - Logs/Agent Handoff Log#{today_date}]]"
        }
        
    active_blocks.append(target_block)
    
    new_active_str = "\n\n".join([format_block(b) for b in active_blocks]) if active_blocks else "No active claims."
    new_queue_str = "\n\n".join([format_block(b) for b in queue_blocks]) if queue_blocks else "No unclaimed tasks in queue."
    
    board_content = replace_section_content(board_content, "Active Claims", new_active_str)
    board_content = replace_section_content(board_content, "Queue", new_queue_str)
    
    with open(board_path, "w", encoding="utf-8") as f:
        f.write(board_content)
    print(f"[+] Successfully claimed task '{task_id}' for {owner}.")
    return True

def release_task(board_path, task_id, status="done"):
    board_content = load_board(board_path)
    if not board_content:
        print(f"[!] Board file not found at {board_path}")
        return False
        
    active_str = get_section_content(board_content, "Active Claims")
    active_blocks = parse_yaml_like_blocks(active_str)
    
    target_block = None
    for block in active_blocks:
        if block["id"] == task_id:
            target_block = block
            active_blocks.remove(block)
            break
            
    if not target_block:
        print(f"[!] Active claim with ID '{task_id}' not found.")
        return False
        
    new_active_str = "\n\n".join([format_block(b) for b in active_blocks]) if active_blocks else "No active claims."
    board_content = replace_section_content(board_content, "Active Claims", new_active_str)
    
    if status.lower() == "done":
        done_str = get_section_content(board_content, "Done")
        today = datetime.now().strftime("%Y-%m-%d")
        done_entry = f"- {today}: {target_block.get('owner')} completed task `{task_id}`: {target_block.get('task')}"
        if not done_str or done_str.strip() == "No completed tasks.":
            new_done_str = done_entry
        else:
            new_done_str = done_entry + "\n" + done_str
        board_content = replace_section_content(board_content, "Done", new_done_str)
        print(f"[+] Task '{task_id}' completed and logged in Done section.")
    elif status.lower() == "blocked":
        blocked_str = get_section_content(board_content, "Blocked")
        target_block["status"] = "blocked"
        if not blocked_str or blocked_str.strip() == "No blocked coordination tasks.":
            new_blocked_str = format_block(target_block)
        else:
            blocked_blocks = parse_yaml_like_blocks(blocked_str)
            blocked_blocks.append(target_block)
            new_blocked_str = "\n\n".join([format_block(b) for b in blocked_blocks])
        board_content = replace_section_content(board_content, "Blocked", new_blocked_str)
        print(f"[+] Task '{task_id}' marked as blocked.")
    else:
        # Move back to Queue
        queue_str = get_section_content(board_content, "Queue")
        target_block["status"] = "ready"
        target_block.pop("started", None)
        target_block.pop("stale_after", None)
        target_block.pop("handoff", None)
        if not queue_str or queue_str.strip() == "No unclaimed tasks in queue.":
            new_queue_str = format_block(target_block)
        else:
            queue_blocks = parse_yaml_like_blocks(queue_str)
            queue_blocks.append(target_block)
            new_queue_str = "\n\n".join([format_block(b) for b in queue_blocks])
        board_content = replace_section_content(board_content, "Queue", new_queue_str)
        print(f"[+] Task '{task_id}' returned to Queue.")
        
    with open(board_path, "w", encoding="utf-8") as f:
        f.write(board_content)
    return True
