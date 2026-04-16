import re

with open("automation/modules/chat.py", "r") as f:
    content = f.read()

old_load = """def ensure_agent_mode(driver, js_dir: Path):
    try:
        driver.set_page_load_timeout(45)
        driver.get("https://chat.z.ai/")
    except TimeoutException:
        print(
            "[!] Page load timed out. Proceeding anyway since the UI might be partially rendered..."
        )
    except Exception as e:
        print(f"[!] Error loading chat.z.ai: {e}")"""

new_load = """def ensure_agent_mode(driver, js_dir: Path):
    driver.set_page_load_timeout(45)
    for attempt in range(3):
        try:
            driver.get("https://chat.z.ai/")
            if "ERR_SOCKS_CONNECTION_FAILED" in driver.page_source or "ERR_PROXY_CONNECTION_FAILED" in driver.page_source or "ERR_CONNECTION_CLOSED" in driver.page_source:
                raise Exception("Proxy/Network error page displayed")
            break
        except TimeoutException:
            print("[!] Page load timed out. Proceeding anyway since the UI might be partially rendered...")
            break
        except Exception as e:
            if attempt == 2:
                print(f"[!] Error loading chat.z.ai after 3 attempts: {e}")
                return False
            print(f"[!] Failed to load chat.z.ai, retrying ({attempt + 1}/3)...")
            time.sleep(2)"""

content = content.replace(old_load, new_load)
with open("automation/modules/chat.py", "w") as f:
    f.write(content)
