import urllib.request
import base64
import csv
import os
import sys

DEST_DIR = "/mnt/vault/Downloads/vpns"
if not os.path.exists(DEST_DIR):
    os.makedirs(DEST_DIR, exist_ok=True)

print("[*] Fetching VPNGate list...")
try:
    req = urllib.request.Request("http://www.vpngate.net/api/iphone/", headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        data = response.read().decode('utf-8')
except Exception as e:
    print(f"[!] Failed to fetch VPNGate: {e}")
    sys.exit(1)

# VPNGate CSV format starts with 2 comment lines
lines = data.split('\n')
csv_lines = [l for l in lines if not l.startswith('*') and l.strip()]

reader = csv.reader(csv_lines)
header = next(reader)
try:
    b64_idx = header.index("OpenVPN_ConfigData_Base64")
    score_idx = header.index("Score")
    ip_idx = header.index("IP")
    country_idx = header.index("CountryShort")
except ValueError as e:
    print(f"[!] Could not parse CSV headers: {e}")
    sys.exit(1)

# sort by score
servers = []
for row in reader:
    if len(row) > b64_idx:
        try:
            score = int(row[score_idx])
            servers.append(row)
        except:
            pass

servers.sort(key=lambda x: int(x[score_idx]), reverse=True)

# Take top 200 to give you a massive pool and recover the ones we just lost
top_n = servers[:200]

count = 0
for row in top_n:
    ip = row[ip_idx]
    country = row[country_idx]
    b64_data = row[b64_idx]
    
    if not b64_data:
        continue
        
    try:
        ovpn_content = base64.b64decode(b64_data).decode('utf-8')
        
        filename = f"vpngate_{country}_{ip.replace('.', '_')}.ovpn"
        filepath = os.path.join(DEST_DIR, filename)
        
        # Don't overwrite if it already exists, just add new ones
        if not os.path.exists(filepath):
            with open(filepath, "w") as f:
                f.write(ovpn_content)
            count += 1
    except Exception as e:
        print(f"[!] Failed to decode {ip}: {e}")

print(f"[*] Successfully saved {count} new VPNGate OpenVPN configs to {DEST_DIR}!")
