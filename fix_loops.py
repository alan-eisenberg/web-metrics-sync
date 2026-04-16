import sys

with open('automation/main.py', 'r') as f:
    lines = f.readlines()

# find def run():
run_idx = -1
for i, line in enumerate(lines):
    if line.startswith('def run() -> int:'):
        run_idx = i
        break

# find the main for loop
for_idx = -1
for i in range(run_idx, len(lines)):
    if 'for idx, state_name in enumerate(STATE_ORDER):' in lines[i]:
        for_idx = i
        break

# find the end of the script before return 0
return_idx = -1
for i in range(len(lines)-1, -1, -1):
    if 'return 0' in lines[i]:
        return_idx = i
        break

new_lines = lines[:for_idx]
new_lines.append('    try:\n')

for i in range(for_idx, return_idx):
    if lines[i].strip() == '':
        new_lines.append('\n')
    else:
        new_lines.append('    ' + lines[i])

new_lines.extend([
    '    except KeyboardInterrupt:\n',
    '        log.warning("User interrupted script execution.")\n',
    '    finally:\n',
    '        if state.preview_urls:\n',
    '            from automation.modules import altissia\n',
    '            log.info("Pushing %d accumulated preview urls to altissiabooster...", len(state.preview_urls))\n',
    '            altissia.append_and_push_links(state.preview_urls)\n',
    '        vpn.cleanup(state.metadata)\n',
    '        if args.gh and gh_display:\n',
    '            gh_display.stop()\n',
    '    return 0\n',
    '\n',
    'if __name__ == "__main__":\n',
    '    raise SystemExit(run())\n'
])

with open('automation/main.py', 'w') as f:
    f.writelines(new_lines)
