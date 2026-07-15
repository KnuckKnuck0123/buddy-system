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

def print_status(config):
    memory_file = config["memory_file"]
    if not os.path.exists(memory_file):
        print(f"[!] Memory file not found at {memory_file}")
        return
        
    with open(memory_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    orange = "\033[38;5;208m"
    bold = "\033[1m"
    reset = "\033[0m"
    cyan = "\033[36m"
    green = "\033[32m"
    gray = "\033[90m"
    
    print(f"\n{orange}{bold}======================================================================{reset}")
    print(f"{orange}{bold}               BUDDY SYSTEM MEMORY COMMAND CENTER               {reset}")
    print(f"{orange}{bold}======================================================================{reset}")
    print(f"{gray}Last Updated: {bold}{data.get('last_updated', 'N/A')}{reset}")
    print(f"{gray}Memory File:  {memory_file} ({os.path.getsize(memory_file)} bytes){reset}")
    print(f"{gray}Journal:      {config['journal_file']}{reset}")
    print(f"{gray}Vault Path:   {config['vault_path']}{reset}")
    print(f"{orange}{bold}----------------------------------------------------------------------{reset}")
    
    print(f"\n{orange}{bold}🟥 ACTIVE PROJECTS (Memory & Buddy02 Dashboard){reset}")
    projects = data.get("active_projects", {})
    if projects:
        for name, info in projects.items():
            path = info.get("path", "N/A")
            status = info.get("status", "N/A")
            status_color = green if "active" in status.lower() or "deployed" in status.lower() else cyan
            print(f"  {bold}• {name}{reset} {gray}[{status_color}{status}{gray}]{reset}")
            print(f"    {gray}Path:   {path}{reset}")
            features = info.get("features", [])
            if features:
                print(f"    {gray}Specs:  {', '.join(features)}{reset}")
    else:
        print(f"  {gray}No active projects recorded.{reset}")
        
    print(f"\n{orange}{bold}📐 TECHNICAL ECOSYSTEM{reset}")
    tech = data.get("technical_additions", [])
    if tech:
        tech_str = ", ".join(tech)
        print(f"  {cyan}{tech_str}{reset}")
    else:
        print(f"  {gray}No technical additions recorded.{reset}")
        
    print(f"\n{orange}{bold}⚡ OPERATIONAL RULES{reset}")
    rules = data.get("operational_rules", [])
    if rules:
        for i, rule in enumerate(rules, 1):
            print(f"  {orange}{i:02d}.{reset} {rule}")
    else:
        print(f"  {gray}No custom rules active.{reset}")
        
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
    sync_parser.add_argument("--summary", help="Optional summary of this session's progress")
    sync_parser.add_argument("--next-steps", help="Optional next steps/milestones")
    
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
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
        
    if args.command == "init":
        init_config(args.vault_path)
    elif args.command == "status":
        print_status(config)
    elif args.command == "sync":
        sync_conversation(args.conv_id, args.summary, args.next_steps, config)
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

if __name__ == "__main__":
    main()
