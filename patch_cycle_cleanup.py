with open("automation/main.py", "r") as f:
    content = f.read()

# Let's find the end of the cycle loop to add aggressive tab cleanup and memory freeing
old_end_cycle = """                        try:
                            if driver.window_handles:
                                driver.switch_to.window(original_window)
                        except Exception:
                            pass"""

new_end_cycle = """                        try:
                            if driver.window_handles:
                                # Aggressively close any tab that isn't the original to free RAM
                                for handle in driver.window_handles:
                                    if handle != original_window:
                                        try:
                                            driver.switch_to.window(handle)
                                            driver.close()
                                        except:
                                            pass
                                
                                driver.switch_to.window(original_window)
                                # Navigate to a blank page to force Chrome to flush DOM memory from the previous cycle
                                driver.get("about:blank")
                                time.sleep(2)
                        except Exception:
                            pass"""

content = content.replace(old_end_cycle, new_end_cycle)
with open("automation/main.py", "w") as f:
    f.write(content)
