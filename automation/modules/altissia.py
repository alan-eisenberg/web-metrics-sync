import json
import subprocess
import os
import time
import random
from pathlib import Path


LOCK_FILE = Path("/tmp/web-metrics-sync-push.lock")
LOCK_TIMEOUT = 120


def acquire_lock():
    start = time.time()
    while True:
        if not LOCK_FILE.exists():
            try:
                LOCK_FILE.write_text(str(os.getpid()))
                return True
            except FileExistsError:
                pass
        if time.time() - start > LOCK_TIMEOUT:
            return False
        time.sleep(0.5)


def release_lock():
    try:
        LOCK_FILE.unlink()
    except FileNotFoundError:
        pass


def append_and_push_links(links: list[str], use_git: bool = False) -> None:
    if not links:
        return

    default_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    altissia_path = os.environ.get("ALTISSIA_DIR", default_path)
    altissia_dir = Path(altissia_path)
    links_file = altissia_dir / "automation" / "data" / "links.json"

    links_file.parent.mkdir(parents=True, exist_ok=True)
    if not links_file.exists():
        links_file.write_text("[]\n", encoding="utf-8")

    if not acquire_lock():
        print(
            "[!] Could not acquire push lock (another workflow is pushing). Skipping push."
        )
        return

    try:
        try:
            data = json.loads(links_file.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                data = []
        except Exception as e:
            print(f"[!] Error reading links.json: {e}")
            data = []

        added = False
        for link in links:
            if link not in data:
                data.append(link)
                added = True

        if not added:
            print("[*] No new links to add.")
            return

        if not use_git:
            links_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            print(f"[*] Written {len(links)} links locally.")
            return

        max_retries = 10
        base_delay = 2

        for attempt in range(max_retries):
            try:
                subprocess.run(
                    ["git", "fetch", "origin"],
                    cwd=altissia_dir,
                    capture_output=True,
                )

                subprocess.run(
                    ["git", "reset", "--hard", "origin/master"],
                    cwd=altissia_dir,
                    capture_output=True,
                )

                try:
                    current_data = json.loads(links_file.read_text(encoding="utf-8"))
                    if not isinstance(current_data, list):
                        current_data = []
                except Exception:
                    current_data = []

                changed = False
                for link in links:
                    if link not in current_data:
                        current_data.append(link)
                        changed = True

                if changed:
                    links_file.write_text(
                        json.dumps(current_data, indent=2) + "\n", encoding="utf-8"
                    )

                git_email = os.environ.get(
                    "GIT_USER_EMAIL", "bot@web-metrics-sync.local"
                )
                git_name = os.environ.get("GIT_USER_NAME", "Metrics Bot")

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

                subprocess.run(
                    ["git", "commit", "-m", "chore: sync new metrics links"],
                    cwd=altissia_dir,
                    capture_output=True,
                )

                print(f"[*] Pushing to origin (Attempt {attempt + 1})...")
                push_res = subprocess.run(
                    ["git", "push"],
                    cwd=altissia_dir,
                    capture_output=True,
                    text=True,
                )

                if push_res.returncode == 0:
                    print(f"[*] Successfully pushed {len(links)} links.")
                    break
                else:
                    print(f"[!] Push failed: {push_res.stderr.strip()}")
                    raise RuntimeError("Git push failed")

            except Exception as e:
                print(f"[!] Git op failed (Attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    jitter = random.uniform(0.5, 3.0)
                    sleep_time = (base_delay * (attempt + 1)) + jitter
                    print(f"[*] Retrying in {sleep_time:.1f}s...")
                    time.sleep(sleep_time)
                else:
                    print("[!] Max retries reached.")

    finally:
        release_lock()
