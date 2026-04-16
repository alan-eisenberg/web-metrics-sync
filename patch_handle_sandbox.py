with open("automation/modules/chat.py", "r") as f:
    content = f.read()

old_sandbox = """def handle_sandbox_popup(driver) -> bool:
    try:
        modals = driver.find_elements(By.CSS_SELECTOR, "div.modal-container, div[role='dialog']")
        for modal in modals:
            text = modal.text.lower() if modal.text else ""
            if "sandbox concurrency" in text or "limit" in text or "sandbox limit" in text:
                try:
                    close_btn = modal.find_element(By.CSS_SELECTOR, "button.dismiss-button, button.close, button[aria-label='Close']")
                    if close_btn.is_displayed():
                        close_btn.click()
                        time.sleep(1)
                        print("[*] Handled sandbox concurrency limit popup.")
                        return True
                except:
                    pass
    except Exception as e:
        print(f"[!] Error handling sandbox popup: {e}")
    return False

def check_generation_status(driver) -> tuple[str, ChatResult | None]:
    # 0. Check and clear any Limit Sandbox Concurrency popups
    if handle_sandbox_popup(driver):
        # We hit a limit and cleared it. Let the main loop know we hit the sandbox limit so it can retry
        return "SANDBOX_LIMIT", None

    # 1. Check if error/regenerate is visible
    if click_regenerate(driver):
        return "ERROR", None"""

new_sandbox = """def handle_sandbox_popup(driver) -> bool:
    try:
        modals = driver.find_elements(By.CSS_SELECTOR, "div.modal-container, div[role='dialog']")
        for modal in modals:
            text = modal.text.lower() if modal.text else ""
            if "sandbox concurrency" in text or "limit" in text or "sandbox limit" in text:
                try:
                    close_btn = modal.find_element(By.CSS_SELECTOR, "button.dismiss-button, button.close, button[aria-label='Close']")
                    if close_btn.is_displayed():
                        close_btn.click()
                        time.sleep(1)
                        print("[*] Handled sandbox concurrency limit popup.")
                        return True
                except:
                    pass
    except Exception as e:
        if "invalid session id" in str(e).lower() or "tab crashed" in str(e).lower() or "no such window" in str(e).lower():
            raise e
        print(f"[!] Error handling sandbox popup: {e}")
    return False

def check_generation_status(driver) -> tuple[str, ChatResult | None]:
    try:
        # 0. Check and clear any Limit Sandbox Concurrency popups
        if handle_sandbox_popup(driver):
            # We hit a limit and cleared it. Let the main loop know we hit the sandbox limit so it can retry
            return "SANDBOX_LIMIT", None

        # 1. Check if error/regenerate is visible
        if click_regenerate(driver):
            return "ERROR", None
    except Exception as e:
        if "invalid session id" in str(e).lower() or "tab crashed" in str(e).lower() or "no such window" in str(e).lower():
            raise e
        print(f"[!] Error checking status: {e}")
        return "GENERATING", None"""

content = content.replace(old_sandbox, new_sandbox)
with open("automation/modules/chat.py", "w") as f:
    f.write(content)

