with open("automation/modules/chat.py", "r") as f:
    content = f.read()

old_wait = """    try:
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea#chat-input"))
        )
    except TimeoutException:
        print("[!] Timeout waiting for chat input. Proceeding...")"""

new_wait = """    try:
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea#chat-input"))
        )
    except TimeoutException:
        print("[!] Timeout waiting for chat input. Proceeding...")
    except Exception as e:
        print(f"[!] Error waiting for chat input: {e}")
        return False"""

content = content.replace(old_wait, new_wait)

with open("automation/modules/chat.py", "w") as f:
    f.write(content)
