import os
import time
import random
import requests
import subprocess
from pathlib import Path
import sys

# Ensure automation modules can be imported
sys.path.append("/home/alan/zai-automation")
from automation.modules.vpn import connect_vpn, cleanup, VPNError


def test_vpns(num_to_test=5):
    ovpn_dir = Path("/mnt/vault/Downloads/vpns/free_ovpn")
    profiles = list(ovpn_dir.glob("*.ovpn"))

    if not profiles:
        print("No .ovpn files found!")
        return

    random.shuffle(profiles)
    test_profiles = profiles[:num_to_test]

    print(f"Testing {len(test_profiles)} random VPN profiles from VPN Gate...")
    print("-" * 60)

    results = []

    for i, profile in enumerate(test_profiles):
        print(f"\n[{i + 1}/{len(test_profiles)}] Testing {profile.name}...")
        start_time = time.time()

        # We need an auth path to satisfy connect_vpn signature,
        # though connect_vpn auto-creates one for 'vpngate'
        dummy_auth = Path("/tmp/dummy_auth.txt")
        dummy_auth.write_text("vpn\nvpn\n")

        run_id = f"test_{int(time.time())}_{i}"
        metadata = {}

        try:
            # 1. Connect
            metadata = connect_vpn(profile, dummy_auth, run_id)
            connect_time = time.time() - start_time
            proxy = metadata.get("proxy")
            public_ip = metadata.get("public_ip")

            # 2. Test speed/latency via proxy
            print(f"    Connected successfully in {connect_time:.2f}s! IP: {public_ip}")
            print(f"    Testing proxy {proxy} with curl...")

            req_start = time.time()
            res = subprocess.run(
                ["curl", "-s", "--max-time", "10", "-x", proxy, "https://ifconfig.me"],
                capture_output=True,
                text=True,
            )
            latency = time.time() - req_start

            if res.returncode == 0 and res.stdout.strip():
                print(
                    f"    Ping test successful! Latency: {latency:.2f}s, Response IP: {res.stdout.strip()}"
                )
                results.append(
                    {
                        "profile": profile.name,
                        "status": "Success",
                        "connect_time": connect_time,
                        "latency": latency,
                        "ip": public_ip,
                        "response_ip": res.stdout.strip(),
                    }
                )
            else:
                print(f"    Ping test failed: {res.stderr}")
                results.append(
                    {
                        "profile": profile.name,
                        "status": f"Failed (Ping) {res.returncode}",
                    }
                )

        except Exception as e:
            err_msg = str(e)
            print(f"    Connection failed: {err_msg[:100]}")
            results.append(
                {"profile": profile.name, "status": f"Failed ({err_msg[:40]}...)"}
            )

        finally:
            print("    Cleaning up...")
            if not metadata:
                metadata = {"vpn_pid_file": f"/tmp/openvpn_{run_id}.pid"}
            cleanup(metadata)
            time.sleep(1)

    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    for r in results:
        if r["status"] == "Success":
            print(
                f"✅ {r['profile']:<35} | Connect: {r['connect_time']:.2f}s | Latency: {r['latency']:.2f}s | IP: {r['ip']}"
            )
        else:
            print(f"❌ {r['profile']:<35} | Error: {r['status']}")
    print("=" * 80)


if __name__ == "__main__":
    test_vpns(5)
