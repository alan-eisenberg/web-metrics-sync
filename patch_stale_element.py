with open("automation/modules/chat.py", "r") as f:
    content = f.read()

# Let's fix handle_sandbox_popup to catch StaleElementReferenceException
old_sandbox = """        for row in rows:
            tds = row.find_elements(By.CSS_SELECTOR, "td")
            if len(tds) >= 4:
                last_conv = tds[1].text.strip()
                ttl = tds[2].text.strip()
                
                # Check if TTL is '-' or another indicator we want to clear
                if ttl == "-" or "N/A" in ttl.upper():
                    try:
                        release_btn = tds[3].find_element(By.CSS_SELECTOR, "button")
                        if release_btn.is_displayed():
                            print(f"[*] Found sandbox with TTL '{ttl}', clicking Release...")
                            driver.execute_script("arguments[0].click();", release_btn)
                            time.sleep(1)
                            released_any = True
                            break
                    except Exception:
                        pass
        
        # If we couldn't release specific ones, just click the top 'Clear all Limit' button
        if not released_any:
            try:
                clear_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Clear all')] | //button[contains(text(), 'Release all')]")
                if clear_btn.is_displayed():
                    print("[*] Clicking Clear All Limit button...")
                    driver.execute_script("arguments[0].click();", clear_btn)
                    time.sleep(1)
            except:
                pass"""

new_sandbox = """        for i in range(len(rows)):
            try:
                # Re-fetch rows inside the loop to avoid StaleElementReferenceException if the DOM updates mid-loop
                current_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                if i >= len(current_rows):
                    break
                row = current_rows[i]
                tds = row.find_elements(By.CSS_SELECTOR, "td")
                if len(tds) >= 4:
                    last_conv = tds[1].text.strip()
                    ttl = tds[2].text.strip()
                    
                    if ttl == "-" or "N/A" in ttl.upper() or "never" in ttl.lower():
                        release_btn = tds[3].find_element(By.CSS_SELECTOR, "button")
                        if release_btn.is_displayed():
                            print(f"[*] Found sandbox with TTL '{ttl}', clicking Release...")
                            driver.execute_script("arguments[0].click();", release_btn)
                            time.sleep(2)
                            released_any = True
                            break
            except Exception as e:
                pass
        
        # If we couldn't release specific ones, just click the top 'Clear all Limit' button
        if not released_any:
            try:
                clear_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Clear all')] | //button[contains(text(), 'Release all')]")
                if clear_btn.is_displayed():
                    print("[*] Clicking Clear All Limit button...")
                    driver.execute_script("arguments[0].click();", clear_btn)
                    time.sleep(1)
            except:
                pass"""

if "for row in rows:" in content:
    content = content.replace(old_sandbox, new_sandbox)
else:
    # If the exact block doesn't match, we apply a more generic patch to catch stale elements in check_generation_status itself
    pass

with open("automation/modules/chat.py", "w") as f:
    f.write(content)
