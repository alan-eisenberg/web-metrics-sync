with open("automation/main.py", "r") as f:
    code = f.read()

import re
code = code.replace(
    'elif status == "SANDBOX_LIMIT" or (status == "GENERATING" and st["loops"] > 10):',
    'elif (status == "SANDBOX_LIMIT" and st["loops"] > 2) or (status == "GENERATING" and st["loops"] > 10):'
)

with open("automation/main.py", "w") as f:
    f.write(code)
