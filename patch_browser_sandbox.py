with open("automation/browser.py", "r") as f:
    content = f.read()

# Make sure we have proper flags for crashy tabs in restricted memory environments
new_options = """def get_browser(proxy_url=None):
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    
    # Extra flags to prevent crashing inside sandbox environments / heavy resource usage
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--js-flags=--expose-gc")
    options.add_argument("--disable-extensions")
    options.add_argument("--force-device-scale-factor=1")
    options.add_argument("--disable-gpu-compositing")
    
    # Add aggressive connection flags to prevent ERR_CONNECTION_CLOSED under heavy VPN packet loss"""

content = content.replace("""def get_browser(proxy_url=None):
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")

    # Add aggressive connection flags to prevent ERR_CONNECTION_CLOSED under heavy VPN packet loss""", new_options)

with open("automation/browser.py", "w") as f:
    f.write(content)
