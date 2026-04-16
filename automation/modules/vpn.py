import random
import subprocess
import time
from pathlib import Path


import socket


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def cleanup(metadata: dict[str, str]):
    if "vpn_pid_file" in metadata:
        pid_file = Path(metadata["vpn_pid_file"])
        if pid_file.exists():
            try:
                res = subprocess.run(
                    ["sudo", "cat", str(pid_file)], capture_output=True, text=True
                )
                if res.returncode == 0:
                    pid = res.stdout.strip()
                    print(f"[*] Stopping OpenVPN (PID {pid})...")
                    subprocess.run(["sudo", "kill", pid], capture_output=True)
                subprocess.run(["sudo", "rm", "-f", str(pid_file)], capture_output=True)
            except Exception as e:
                print(f"[!] Failed to kill OpenVPN: {e}")
    if "proxy_pid" in metadata:
        pid = metadata["proxy_pid"]
        print(f"[*] Stopping SOCKS5 proxy (PID {pid})...")
        try:
            subprocess.run(["kill", pid], capture_output=True)
        except Exception:
            pass


class VPNError(RuntimeError):
    pass


def load_profiles(profiles_dir: Path) -> list[Path]:
    profiles = sorted(profiles_dir.glob("vpngate_*.ovpn")) + sorted(
        profiles_dir.glob("us-free-*.ovpn")
    )
    if not profiles:
        raise VPNError(
            f"No vpngate_*.ovpn or us-free-*.ovpn profiles found in {profiles_dir}"
        )
    return profiles


def pick_profile(profiles: list[Path], seed: int | None = None) -> Path:
    rng = random.Random(seed)

    last_vpn_file = profiles[0].parent.parent / "last_vpn.txt"
    last_vpn = None
    if last_vpn_file.exists():
        last_vpn = last_vpn_file.read_text(encoding="utf-8").strip()

    available_profiles = [p for p in profiles if str(p) != last_vpn]
    if not available_profiles:
        available_profiles = profiles

    chosen = rng.choice(available_profiles)
    try:
        last_vpn_file.parent.mkdir(parents=True, exist_ok=True)
        last_vpn_file.write_text(str(chosen), encoding="utf-8")
    except Exception:
        pass

    return chosen


