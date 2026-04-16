with open("automation/main.py", "r") as f:
    code = f.read()

import re

# Update tab_states initialization
code = code.replace(
    'tab_states[handle] = {"status": "GENERATING", "url": None, "id": i + 1}',
    'tab_states[handle] = {"status": "GENERATING", "url": None, "id": i + 1, "loops": 0}'
)

# Update the loop to increment loops and check for sandbox limit
new_loop = """                    driver.switch_to.window(handle)
                    # Give the tab focus for a bit to prevent Chrome from throttling its JS/WebSocket!
                    import time
                    time.sleep(3)
                    
                    st["loops"] += 1
                    
                    status, result = chat.check_generation_status(driver)

                    if status == "FINISHED":"""

code = code.replace(
    """                    driver.switch_to.window(handle)
                    # Give the tab focus for a bit to prevent Chrome from throttling its JS/WebSocket!
                    import time
                    time.sleep(3)
                    
                    status, result = chat.check_generation_status(driver)

                    if status == "FINISHED":""",
    new_loop
)

new_sandbox_check = """                    elif status == "ERROR":
                        log.info(
                            "[%s] Tab %d encountered an error/regenerate state. Healing triggered.",
                            state_name,
                            st["id"],
                        )
                        # The check_generation_status function already clicked regenerate if it returned ERROR
                        st["status"] = "GENERATING"  # Put back in generating state

                    # Sandbox limit or stuck prompt handler
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
                            pass
"""

code = code.replace(
    """                    elif status == "ERROR":
                        log.info(
                            "[%s] Tab %d encountered an error/regenerate state. Healing triggered.",
                            state_name,
                            st["id"],
                        )
                        # The check_generation_status function already clicked regenerate if it returned ERROR
                        st["status"] = "GENERATING"  # Put back in generating state""",
    new_sandbox_check
)

with open("automation/main.py", "w") as f:
    f.write(code)
