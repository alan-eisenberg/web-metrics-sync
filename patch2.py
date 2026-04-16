with open("automation/modules/auth_zai.py", "r") as f:
    code = f.read()

import re

# Replace the single iframe wait with a search over all iframes
replacement = """    # Find verify link in iframe
    print("[*] Waiting for iframes...")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe")))
    time.sleep(3) # Give time for iframe content to load
    iframes = driver.find_elements(By.CSS_SELECTOR, "iframe")
    print(f"[*] Found {len(iframes)} iframes")
    
    href = None
    for i, iframe in enumerate(iframes):
        try:
            driver.switch_to.frame(iframe)
            links = driver.find_elements(By.CSS_SELECTOR, "a")
            for a in links:
                h = a.get_attribute("href")
                if h and ('verify' in h.lower() or 'auth' in h.lower()):
                    href = h
                    break
            if href:
                print(f"[*] Found verification link in iframe {i}: {href}")
                break
        except Exception as e:
            print(f"[*] Error inspecting iframe {i}: {e}")
        finally:
            driver.switch_to.default_content()

    if not href:
        raise RuntimeError("Could not find verification link in any iframe")
"""

code = re.sub(
    r"    # Find verify link in iframe.*?except Exception as e:\n        print\(f\"\[\*\] Failed to find link in iframe. Source:\\n\{driver.page_source\}\"\)\n        raise e\n",
    replacement,
    code,
    flags=re.DOTALL
)

# For the "Open verify link" part, we just need to driver.get(href) instead of finding the iframe again and clicking! 
# That's much safer and faster!
replacement2 = """    # Open verify link
    print(f"[*] Navigating to {href}")
    driver.execute_script(f"window.open('{href}', '_blank');")
    time.sleep(5)"""

code = re.sub(
    r"    # Open verify link.*?driver\.switch_to\.default_content\(\)\n    time\.sleep\(5\)",
    replacement2,
    code,
    flags=re.DOTALL
)

with open("automation/modules/auth_zai.py", "w") as f:
    f.write(code)