def validate_auth_file(auth_path: Path) -> tuple[str, str]:
    if not auth_path.exists():
        raise VPNError(f"OpenVPN auth file missing: {auth_path}")
    lines = [
        ln.strip()
        for ln in auth_path.read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    if len(lines) < 2:
        raise VPNError(
            "OpenVPN auth file must contain username and password on separate lines"
        )
    return lines[0], lines[1]


def ensure_auth_file(
    auth_path: Path, username: str | None, password: str | None
) -> tuple[str, str]:
    if auth_path.exists():
        return validate_auth_file(auth_path)

    # Check for encrypted base64 auth file (obfuscated credentials without secrets)
    enc_path = auth_path.with_suffix(".enc")
    if enc_path.exists():
        import base64

        try:
            enc_data = enc_path.read_text(encoding="utf-8").strip()
            # Simple XOR decode using hardcoded key 'ZAI_FARM_OBFUSCATION'
            key = "ZAI_FARM_OBFUSCATION"
            decoded_b64 = base64.b64decode(enc_data).decode("utf-8")
            decrypted = "".join(
                chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(decoded_b64)
            )

            auth_path.parent.mkdir(parents=True, exist_ok=True)
            auth_path.write_text(decrypted, encoding="utf-8")
            return validate_auth_file(auth_path)
        except Exception as e:
            raise VPNError(f"Failed to decrypt {enc_path}: {e}")

    if not username or not password:
        raise VPNError(
            "OpenVPN credentials missing. Provide auth.txt, auth.enc, or OPENVPN_USERNAME/OPENVPN_PASSWORD env vars"
        )
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    auth_path.write_text(f"{username}\n{password}\n", encoding="utf-8")
    return username, password


def connect_vpn(
    profile: Path, auth_path: Path, run_id: str, fixed_proxy_port: int = None
) -> dict[str, str]:
    """Connects to OpenVPN."""
    print(f"[*] Starting OpenVPN connect to {profile.name}...")

    # Get current IP for comparison
    if "vpngate" in profile.name.lower():
        vpngate_auth = Path("/tmp/vpngate_auth.txt")
        vpngate_auth.write_text("vpn\nvpn\n", encoding="utf-8")
        auth_path = vpngate_auth
    else:
        # For ProtonVPN or other custom profiles, rely on the global auth_path
        # passed into the function (automation/data/openvpn/auth.txt)
        pass
    try:
        res = subprocess.run(
            ["curl", "-4", "-s", "--connect-timeout", "5", "ifconfig.me"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        original_ip = res.stdout.strip()
    except Exception:
        original_ip = None

    print(f"[*] Original IP: {original_ip}")

    # No killall openvpn or pkill socks5_proxy.py anymore to support concurrency
    log_file = Path(f"/tmp/openvpn_{run_id}.log")
    pid_file = Path(f"/tmp/openvpn_{run_id}.pid")
    subprocess.run(
        ["sudo", "rm", "-f", str(log_file), str(pid_file)], capture_output=True
    )

    cmd = [
        "sudo",
        "openvpn",
        "--config",
        str(profile),
        "--auth-user-pass",
        str(auth_path),
        "--daemon",
        "--route-nopull",
        "--pull-filter",
        "ignore",
        "dhcp-option DNS",  # Crucial: Prevent OpenVPN from hijacking system DNS
        "--script-security",
        "2",
        "--up",
        "/bin/true",  # Override any default 'up' scripts in the .ovpn file that might mess with resolv.conf
        "--down",
        "/bin/true",  # Override 'down' scripts
        "--log",
        str(log_file),
        "--writepid",
        str(pid_file),
        "--dev",
        "tun",  # Force dynamic tun allocation
        "--data-ciphers",
        "DEFAULT:AES-128-CBC:AES-256-CBC",
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise VPNError(f"Failed to start OpenVPN daemon: {e}")

    print(
        "[*] Waiting for VPN connection to establish and interface to be allocated..."
    )

    assigned_tun = None
    # Wait for the tun interface to be allocated in logs
    for _ in range(15):
        time.sleep(1)
        try:
            if log_file.exists():
                res = subprocess.run(
                    ["sudo", "cat", str(log_file)], capture_output=True, text=True
                )
                if res.returncode == 0:
                    import re

                    match = re.search(r"(tun\d+)", res.stdout)
                    if match:
                        assigned_tun = match.group(1)
                        break
        except Exception:
            pass

    if not assigned_tun:
        print("[!] VPN connection failed to allocate an interface. OpenVPN log:")
        try:
            subprocess.run(["sudo", "cat", str(log_file)])
        except Exception:
            pass
        cleanup({"vpn_pid_file": str(pid_file)})
        raise VPNError(
            "VPN connection failed to allocate tun interface within 15 seconds."
        )

    print(f"[*] VPN assigned interface: {assigned_tun}")

    new_ip = None
    for i in range(15):
        time.sleep(2)
        try:
            res = subprocess.run(
                [
                    "curl",
                    "-4",
                    "-s",
                    "--interface",
                    assigned_tun,
                    "--max-time",
                    "5",
                    "https://api.ipify.org",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            current_ip = res.stdout.strip()
            if current_ip and current_ip != original_ip and "." in current_ip:
                new_ip = current_ip
                break
        except Exception:
            pass

    if not new_ip:
        print("[!] VPN connection failed or IP did not change. OpenVPN log:")
        try:
            subprocess.run(["sudo", "cat", str(log_file)])
        except Exception:
            pass
        cleanup({"vpn_pid_file": str(pid_file)})
        raise VPNError(f"VPN connection failed. IP did not change from {original_ip}")

    print(f"[*] Connected. New IP: {new_ip}")

    # Start local SOCKS5 proxy bound to specific tun interface on a free port
    proxy_port = fixed_proxy_port if fixed_proxy_port else get_free_port()
    print(
        f"[*] Starting local SOCKS5 proxy on port {proxy_port} bound to {assigned_tun}..."
    )

    proxy_script = Path(__file__).parent / "socks5_proxy.py"
    proxy_log = open(f"/tmp/socks5_{run_id}.log", "w")
    proxy_proc = subprocess.Popen(
        [
            "python3",
            str(proxy_script),
            "--bind-iface",
            assigned_tun,
            "--port",
            str(proxy_port),
        ],
        stdout=proxy_log,
        stderr=subprocess.STDOUT,
    )
    time.sleep(2)  # Give proxy time to start

    username, _ = validate_auth_file(auth_path)
    return {
        "vpn_profile": str(profile),
        "vpn_user": username,
        "public_ip": new_ip,
        "connected": "true",
        "proxy": f"socks5://127.0.0.1:{proxy_port}",
        "vpn_pid_file": str(pid_file),
        "proxy_pid": str(proxy_proc.pid),
    }
