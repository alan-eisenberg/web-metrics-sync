with open("automation/modules/vpn.py", "r") as f:
    code = f.read()

import re

new_auth = """    # Get current IP for comparison
    if "vpngate" in profile.name.lower():
        vpngate_auth = Path("/tmp/vpngate_auth.txt")
        vpngate_auth.write_text("vpn\\nvpn\\n", encoding="utf-8")
        auth_path = vpngate_auth"""

code = code.replace("    # Get current IP for comparison", new_auth)

with open("automation/modules/vpn.py", "w") as f:
    f.write(code)
