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

    item_html = found.get_attribute("outerHTML")
    print("Item HTML:", item_html[:200])
    
    # Try fetching the email body via JS directly from the iframe we already found
    iframes = driver.find_elements(By.CSS_SELECTOR, "iframe")
    for frame in iframes:
        id_ = frame.get_attribute("id")
        if "emailFrame" in id_:
            print(f"Found email frame: {id_}")
            break
            
    print("Executing JS to get iframe contentWindow.document.documentElement.outerHTML")
    js = """
    var frame = document.querySelector('iframe[id^="emailFrame"]');
    if (frame && frame.contentWindow && frame.contentWindow.document) {
        return frame.contentWindow.document.documentElement.outerHTML;
    }
    return "NO_FRAME";
    """
    html = driver.execute_script(js)
    print("JS HTML len:", len(html) if html else 0)
    print("JS HTML snippet:", html[:300] if html else "None")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    driver.quit()
