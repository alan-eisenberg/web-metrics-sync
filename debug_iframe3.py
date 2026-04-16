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

    found.click()
    time.sleep(5)
    
    iframes = driver.find_elements(By.CSS_SELECTOR, "iframe")
    for frame in iframes:
        if "emailFrame" in frame.get_attribute("id"):
            srcdoc = frame.get_attribute("srcdoc")
            print("SRCDOC:", srcdoc[:500] if srcdoc else None)
            
            # evaluate script to get contentWindow.document.body.innerHTML
            html = driver.execute_script("return arguments[0].contentWindow.document.body.innerHTML;", frame)
            print("JS HTML:", html[:500] if html else None)
            
            # Maybe the link is in the email body container?
            body = driver.execute_script("return arguments[0].contentWindow.document.body.innerText;", frame)
            print("JS TEXT:", body[:500] if body else None)
    
except Exception as e:
    print(f"Error: {e}")
finally:
    driver.quit()
