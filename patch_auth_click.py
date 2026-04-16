with open("automation/modules/auth_zai.py", "r") as f:
    content = f.read()

# Instead of just relying on toggleEmailDetail, let's aggressively click everything that expands the email, including any 'unread' rows that might have changed structure
old_click = """    try:
        email_id = target_email_element.get_attribute("data-email-id")
        if email_id:
            driver.execute_script(f"toggleEmailDetail('{email_id}')")
        else:
            # Fallback to clicking wrapper
            wrapper = target_email_element.find_element(
                By.CSS_SELECTOR, ".email-content-wrapper"
            )
            driver.execute_script("arguments[0].click();", wrapper)
    except Exception as e:
        print(f"[!] Failed to open email via JS or wrapper: {e}")
        try:
            target_email_element.click()
        except:
            driver.execute_script("arguments[0].click();", target_email_element)"""

new_click = """    try:
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
            pass"""

content = content.replace(old_click, new_click)
with open("automation/modules/auth_zai.py", "w") as f:
    f.write(content)
