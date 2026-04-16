import json
import subprocess
import os
from pathlib import Path


def append_and_push_links(links: list[str], use_git: bool = False) -> None:
    if not links:
        return

    # Use the current zai-automation repository
    # Store links.json directly inside the current repo
    default_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    altissia_path = os.environ.get("ALTISSIA_DIR", default_path)
    altissia_dir = Path(altissia_path)
    links_file = altissia_dir / "automation" / "data" / "links.json"

    # Ensure the directory exists and create an empty list if no file exists
    links_file.parent.mkdir(parents=True, exist_ok=True)
    if not links_file.exists():
        links_file.write_text("[]\n", encoding="utf-8")

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
        print("[*] No new links to add to repository.")
        return

    # Write back to links.json
    try:
        links_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f"[*] Added {len(links)} links to {links_file.name}")
    except Exception as e:
        print(f"[!] Error writing to links.json: {e}")
        return

    # Git commit and push
    if not use_git:
        return

    import time
    import random

    max_retries = 10
    base_delay = 2

    for attempt in range(max_retries):
        try:
            # Revert local changes to avoid unstaged changes error during pull
            subprocess.run(
                ["git", "checkout", "--", "automation/data/links.json"],
                cwd=altissia_dir,
                capture_output=True,
            )

            # Sync with remote first
            pull_res = subprocess.run(
                ["git", "pull", "--rebase"],
                cwd=altissia_dir,
                capture_output=True,
                text=True,
            )
            if pull_res.returncode != 0:
                print(f"[!] Git pull --rebase failed:\n{pull_res.stderr}")
                subprocess.run(
                    ["git", "rebase", "--abort"], cwd=altissia_dir, capture_output=True
                )

            # Re-read the file in case it was updated by git pull
            try:
                current_data = json.loads(links_file.read_text(encoding="utf-8"))
                if not isinstance(current_data, list):
                    current_data = []
            except Exception:
                current_data = []

            # Ensure all our links are in there
            changed = False
            for link in links:
                if link not in current_data:
                    current_data.append(link)
                    changed = True

            if changed:
                links_file.write_text(
                    json.dumps(current_data, indent=2) + "\n", encoding="utf-8"
                )

            git_email = os.environ.get("GIT_USER_EMAIL", "bot@zai-automation.local")
            git_name = os.environ.get("GIT_USER_NAME", "ZAI Bot")

            subprocess.run(
                ["git", "config", "user.email", git_email],
                cwd=altissia_dir,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", git_name],
                cwd=altissia_dir,
                capture_output=True,
            )

            subprocess.run(
                ["git", "add", "automation/data/links.json"],
                cwd=altissia_dir,
                check=True,
                capture_output=True,
            )

            commit_res = subprocess.run(
                ["git", "commit", "-m", "Add new preview links from zai-automation"],
                cwd=altissia_dir,
                capture_output=True,
                text=True,
            )
            # It's possible there is nothing to commit if changed == False and we just rebased

            print(f"[*] Pushing to origin (Attempt {attempt + 1})...")
            push_res = subprocess.run(
                ["git", "push"], cwd=altissia_dir, capture_output=True, text=True
            )

            if push_res.returncode == 0:
                print("[*] Successfully pushed links.json to repository.")
                break
            else:
                print(f"[!] Failed to push. Output:\n{push_res.stderr}")
                raise RuntimeError("Git push failed")

        except Exception as e:
            print(
                f"[!] Error during git operations (Attempt {attempt + 1}/{max_retries}): {e}"
            )
            if attempt < max_retries - 1:
                subprocess.run(
                    ["git", "reset", "--hard", "origin/main"],
                    cwd=altissia_dir,
                    capture_output=True,
                )
                jitter = random.uniform(0.5, 3.0)
                sleep_time = (base_delay * attempt) + jitter
                print(f"[*] Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
            else:
                print("[!] Max retries reached. Could not push to repository.")
