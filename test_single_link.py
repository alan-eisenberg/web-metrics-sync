import requests
url = "https://preview-chat-5344af63-a12c-4cfa-847b-ec3fc2d8cbdb.space.z.ai/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
try:
    resp = requests.get(url, headers=headers, timeout=15)
    print(f"Status Code: {resp.status_code}")
    if "404" in resp.text and "this page could not be found" in resp.text.lower():
        print("DETECTED NEXT.JS 404 PAGE")
    else:
        print("PAGE LOADED DIFFERENTLY")
except Exception as e:
    print(f"Error: {e}")
