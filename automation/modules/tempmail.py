from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import string

BASE_WORDS = ["golden", "swift", "ocean", "alpha", "zebra", "ember", "nova", "xray"]

def generate_username() -> str:
    left = random.choice(BASE_WORDS)
    right = random.choice(BASE_WORDS)
    suffix = random.randint(10, 99)
    return f"{left}{right}{suffix}"

def close_consent_popups(driver):
    try:
        overlays = driver.find_elements(By.CSS_SELECTOR, ".fc-dialog-overlay, [class*='cookie'], [class*='consent']")
        for overlay in overlays:
            if overlay.is_displayed():
                driver.execute_script("arguments[0].remove();", overlay)
        buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='accept'], button[class*='accept'], button[id*='cookie']")
        for btn in buttons:
            if btn.is_displayed():
                btn.click()
                time.sleep(0.5)
    except: pass

def get_temp_mail(driver) -> str:
    wait = WebDriverWait(driver, 15)
    driver.get("https://cleantempmail.com")
    time.sleep(3)
    close_consent_popups(driver)
    
    selectors = ["#emailDisplay", ".email-display", "#email", "[id*='email']", ".email-address"]
    email = None
    for selector in selectors:
        try:
            el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            if el.is_displayed():
                email = el.text or el.get_attribute("value") or ""
                email = email.strip()
                if email and "@" in email:
                    return email
        except: continue
    raise RuntimeError("Could not find email address on cleantempmail.com")

def build_verify_url(token: str, email: str, username: str) -> str:
    return f"https://chat.z.ai/auth/verify_email?token={token}&email={email}&username={username}&language=en"
