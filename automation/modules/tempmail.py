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
        overlays = driver.find_elements(
            By.CSS_SELECTOR, ".fc-dialog-overlay, [class*='cookie'], [class*='consent']"
        )
        for overlay in overlays:
            if overlay.is_displayed():
                driver.execute_script("arguments[0].remove();", overlay)
        buttons = driver.find_elements(
            By.CSS_SELECTOR,
            "button[aria-label*='accept'], button[class*='accept'], button[id*='cookie']",
        )
        for btn in buttons:
            if btn.is_displayed():
                btn.click()
                time.sleep(0.5)
    except:
        pass


def get_temp_mail(driver) -> str:
    wait = WebDriverWait(driver, 30)
    print("[tempmail] Loading cleantempmail.com...")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            driver.get("https://cleantempmail.com")
            if "ERR_SOCKS_CONNECTION_FAILED" in driver.page_source or "ERR_CONNECTION_CLOSED" in driver.page_source or "ERR_PROXY_CONNECTION_FAILED" in driver.page_source:
                raise Exception("Proxy/Network error page displayed")
            break
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            print(
                f"[!] Failed to load cleantempmail.com, retrying ({attempt + 1}/{max_retries})..."
            )
            time.sleep(2)

    time.sleep(5)
    close_consent_popups(driver)

    selectors = [
        "#emailDisplay",
        ".email-display",
        "#email",
        "[id*='email']",
        ".email-address",
    ]

    end_time = time.time() + 30
    while time.time() < end_time:
        for selector in selectors:
            try:
                els = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in els:
                    email = driver.execute_script("return arguments[0].textContent", el)
                    if email:
                        email = email.strip()
                    else:
                        email = el.get_attribute("value") or ""
                        email = email.strip()
                    if email and "@" in email and len(email) < 100:
                        return email
            except:
                pass
        time.sleep(2)
        close_consent_popups(driver)

    with open("/tmp/tempmail_error_source.html", "w") as f:
        f.write(driver.page_source)
    print("[tempmail] Page source saved to /tmp/tempmail_error_source.html")

    raise RuntimeError("Could not find email address on cleantempmail.com")


def build_verify_url(token: str, email: str, username: str) -> str:
    return f"https://chat.z.ai/auth/verify_email?token={token}&email={email}&username={username}&language=en"
