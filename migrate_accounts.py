#!/usr/bin/env python3
"""
Quick migration script to add account_username to existing repos in state.json
"""
import json
import yaml
from pathlib import Path

# Load config
config_path = Path.home() / '.config/code-backup/config.yaml'
with open(config_path) as f:
    config = yaml.safe_load(f)

# Load state
state_path = Path.home() / '.local/share/code-backup/state.json'
with open(state_path) as f:
    state = json.load(f)

# Migrate repos
tracked_repos = state.get('tracked_repos', {})
updated_count = 0

for repo_path, repo_info in tracked_repos.items():
    # Skip if already has account_username
    if repo_info.get('account_username') and repo_info['account_username'] != 'unknown':
        print(f"✓ {repo_info['name']}: already has account {repo_info['account_username']}")
        continue

    # Find matching watched path
    found = False
    for path_config in config.get('watched_paths', []):
        watched_path = Path(path_config.get('path')).expanduser().resolve()
        repo_path_obj = Path(repo_path)

        try:
            repo_path_obj.relative_to(watched_path)
            # Found match
            account_username = path_config['account']['username']
            repo_info['account_username'] = account_username
            print(f"✓ {repo_info['name']}: migrated to account {account_username}")
            updated_count += 1
            found = True
            break
        except (ValueError, KeyError):
            continue

    if not found:
        print(f"✗ {repo_info['name']}: could not find matching account")

# Save updated state
if updated_count > 0:
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)
    print(f"\n✅ Successfully migrated {updated_count} repositories!")
    print("Please restart the daemon to load the updated state.")
else:
    print("\n✅ No repositories needed migration.")
