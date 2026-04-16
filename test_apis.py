import requests
import json
import concurrent.futures

with open('/mnt/vault/repos/altissiabooster/links.json', 'r') as f:
    links = json.load(f)

def test_api(url):
    api_url = url.rstrip('/') + '/api/terminal'
    try:
        resp = requests.post(api_url, json={"action": "init"}, timeout=10)
        return url, resp.status_code, resp.text[:100]
    except Exception as e:
        return url, 0, str(e)

alive_count = 0
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    for url, status, text in executor.map(test_api, links):
        if status == 200 and 'success' in text:
            alive_count += 1
            print(f"ALIVE: {url}")
        elif status == 200:
            print(f"WEIRD 200: {url} -> {text}")
            
print(f"Total API Alive: {alive_count}")
