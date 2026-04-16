import json
import time
import requests
import concurrent.futures
from datetime import datetime

LINKS_FILE = '/mnt/vault/repos/altissiabooster/links.json'

def check_and_revive(url):
    api_url = url.rstrip('/') + '/api/terminal'
    status = "DEAD"
    error = ""
    
    try:
        # Send an init request which triggers the auto-start script in the backend
        resp = requests.post(api_url, json={"action": "init"}, timeout=15)
        
        if resp.status_code == 200:
            try:
                data = resp.json()
                if data.get('success') or 'sessionId' in data:
                    status = "ALIVE"
                else:
                    status = "WEIRD_RESPONSE"
                    error = str(data)[:50]
            except:
                status = "INVALID_JSON"
                error = resp.text[:50]
        else:
            status = f"HTTP_{resp.status_code}"
            
    except Exception as e:
        status = "ERROR"
        error = str(e)
        
    return url, status, error

def main():
    while True:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting health check cycle...")
        
        try:
            with open(LINKS_FILE, 'r') as f:
                links = json.load(f)
        except Exception as e:
            print(f"Error reading links.json: {e}")
            time.sleep(60)
            continue
            
        alive_count = 0
        dead_count = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_url = {executor.submit(check_and_revive, url): url for url in links}
            
            for future in concurrent.futures.as_completed(future_to_url):
                url, status, error = future.result()
                
                if status == "ALIVE":
                    alive_count += 1
                else:
                    dead_count += 1
                    
        print(f"Cycle complete. ALIVE: {alive_count} | DEAD/UNREACHABLE: {dead_count}")
        
        # Sleep for 5 minutes before next cycle
        print("Sleeping for 5 minutes...")
        time.sleep(300)

if __name__ == "__main__":
    main()
