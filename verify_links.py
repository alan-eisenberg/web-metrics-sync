import json
import time
import os
import sys
from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException


def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    # Mute logging
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    # We can reuse webdriver manager from the project
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(15)
    return driver


def check_link(url, index, total):
    driver = None
    try:
        driver = create_driver()
        print(f"[{index}/{total}] Loading: {url}")

        try:
            driver.get(url)
        except TimeoutException:
            # Maybe the page just took too long, try reading whatever loaded
            pass

        time.sleep(4)  # Wait for initial render

        # Capture current URL to check for redirect
        first_url = driver.current_url

        # Check for specific error phrases
        page_source = driver.page_source.lower()

        if "application error" in page_source:
            return url, "BROKEN", "Application Error text found"

        if "not found" in page_source and "404" in page_source:
            return url, "BROKEN", "404 Not Found"

        # Wait a bit more to detect infinite refresh loops
        time.sleep(3)
        second_url = driver.current_url

        # Detect redirects away from space.z.ai
        if "preview-chat-" not in second_url and "space.z.ai" not in second_url:
            return url, "BROKEN", f"Redirected unexpectedly to {second_url}"

        if first_url != second_url:
            return (
                url,
                "BROKEN",
                f"URL refresh loop detected ({first_url} -> {second_url})",
            )

        # If no obvious errors, assume working
        return url, "WORKING", "Page loaded cleanly"

    except Exception as e:
        return url, "BROKEN", f"WebDriver exception: {str(e)}"
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def main():
    links_file = "/mnt/vault/repos/altissiabooster/links.json"
    if not os.path.exists(links_file):
        print("links.json not found!")
        return

    with open(links_file, "r") as f:
        links = json.load(f)

    # For testing, just do the last 10, but we can do all if needed.
    # Let's do all of them, but cap concurrency to 5.
    total = len(links)
    print(f"Starting verification of {total} links...")

    working = []
    broken = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i, url in enumerate(links, 1):
            futures.append(executor.submit(check_link, url, i, total))

        for future in futures:
            url, status, reason = future.result()
            if status == "WORKING":
                print(f"✅ WORKING: {url}")
                working.append(url)
            else:
                print(f"❌ BROKEN:  {url} ({reason})")
                broken.append({"url": url, "reason": reason})

    print("\n--- RESULTS ---")
    print(f"Total Working: {len(working)}")
    print(f"Total Broken:  {len(broken)}")

    with open("verification_report.json", "w") as f:
        json.dump({"working": working, "broken": broken}, f, indent=2)
    print("Report saved to verification_report.json")


if __name__ == "__main__":
    main()
