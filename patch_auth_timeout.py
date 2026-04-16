with open("automation/modules/auth_zai.py", "r") as f:
    content = f.read()

old_wait = """    # Find new z.ai tab
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if "chat.z.ai" in driver.current_url:
            break

    # Fill password
    close_consent_popups(driver)
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#password"))
    ).send_keys(password)"""

new_wait = """    # Find new z.ai tab
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if "chat.z.ai" in driver.current_url:
            break

    # Fill password
    close_consent_popups(driver)
    try:
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#password"))
        ).send_keys(password)
    except Exception as e:
        print(f"[!] Error finding password field. Perhaps it was already verified or the page didn't load properly: {e}")
        try:
            print("[*] URL:", driver.current_url)
            driver.save_screenshot("/home/alan/zai-automation/artifacts/screenshots/password_fail.png")
        except:
            pass
        raise RuntimeError("Failed to verify email, password field not found.")"""

content = content.replace(old_wait, new_wait)

with open("automation/modules/auth_zai.py", "w") as f:
    f.write(content)
