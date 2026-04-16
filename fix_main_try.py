import sys

lines = open("automation/main.py").readlines()
out = []

in_loop = False
loop_indent = "    "
for line in lines:
    if line.startswith("    for idx, state_name in enumerate(STATE_ORDER):"):
        out.append("    try:\n")
        out.append("        for idx, state_name in enumerate(STATE_ORDER):\n")
        in_loop = True
        continue

    if in_loop:
        if (
            line.strip()
            == "if driver is not None and not args.keep_open and not args.open:"
        ):
            in_loop = False
            out.append("    finally:\n")
            out.append("        vpn.cleanup(state.metadata)\n")
            out.append("        if args.gh and gh_display:\n")
            out.append("            gh_display.stop()\n")
            out.append(
                "        if driver is not None and not args.keep_open and not args.open:\n"
            )
            continue
        out.append("    " + line)
    else:
        out.append(line)

open("automation/main.py", "w").write("".join(out))
