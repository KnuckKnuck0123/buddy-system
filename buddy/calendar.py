import subprocess
import json
import datetime
from typing import List, Dict, Any, Optional

def run_applescript(script: str) -> str:
    result = subprocess.run(["/usr/bin/osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"AppleScript error ({result.returncode}): {result.stderr.strip()}")
    return result.stdout.strip()

def get_calendars() -> List[str]:
    script = 'tell application "Calendar" to get name of every calendar'
    output = run_applescript(script)
    if not output:
        return []
    return [c.strip() for c in output.split(", ")]

def list_events(days_back: int = 1, days_ahead: int = 14, calendar_name: Optional[str] = None) -> List[Dict[str, Any]]:
    script = f"""
tell application "Calendar"
    set today to current date
    set startDate to today - ({days_back} * days)
    set hours of startDate to 0
    set minutes of startDate to 0
    set seconds of startDate to 0
    set endDate to today + ({days_ahead} * days)
    set hours of endDate to 23
    set minutes of endDate to 59
    set seconds of endDate to 59
    
    set output to ""
    set targetCals to calendars
    {'if exists calendar "' + calendar_name + '" then set targetCals to {calendar "' + calendar_name + '"} end if' if calendar_name else ""}
    
    repeat with c in targetCals
        set calName to name of c
        try
            set evList to (every event of c whose start date >= startDate and start date <= endDate)
            repeat with ev in evList
                set evSummary to summary of ev
                set evStart to ((start date of ev) as «class isot» as string)
                set evEnd to ((end date of ev) as «class isot» as string)
                set evLoc to ""
                try
                    set evLoc to location of ev
                end try
                set evDesc to ""
                try
                    set evDesc to description of ev
                end try
                set output to output & calName & "<|>" & evSummary & "<|>" & evStart & "<|>" & evEnd & "<|>" & evLoc & "<|>" & evDesc & "<//>" & return
            end repeat
        end try
    end repeat
    return output
end tell
"""
    raw_output = run_applescript(script)
    events = []
    if not raw_output:
        return events
        
    records = raw_output.split("<//>")
    for rec in records:
        rec = rec.strip()
        if not rec:
            continue
        parts = rec.split("<|>")
        if len(parts) >= 4:
            events.append({
                "calendar": parts[0].strip(),
                "summary": parts[1].strip(),
                "start": parts[2].strip(),
                "end": parts[3].strip(),
                "location": parts[4].strip() if len(parts) > 4 else "",
                "description": parts[5].strip() if len(parts) > 5 else ""
            })
    return events

def event_exists(title: str, start_dt_str: str, calendar_name: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        target_date = datetime.datetime.fromisoformat(start_dt_str).date()
    except Exception:
        target_date = datetime.datetime.strptime(start_dt_str[:10], "%Y-%m-%d").date()
        
    events = list_events(days_back=30, days_ahead=60, calendar_name=calendar_name)
    matches = []
    for ev in events:
        try:
            ev_date = datetime.datetime.fromisoformat(ev["start"]).date()
        except Exception:
            ev_date = datetime.datetime.strptime(ev["start"][:10], "%Y-%m-%d").date()
            
        if ev["summary"].strip().lower() == title.strip().lower() and ev_date == target_date:
            matches.append(ev)
    return matches

def add_event(
    title: str,
    start_str: str,
    end_str: str,
    calendar_name: str,
    description: str = "",
    location: str = "",
    force: bool = False
) -> Dict[str, Any]:
    if not force:
        existing = event_exists(title, start_str, calendar_name)
        if existing:
            return {
                "status": "skipped",
                "message": f"Duplicate detected: Event '{title}' already exists on {start_str[:10]} in calendar '{existing[0]['calendar']}'. Pass --force to override.",
                "existing": existing
            }
            
    safe_title = title.replace('"', '\\"')
    safe_desc = description.replace('"', '\\"')
    safe_loc = location.replace('"', '\\"')
    safe_cal = calendar_name.replace('"', '\\"')
    
    start_dt = datetime.datetime.fromisoformat(start_str.replace("Z", ""))
    end_dt = datetime.datetime.fromisoformat(end_str.replace("Z", ""))
    
    script = f"""
tell application "Calendar"
    if not (exists calendar "{safe_cal}") then
        make new calendar with properties {{name:"{safe_cal}"}}
    end if
    set targetCal to calendar "{safe_cal}"
    
    set startDate to (current date)
    set year of startDate to {start_dt.year}
    set month of startDate to {start_dt.month}
    set day of startDate to {start_dt.day}
    set hours of startDate to {start_dt.hour}
    set minutes of startDate to {start_dt.minute}
    set seconds of startDate to {start_dt.second}
    
    set endDate to (current date)
    set year of endDate to {end_dt.year}
    set month of endDate to {end_dt.month}
    set day of endDate to {end_dt.day}
    set hours of endDate to {end_dt.hour}
    set minutes of endDate to {end_dt.minute}
    set seconds of endDate to {end_dt.second}
    
    tell targetCal
        set newEv to make new event with properties {{summary:"{safe_title}", start date:startDate, end date:endDate, description:"{safe_desc}", location:"{safe_loc}"}}
    end tell
end tell
"""
    run_applescript(script)
    return {
        "status": "created",
        "calendar": calendar_name,
        "summary": title,
        "start": start_str,
        "end": end_str
    }

def find_duplicates(calendar_name: Optional[str] = None, days_back: int = 30, days_ahead: int = 90) -> Dict[str, List[Dict[str, Any]]]:
    events = list_events(days_back=days_back, days_ahead=days_ahead, calendar_name=calendar_name)
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    
    for ev in events:
        key = f"{ev['summary'].strip().lower()}|{ev['start'][:10]}"
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(ev)
        
    duplicates = {k: v for k, v in grouped.items() if len(v) > 1}
    return duplicates
