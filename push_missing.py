import json
import os
import subprocess

CRED_PATH = "automation/data/credentials.json"
REPO_DIR = "/mnt/vault/repos/altissiabooster"
LINKS_JSON = os.path.join(REPO_DIR, "links.json")

# Links to add
chat_links = [
    "https://chat.z.ai/c/0400cbb6-a4bb-4abf-934d-de5d890ec32f",
    "https://chat.z.ai/c/7f146ca7-f7b8-4d43-b3ca-29b8f8c359d3",
    "https://chat.z.ai/c/84b417b2-ff8b-4861-8b35-b077f205ed0b",
]

preview_links = []
for chat_url in chat_links:
    uuid = chat_url.split("/c/", 1)[1].split("?", 1)[0]
    preview_url = f"https://preview-chat-{uuid}.space.z.ai/"
    preview_links.append(preview_url)

with open(CRED_PATH, "r") as f:
    creds = json.load(f)

# The last item in the list
last_cred = creds[-1]
if "preview_urls" not in last_cred:
    last_cred["preview_urls"] = []

for preview_link in preview_links:
    if preview_link not in last_cred["preview_urls"]:
        last_cred["preview_urls"].append(preview_link)

with open(CRED_PATH, "w") as f:
    json.dump(creds, f, indent=2)
print(f"[*] Added {len(preview_links)} to credentials.json.")

if os.path.exists(LINKS_JSON):
    with open(LINKS_JSON, "r") as f:
        repo_links = json.load(f)
else:
    repo_links = []

for preview_link in preview_links:
    if preview_link not in repo_links:
        repo_links.append(preview_link)

with open(LINKS_JSON, "w") as f:
    json.dump(repo_links, f, indent=2)
print("[*] Added to altissiabooster links.json...")

print("[*] Committing to repo...")
subprocess.run(["git", "add", "links.json"], cwd=REPO_DIR)
subprocess.run(
    [
        "git",
        "commit",
        "-m",
        f"Add missing preview links for {last_cred.get('email', 'last_user')}",
    ],
    cwd=REPO_DIR,
)
subprocess.run(["git", "push", "origin", "master"], cwd=REPO_DIR)
print("[*] Done!")
