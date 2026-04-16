import json
import os
import time
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--blink-settings=imagesEnabled=false") # disable images to speed up
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver

def check_link(url):
    driver = None
    try:
        driver = get_driver()
        driver.get(url)
        
        # Wait for Next.js to hydrate and load the sandbox (which hides the 404 shell)
        time.sleep(6)
        
        text = driver.page_source.lower()
        
        is_refresh_loop = "settimeout(() =>" in text and "window.location.href" in text
        is_502 = "502 bad gateway" in text
        is_404 = "404" in text and "this page could not be found" in text
        is_app_error = "application error" in text
        
        if is_refresh_loop or is_502:
            return url, "BROKEN", "Dead Sandbox (502 / Auto-Refresh Loop)"
            
        if is_404:
            return url, "BROKEN", "Soft 404 (Page not found)"
            
        if is_app_error:
            return url, "BROKEN", "Application Error in body"
            
        return url, "WORKING", "Page rendered successfully"
        
    except Exception as e:
        return url, "BROKEN", f"Exception: {str(e)}"
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def main():
    links_file = "/mnt/vault/repos/altissiabooster/links.json"
    if not os.path.exists(links_file):
        print(f"{links_file} not found!")
        return

    with open(links_file, "r") as f:
        links = json.load(f)

    total = len(links)
    print(f"Starting SELENIUM verification of {total} links...")
    print("This will take some time as it boots real headless browsers.")

    working = []
    broken = []

    # Using 5 workers to avoid crashing the system with too many Chrome instances
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_to_url = {executor.submit(check_link, url): url for url in links}

        count = 0
        for future in concurrent.futures.as_completed(future_to_url):
            count += 1
            url = future_to_url[future]
            try:
                url_res, status, reason = future.result()
                if status == "WORKING":
                    print(f"[{count}/{total}] ✅ WORKING: {url_res}")
                    working.append(url_res)
                else:
                    print(f"[{count}/{total}] ❌ BROKEN:  {url_res} ({reason})")
                    broken.append({"url": url_res, "reason": reason})
            except Exception as exc:
                print(f"[{count}/{total}] ❌ ERROR:   {url} generated an exception: {exc}")
                broken.append({"url": url, "reason": "Exception during check"})

    print("\n--- RESULTS ---")
    print(f"Total Working: {len(working)}")
    print(f"Total Broken:  {len(broken)}")

    with open("verification_report_selenium.json", "w") as f:
        json.dump({"working": working, "broken": broken}, f, indent=2)
    print("Report saved to verification_report_selenium.json")

if __name__ == "__main__":
    main()
