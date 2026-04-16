with open("automation/modules/chat.py", "r") as f:
    content = f.read()

# Make sure time module is imported in chat.py if it isn't
if "import time" not in content:
    content = "import time\n" + content
    with open("automation/modules/chat.py", "w") as f:
        f.write(content)
