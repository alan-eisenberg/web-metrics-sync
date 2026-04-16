import requests
url = "https://preview-chat-820760c0-f15e-4b03-b5d7-9f674b8c3e6b.space.z.ai/"
resp = requests.get(url)
print(f"Status: {resp.status_code}")
print(f"Title: {resp.text.split('<title>')[1].split('</title>')[0] if '<title>' in resp.text else 'No Title'}")
