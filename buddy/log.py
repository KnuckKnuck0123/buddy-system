import os
import re
from datetime import datetime

def append_handoff(log_path, owner, task_id, summary, next_step, changed="", decisions="", verified="", blockers=""):
    """
    Appends a formatted handoff entry under today's date heading in Agent Handoff Log.md.
    Prepend new entries under the today heading to keep newest at the top.
    """
    if not os.path.exists(log_path):
        print(f"[!] Handoff log file not found at {log_path}")
        return False
        
    now = datetime.now()
    today_header = f"## {now.strftime('%Y-%m-%d')}"
    time_str = now.strftime("%H:%M")
    
    # Format the handoff entry
    entry = f"### {time_str} - {owner} / {task_id}\n"
    entry += f"- Summary: {summary}\n"
    entry += f"- Changed: {changed or 'None'}\n"
    if decisions:
        entry += f"- Decisions: {decisions}\n"
    if verified:
        entry += f"- Verified: {verified}\n"
    entry += f"- Next: {next_step or 'None'}\n"
    if blockers:
        entry += f"- Blockers: {blockers}\n"
        
    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    if today_header in content:
        # Heading exists, insert right under it
        parts = content.split(today_header, 1)
        rest = parts[1].lstrip()
        new_content = f"{parts[0]}{today_header}\n\n{entry}\n{rest}"
    else:
        # Heading doesn't exist, we must insert it before the first existing date heading
        match = re.search(r"\n(## 20\d{2}-\d{2}-\d{2})", content)
        if match:
            idx = match.start()
            new_content = f"{content[:idx]}\n\n{today_header}\n\n{entry}\n\n{content[idx:].lstrip()}"
        else:
            new_content = f"{content.strip()}\n\n{today_header}\n\n{entry}\n"
            
    # Clean up excess blank lines
    new_content = re.sub(r'\n{3,}', '\n\n', new_content)
            
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"[+] Successfully logged handoff for {owner} / {task_id}.")
    return True
