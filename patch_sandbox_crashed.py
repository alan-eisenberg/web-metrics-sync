with open("automation/modules/chat.py", "r") as f:
    content = f.read()

old_sandbox = """        modals = driver.find_elements(
            By.CSS_SELECTOR,
            "button.dismiss-button, .modal-close, button[aria-label='Close'], button[class*='close']",
        )
        for modal in modals:
            try:
                if modal.is_displayed():
                    modal.click()
                    time.sleep(1)
            except:
                pass
    except Exception as e:
        pass"""

new_sandbox = """        modals = driver.find_elements(
            By.CSS_SELECTOR,
            "button.dismiss-button, .modal-close, button[aria-label='Close'], button[class*='close']",
        )
        for modal in modals:
            try:
                if modal.is_displayed():
                    modal.click()
                    time.sleep(1)
            except:
                pass
    except Exception as e:
        pass"""

# Let's check check_generation_status in chat.py
