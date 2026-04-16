with open("automation/modules/tempmail.py", "r") as f:
    content = f.read()

old_get = """        try:
            driver.get("https://cleantempmail.com")
            break
        except Exception as e:"""

new_get = """        try:
            driver.get("https://cleantempmail.com")
            if "ERR_SOCKS_CONNECTION_FAILED" in driver.page_source or "ERR_CONNECTION_CLOSED" in driver.page_source or "ERR_PROXY_CONNECTION_FAILED" in driver.page_source:
                raise Exception("Proxy/Network error page displayed")
            break
        except Exception as e:"""

content = content.replace(old_get, new_get)

with open("automation/modules/tempmail.py", "w") as f:
    f.write(content)
