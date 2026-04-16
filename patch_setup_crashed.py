with open("automation/main.py", "r") as f:
    content = f.read()

old_setup = """                        for i, window in enumerate(windows):
                            driver.switch_to.window(window)
                            chat.ensure_agent_mode(driver, settings.js_dir)
                            log.info(
                                "[%s] Attempting generation in tab %d (Cycle %d)...",
                                state_name,
                                i + 1,
                                cycle + 1,
                            )
                            if not chat.start_prompt(driver, current_prompt):
                                log.warning(
                                    "[%s] Failed to start prompt in tab %d.",
                                    state_name,
                                    i + 1,
                                )"""

new_setup = """                        finished_tabs = set()
                        for i, window in enumerate(windows):
                            try:
                                driver.switch_to.window(window)
                                chat.ensure_agent_mode(driver, settings.js_dir)
                                log.info(
                                    "[%s] Attempting generation in tab %d (Cycle %d)...",
                                    state_name,
                                    i + 1,
                                    cycle + 1,
                                )
                                if not chat.start_prompt(driver, current_prompt):
                                    log.warning(
                                        "[%s] Failed to start prompt in tab %d.",
                                        state_name,
                                        i + 1,
                                    )
                                    finished_tabs.add(i)
                            except Exception as e:
                                log.warning("[%s] Setup failed for tab %d: %s", state_name, i + 1, e)
                                finished_tabs.add(i)"""

content = content.replace(old_setup, new_setup)
# We need to make sure we don't redeclare finished_tabs if it's already there right after
old_finished = """                        
                        import automation.modules.altissia as altissia
                        
                        finished_tabs = set()"""

new_finished = """                        
                        import automation.modules.altissia as altissia
                        
                        # finished_tabs may already have crashed setup tabs"""

content = content.replace(old_finished, new_finished)

with open("automation/main.py", "w") as f:
    f.write(content)
