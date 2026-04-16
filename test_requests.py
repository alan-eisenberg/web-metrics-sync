import requests
import sys

url = sys.argv[1]
try:
    resp = requests.get(url, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Title 404? {'404' in resp.text and 'not be found' in resp.text.lower()}")
except Exception as e:
    print(f"Error: {e}")
