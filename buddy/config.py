import os
import json


def _expand_paths(config):
    expanded = config.copy()
    for key in [
        "memory_file",
        "journal_file",
        "status_file",
        "vault_path",
        "codex_sessions_root",
        "opencode_db",
    ]:
        value = expanded.get(key)
        if value:
            expanded[key] = os.path.expanduser(value)

    expanded["brain_dirs"] = [
        os.path.expanduser(path) for path in expanded.get("brain_dirs", [])
    ]
    return expanded


DEFAULT_CONFIG = {
    "memory_file": "~/.config/buddy/memory.json",
    "journal_file": "~/.local/state/buddy/journal.md",
    "status_file": "~/.local/state/buddy/status.json",
    "vault_path": "~/BuddyVault",
    "brain_dirs": [
        "~/.gemini/antigravity-cli/brain",
        "~/.gemini/antigravity/brain",
        "~/.gemini/antigravity-ide/brain",
    ],
    "codex_sessions_root": "~/.codex/sessions",
    "opencode_db": "~/.local/share/opencode/opencode.db",
}

def load_config():
    """
    Loads configuration merging defaults, home configuration,
    local directory configuration, and environment variables.
    """
    config = DEFAULT_CONFIG.copy()
    
    # 1. Load from home directory config
    home_config_dir = os.path.expanduser("~/.config/buddy")
    home_config_path = os.path.join(home_config_dir, "config.json")
    if os.path.exists(home_config_path):
        try:
            with open(home_config_path, "r", encoding="utf-8") as f:
                home_data = json.load(f)
                config.update(home_data)
        except Exception as e:
            print(f"[!] Error loading global config: {e}")
            
    # 2. Load from current directory config
    for local_name in [".buddy.json", "buddy.config.json"]:
        local_path = os.path.join(os.getcwd(), local_name)
        if os.path.exists(local_path):
            try:
                with open(local_path, "r", encoding="utf-8") as f:
                    local_data = json.load(f)
                    config.update(local_data)
            except Exception as e:
                print(f"[!] Error loading local config {local_name}: {e}")
                
    # 3. Load from Environment variables
    env_mapping = {
        "BUDDY_MEMORY_FILE": "memory_file",
        "BUDDY_JOURNAL_FILE": "journal_file",
        "BUDDY_STATUS_FILE": "status_file",
        "BUDDY_VAULT_PATH": "vault_path",
        "BUDDY_CODEX_SESSIONS_ROOT": "codex_sessions_root",
        "BUDDY_OPENCODE_DB": "opencode_db"
    }
    for env_key, config_key in env_mapping.items():
        val = os.environ.get(env_key)
        if val:
            config[config_key] = val
            
    env_brains = os.environ.get("BUDDY_BRAIN_DIRS")
    if env_brains:
        config["brain_dirs"] = [p.strip() for p in env_brains.split(",")]
        
    return _expand_paths(config)

def init_config(vault_path=None):
    """
    Initializes a new global config file at ~/.config/buddy/config.json
    """
    home_config_dir = os.path.expanduser("~/.config/buddy")
    os.makedirs(home_config_dir, exist_ok=True)
    home_config_path = os.path.join(home_config_dir, "config.json")
    
    config = DEFAULT_CONFIG.copy()
    if vault_path:
        config["vault_path"] = os.path.abspath(os.path.expanduser(vault_path))
        
    with open(home_config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    print(f"[+] Initialized global configuration file: {home_config_path}")
    return config
