import requests

live_url = "https://preview-chat-a941c366-ed1d-41d4-bf58-ab387cf939b7.space.z.ai/"
dead_url = "https://preview-chat-51c34b1d-81ce-43b0-9eab-43a19c37edb2.space.z.ai/"

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

print("Fetching LIVE...")
live_resp = requests.get(live_url, headers=headers)
live_text = live_resp.text

print(f"Live Status: {live_resp.status_code}, Length: {len(live_text)}")

print("\nFetching DEAD...")
dead_resp = requests.get(dead_url, headers=headers)
dead_text = dead_resp.text

print(f"Dead Status: {dead_resp.status_code}, Length: {len(dead_text)}")

print("\n--- DEAD TEXT SNIPPET ---")
print(dead_text[:500])

if live_text == dead_text:
    print("\nThey are exactly the same HTML!")
else:
    print("\nThey are different. Let's find unique strings in DEAD.")
    if "404" in dead_text: print("- Contains '404'")
    if "deployment not found" in dead_text.lower(): print("- Contains 'deployment not found'")
    if "sandbox" in dead_text.lower(): print("- Contains 'sandbox'")

