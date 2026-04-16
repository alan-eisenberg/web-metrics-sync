import time
from automation.browser import get_browser
from automation.modules import tempmail, auth_zai

driver = get_browser()
try:
    print("Getting email...")
    email = tempmail.get_temp_mail(driver)
    print(f"Email: {email}")
    username = tempmail.generate_username()
    verify_url = tempmail.build_verify_url("test-token-1234", email, username)
    
    print("Opening verify/resend...")
    auth_zai.open_verify_resend(driver, verify_url)
    
    # switch back to temp mail
    driver.switch_to.window(driver.window_handles[0])
    print("Polling inbox...")
    
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
        if i > 0 and i % 3 == 0: driver.refresh(); time.sleep(1)
        time.sleep(2)

    found.click()
    print("Clicked email, waiting 10 seconds...")
    time.sleep(10)
    
    iframes = driver.find_elements(By.CSS_SELECTOR, "iframe")
    for i, frame in enumerate(iframes):
        print(f"Iframe {i}: {frame.get_attribute('id')} src={frame.get_attribute('src')}")
        driver.switch_to.frame(frame)
        print("  Text:", driver.find_element(By.TAG_NAME, "body").text[:200])
        driver.switch_to.default_content()
    
    # Check if there is anything in main DOM that we missed
    print("Main DOM links:", [a.get_attribute("href") for a in driver.find_elements(By.CSS_SELECTOR, "a") if a.get_attribute("href") and "chat.z.ai" in a.get_attribute("href")])
    
except Exception as e:
    print(f"Error: {e}")
finally:
    driver.quit()
