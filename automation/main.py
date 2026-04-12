from __future__ import annotations

import argparse
import time
import uuid
from pathlib import Path

from automation.config import STATE_ORDER, STAGE_TO_LAST_STATE, default_settings
from automation.logger import configure_logging, get_logger
from automation.modules import (
    auth_zai,
    chat,
    evaluator_groq,
    extractor,
    storage,
    tempmail,
    vpn,
)
from automation.state_store import RunState, save_state


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ZAI modular automation orchestrator")
    parser.add_argument(
        "--stage",
        choices=["vpn", "mail", "chat", "full"],
        default="full",
        help="Run only up to a specific stage",
    )
    parser.add_argument(
        "--keep-open",
        action="store_true",
        help="Do not close browser at end (placeholder flag for Selenium integration)",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Do not close browser at end (placeholder flag for Selenium integration)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed for deterministic profile selection",
    )
    return parser.parse_args()


def _touch_data_files(base_dir: Path) -> None:
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    credentials = data_dir / "credentials.json"
    if not credentials.exists():
        credentials.write_text("[]\n", encoding="utf-8")

    auth_path = data_dir / "openvpn" / "auth.txt"
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    if not auth_path.exists():
        auth_path.write_text("", encoding="utf-8")

    prompt1 = data_dir / "prompts" / "prompt1.txt"
    prompt1.parent.mkdir(parents=True, exist_ok=True)
    full_prompt = data_dir / "prompts" / "full_prompt.txt"
    if not full_prompt.exists():
        full_prompt.write_text(
            "Build a production-ready application output.", encoding="utf-8"
        )

    if not prompt1.exists():
        prompt1.write_text("Create production-ready code output.", encoding="utf-8")

    prompt2 = data_dir / "prompts" / "prompt2.txt"
    if not prompt2.exists():
        prompt2.write_text("Refine and harden the previous output.", encoding="utf-8")


