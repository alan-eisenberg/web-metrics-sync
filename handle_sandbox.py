with open("automation/main.py", "r") as f:
    code = f.read()

import re

new_code = """                    elif status == "SANDBOX_LIMIT" or (status == "GENERATING" and st["loops"] > 10):
                        try:
                            containers = driver.find_elements(By.CSS_SELECTOR, "#response-content-container, .response-content")
                            if not containers:
                                log.warning("[%s] Tab %d failed to start generating! Assuming Sandbox Limit. Releasing sandboxes...", state_name, st["id"])
                                chat.release_sandboxes(driver)
                                log.info("[%s] Tab %d retrying prompt generation...", state_name, st["id"])
                                chat.ensure_agent_mode(driver, settings.js_dir)
                                chat.start_prompt(driver, full_prompt)
                                st["loops"] = 0 # reset loop counter
                        except Exception as e:
                            log.error("Failed to release sandboxes: %s", e)"""

code = code.replace("""                    # Sandbox limit or stuck prompt handler
                    if st["status"] == "GENERATING" and st["loops"] > 10:
                        try:
                            containers = driver.find_elements(By.CSS_SELECTOR, "#response-content-container, .response-content")
                            if not containers:
                                log.warning("[%s] Tab %d has no response after 30s! Assuming Sandbox Limit. Releasing sandboxes...", state_name, st["id"])
                                chat.release_sandboxes(driver)
                                log.info("[%s] Tab %d retrying prompt generation...", state_name, st["id"])
                                chat.ensure_agent_mode(driver, settings.js_dir)
                                chat.start_prompt(driver, full_prompt)
                                st["loops"] = 0 # reset loop counter
                        except Exception as e:
                            pass""", new_code)

with open("automation/main.py", "w") as f:
    f.write(code)
