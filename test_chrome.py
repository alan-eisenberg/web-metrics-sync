from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os

print("Setting up Chrome options...")
options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.binary_location = "/usr/bin/google-chrome" # Force correct binary

print("Starting driver...")
try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    print("Success! Driver started.")
    driver.quit()
except Exception as e:
    print(f"Failed: {e}")