def run() -> int:
    args = parse_args()
    settings = default_settings()
    _touch_data_files(settings.base_dir)

    log_file = settings.logs_dir / f"run-{int(time.time())}.log"
    configure_logging(log_file)
    log = get_logger("automation")

    run_id = str(uuid.uuid4())
    state = RunState(run_id=run_id)

    last_state = STAGE_TO_LAST_STATE[args.stage]
    last_idx = STATE_ORDER.index(last_state)

    log.info("Starting run_id=%s stage=%s", run_id, args.stage)

    profiles = []
    selected_profile = None
    prompt_one_result = None
    prompt_two_result = None
    driver = None

    for idx, state_name in enumerate(STATE_ORDER):
        state.state = state_name
        save_state(settings.run_state_path, state)
        log.info("[%s] Enter", state_name)

        if state_name == "INIT":
            pass

        elif state_name == "LOAD_OPENVPN_PROFILES":
            profiles = vpn.load_profiles(settings.openvpn_profiles_dir)
            selected_profile = vpn.pick_profile(profiles, seed=args.seed)
            state.metadata["vpn_profile"] = str(selected_profile)
            log.info("Randomly selected VPN profile: %s", selected_profile.name)

        elif state_name == "CONNECT_OPENVPN":
            if selected_profile is None:
                raise RuntimeError("Profile is not selected")
            vpn.ensure_auth_file(
                settings.openvpn_auth_path,
                settings.openvpn_username,
                settings.openvpn_password,
            )
            conn_info = vpn.connect_vpn(
                selected_profile, settings.openvpn_auth_path, state.run_id
            )
            state.metadata.update(conn_info)

        elif state_name == "VERIFY_PUBLIC_IP":
            if "public_ip" not in state.metadata:
                raise RuntimeError("Public IP not available after VPN connect")

        elif state_name == "MAIL_BOOTSTRAP":
            from automation.browser import get_browser

            if driver is None:
                driver = get_browser(proxy_url=state.metadata.get("proxy"))
            email = tempmail.get_temp_mail(driver)
            username = tempmail.generate_username()
            verify_url = tempmail.build_verify_url(settings.base_token, email, username)
            state.email = email
            state.username = username
            state.metadata["verify_url"] = verify_url

            auth_zai.open_verify_resend(driver, verify_url)

        elif state_name == "SAVE_CREDENTIALS":
            from automation.browser import get_browser

            if not state.email or not state.username:
                raise RuntimeError("Cannot save credentials without email/username")
            if driver is None:
                driver = get_browser(proxy_url=state.metadata.get("proxy"))
            driver.get("https://cleantempmail.com")
            # Wait for email to arrive and click verify
            registered = auth_zai.poll_inbox_and_verify(driver, password=state.email)

            entry = {
                **registered,
                "run_id": state.run_id,
                "vpn_profile": state.metadata.get("vpn_profile"),
                "public_ip": state.metadata.get("public_ip"),
                "status": "registered",
                "preview_urls": state.preview_urls,
            }
            storage.upsert_credential(settings.credentials_path, entry)

        elif state_name in ("CHAT_CYCLE_ONE", "CHAT_CYCLE_TWO", "CHAT_CYCLE_THREE"):
            from automation.browser import get_browser

            if driver is None:
                driver = get_browser(proxy_url=state.metadata.get("proxy"))

            full_prompt = (settings.prompts_dir / "full_prompt.txt").read_text(
                encoding="utf-8"
            )

            chat.ensure_agent_mode(driver, settings.js_dir)
            current_prompt = full_prompt

            for attempt in range(settings.eval_max_attempts):
                log.info(
                    "[%s] Attempt %d with prompt length %d",
                    state_name,
                    attempt + 1,
                    len(current_prompt),
                )
                result = chat.run_prompt(driver, current_prompt)

                extracted = extractor.extract_response(
                    result.response_html,
                    result.response_text,
                )

                eval_result = evaluator_groq.evaluate_response(extracted.text)
                if eval_result.approved:
                    preview_url = chat.to_preview_url(result.chat_url)
                    state.preview_urls.append(preview_url)
                    log.info("[%s] Approved! Preview URL: %s", state_name, preview_url)

                    if state.email:
                        storage.upsert_credential(
                            settings.credentials_path,
                            {
                                "email": state.email,
                                "username": state.username,
                                "preview_urls": state.preview_urls,
                                "status": "completed",
                                "run_id": state.run_id,
                            },
                        )
                    break
                else:
                    log.warning(
                        "[%s] Attempt %d rejected: %s",
                        state_name,
                        attempt + 1,
                        eval_result.reason,
                    )
                    current_prompt = eval_result.reason

            else:
                log.error(
                    "[%s] Failed to get an approved response after %d attempts",
                    state_name,
                    settings.eval_max_attempts,
                )
                # We could raise here or just let it continue to the next cycle
                # raise RuntimeError(f"{state_name} failed after max attempts")

        elif state_name == "FINALIZE":
            state.metadata["keep_open"] = "true" if args.keep_open else "false"

        log.info("[%s] Done", state_name)

        if idx >= last_idx:
            log.info("Reached requested stage=%s at state=%s", args.stage, state_name)
            break

    if driver is not None and not args.keep_open and not args.open:
        try:
            driver.quit()
        except Exception as e:
            log.warning("Failed to quit browser gracefully: %s", e)

    if not args.keep_open and not args.open:
        vpn.cleanup(state.metadata)

    save_state(settings.run_state_path, state)
    log.info("Run completed with %d preview url(s)", len(state.preview_urls))

    if args.open or args.keep_open:
        log.info(
            "Browser is kept open. You can paste preview URLs below and press Enter to save."
        )
        log.info("Type 'exit' to quit.")
        import sys

        while True:
            try:
                print("Link> ", end="", flush=True)
                user_input = sys.stdin.readline().strip()
                if not user_input or user_input.lower() in ("exit", "quit"):
                    if user_input.lower() in ("exit", "quit"):
                        break
                    continue
                if user_input.startswith("http"):
                    state.preview_urls.append(user_input)
                    if state.email:
                        storage.upsert_credential(
                            settings.credentials_path,
                            {
                                "email": state.email,
                                "username": state.username,
                                "password": state.email,  # email is used as password
                                "preview_urls": state.preview_urls,
                                "status": "completed",
                                "run_id": state.run_id,
                                "vpn_profile": state.metadata.get("vpn_profile"),
                                "public_ip": state.metadata.get("public_ip"),
                            },
                        )
                        log.info("Saved link: %s", user_input)
                    else:
                        log.warning("No email registered yet. Saved to state only.")
                else:
                    log.info("Ignored non-URL input.")
            except KeyboardInterrupt:
                break
            except Exception as e:
                log.error("Input error: %s", e)

    if state.preview_urls:
        log.info(
            "Pushing %d accumulated preview urls to altissiabooster...",
            len(state.preview_urls),
        )
        altissia.append_and_push_links(state.preview_urls)

    vpn.cleanup(state.metadata)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
