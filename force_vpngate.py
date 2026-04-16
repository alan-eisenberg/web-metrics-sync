with open("automation/modules/vpn.py", "r") as f:
    code = f.read()

import re

# Force it to only select VPNGate profiles
new_code = """def load_profiles(profiles_dir: Path) -> list[Path]:
    profiles = sorted(profiles_dir.glob("vpngate_*.ovpn"))
    if not profiles:
        raise VPNError(f"No vpngate_*.ovpn profiles found in {profiles_dir}")
    return profiles"""

code = re.sub(r"def load_profiles\(profiles_dir: Path\) -> list\[Path\]:.*?return profiles", new_code, code, flags=re.DOTALL)

with open("automation/modules/vpn.py", "w") as f:
    f.write(code)
