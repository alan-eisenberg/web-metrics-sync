import re

with open("automation/main.py", "r") as f:
    content = f.read()

# find the start of CHAT_PARALLEL_GENERATE logic
pattern = r'(if state_name == "CHAT_PARALLEL_GENERATE":\n)(.*?)(else:\n\s+chat\.ensure_agent_mode\(driver, settings\.js_dir\))'
match = re.search(pattern, content, flags=re.DOTALL)
if match:
    indent = " " * 20
    new_block = (
        indent + 'for cycle in range(args.cycles):\n' +
        indent + '    log.info("[%s] Starting cycle %d/%d with %d parallel tabs...", state_name, cycle + 1, args.cycles, args.parallel)\n' +
        indent + '\n' +
        indent + '    original_window = driver.current_window_handle\n' +
        indent + '    windows = [original_window]\n' +
        indent + '    driver.switch_to.window(original_window)\n' +
        indent + '    if cycle > 0:\n' +
        indent + '        driver.get("https://chat.z.ai/")\n' +
        indent + '        time.sleep(2)\n' +
        indent + '        \n' +
        indent + '    for _ in range(args.parallel - 1):\n' +
        indent + '        driver.execute_script("window.open(\'https://chat.z.ai/\', \'_blank\');")\n' +
        indent + '        time.sleep(1)\n' +
        indent + '        windows.append(driver.window_handles[-1])\n' +
        indent + '\n' +
        indent + '    for i, window in enumerate(windows):\n' +
        indent + '        driver.switch_to.window(window)\n' +
        indent + '        chat.ensure_agent_mode(driver, settings.js_dir)\n' +
        indent + '        log.info("[%s] Attempting generation in tab %d (Cycle %d)...", state_name, i + 1, cycle + 1)\n' +
        indent + '        if not chat.start_prompt(driver, current_prompt):\n' +
        indent + '            log.warning("[%s] Failed to start prompt in tab %d.", state_name, i + 1)\n' +
        indent + '\n' +
        indent + '    log.info("[%s] Polling %d tabs for completion (Cycle %d)...", state_name, args.parallel, cycle + 1)\n' +
        indent + '    finished_tabs = set()\n' +
        indent + '    for _ in range(100):\n' +
        indent + '        any_still_generating = False\n' +
        indent + '        try:\n' +
        indent + '            current_handles = driver.window_handles\n' +
        indent + '        except Exception:\n' +
        indent + '            break\n' +
        indent + '\n' +
        indent + '        for i, window in enumerate(windows):\n' +
        indent + '            if i in finished_tabs:\n' +
        indent + '                continue\n' +
        indent + '            if window not in current_handles:\n' +
        indent + '                finished_tabs.add(i)\n' +
        indent + '                continue\n' +
        indent + '\n' +
        indent + '            try:\n' +
        indent + '                driver.switch_to.window(window)\n' +
        indent + '                status, result = chat.check_generation_status(driver)\n' +
        indent + '            except Exception as e:\n' +
        indent + '                log.warning("[%s] Error checking tab %d: %s", state_name, i + 1, e)\n' +
        indent + '                any_still_generating = True\n' +
        indent + '                continue\n' +
        indent + '\n' +
        indent + '            if status == "GENERATING":\n' +
        indent + '                any_still_generating = True\n' +
        indent + '            elif status == "FINISHED" and result:\n' +
        indent + '                log.info("[%s] Tab %d finished generating!", state_name, i + 1)\n' +
        indent + '                finished_tabs.add(i)\n' +
        indent + '                extracted = extractor.extract_response(result.response_html, result.response_text)\n' +
        indent + '                eval_result = evaluator_groq.evaluate_response(extracted.html, extracted.text)\n' +
        indent + '                if eval_result.approved:\n' +
        indent + '                    preview_url = chat.to_preview_url(result.chat_url)\n' +
        indent + '                    if preview_url not in state.preview_urls:\n' +
        indent + '                        state.preview_urls.append(preview_url)\n' +
        indent + '                        log.info("[%s] Approved in tab %d! URL: %s", state_name, i + 1, preview_url)\n' +
        indent + '                        if state.email:\n' +
        indent + '                            storage.upsert_credential(settings.credentials_path, {\n' +
        indent + '                                "email": state.email,\n' +
        indent + '                                "username": state.username,\n' +
        indent + '                                "preview_urls": state.preview_urls,\n' +
        indent + '                                "status": "completed",\n' +
        indent + '                                "run_id": state.run_id,\n' +
        indent + '                            })\n' +
        indent + '                try:\n' +
        indent + '                    if len(driver.window_handles) > 1 and driver.current_window_handle != original_window:\n' +
        indent + '                        driver.close()\n' +
        indent + '                except Exception:\n' +
        indent + '                    pass\n' +
        indent + '            elif status in ("ERROR", "SANDBOX_LIMIT"):\n' +
        indent + '                log.warning("[%s] Tab %d hit %s. Closing it.", state_name, i + 1, status)\n' +
        indent + '                finished_tabs.add(i)\n' +
        indent + '                try:\n' +
        indent + '                    if len(driver.window_handles) > 1 and driver.current_window_handle != original_window:\n' +
        indent + '                        driver.close()\n' +
        indent + '                except Exception:\n' +
        indent + '                    pass\n' +
        indent + '\n' +
        indent + '        if not any_still_generating:\n' +
        indent + '            break\n' +
        indent + '        time.sleep(5)\n' +
        indent + '\n' +
        indent + '    if driver.window_handles:\n' +
        indent + '        driver.switch_to.window(original_window)\n'
    )
    new_content = content[:match.start(2)] + new_block + content[match.end(2):]
    with open("automation/main.py", "w") as f:
        f.write(new_content)
    print("Patched main.py")
else:
    print("Could not find pattern in main.py")
