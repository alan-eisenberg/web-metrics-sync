import time
from automation.browser import get_browser
from automation.modules import tempmail, auth_zai

driver = get_browser()
try:
    print("Getting email...")
    email = tempmail.get_temp_mail(driver)
    print(f"Email: {email}")
    username = tempmail.generate_username()
    verify_url = tempmail.build_verify_url("60182646-1be4-414c-b697-99543c8cc974", email, username)
    print(f"Verify URL: {verify_url}")
    
    print("Opening verify/resend...")
    auth_zai.open_verify_resend(driver, verify_url)
    
    # switch back to temp mail
    driver.switch_to.window(driver.window_handles[0])
    print("Polling inbox...")
    
    html = driver.page_source
    with open("tempmail_before_poll.html", "w") as f:
        f.write(html)
        
    auth_zai.poll_inbox_and_verify(driver, password=email)
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
    driver.save_screenshot("error_screenshot.png")
    with open("error_page.html", "w") as f:
        f.write(driver.page_source)
finally:
    driver.quit()
