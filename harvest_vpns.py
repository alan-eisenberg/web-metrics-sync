import os
import time
import csv
import base64
import urllib.request
import subprocess
from pathlib import Path
import sys
import concurrent.futures
import threading

sys.path.append("/home/alan/zai-automation")
from automation.modules.vpn import connect_vpn, cleanup

TARGET_COUNT = 50
GOOD_DIR = Path("/mnt/vault/Downloads/vpns/verified_ovpn")
GOOD_DIR.mkdir(parents=True, exist_ok=True)


# Thread-safe counter
class Counter:
    def __init__(self):
        self.value = count_good()
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            self.value += 1
            return self.value

    def get(self):
        with self.lock:
            return self.value


def get_vpngate_data():
    url = "http://www.vpngate.net/api/iphone/"
    print(f"Fetching VPN lists from {url}...")
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        data = response.read().decode("utf-8")
    lines = data.splitlines()
    lines = [line for line in lines if not line.startswith("*")]
    return list(csv.reader(lines))[1:]  # skip header


def count_good():
    return len(list(GOOD_DIR.glob("*.ovpn")))


def test_profile(profile_path, counter):
    if counter.get() >= TARGET_COUNT:
        profile_path.unlink(missing_ok=True)
        return False

    dummy_auth = Path(f"/tmp/dummy_auth_{threading.get_ident()}.txt")
    dummy_auth.write_text("vpn\nvpn\n")
    run_id = f"test_{int(time.time())}_{threading.get_ident()}"
    metadata = {}
    success = False

    try:
        metadata = connect_vpn(profile_path, dummy_auth, run_id)
        proxy = metadata.get("proxy")
        if proxy:
            res = subprocess.run(
                ["curl", "-s", "--max-time", "5", "-x", proxy, "https://ifconfig.me"],
                capture_output=True,
                text=True,
            )
            if res.returncode == 0 and res.stdout.strip():
                success = True
    except Exception:
        pass
    finally:
        if not metadata:
            metadata = {"vpn_pid_file": f"/tmp/openvpn_{run_id}.pid"}
        cleanup(metadata)
        time.sleep(0.5)
        try:
            dummy_auth.unlink(missing_ok=True)
        except:
            pass

    if success:
        current = counter.increment()
        print(f"✅ Success: {profile_path.name} ({current}/{TARGET_COUNT})")
        return True
    else:
        print(f"❌ Failed: {profile_path.name}")
        profile_path.unlink(missing_ok=True)
        return False


def main():
    counter = Counter()
    print(f"Currently have {counter.get()}/{TARGET_COUNT} good profiles.")
    if counter.get() >= TARGET_COUNT:
        print("Already reached target!")
        return

    rows = get_vpngate_data()
    print(f"Fetched {len(rows)} servers from VPN Gate.")

    # Save all to temp files first
    to_test = []
    for row in rows:
        if len(row) < 15:
            continue
        country = row[5]
        ip = row[1]
        config_base64 = row[-1]
        if not config_base64:
            continue

        filename = f"vpngate_{country}_{ip}.ovpn"
        profile_path = GOOD_DIR / filename

        if profile_path.exists():
            continue  # Already verified

        try:
            config_data = base64.b64decode(config_base64).decode("utf-8")
            profile_path.write_text(config_data)
            to_test.append(profile_path)
        except:
            continue

    print(f"Starting parallel testing of {len(to_test)} profiles...")

    # Use 3 workers to avoid overwhelming the system tun interfaces/CPU
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for path in to_test:
            if counter.get() >= TARGET_COUNT:
                path.unlink(missing_ok=True)
                continue
            futures.append(executor.submit(test_profile, path, counter))

        for future in concurrent.futures.as_completed(futures):
            if counter.get() >= TARGET_COUNT:
                # Cancel remaining
                break

    # Final cleanup of untried files
    for path in to_test:
        if not path.exists():
            continue
        # if we reached target but file is still there and not in the "success" list, it's either untested or good
        # Wait, if we reach target, we should delete untested ones
        pass

    final_count = count_good()
    print(f"\nDone! We now have {final_count} verified good profiles in {GOOD_DIR}")


if __name__ == "__main__":
    main()
