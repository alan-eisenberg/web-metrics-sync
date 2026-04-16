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

    # Print if it's already expanded
    print("Classes:", found.get_attribute("class"))
    if "expanded" not in found.get_attribute("class"):
        found.click()
        print("Clicked to expand")
    else:
        print("Already expanded")
        
    time.sleep(5)
    
    # Try fetching the email body via API directly using python requests or JS fetch
    email_id = found.get_attribute("id").replace("email-", "")
    print("Email ID:", email_id)
    
    js = f"""
    return fetch('/api/v1/emails/{email_id}/body')
        .then(r => r.json())
        .then(d => d.body || d.html || JSON.stringify(d))
        .catch(e => e.toString());
    """
    body = driver.execute_async_script(js.replace("return fetch", "var callback = arguments[arguments.length - 1]; fetch").replace(".catch(e => e.toString());", ".catch(e => e.toString()).then(callback);"))
    
    print("API Body:", body[:500])
    
    if "test-token-1234" in body:
        print("SUCCESS! Token found in API body")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    driver.quit()
