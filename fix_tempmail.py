with open("automation/modules/tempmail.py", "r") as f:
    code = f.read()

import re

# Change wait times
code = code.replace("wait = WebDriverWait(driver, 10)", "wait = WebDriverWait(driver, 30)")

with open("automation/modules/tempmail.py", "w") as f:
    f.write(code)
