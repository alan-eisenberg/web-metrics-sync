with open("automation/modules/chat.py", "r") as f:
    code = f.read()

import re

new_func = """def check_generation_status(driver) -> tuple[str, ChatResult | None]:
    # 1. Check if error/regenerate is visible
    if click_regenerate(driver):
        return "ERROR", None

    # 2. Check if a preview iframe is present (meaning the code generated and deployed)
    try:
        # Z.ai apps generate a preview iframe once they are complete.
        iframes = driver.find_elements(
            By.CSS_SELECTOR,
            "iframe[src*='preview-chat'], iframe[title*='Preview'], iframe[src*='space.z.ai']"
        )
        if iframes:
            # Found the web preview!
            return "FINISHED", ChatResult(
                chat_url=driver.current_url,
                response_html="",
                response_text="",
            )
            
        # Is there a "stop generating" button? If not, and there is a lot of text, maybe it finished without a preview?
        # But z.ai always creates a preview for agent apps.
        # We will strictly wait for the iframe to ensure the app is deployed before grabbing the URL!
        
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
