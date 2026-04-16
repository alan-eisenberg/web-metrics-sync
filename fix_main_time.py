with open("automation/main.py", "r") as f:
    code = f.read()

import re

# Remove the inline import time from main.py
code = code.replace("import time\n                    time.sleep(3)", "time.sleep(3)")

with open("automation/main.py", "w") as f:
    f.write(code)
