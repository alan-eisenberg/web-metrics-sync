with open("automation/modules/chat.py", "r") as f:
    content = f.read()

# Make check_generation_status absolutely bulletproof against StaleElementReferenceException
old_def = """def check_generation_status(driver) -> tuple[str, ChatResult | None]:
    # 0. Check and clear any Limit Sandbox Concurrency popups
    if handle_sandbox_popup(driver):
        # We hit a limit and cleared it. Let the main loop know we hit the sandbox limit so it can retry
        return "SANDBOX_LIMIT", None

    # 1. Check if error/regenerate is visible
    if click_regenerate(driver):
        return "ERROR", None"""

new_def = """def check_generation_status(driver) -> tuple[str, ChatResult | None]:
    try:
        # 0. Check and clear any Limit Sandbox Concurrency popups
        if handle_sandbox_popup(driver):
            # We hit a limit and cleared it. Let the main loop know we hit the sandbox limit so it can retry
            return "SANDBOX_LIMIT", None

        # 1. Check if error/regenerate is visible
        if click_regenerate(driver):
            return "ERROR", None
    except Exception as e:
        if "stale element reference" in str(e).lower() or "staleelementreference" in str(e).lower():
            # Silently ignore stale elements as React is just updating the DOM
            return "GENERATING", None
        if "invalid session id" in str(e).lower() or "tab crashed" in str(e).lower() or "no such window" in str(e).lower():
            raise e
        print(f"[!] Warning checking status (safely ignored): {e}")
        return "GENERATING", None"""

content = content.replace(old_def, new_def)
with open("automation/modules/chat.py", "w") as f:
    f.write(content)
