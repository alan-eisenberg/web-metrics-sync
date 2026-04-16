with open("automation/modules/vpn.py", "r") as f:
    content = f.read()

# Make sure SOCKS processes are ruthlessly killed
old_cleanup = """        pid_file = Path(metadata["socks_pid_file"])
        if pid_file.exists():
            try:
                with open(pid_file) as f:
                    pid = f.read().strip()
                print(f"[*] Stopping SOCKS5 proxy (PID {pid})...")
                subprocess.run(["kill", pid], check=False, stderr=subprocess.DEVNULL)
                pid_file.unlink(missing_ok=True)
            except Exception as e:
                print(f"[!] Warning: failed to read/kill socks proxy: {e}")"""

new_cleanup = """        pid_file = Path(metadata["socks_pid_file"])
        if pid_file.exists():
            try:
                with open(pid_file) as f:
                    pid = f.read().strip()
                print(f"[*] Stopping SOCKS5 proxy (PID {pid})...")
                subprocess.run(["kill", "-9", pid], check=False, stderr=subprocess.DEVNULL)
                pid_file.unlink(missing_ok=True)
            except Exception as e:
                print(f"[!] Warning: failed to read/kill socks proxy: {e}")
        
        # aggressively kill any dangling tun2socks processes just in case
        subprocess.run(["killall", "-9", "tun2socks"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)"""

content = content.replace(old_cleanup, new_cleanup)
with open("automation/modules/vpn.py", "w") as f:
    f.write(content)
