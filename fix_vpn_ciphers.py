with open("automation/modules/vpn.py", "r") as f:
    code = f.read()

import re

# Add data-ciphers to the openvpn command arguments
new_cmd = """    cmd = [
        "sudo",
        "openvpn",
        "--config",
        str(profile),
        "--auth-user-pass",
        str(auth_path),
        "--daemon",
        "--route-nopull",
        "--log",
        str(log_file),
        "--writepid",
        str(pid_file),
        "--dev",
        "tun",  # Force dynamic tun allocation
        "--data-ciphers",
        "DEFAULT:AES-128-CBC:AES-256-CBC",
    ]"""

code = re.sub(r"    cmd = \[\n        \"sudo\",\n        \"openvpn\",.*?\"tun\",  # Force dynamic tun allocation\n    \]", new_cmd, code, flags=re.DOTALL)

with open("automation/modules/vpn.py", "w") as f:
    f.write(code)
