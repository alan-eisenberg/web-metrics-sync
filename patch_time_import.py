with open("automation/main.py", "r") as f:
    content = f.read()

# Remove the inline import time that is messing up the local scope in the run() function
old_code = """                # Retry loading cleantempmail in case of VPN/SOCKS drops
                import time
                for load_attempt in range(3):"""

new_code = """                # Retry loading cleantempmail in case of VPN/SOCKS drops
                for load_attempt in range(3):"""

content = content.replace(old_code, new_code)

with open("automation/main.py", "w") as f:
    f.write(content)
