import csv
import base64
import urllib.request
import os

url = "http://www.vpngate.net/api/iphone/"
output_dir = "/mnt/vault/Downloads/vpns/free_ovpn"

os.makedirs(output_dir, exist_ok=True)
print(f"Fetching VPN lists from {url}...")

req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    data = response.read().decode("utf-8")

lines = data.splitlines()
lines = [line for line in lines if not line.startswith("*")]

reader = csv.reader(lines)
headers = next(reader)

count = 0
for row in reader:
    if len(row) < 15:
        continue
    host_name = row[0]
    ip = row[1]
    country = row[5]
    config_base64 = row[-1]

    if not config_base64:
        continue

    try:
        config_data = base64.b64decode(config_base64).decode("utf-8")
        filename = os.path.join(output_dir, f"vpngate_{country}_{ip}.ovpn")
        with open(filename, "w") as f:
            f.write(config_data)
        count += 1
        if count >= 50:  # Limit to 50 for now
            break
    except Exception as e:
        print(f"Failed to parse row for {ip}: {e}")

print(f"Successfully downloaded and saved {count} .ovpn files to {output_dir}")
