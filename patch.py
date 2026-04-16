with open("automation/modules/auth_zai.py", "r") as f:
    code = f.read()

import re

# Replace fixed 2s sleep and single find_element with a wait loop
replacement = """    # Find verify link in iframe
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe")))
    iframe = driver.find_element(By.CSS_SELECTOR, "iframe")
    driver.switch_to.frame(iframe)
    
    # Wait for the email body to load, which might take longer on slow proxies
    try:
        link = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a")))
        href = link.get_attribute("href")
        print(f"[*] Found link in iframe: {href}")
        # if the href doesn't contain verify_email, log the source for debugging
        if 'verify' not in href.lower() and 'auth' not in href.lower():
            print(f"[*] WARNING: Link might not be verification: {href}")
            print(f"[*] Iframe source: {driver.page_source[:500]}")
    except Exception as e:
        print(f"[*] Failed to find link in iframe. Source:\\n{driver.page_source}")
        raise e
"""

code = re.sub(
    r"    # Find verify link in iframe.*?link\.get_attribute\(\"href\"\)",
    replacement,
    code,
    flags=re.DOTALL
)

# Also fix the second interaction where it opens the link
replacement2 = """    # Open verify link
    driver.switch_to.window(driver.window_handles[0])
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe")))
    iframe = driver.find_element(By.CSS_SELECTOR, "iframe")
    driver.switch_to.frame(iframe)
    link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a")))
    link.click()"""

code = re.sub(
    r"    # Open verify link.*?link\.click\(\)",
    replacement2,
    code,
    flags=re.DOTALL
)

with open("automation/modules/auth_zai.py", "w") as f:
    f.write(code)
