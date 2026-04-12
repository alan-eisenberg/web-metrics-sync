from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import tempfile
import os


def get_browser(proxy_url=None):
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")

    if proxy_url:
        options.add_argument(f"--proxy-server={proxy_url}")

    options.add_experimental_option("detach", True)
    temp_profile = tempfile.mkdtemp(prefix="zai_browser_")
    options.add_argument(f"--user-data-dir={temp_profile}")

    chromedriver_path = "/tmp/chromedriver-linux64/chromedriver-linux64/chromedriver"
    if os.path.exists(chromedriver_path):
        service = Service(chromedriver_path)
    else:
        service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        },
    )
    return driver
