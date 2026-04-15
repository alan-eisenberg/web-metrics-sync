# Z.ai Automation Farm: Architecture & AI Context

This document is specifically written to provide full context to any AI model or developer analyzing this codebase. It explains the purpose, architecture, and deployment strategy of the Z.ai Automation Farm.

## 1. High-Level Overview

The **Z.ai Automation Farm** is an orchestrated, multi-stage browser automation pipeline designed to generate production-ready application outputs via the Z.ai chat interface. 
Because the target application has rate limits, proxy bans, and headless browser detection, the system employs advanced evasion techniques, including IP rotation via OpenVPN, temporary email verification, and headful browser execution using `Xvfb`.

The outputs (preview URLs) are continuously aggregated and pushed to an external repository (`altissiabooster`) containing a `links.json` file.

## 2. Core Execution Flow (The State Machine)

The core orchestrator is `automation/main.py`. It runs as a state machine to ensure idempotency and recovery from crashes.

The stages (`STATE_ORDER`) are:
1. **INIT**: Setup directories and data files.
2. **LOAD_OPENVPN_PROFILES / CONNECT_OPENVPN**: Picks a random OpenVPN profile and establishes a tunnel. Retries if the connection fails.
3. **VERIFY_PUBLIC_IP**: Ensures the VPN successfully masked the host IP.
4. **MAIL_BOOTSTRAP / SAVE_CREDENTIALS**: Bootstraps a temporary email (`cleantempmail`), registers on Z.ai, waits for the verification email, and verifies the account.
5. **CHAT_PARALLEL_GENERATE**: 
   - Spawns multiple browser tabs (`--parallel`).
   - Sends prompts to Z.ai agents.
   - Polls tabs simultaneously for generation completion (handles up to 8-minute timeouts).
   - Evaluates the output using `evaluator_groq.py` and extracts the HTML/Text using `extractor.py`.
   - If approved, extracts the preview URL.
6. **FINALIZE**: Cleans up browser instances and kills the OpenVPN tunnel.

## 3. Browser Automation & Evasion (`browser.py`)

Z.ai frequently detects and blocks standard headless browsers.
- **Headful Execution**: We run Chromium in standard headful mode.
- **CI/CD Compatibility (Xvfb)**: Because GitHub Actions Ubuntu runners lack a display, we wrap the execution in `xvfb-run` (X Virtual Framebuffer). This creates a virtual display (`-screen 0 1920x1080x24`) allowing Chromium to render visually in memory without crashing or triggering headless detection.

## 4. Massive Parallelization (GitHub Actions)

To avoid GitHub Actions Runner limits (specifically Out-Of-Memory / OOM errors due to only having 7GB of RAM per runner), the pipeline uses **Horizontal Scaling via Matrix Jobs**.

File: `.github/workflows/farm.yml`
- We use a GitHub Actions `matrix` strategy (e.g., `runner: [1, 2, 3, 4, 5]`).
- This spins up 5 entirely independent Ubuntu virtual machines simultaneously.
- Each VM establishes its own VPN tunnel, generates its own temp emails, and runs a subset of parallel browser tabs (e.g., `--parallel 3`), resulting in 15 concurrent generations globally.

## 5. Concurrent Git Pushing & Conflict Resolution (`altissia.py`)

Because multiple runners are finishing generations and pushing to the same `altissiabooster` repository simultaneously, Git merge conflicts are guaranteed.

We solved this in `automation/modules/altissia.py` by implementing a **Jitter & Retry Loop**:
1. Pull remote changes with `git pull --rebase`.
2. Read the latest `links.json` from disk.
3. Append our new local links (checking for duplicates).
4. Save the file and `git commit`.
5. Attempt `git push`.
6. **Conflict Handling**: If the push fails (because another matrix runner pushed milliseconds before us), we abort, execute `git reset --hard origin/main`, sleep for a randomized exponential backoff (jitter), and retry the entire read-append-push loop (up to 10 times).

## 6. Multi-Account Git Pushing

To spread API limits or distribute repository activity, the CI/CD pipeline supports dynamic GitHub identities.

- The `.github/workflows/farm.yml` allows manual trigger inputs (Workflow Dispatch).
- The user selects `account1` or `account2`.
- The Action dynamically sets the `$GIT_USER_EMAIL` and `$GIT_USER_NAME` environment variables.
- The Action injects the correct Personal Access Token (`secrets.ALTISSIA_PAT_1` vs `secrets.ALTISSIA_PAT_2`) into the checkout step.
- `altissia.py` reads the environment variables and configures the local git environment before pushing.

## 7. Development & Debugging

- **CLI Options**: Run `python -m automation.main --git --parallel 3 --cycles 2`.
- The `--git` flag is required to trigger pushes to the remote `altissiabooster` repo. Without it, the script only saves links locally to `.data/credentials.json`.
- Logs are aggressively captured in `automation/logger.py` to allow tracing parallel tab failures.
