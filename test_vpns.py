import sys
import time
from pathlib import Path
import subprocess

# Add project root to path
sys.path.append('/home/alan/zai-automation')
from automation.modules import vpn

vpn_dir = Path("/mnt/vault/Downloads/vpns")
# Pick 3 random VPNGate profiles to test
import random
profiles = list(vpn_dir.glob("vpngate_*.ovpn"))
random.shuffle(profiles)
test_profiles = profiles[:3]

auth_path = Path("/tmp/vpngate_auth.txt")
auth_path.write_text("vpn\nvpn\n")

print(f"[*] Found {len(profiles)} VPNGate profiles. Testing 3 random ones...")

for profile in test_profiles:
    print(f"\n{'='*40}")
    print(f"[*] Testing Profile: {profile.name}")
    print(f"{'='*40}")
    
    run_id = f"test_{int(time.time())}"
    conn_info = {}
    try:
        conn_info = vpn.connect_vpn(profile, auth_path, run_id)
        print(f"\n[+] SUCCESS!")
        print(f"    Assigned IP : {conn_info.get('public_ip')}")
        print(f"    SOCKS5 Proxy: {conn_info.get('proxy')}")
        
        # Verify proxy actually routes traffic
        print("    Verifying traffic through proxy...")
        res = subprocess.run(
            ["curl", "-s", "-x", conn_info['proxy'], "ifconfig.me"], 
            capture_output=True, text=True, timeout=10
        )
        print(f"    Proxy Output: {res.stdout.strip()}")
        
    except Exception as e:
        print(f"\n[-] FAILED: {e}")
    finally:
        print("[*] Cleaning up connection...")
        if not conn_info:
            conn_info = {"vpn_pid_file": f"/tmp/openvpn_{run_id}.pid"}
        vpn.cleanup(conn_info)
        time.sleep(2)
