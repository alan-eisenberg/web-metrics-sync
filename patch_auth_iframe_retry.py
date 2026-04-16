with open("automation/modules/auth_zai.py", "r") as f:
    content = f.read()

# Let's see if the iframe just takes too long to load
old_iframe_loop = """        print("[*] Link not in main content, checking iframes...")
        iframes = driver.find_elements(By.CSS_SELECTOR, "iframe")
        print(f"[*] Found {len(iframes)} iframes")"""

new_iframe_loop = """        print("[*] Link not in main content, checking iframes...")
        # Re-fetch the page source inside the loop in case the network took a moment
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        iframes = driver.find_elements(By.CSS_SELECTOR, "iframe")
        print(f"[*] Found {len(iframes)} iframes")"""

content = content.replace(old_iframe_loop, new_iframe_loop)

with open("automation/modules/auth_zai.py", "w") as f:
    f.write(content)
