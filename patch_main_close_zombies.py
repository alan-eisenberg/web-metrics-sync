with open("automation/main.py", "r") as f:
    content = f.read()

# Add a failsafe at the very beginning of run() to kill Chrome if running via loop script
new_run = """def run() -> int:
    import subprocess
    # Attempt to clear dead chrome/chromedriver instances if repeating cycles/loops massively
    subprocess.run(["killall", "-9", "chrome", "chromedriver"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    
    args = parse_args()"""

content = content.replace("""def run() -> int:
    args = parse_args()""", new_run)

with open("automation/main.py", "w") as f:
    f.write(content)
