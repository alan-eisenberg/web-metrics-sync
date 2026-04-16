with open("automation/modules/chat.py", "r") as f:
    code = f.read()

import re

new_func = """def check_generation_status(driver) -> tuple[str, ChatResult | None]:
    # 1. Check if error/regenerate is visible
    if click_regenerate(driver):
        return "ERROR", None

    # 2. Check if a preview iframe is present (meaning the code generated and deployed)
    try:
        iframes = driver.find_elements(
            By.CSS_SELECTOR,
            "iframe[src*='preview-chat'], iframe[title*='Preview'], iframe[src*='space.z.ai']"
        )
        if iframes:
            return "FINISHED", ChatResult(
                chat_url=driver.current_url,
                response_html="",
                response_text="",
            )
            
        # Also check if it's "Done" by looking for the "Send" button being re-enabled, 
        # BUT only if we also have response text (as a fallback in case the app doesn't have an iframe but generation stopped)
        send_btn = driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='end'], #send-message-button")
        if send_btn and send_btn[-1].is_enabled():
            containers = driver.find_elements(By.CSS_SELECTOR, "#response-content-container, .response-content")
            if containers and len(containers[-1].text) > 100:
                # Give it a few extra seconds to render the iframe just in case
                import time
                time.sleep(5)
                iframes_after = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='preview-chat'], iframe[title*='Preview'], iframe[src*='space.z.ai']")
                if iframes_after:
                    return "FINISHED", ChatResult(chat_url=driver.current_url, response_html="", response_text="")
                else:
                    # It finished generating but no iframe. Maybe the prompt didn't yield an app.
                    return "FINISHED", ChatResult(chat_url=driver.current_url, response_html="", response_text="")
    except Exception as e:
        print(f"[!] Error checking status: {e}")

    # 3. Otherwise, still generating
    return "GENERATING", None
"""

code = re.sub(
    r"def check_generation_status\(driver\) -> tuple\[str, ChatResult \| None\]:.*?return \"GENERATING\", None\n",
    new_func,
    code,
    flags=re.DOTALL
)

with open("automation/modules/chat.py", "w") as f:
    f.write(code)
