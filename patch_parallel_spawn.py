with open("automation/main.py", "r") as f:
    content = f.read()

old_spawn = """                        for _ in range(args.parallel - 1):
                            driver.execute_script(
                                "window.open('https://chat.z.ai/', '_blank');"
                            )
                            time.sleep(1)
                            windows.append(driver.window_handles[-1])"""

new_spawn = """                        for _ in range(args.parallel - 1):
                            try:
                                driver.execute_script(
                                    "window.open('https://chat.z.ai/', '_blank');"
                                )
                                time.sleep(2)
                                windows.append(driver.window_handles[-1])
                            except Exception as e:
                                log.warning("Failed to open parallel tab: %s", e)"""

content = content.replace(old_spawn, new_spawn)

with open("automation/main.py", "w") as f:
    f.write(content)
