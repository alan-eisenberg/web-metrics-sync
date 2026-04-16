with open("automation/modules/auth_zai.py", "r") as f:
    content = f.read()

old_poll_loop = """        # Refresh the page every 6 seconds to force inbox update
        if i > 0 and i % 3 == 0:
            print(
                f"[*] Z.ai Verification email not found yet, refreshing CleanTempMail ({i * 2}s)..."
            )
            driver.refresh()
            time.sleep(1)  # wait a moment after refresh"""

new_poll_loop = """        # Refresh the page every 6 seconds to force inbox update
        if i > 0 and i % 3 == 0:
            print(
                f"[*] Z.ai Verification email not found yet, refreshing CleanTempMail ({i * 2}s)..."
            )
            try:
                driver.refresh()
                if "ERR_SOCKS_CONNECTION_FAILED" in driver.page_source or "ERR_PROXY_CONNECTION_FAILED" in driver.page_source or "ERR_CONNECTION_CLOSED" in driver.page_source:
                    print("[!] Network dropped. Attempting to reload cleantempmail.com...")
                    time.sleep(2)
                    driver.get("https://cleantempmail.com")
            except Exception as e:
                print(f"[!] Error refreshing page: {e}")
                
            time.sleep(1)  # wait a moment after refresh"""

content = content.replace(old_poll_loop, new_poll_loop)

with open("automation/modules/auth_zai.py", "w") as f:
    f.write(content)
