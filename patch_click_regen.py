with open("automation/modules/chat.py", "r") as f:
    content = f.read()

old_click = """def click_regenerate(driver):
    try:
        regen_btn = driver.find_element(
            By.CSS_SELECTOR,
            "button[aria-label*='egenerate'], .regenerate-button, button.regenerate",
        )
        if regen_btn.is_displayed() and regen_btn.is_enabled():
            print("[*] Found Regenerate button. Clicking it to heal generation...")
            driver.execute_script("arguments[0].click();", regen_btn)
            time.sleep(2)
            return True
    except:
        pass"""

new_click = """def click_regenerate(driver):
    try:
        regen_btn = driver.find_element(
            By.CSS_SELECTOR,
            "button[aria-label*='egenerate'], .regenerate-button, button.regenerate",
        )
        if regen_btn.is_displayed() and regen_btn.is_enabled():
            print("[*] Found Regenerate button. Clicking it to heal generation...")
            driver.execute_script("arguments[0].click();", regen_btn)
            time.sleep(2)
            return True
    except Exception as e:
        if "invalid session id" in str(e).lower() or "tab crashed" in str(e).lower() or "no such window" in str(e).lower():
            raise e"""

content = content.replace(old_click, new_click)
with open("automation/modules/chat.py", "w") as f:
    f.write(content)
