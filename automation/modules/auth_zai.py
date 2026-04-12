from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from automation.modules.tempmail import close_consent_popups
import time


def open_verify_resend(driver, verify_url: str):
    driver.execute_script(f"window.open('{verify_url}', '_blank');")
    time.sleep(2)
    driver.switch_to.window(driver.window_handles[-1])

    wait = WebDriverWait(driver, 30)
    print("[*] Waiting for the resend button to appear...")

    try:
        # Based on the exact class list provided by the user
        resend_btn = wait.until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "button.buttonGradient, button[class*='buttonGradient']",
                )
            )
        )
        close_consent_popups(driver)
        time.sleep(1)  # Give a small buffer after popups close
        resend_btn.click()
        print("[*] Successfully clicked the resend button.")
        time.sleep(2)
    except Exception as e:
        print(f"[!] Failed to click the resend button. Error: {e}")
        driver.save_screenshot(
            "/home/alan/zai-automation/artifacts/screenshots/resend_fail.png"
        )
        raise RuntimeError(
            "Could not find or click the resend button within 30 seconds."
        )

    driver.switch_to.window(driver.window_handles[0])


def poll_inbox_and_verify(driver, password: str):
    wait = WebDriverWait(driver, 15)
    email_found = False

    # Wait for inbox item
    for _ in range(30):
        close_consent_popups(driver)
        try:
            inbox = driver.find_elements(By.CSS_SELECTOR, ".email-item")
            if inbox:
                email_found = True
                break
        except:
            pass
        time.sleep(2)

    if not email_found:
        raise RuntimeError("Verification email did not arrive in 60s")

    # Click email
    first_email = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".email-item"))
    )
    first_email.click()
    time.sleep(2)

    # Find verify link in iframe
    iframe = driver.find_element(By.CSS_SELECTOR, "iframe")
    driver.switch_to.frame(iframe)
    time.sleep(2)

    link = driver.find_element(By.CSS_SELECTOR, "a[href*='verify_email']")
    href = link.get_attribute("href")
    driver.switch_to.default_content()

    # Close existing z.ai tab
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if "chat.z.ai" in driver.current_url:
            driver.close()
            break

    # Open verify link
    driver.switch_to.window(driver.window_handles[0])
    iframe = driver.find_element(By.CSS_SELECTOR, "iframe")
    driver.switch_to.frame(iframe)
    link = driver.find_element(By.CSS_SELECTOR, "a[href*='verify_email']")
    link.click()
    driver.switch_to.default_content()
    time.sleep(5)

    # Find new z.ai tab
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if "chat.z.ai" in driver.current_url:
            break

    # Fill password
    close_consent_popups(driver)
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#password"))
    ).send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "#confirmPassword").send_keys(password)

    # Submit
    try:
        btn = driver.find_element(
            By.XPATH,
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'complete registration')]",
        )
        btn.click()
    except:
        driver.find_element(By.CSS_SELECTOR, "button.buttonGradient").click()

    time.sleep(5)
    return {"registration": "ok", "password": password}
