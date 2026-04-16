import time
from automation.browser import get_browser
from automation.modules import tempmail, auth_zai

driver = get_browser()
try:
    print("Getting email...")
    email = tempmail.get_temp_mail(driver)
    username = tempmail.generate_username()
    verify_url = tempmail.build_verify_url("test-token-1234", email, username)
    auth_zai.open_verify_resend(driver, verify_url)
    driver.switch_to.window(driver.window_handles[0])
    
    from selenium.webdriver.common.by import By
    for i in range(30):
        tempmail.close_consent_popups(driver)
        items = driver.find_elements(By.CSS_SELECTOR, ".email-item")
        found = None
        for item in items:
            text = item.text.lower() if item.text else ""
            if "z.ai" in text or "verify" in text:
                found = item
                break
        if found: break
        time.sleep(2)

    email_id = found.get_attribute("data-email-id")
    print("Email ID:", email_id)
    
    print("Calling toggleEmailDetail via JS")
    driver.execute_script(f"toggleEmailDetail('{email_id}')")
    time.sleep(3)
    
    print("Executing JS to get iframe contentWindow.document.documentElement.outerHTML")
    js = f"""
    var frame = document.querySelector('iframe#emailFrame-{email_id}');
    if (frame && frame.contentWindow && frame.contentWindow.document) {{
        return frame.contentWindow.document.documentElement.outerHTML;
    }}
    return "NO_FRAME";
    """
    html = driver.execute_script(js)
    print("JS HTML len:", len(html) if html else 0)
    print("JS HTML snippet:", html[:300] if html else "None")
    
    # Try fetching the iframe src url
    print("Frame src:", driver.execute_script(f"return document.querySelector('iframe#emailFrame-{email_id}')?.src;"))
    
except Exception as e:
    print(f"Error: {e}")
finally:
    driver.quit()
