with open("automation/main.py", "r") as f:
    content = f.read()

old_get = """                if driver is None:
                    driver = get_browser(proxy_url=state.metadata.get("proxy"))
                driver.get("https://cleantempmail.com")
                # Wait for email to arrive and click verify"""

new_get = """                if driver is None:
                    driver = get_browser(proxy_url=state.metadata.get("proxy"))
                
                # Retry loading cleantempmail in case of VPN/SOCKS drops
                import time
                for load_attempt in range(3):
                    try:
                        driver.get("https://cleantempmail.com")
                        if "ERR_SOCKS_CONNECTION_FAILED" in driver.page_source or "ERR_CONNECTION_CLOSED" in driver.page_source:
                            raise Exception("Browser rendered a network error page instead of cleantempmail")
                        break
                    except Exception as e:
                        if load_attempt == 2:
                            log.error("[SAVE_CREDENTIALS] Failed to load cleantempmail.com after 3 attempts: %s", e)
                            raise RuntimeError(f"VPN or Proxy dropped connection to cleantempmail: {e}")
                        log.warning("[SAVE_CREDENTIALS] Error loading cleantempmail.com, retrying... (%s)", e)
                        time.sleep(3)
                        
                # Wait for email to arrive and click verify"""

content = content.replace(old_get, new_get)

with open("automation/main.py", "w") as f:
    f.write(content)
