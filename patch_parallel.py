import re

with open("automation/main.py", "r") as f:
    content = f.read()

# 1. Add retry logic inside CHAT_PARALLEL_GENERATE
# We'll replace the polling loop with a new one that tracks elapsed time per tab
old_polling = """                        log.info(
                            "[%s] Polling %d tabs for completion (Cycle %d)...",
                            state_name,
                            args.parallel,
                            cycle + 1,
                        )
                        finished_tabs = set()
                        for _ in range(100):
                            any_still_generating = False
                            try:
                                current_handles = driver.window_handles
                            except Exception:
                                break

                            for i, window in enumerate(windows):
                                if i in finished_tabs:
                                    continue
                                if window not in current_handles:
                                    finished_tabs.add(i)
                                    continue

                                try:
                                    driver.switch_to.window(window)
                                    status, result = chat.check_generation_status(
                                        driver
                                    )
                                except Exception as e:
                                    log.warning(
                                        "[%s] Error checking tab %d: %s",
                                        state_name,
                                        i + 1,
                                        e,
                                    )
                                    any_still_generating = True
                                    continue

                                if status == "GENERATING":
                                    any_still_generating = True
                                elif status == "FINISHED" and result:
                                    log.info(
                                        "[%s] Tab %d finished generating!",
                                        state_name,
                                        i + 1,
                                    )
                                    finished_tabs.add(i)
                                    extracted = extractor.extract_response(
                                        result.response_html, result.response_text
                                    )
                                    eval_result = evaluator_groq.evaluate_response(
                                        extracted.html, extracted.text
                                    )
                                    if eval_result.approved:
                                        preview_url = chat.to_preview_url(
                                            result.chat_url
                                        )
                                        if preview_url not in state.preview_urls:
                                            state.preview_urls.append(preview_url)
                                            log.info(
                                                "[%s] Approved in tab %d! URL: %s",
                                                state_name,
                                                i + 1,
                                                preview_url,
                                            )
                                            if state.email:
                                                storage.upsert_credential(
                                                    settings.credentials_path,
                                                    {
                                                        "email": state.email,
                                                        "username": state.username,
                                                        "preview_urls": state.preview_urls,
                                                        "status": "completed",
                                                        "run_id": state.run_id,
                                                    },
                                                )
                                    try:
                                        if (
                                            len(driver.window_handles) > 1
                                            and driver.current_window_handle
                                            != original_window
                                        ):
                                            driver.close()
                                    except Exception:
                                        pass
                                elif status in ("ERROR", "SANDBOX_LIMIT"):
                                    log.warning(
                                        "[%s] Tab %d hit %s. Closing it.",
                                        state_name,
                                        i + 1,
                                        status,
                                    )
                                    finished_tabs.add(i)
                                    try:
                                        if (
                                            len(driver.window_handles) > 1
                                            and driver.current_window_handle
                                            != original_window
                                        ):
                                            driver.close()
                                    except Exception:
                                        pass

                            if not any_still_generating:
                                break
                            time.sleep(5)

                        if driver.window_handles:
                            driver.switch_to.window(original_window)"""

