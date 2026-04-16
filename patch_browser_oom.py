with open("automation/browser.py", "r") as f:
    content = f.read()

# Add even stricter RAM limits
old_flags = """    options.add_argument("--js-flags=--expose-gc")"""
new_flags = """    options.add_argument("--js-flags=--expose-gc --max-old-space-size=256")
    options.add_argument("--disable-site-isolation-trials")
    options.add_argument("--disable-logging")
    options.add_argument("--v=99") # suppress noisy warnings
    options.add_argument("--single-process") # WARNING: this might be necessary to keep IPC overhead low on VPSs
    options.add_argument("--disable-features=Translate")
    options.add_argument("--disable-features=OptimizationHints")"""

content = content.replace(old_flags, new_flags)

# Let's not use single-process as it can crash Chrome entirely on Linux sometimes, we'll omit it
new_flags = """    options.add_argument("--js-flags=--expose-gc --max-old-space-size=256")
    options.add_argument("--disable-site-isolation-trials")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-features=Translate")
    options.add_argument("--disable-features=OptimizationHints")
    # Tell Chrome to heavily limit its cache size to stop it from bloating memory over time
    options.add_argument("--disk-cache-size=1048576")"""
content = content.replace("""    options.add_argument("--js-flags=--expose-gc --max-old-space-size=256")
    options.add_argument("--disable-site-isolation-trials")
    options.add_argument("--disable-logging")
    options.add_argument("--v=99") # suppress noisy warnings
    options.add_argument("--single-process") # WARNING: this might be necessary to keep IPC overhead low on VPSs
    options.add_argument("--disable-features=Translate")
    options.add_argument("--disable-features=OptimizationHints")""", new_flags)

with open("automation/browser.py", "w") as f:
    f.write(content)
