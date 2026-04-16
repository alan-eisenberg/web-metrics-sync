with open("automation/main.py", "r") as f:
    content = f.read()

old_poll = """                driver.get("https://cleantempmail.com")
                # Wait for email to arrive and click verify
                registered = auth_zai.poll_inbox_and_verify(
                    driver, password=state.email
                )

                entry = {
                    **registered,
                    "run_id": state.run_id,
                    "vpn_profile": state.metadata.get("vpn_profile"),
                    "public_ip": state.metadata.get("public_ip"),
                    "status": "registered",
                    "preview_urls": state.preview_urls,
                }
                storage.upsert_credential(settings.credentials_path, entry)"""

new_poll = """                driver.get("https://cleantempmail.com")
                # Wait for email to arrive and click verify
                try:
                    registered = auth_zai.poll_inbox_and_verify(
                        driver, password=state.email
                    )
                except Exception as e:
                    log.error("[SAVE_CREDENTIALS] Verification failed: %s", e)
                    # We continue to the next state (or the next run if handled appropriately)
                    # We might just want to raise it so the run restarts from scratch
                    raise RuntimeError(f"Email verification failed: {e}")

                entry = {
                    **registered,
                    "run_id": state.run_id,
                    "vpn_profile": state.metadata.get("vpn_profile"),
                    "public_ip": state.metadata.get("public_ip"),
                    "status": "registered",
                    "preview_urls": state.preview_urls,
                }
                storage.upsert_credential(settings.credentials_path, entry)"""

content = content.replace(old_poll, new_poll)
with open("automation/main.py", "w") as f:
    f.write(content)
