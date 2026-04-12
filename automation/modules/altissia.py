import json
import subprocess
from pathlib import Path

def append_and_push_links(links: list[str]) -> None:
    if not links:
        return
        
    altissia_dir = Path("/mnt/vault/repos/altissiabooster")
    links_file = altissia_dir / "links.json"
    
    if not links_file.exists():
        print(f"[!] Warning: {links_file} does not exist.")
        return

    try:
        data = json.loads(links_file.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            data = []
    except Exception as e:
        print(f"[!] Error reading links.json: {e}")
        data = []

    # Append new links avoiding duplicates
    added = False
    for link in links:
        if link not in data:
            data.append(link)
            added = True

    if not added:
        print("[*] No new links to add to altissiabooster.")
        return

    # Write back to links.json
    try:
        links_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f"[*] Added {len(links)} links to {links_file.name}")
    except Exception as e:
        print(f"[!] Error writing to links.json: {e}")
        return

    # Git commit and push
    try:
        subprocess.run(["git", "add", "links.json"], cwd=altissia_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add new preview links from zai-automation"], cwd=altissia_dir, check=True, capture_output=True)
        print("[*] Committing changes to altissiabooster...")
        
        res = subprocess.run(["git", "push"], cwd=altissia_dir, capture_output=True, text=True)
        if res.returncode == 0:
            print("[*] Successfully pushed links.json to altissiabooster repository.")
        else:
            print(f"[!] Failed to push to altissiabooster repository. Output:\n{res.stderr}")
    except Exception as e:
        print(f"[!] Error during git operations in altissiabooster: {e}")

