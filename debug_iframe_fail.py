with open("automation/modules/auth_zai.py", "r") as f:
    content = f.read()

# Let's see what the iframe fail logic is doing and patch it to dump the DOM so we can see why it didn't find the iframe
old_fail = """    if not href:
        driver.save_screenshot(
            "/home/alan/zai-automation/artifacts/screenshots/iframe_fail.png"
        )
        print(
            "[!] Saved screenshot of failure to /home/alan/zai-automation/artifacts/screenshots/iframe_fail.png"
        )
        raise RuntimeError("Could not find verification link anywhere")"""

new_fail = """    if not href:
        driver.save_screenshot(
            "/home/alan/zai-automation/artifacts/screenshots/iframe_fail.png"
        )
        print(
            "[!] Saved screenshot of failure to /home/alan/zai-automation/artifacts/screenshots/iframe_fail.png"
        )
        
        # Dump the outer HTML so we can see what cleantempmail's DOM actually looked like when it failed
        try:
            with open("/home/alan/zai-automation/artifacts/screenshots/iframe_fail_dom.html", "w") as f:
                f.write(driver.page_source)
            print("[!] Dumped DOM to iframe_fail_dom.html")
        except:
            pass
            
        raise RuntimeError("Could not find verification link anywhere")"""

content = content.replace(old_fail, new_fail)

with open("automation/modules/auth_zai.py", "w") as f:
    f.write(content)
