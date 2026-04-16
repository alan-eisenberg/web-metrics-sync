import json
import os
import requests
import concurrent.futures
from urllib.parse import urlparse


def check_link(url):
    try:
        # Increase timeout just in case the backend is slow
        resp = requests.get(url, timeout=15)
        text = resp.text.lower()

        # Check if the page is the Z.ai 502/Loading refresh page
        is_refresh_loop = (
            "setTimeout(() => {" in resp.text
            and "window.location.href = window.location.href;" in resp.text
        )

        # Next.js standard 404 page
        is_404 = "404" in text and "this page could not be found" in text
        # Vercel / Generic application errors
        is_app_error = "application error" in text

        if is_refresh_loop or resp.status_code == 502:
            return url, "BROKEN", "Dead Sandbox (502 / Auto-Refresh Loop)"

        # If it returns an explicit error status code
        if (
            resp.status_code >= 400 and resp.status_code != 403
        ):  # Allow 403 just to inspect the body, some anti-bot returns 403
            return url, "BROKEN", f"HTTP {resp.status_code}"

        if is_404:
            return url, "BROKEN", "Soft 404 (Page not found)"

        if is_app_error:
            return url, "BROKEN", "Application Error in body"

        # Check if the page actually contains typical z.ai chat UI content
        # E.g., we expect the body to have something other than just a generic Next.js scaffold 404.
        # But for now, if it didn't match the error signatures, assume it's working.
        return url, "WORKING", f"HTTP {resp.status_code}, no error signatures"

    except requests.exceptions.RequestException as e:
        return url, "BROKEN", f"Request Exception: {str(e)}"


def main():
    links_file = "/mnt/vault/repos/altissiabooster/links.json"
    if not os.path.exists(links_file):
        print(f"{links_file} not found!")
        return

    with open(links_file, "r") as f:
        links = json.load(f)

    total = len(links)
    print(f"Starting highly accurate verification of {total} links using requests...")

    working = []
    broken = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        # Map futures to urls
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
                print(
                    f"[{count}/{total}] ❌ ERROR:   {url} generated an exception: {exc}"
                )
                broken.append({"url": url, "reason": "Exception during check"})

    print("\n--- RESULTS ---")
    print(f"Total Working: {len(working)}")
    print(f"Total Broken:  {len(broken)}")

    with open("verification_report_v2.json", "w") as f:
        json.dump({"working": working, "broken": broken}, f, indent=2)
    print("Report saved to verification_report_v2.json")


if __name__ == "__main__":
    main()
