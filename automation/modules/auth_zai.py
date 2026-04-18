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
        target_btn = None
        # We must wait until a button actually containing 'resend' OR having the 'buttonGradient' class appears.
        for _ in range(30):
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for b in buttons:
                text = b.text.lower() if b.text else ""
                class_attr = b.get_attribute("class") or ""
                if "resend" in text or "buttongradient" in class_attr.lower():
                    target_btn = b
                    break

            if target_btn and target_btn.is_displayed() and target_btn.is_enabled():
                break
            target_btn = None
            time.sleep(1)

        if not target_btn:
            raise Exception("Resend button never appeared in DOM or became visible")

        close_consent_popups(driver)
        time.sleep(1)  # Give a small buffer after popups close
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", target_btn
        )
        time.sleep(0.5)

        try:
            target_btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", target_btn)

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
    target_email_element = None

    # Wait for inbox item containing "Z.ai" or "Verify"
    for i in range(30):
        close_consent_popups(driver)
        try:
            inbox_items = driver.find_elements(By.CSS_SELECTOR, ".email-item")
            for item in inbox_items:
                text = item.text.lower() if item.text else ""
                if "z.ai" in text or "verify" in text:
                    target_email_element = item
                    break

            if target_email_element:
                break
        except:
            pass

        # Refresh the page every 6 seconds to force inbox update
        if i > 0 and i % 3 == 0:
            print(
                f"[*] Z.ai Verification email not found yet, refreshing CleanTempMail ({i * 2}s)..."
            )
            try:
                driver.refresh()
                if (
                    "ERR_SOCKS_CONNECTION_FAILED" in driver.page_source
                    or "ERR_PROXY_CONNECTION_FAILED" in driver.page_source
                    or "ERR_CONNECTION_CLOSED" in driver.page_source
                ):
                    print(
                        "[!] Network dropped. Attempting to reload cleantempmail.com..."
                    )
                    time.sleep(2)
                    driver.get("https://cleantempmail.com")
            except Exception as e:
                print(f"[!] Error refreshing page: {e}")

            time.sleep(1)  # wait a moment after refresh

        time.sleep(2)

    if not target_email_element:
        raise RuntimeError("Z.ai Verification email did not arrive in 60s")

    # Click email
    print("[*] Opening verification email...")

    try:
        email_id = target_email_element.get_attribute("data-email-id")
        if email_id:
            driver.execute_script(f"toggleEmailDetail('{email_id}')")
        else:
            raise Exception("No data-email-id attribute found")
    except Exception as e:
        print(f"[!] Failed to open email via JS: {e}")
        try:
            # Fallback to clicking wrapper
            wrapper = target_email_element.find_element(
                By.CSS_SELECTOR, ".email-content-wrapper"
            )
            driver.execute_script("arguments[0].click();", wrapper)
        except:
            try:
                target_email_element.click()
            except:
                driver.execute_script("arguments[0].click();", target_email_element)

    # Wait 2 seconds and check if the email actually expanded (it should have class 'expanded')
    time.sleep(2)
    classes = target_email_element.get_attribute("class") or ""
    if "expanded" not in classes.lower():
        print("[!] Email did not seem to expand properly, forcing a click again...")
        try:
            driver.execute_script("arguments[0].click();", target_email_element)
        except:
            pass

    time.sleep(4)

    # Find verify link
    print("[*] Waiting for email content to load...")
    href = None
    for attempt in range(15):
        time.sleep(2)

        # First check main content
        links = driver.find_elements(By.CSS_SELECTOR, "a")
        for a in links:
            h = a.get_attribute("href")
            if h and (
                "verify" in h.lower() or "auth" in h.lower() or "chat.z.ai" in h.lower()
            ):
                href = h
                break

        if href:
            print(f"[*] Found verification link in main content: {href}")
            break

        print("[*] Link not in main content, checking iframes...")
        # Re-fetch the page source inside the loop in case the network took a moment
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        iframes = driver.find_elements(By.CSS_SELECTOR, "iframe")
        print(f"[*] Found {len(iframes)} iframes")

        for i, iframe in enumerate(iframes):
            try:
                driver.switch_to.frame(iframe)
                links = driver.find_elements(By.CSS_SELECTOR, "a")
                for a in links:
                    h = a.get_attribute("href")
                    if h:
                        print(f"[*] iframe {i} link: {h}")
                    if h and (
                        "verify" in h.lower()
                        or "auth" in h.lower()
                        or "chat.z.ai" in h.lower()
                    ):
                        href = h
                        break
                if href:
                    print(f"[*] Found verification link in iframe {i}: {href}")
                    break
            except Exception as e:
                print(f"[*] Error inspecting iframe {i}: {e}")
            finally:
                driver.switch_to.default_content()

        if href:
            break

    if not href:
        driver.save_screenshot(
            "/home/alan/zai-automation/artifacts/screenshots/iframe_fail.png"
        )
        print(
            "[!] Saved screenshot of failure to /home/alan/zai-automation/artifacts/screenshots/iframe_fail.png"
        )

        # Dump the outer HTML so we can see what cleantempmail's DOM actually looked like when it failed
        try:
            with open(
                "/home/alan/zai-automation/artifacts/screenshots/iframe_fail_dom.html",
                "w",
            ) as f:
                f.write(driver.page_source)
            print("[!] Dumped DOM to iframe_fail_dom.html")
        except:
            pass

        raise RuntimeError("Could not find verification link anywhere")

    driver.switch_to.default_content()

    # Close existing z.ai tab
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if "chat.z.ai" in driver.current_url:
            driver.close()
            break

    # Open verify link
    driver.switch_to.window(driver.window_handles[0])
    print(f"[*] Navigating to {href}")
    driver.execute_script(f"window.open('{href}', '_blank');")
    time.sleep(5)

    # Find new z.ai tab
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if "chat.z.ai" in driver.current_url:
            break

    # Fill password
    close_consent_popups(driver)
    try:
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#password"))
        ).send_keys(password)
    except Exception as e:
        print(
            f"[!] Error finding password field. Perhaps it was already verified or the page didn't load properly: {e}"
        )
        try:
            print("[*] URL:", driver.current_url)
            driver.save_screenshot(
                "/home/alan/zai-automation/artifacts/screenshots/password_fail.png"
            )
        except:
            pass
        raise RuntimeError("Failed to verify email, password field not found.")
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

    # Harvest cookies and localStorage right after registration (while still logged in)
    cookies = driver.get_cookies()
    print(f"[*] Harvested {len(cookies)} cookies after registration")

    local_storage = {}
    try:
        local_storage = driver.execute_script(
            "var ls = {}; for (var i = 0; i < localStorage.length; i++) { var k = localStorage.key(i); ls[k] = localStorage.getItem(k); return ls;"
        )
        print(f"[*] Harvested {len(local_storage)} localStorage keys")
    except Exception as e:
        print(f"[!] localStorage harvest failed: {e}")

    session_storage = {}
    try:
        session_storage = driver.execute_script(
            "var ss = {}; for (var i = 0; i < sessionStorage.length; i++) { var k = sessionStorage.key(i); ss[k] = sessionStorage.getItem(k); return ss;"
        )
        print(f"[*] Harvested {len(session_storage)} sessionStorage keys")
    except Exception as e:
        print(f"[!] sessionStorage harvest failed: {e}")

    session_storage = {}
    try:
        session_storage = driver.execute_script(
            "var ss = {}; for (var i = 0; i < sessionStorage.length; i++) { var k = sessionStorage.key(i); ss[k] = sessionStorage.getItem(k); } return ss;"
        )
    except:
        pass

    return {
        "registration": "ok",
        "password": password,
        "cookies": cookies,
        "local_storage": local_storage,
        "session_storage": session_storage,
    }
