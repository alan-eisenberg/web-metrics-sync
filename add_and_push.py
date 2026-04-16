import json
import os
import subprocess

CRED_PATH = "automation/data/credentials.json"
REPO_DIR = "/mnt/vault/repos/altissiabooster"
LINKS_JSON = os.path.join(REPO_DIR, "links.json")

# Link to add
chat_link = "https://chat.z.ai/c/a280f083-15e9-43f1-95db-e3c6228a323e"
preview_link = "https://preview-chat-a280f083-15e9-43f1-95db-e3c6228a323e.space.z.ai/"

print(f"[*] Adding {preview_link} to the last credential...")

with open(CRED_PATH, "r") as f:
    creds = json.load(f)

# The last item in the list
last_cred = creds[-1]
if "preview_urls" not in last_cred:
    last_cred["preview_urls"] = []

if preview_link not in last_cred["preview_urls"]:
    last_cred["preview_urls"].append(preview_link)

with open(CRED_PATH, "w") as f:
    json.dump(creds, f, indent=2)
print("[*] credentials.json updated.")

print("[*] Adding to altissiabooster links.json...")
if os.path.exists(LINKS_JSON):
    with open(LINKS_JSON, "r") as f:
        repo_links = json.load(f)
else:
    repo_links = []

if preview_link not in repo_links:
    repo_links.append(preview_link)

with open(LINKS_JSON, "w") as f:
    json.dump(repo_links, f, indent=2)

print("[*] Committing to repo...")
subprocess.run(["git", "add", "links.json"], cwd=REPO_DIR)
subprocess.run(["git", "commit", "-m", f"Add missing preview link for {last_cred.get('email', 'last_user')}"], cwd=REPO_DIR)
subprocess.run(["git", "push", "origin", "master"], cwd=REPO_DIR)
print("[*] Done!")
