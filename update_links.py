import json
from pathlib import Path
import os

links_to_add = [
    "https://preview-chat-56e32445-830f-4949-b19e-ee9c4b5e490b.space.z.ai/",
    "https://preview-chat-e4a5433b-4bbd-4665-90f0-73e888af9393.space.z.ai/",
    "https://preview-chat-ef8da2a8-5339-4777-8096-9ad15400b111.space.z.ai/",
]

# 1. Update credentials.json
cred_path = Path("/home/alan/zai-automation/automation/data/credentials.json")
creds = json.loads(cred_path.read_text())

latest_cred = creds[-1]
for link in links_to_add:
    if link not in latest_cred["preview_urls"]:
        latest_cred["preview_urls"].append(link)

cred_path.write_text(json.dumps(creds, indent=2))
print("Updated credentials.json")

# 2. Update local links.json (if there is one in automation/data)
local_links_path = Path("/home/alan/zai-automation/automation/data/links.json")
if local_links_path.exists():
    local_links = json.loads(local_links_path.read_text())
    for link in links_to_add:
        if link not in local_links:
            local_links.append(link)
    local_links_path.write_text(json.dumps(local_links, indent=2))
    print("Updated local links.json")

# 3. Use altissia to push
import sys

sys.path.append("/home/alan/zai-automation")
from automation.modules import altissia

altissia.append_and_push_links(links_to_add, use_git=True)
print("Pushed to altissiabooster")
