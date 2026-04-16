with open("automation/modules/chat.py", "r") as f:
    content = f.read()

# Make sure we catch StaleElementReferenceException explicitly and treat it as "GENERATING" to ignore the error
old_except = """    except Exception as e:
        if "invalid session id" in str(e).lower() or "tab crashed" in str(e).lower() or "no such window" in str(e).lower():
            raise e
        print(f"[!] Error checking status: {e}")
        return "GENERATING", None"""

new_except = """    except Exception as e:
        if "invalid session id" in str(e).lower() or "tab crashed" in str(e).lower() or "no such window" in str(e).lower():
            raise e
        if "stale element reference" in str(e).lower():
            # DOM updated while checking, perfectly normal for React apps
            return "GENERATING", None
        print(f"[!] Error checking status: {e}")
        return "GENERATING", None"""

content = content.replace(old_except, new_except)

# Let's also do it for handle_sandbox_popup
old_sandbox_except = """    except Exception as e:
        if "invalid session id" in str(e).lower() or "tab crashed" in str(e).lower() or "no such window" in str(e).lower():
            raise e
        print(f"[!] Error handling sandbox popup: {e}")
    return False"""

new_sandbox_except = """    except Exception as e:
        if "invalid session id" in str(e).lower() or "tab crashed" in str(e).lower() or "no such window" in str(e).lower():
            raise e
        if "stale element reference" not in str(e).lower():
            print(f"[!] Error handling sandbox popup: {e}")
    return False"""

content = content.replace(old_sandbox_except, new_sandbox_except)

with open("automation/modules/chat.py", "w") as f:
    f.write(content)
