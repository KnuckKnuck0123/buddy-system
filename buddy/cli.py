import os
import sys
import json
import argparse
from datetime import datetime
from .config import load_config, init_config
from .memory import manage_project, manage_rule, manage_tech
from .sync import sync_conversation
from .board import claim_task, release_task
from .log import append_handoff
from .calendar import list_events, add_event, find_duplicates, get_calendars

def print_status(config):
    vault_path = config.get("vault_path", os.path.expanduser("~/Documents/Buddy02 Vault"))
    dash_file = os.path.join(vault_path, "00 - Dashboards/Main Dashboard.md")
    
    orange = "\033[38;5;208m"
    bold = "\033[1m"
    reset = "\033[0m"
    cyan = "\033[36m"
    green = "\033[32m"
    gray = "\033[90m"
    yellow = "\033[33m"
    
    print(f"\n{orange}{bold}======================================================================{reset}")
    print(f"{orange}{bold}               BUDDY SYSTEM COMMAND CENTER (OBSIDIAN)                 {reset}")
    print(f"{orange}{bold}======================================================================{reset}")
    print(f"{gray}Vault Path:   {vault_path}{reset}")
    print(f"{gray}Dashboard:    {dash_file}{reset}")
    print(f"{gray}Journal:      {config.get('journal_file', 'N/A')}{reset}")
    print(f"{orange}{bold}----------------------------------------------------------------------{reset}")
    
    if not os.path.exists(dash_file):
        print(f"[!] Dashboard not found at {dash_file}")
        return
        
    with open(dash_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    current_section = None
    for line in lines:
        sline = line.strip()
        if "### 🔥 In Flight" in sline:
            current_section = "inflight"
            print(f"\n{orange}{bold}🔥 IN FLIGHT (Active Sprints){reset}")
            continue
        elif "### 🧪 The Lab" in sline:
            current_section = "lab"
            print(f"\n{yellow}{bold}🧪 THE LAB (Half-Baked, Spikes & Prototypes){reset}")
            continue
        elif "### 💤 Shelved" in sline:
            current_section = "shelved"
            print(f"\n{gray}{bold}💤 SHELVED / ICEBOX{reset}")
            continue
        elif "### 🏛️ Standing Context" in sline:
            current_section = "context"
            print(f"\n{cyan}{bold}🏛️ STANDING CONTEXT & PRACTICE{reset}")
            continue
        elif sline.startswith("## ") or sline.startswith("> [!caution]"):
            current_section = None
            continue
            
        if current_section in ["inflight", "lab", "shelved", "context"]:
            if sline.startswith("|") and not sline.startswith("| :---") and not sline.startswith("| Project") and not sline.startswith("| Track") and not sline.startswith("| Experiment") and not sline.startswith("| Domain"):
                cols = [c.strip() for c in sline.split("|")[1:-1]]
                if cols:
                    name = cols[0].replace("[[", "").replace("]]", "")
                    if current_section == "inflight":
                        focus = cols[1] if len(cols) > 1 else ""
                        artifact = cols[2] if len(cols) > 2 else ""
                        print(f"  {bold}• {name}{reset} {gray}- {focus}{reset}")
                        if artifact:
                            print(f"    {green}↳ Next: {artifact}{reset}")
                    elif current_section == "lab":
                        scope = cols[1] if len(cols) > 1 else ""
                        artifact = cols[2] if len(cols) > 2 else ""
                        print(f"  {yellow}• {name}{reset} {gray}({scope}){reset}")
                        if artifact:
                            print(f"    {gray}↳ State: {artifact}{reset}")
                    elif current_section == "context":
                        orient = cols[1] if len(cols) > 1 else ""
                        print(f"  {cyan}• {name}{reset} {gray}- {orient}{reset}")
                        
    print(f"\n{orange}{bold}======================================================================{reset}\n")

def main():
    config = load_config()
    
    parser = argparse.ArgumentParser(description="Buddy System CLI - Shared AI context and coordination manager")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")
    
    # Init
    init_parser = subparsers.add_parser("init", help="Initialize global configuration")
    init_parser.add_argument("--vault-path", help="Local directory path of the Obsidian Vault")
    
    # Status
    subparsers.add_parser("status", help="Show current operational memory status")
    
    # Sync
    sync_parser = subparsers.add_parser("sync", help="Sync active conversation log and update memory")
    sync_parser.add_argument("--conv-id", help="Conversation ID to sync (defaults to latest active)")
    sync_parser.add_argument("--summary", help="Summary of this session's progress")
    sync_parser.add_argument("--next-steps", help="Next steps/milestones")
    sync_parser.add_argument("--harness", help="Override harness framework type (gemini, codex, opencode)")
    sync_parser.add_argument("--parent-conv-id", help="Parent conversation ID if syncing a subagent session")
    sync_parser.add_argument("--subagent-role", help="Role description if syncing a subagent session")
    
    # Project
    proj_parser = subparsers.add_parser("project", help="Create or update a project record")
    proj_parser.add_argument("name", help="Name of the project")
    proj_parser.add_argument("--status", default="active", help="Project status (active, stalled, complete, planned)")
    proj_parser.add_argument("--next-action", help="Next meaningful action / milestone")
    proj_parser.add_argument("--path", help="Local directory path of the project")
    proj_parser.add_argument("--features", help="Comma-separated list of specs/features")
    
    # Rule
    rule_parser = subparsers.add_parser("rule", help="Manage operational rules")
    rule_parser.add_argument("action", choices=["add", "rm", "list"], help="Action to perform")
    rule_parser.add_argument("text", nargs="?", help="Rule text to add or remove")
    
    # Tech
    tech_parser = subparsers.add_parser("tech", help="Manage technical ecosystem additions")
    tech_parser.add_argument("action", choices=["add", "rm", "list"], help="Action to perform")
    tech_parser.add_argument("text", nargs="?", help="Tech addition text to add or remove")
    
    # Claim
    claim_parser = subparsers.add_parser("claim", help="Claim a task on the Coordination Board")
    claim_parser.add_argument("task_id", help="The identifier of the task (e.g. YYYYMMDD-short-slug)")
    claim_parser.add_argument("--owner", default="buddy", help="The owner claiming the task")
    claim_parser.add_argument("--task", help="Brief summary of the outcome/task")
    claim_parser.add_argument("--scope", help="Files or areas affected by this task")
    claim_parser.add_argument("--hours", type=int, default=4, help="How many hours until the claim is considered stale")
    
    # Release
    release_parser = subparsers.add_parser("release", help="Release/complete a task on the Coordination Board")
    release_parser.add_argument("task_id", help="The identifier of the task to release")
    release_parser.add_argument("--status", default="done", choices=["done", "ready", "blocked"], help="Status to assign (done/ready/blocked)")
    
    # Handoff
    handoff_parser = subparsers.add_parser("handoff", help="Log a handoff entry in the Handoff Log")
    handoff_parser.add_argument("summary", help="Concise summary of work completed")
    handoff_parser.add_argument("--owner", default="buddy", help="The harness logging this handoff")
    handoff_parser.add_argument("--task-id", default="unclaimed", help="The active task ID associated with this work")
    handoff_parser.add_argument("--next", help="Next actions or milestones")
    handoff_parser.add_argument("--changed", help="Comma-separated list of modified or created files")
    handoff_parser.add_argument("--decisions", help="Important design decisions or trade-offs made")
    handoff_parser.add_argument("--verified", help="Commands or methods used to verify correctness")
    handoff_parser.add_argument("--blockers", help="Any active blockers or missing dependencies")
    
    # Calendar
    cal_parser = subparsers.add_parser("calendar", help="Manage Apple Calendar safely with duplicate prevention")
    cal_subparsers = cal_parser.add_subparsers(dest="cal_command", help="Calendar actions")
    
    cal_list_p = cal_subparsers.add_parser("list", help="List upcoming calendar events")
    cal_list_p.add_argument("--days-ahead", type=int, default=14, help="Days ahead to inspect (default: 14)")
    cal_list_p.add_argument("--days-back", type=int, default=1, help="Days back to inspect (default: 1)")
    cal_list_p.add_argument("--calendar", help="Filter by specific calendar name")
    cal_list_p.add_argument("--json", action="store_true", help="Output as JSON")
    
    cal_cals_p = cal_subparsers.add_parser("cals", help="List all available calendars")
    
    cal_add_p = cal_subparsers.add_parser("add", help="Add an event with duplicate check")
    cal_add_p.add_argument("title", help="Event title/summary")
    cal_add_p.add_argument("--start", required=True, help="Start ISO datetime (e.g. 2026-08-24T14:00:00)")
    cal_add_p.add_argument("--end", required=True, help="End ISO datetime (e.g. 2026-08-24T18:00:00)")
    cal_add_p.add_argument("--calendar", required=True, help="Target calendar name")
    cal_add_p.add_argument("--desc", default="", help="Event description")
    cal_add_p.add_argument("--location", default="", help="Event location or Meet URL")
    cal_add_p.add_argument("--force", action="store_true", help="Force insert even if duplicate exists")
    
    cal_dedup_p = cal_subparsers.add_parser("dedup", help="Scan for duplicate calendar events")
    cal_dedup_p.add_argument("--calendar", help="Filter by calendar name")
    cal_dedup_p.add_argument("--days-ahead", type=int, default=90, help="Days ahead (default: 90)")
    cal_dedup_p.add_argument("--days-back", type=int, default=30, help="Days back (default: 30)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
        
    if args.command == "init":
        init_config(args.vault_path)
    elif args.command == "status":
        print_status(config)
    elif args.command == "sync":
        sync_conversation(
            args.conv_id,
            args.summary,
            args.next_steps,
            config,
            harness_override=args.harness,
            parent_conv_id=args.parent_conv_id,
            subagent_role=args.subagent_role
        )
    elif args.command == "project":
        manage_project(args.name, args.status, args.next_action, args.path, args.features, config)
    elif args.command == "rule":
        manage_rule(args.action, args.text, config)
    elif args.command == "tech":
        manage_tech(args.action, args.text, config)
    elif args.command == "claim":
        board_path = os.path.join(config["vault_path"], "03 - Resources/Workspace/Agent Coordination Board.md")
        claim_task(board_path, args.task_id, args.owner, args.task, args.scope, args.hours)
    elif args.command == "release":
        board_path = os.path.join(config["vault_path"], "03 - Resources/Workspace/Agent Coordination Board.md")
        release_task(board_path, args.task_id, args.status)
    elif args.command == "handoff":
        log_path = os.path.join(config["vault_path"], "02 - Logs/Agent Handoff Log.md")
        append_handoff(log_path, args.owner, args.task_id, args.summary, args.next, args.changed, args.decisions, args.verified, args.blockers)
    elif args.command == "calendar":
        if args.cal_command == "cals":
            cals = get_calendars()
            print("\nAvailable Calendars:")
            for c in cals:
                print(f"  • {c}")
            print()
        elif args.cal_command == "list":
            evs = list_events(days_back=args.days_back, days_ahead=args.days_ahead, calendar_name=args.calendar)
            if args.json:
                print(json.dumps(evs, indent=2))
            else:
                print(f"\nFound {len(evs)} events:")
                for ev in evs:
                    loc = f" ({ev['location']})" if ev['location'] else ""
                    print(f"  [{ev['calendar']}] {ev['start']} - {ev['summary']}{loc}")
                print()
        elif args.cal_command == "add":
            res = add_event(
                title=args.title,
                start_str=args.start,
                end_str=args.end,
                calendar_name=args.calendar,
                description=args.desc,
                location=args.location,
                force=args.force
            )
            print(json.dumps(res, indent=2))
        elif args.cal_command == "dedup":
            dups = find_duplicates(calendar_name=args.calendar, days_back=args.days_back, days_ahead=args.days_ahead)
            if not dups:
                print("\n✅ No duplicate events found!")
            else:
                print(f"\n⚠️  Found {len(dups)} duplicate event clusters:\n")
                for key, items in dups.items():
                    title, date = key.split("|")
                    print(f"  • \"{title}\" on {date} ({len(items)} copies):")
                    for it in items:
                        print(f"      - [{it['calendar']}] {it['start']} -> {it['end']}")
                print()

if __name__ == "__main__":
    main()
