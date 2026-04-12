import json
import sys
from pathlib import Path
import subprocess

def main():
    urls = [
        "https://preview-chat-2ca9a83c-7910-4f62-80e3-34b0de836ae4.space.z.ai/",
        "https://preview-chat-ce6578a3-4bc8-4025-a9b7-e64a57b87761.space.z.ai/",
        "https://preview-chat-d15eb869-1fff-4118-80c2-4944a7b34b72.space.z.ai/"
    ]
    
    # 1. Update credentials.json
    creds_path = Path("/home/alan/zai-automation/automation/data/credentials.json")
    if creds_path.exists():
        with open(creds_path, "r") as f:
            creds = json.load(f)
            
        if creds and isinstance(creds, list):
            last_entry = creds[-1]
            if "preview_urls" not in last_entry:
                last_entry["preview_urls"] = []
            
            for url in urls:
                if url not in last_entry["preview_urls"]:
                    last_entry["preview_urls"].append(url)
                    
            with open(creds_path, "w") as f:
                json.dump(creds, f, indent=2)
            print("[*] Successfully updated credentials.json with the 3 URLs.")
        else:
            print("[!] credentials.json is empty or not a list.")
    else:
        print("[!] credentials.json not found.")

    # 2. Update altissiabooster/links.json and push
    sys.path.append('/home/alan/zai-automation')
    from automation.modules.altissia import append_and_push_links
    print("[*] Pushing links to altissiabooster...")
    append_and_push_links(urls)

if __name__ == "__main__":
    main()
