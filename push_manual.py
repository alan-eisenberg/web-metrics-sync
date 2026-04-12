import json
import sys
from pathlib import Path
import subprocess

def main():
    urls = [
        "https://preview-chat-f28e85cd-6281-44e7-b23d-cbfd42b2cb18.space.z.ai/",
        "https://preview-chat-ffae9770-90fb-409e-a29f-1b3ed97b50cd.space.z.ai/",
        "https://preview-chat-3fb5b959-eba3-47ea-a7c1-a0297df3c36a.space.z.ai/"
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
