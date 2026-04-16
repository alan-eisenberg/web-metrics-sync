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
            
        # Check if the generation failed to even start (Sandbox limit reached)
        send_btn = driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='end'], #send-message-button")
        containers = driver.find_elements(By.CSS_SELECTOR, "#response-content-container, .response-content")
        
        if send_btn and send_btn[-1].is_enabled() and not containers:
            # Send button is clickable but there is no response. It failed to start!
            # Could be the Sandbox Limit toast.
            return "SANDBOX_LIMIT", None
            
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