new_polling = """                        log.info(
                            "[%s] Polling %d tabs for completion (Cycle %d)...",
                            state_name,
                            args.parallel,
                            cycle + 1,
                        )
                        
                        import automation.modules.altissia as altissia
                        
                        finished_tabs = set()
                        tab_attempts = {i: 1 for i in range(len(windows))}
                        tab_elapsed_iters = {i: 0 for i in range(len(windows))}
                        
                        while len(finished_tabs) < len(windows):
                            any_still_generating = False
                            try:
                                current_handles = driver.window_handles
                            except Exception:
                                break

                            for i, window in enumerate(windows):
                                if i in finished_tabs:
                                    continue
                                if window not in current_handles:
                                    finished_tabs.add(i)
                                    continue
                                
                                tab_elapsed_iters[i] += 1
                                # 8 minutes = 480 seconds = 96 iterations of 5s
                                if tab_elapsed_iters[i] > 96:
                                    if tab_attempts[i] < 3:
                                        log.warning("[%s] Tab %d timed out after 8 minutes. Retrying prompt...", state_name, i + 1)
                                        tab_attempts[i] += 1
                                        tab_elapsed_iters[i] = 0
                                        try:
                                            driver.switch_to.window(window)
                                            driver.get("https://chat.z.ai/")
                                            time.sleep(2)
                                            chat.ensure_agent_mode(driver, settings.js_dir)
                                            chat.start_prompt(driver, current_prompt)
                                        except Exception as e:
                                            log.warning("[%s] Error restarting prompt in tab %d: %s", state_name, i + 1, e)
                                        any_still_generating = True
                                        continue
                                    else:
                                        log.warning("[%s] Tab %d timed out after multiple attempts. Giving up.", state_name, i + 1)
                                        finished_tabs.add(i)
                                        try:
                                            if len(driver.window_handles) > 1 and driver.current_window_handle != original_window:
                                                driver.close()
                                        except Exception:
                                            pass
                                        continue

                                try:
                                    driver.switch_to.window(window)
                                    status, result = chat.check_generation_status(driver)
                                except Exception as e:
                                    log.warning("[%s] Error checking tab %d: %s", state_name, i + 1, e)
                                    any_still_generating = True
                                    continue

                                if status == "GENERATING":
                                    any_still_generating = True
                                elif status == "FINISHED" and result:
                                    log.info("[%s] Tab %d finished generating!", state_name, i + 1)
                                    finished_tabs.add(i)
                                    extracted = extractor.extract_response(result.response_html, result.response_text)
                                    eval_result = evaluator_groq.evaluate_response(extracted.html, extracted.text)
                                    if eval_result.approved:
                                        preview_url = chat.to_preview_url(result.chat_url)
                                        if preview_url not in state.preview_urls:
                                            state.preview_urls.append(preview_url)
                                            log.info("[%s] Approved in tab %d! URL: %s", state_name, i + 1, preview_url)
                                            if state.email:
                                                storage.upsert_credential(
                                                    settings.credentials_path,
                                                    {
                                                        "email": state.email,
                                                        "username": state.username,
                                                        "preview_urls": state.preview_urls,
                                                        "status": "completed",
                                                        "run_id": state.run_id,
                                                    },
                                                )
                                            try:
                                                altissia.append_and_push_links([preview_url])
                                                log.info("[%s] Saved preview link to altissiabooster repo.", state_name)
                                            except Exception as e:
                                                log.error("Failed to push to altissiabooster: %s", e)
                                                
                                    try:
                                        if len(driver.window_handles) > 1 and driver.current_window_handle != original_window:
                                            driver.close()
                                    except Exception:
                                        pass
                                elif status in ("ERROR", "SANDBOX_LIMIT"):
                                    log.warning("[%s] Tab %d hit %s. Closing it.", state_name, i + 1, status)
                                    finished_tabs.add(i)
                                    try:
                                        if len(driver.window_handles) > 1 and driver.current_window_handle != original_window:
                                            driver.close()
                                    except Exception:
                                        pass

                            if not any_still_generating and len(finished_tabs) == len(windows):
                                break
                            time.sleep(5)

                        try:
                            if driver.window_handles:
                                driver.switch_to.window(original_window)
                        except Exception:
                            pass"""

content = content.replace(old_polling, new_polling)

# Update the finalize close just in case
content = content.replace(
"""        if driver is not None and not args.keep_open and not args.open:
            try:
                driver.quit()
            except Exception as e:
                log.warning("Failed to quit browser gracefully: %s", e)""",
"""        if driver is not None and not args.keep_open and not args.open:
            try:
                driver.quit()
            except Exception as e:
                log.warning("Failed to quit browser gracefully: %s", e)""")

with open("automation/main.py", "w") as f:
    f.write(content)

print("Patch applied.")
