import time
from automation.browser import get_browser
from automation.modules import tempmail, auth_zai

driver = get_browser()
try:
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
    driver.execute_script(f"toggleEmailDetail('{email_id}')")
    time.sleep(3)
    
    print("Checking iframes for links...")
    iframes = driver.find_elements(By.CSS_SELECTOR, "iframe")
    for i, frame in enumerate(iframes):
        if "emailFrame" in frame.get_attribute("id"):
            driver.switch_to.frame(frame)
            links = driver.find_elements(By.CSS_SELECTOR, "a")
            print(f"Found {len(links)} links in email frame")
            for a in links:
                print(f"  Link text: {a.text.strip()} | href: {a.get_attribute('href')}")
            driver.switch_to.default_content()
    
except Exception as e:
    print(f"Error: {e}")
finally:
    driver.quit()
