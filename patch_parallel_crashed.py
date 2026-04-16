with open("automation/main.py", "r") as f:
    content = f.read()

old_except = """                                except Exception as e:
                                    log.warning("[%s] Error checking tab %d: %s", state_name, i + 1, e)
                                    any_still_generating = True
                                    continue"""

new_except = """                                except Exception as e:
                                    log.warning("[%s] Error checking tab %d: %s", state_name, i + 1, e)
                                    err_str = str(e).lower()
                                    if "invalid session id" in err_str or "tab crashed" in err_str or "no such window" in err_str or "target window already closed" in err_str:
                                        log.warning("[%s] Tab %d is dead. Marking as finished.", state_name, i + 1)
                                        finished_tabs.add(i)
                                        continue
                                    any_still_generating = True
                                    continue"""

content = content.replace(old_except, new_except)

with open("automation/main.py", "w") as f:
    f.write(content)
