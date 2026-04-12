from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
)
from automation.modules.tempmail import close_consent_popups
import time
from dataclasses import dataclass
from automation.modules.regenerate_guard import load_guard_script
from pathlib import Path


@dataclass
class ChatResult:
    chat_url: str
    response_html: str
    response_text: str


def wait_and_click(driver, css_selector: str, timeout: int = 15, description: str = ""):
    wait = WebDriverWait(driver, timeout)
    try:
        el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector)))
        try:
            el.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", el)
        print(f"[*] Clicked {description} successfully.")
        return True
    except TimeoutException:
        print(
            f"[!] Timeout waiting for {description} ('{css_selector}') to become clickable."
        )
        return False


def ensure_agent_mode(driver, js_dir: Path):
    driver.get("https://chat.z.ai/")
    wait = WebDriverWait(driver, 20)

    try:
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea#chat-input"))
        )
    except TimeoutException:
        print("[!] Timeout waiting for chat input. Proceeding...")

    close_consent_popups(driver)

    # Try closing any onboarding modals
    try:
        modals = driver.find_elements(
            By.CSS_SELECTOR,
            "button.dismiss-button, .modal-close, button[aria-label='Close'], button[class*='close']",
        )
        for m in modals:
            if m.is_displayed():
                driver.execute_script("arguments[0].click();", m)
                time.sleep(0.5)
    except:
        pass

    print("[*] Switching to Agent mode...")
    agent_btn = driver.execute_script("""
        return document.querySelector('#sidebar button svg path[d^="M4.65005 5.02227"]')?.closest('button');
    """)
    if agent_btn:
        try:
            wait.until(EC.element_to_be_clickable(agent_btn))
            driver.execute_script("arguments[0].click();", agent_btn)
            print("[*] Clicked Agent mode button.")
        except Exception as e:
            print(f"[!] Failed to click agent button: {e}")
    else:
        print("[!] Agent button not found via SVG path.")

    time.sleep(3)

    print("[*] Selecting GLM-5 model...")
    trigger_found = wait_and_click(
        driver,
        "#model-selector-glm-5-button, .modelSelectorButton, button[data-testid*='model-selector']",
        timeout=10,
        description="Model Dropdown Trigger",
    )

    if trigger_found:
        time.sleep(1)
        wait_and_click(
            driver,
            "button[data-value='glm-5'], li[data-value='glm-5']",
            timeout=10,
            description="GLM-5 Option",
        )

    time.sleep(2)
    guard_script = load_guard_script(js_dir)
    driver.execute_script(guard_script)


def run_prompt(driver, prompt_text: str, wait_seconds: int = 15) -> ChatResult:
    print("[*] Waiting for chat input to be interactable...")
    wait = WebDriverWait(driver, 20)

    chat_input = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "textarea#chat-input"))
    )

    # Inject text via JS to avoid slow typing rendering issues
    driver.execute_script(
        """
        var input = arguments[0], text = arguments[1];
        var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
        nativeInputValueSetter.call(input, text);
        var ev = new Event('input', { bubbles: true });
        input.dispatchEvent(ev);
    """,
        chat_input,
        prompt_text,
    )

    time.sleep(1)

    try:
        chat_input.send_keys(Keys.RETURN)
    except Exception as e:
        print(f"[!] Standard send_keys(RETURN) failed: {e}. Attempting fallback.")
        try:
            # First fallback: explicitly click the send button if it exists
            send_btn = driver.find_element(
                By.CSS_SELECTOR,
                "button[aria-label*='end'], #send-message-button, button[type='submit']",
            )
            driver.execute_script("arguments[0].click();", send_btn)
            print("[*] Clicked the send button via JS fallback.")
        except Exception as btn_e:
            print(f"[!] Fallback button click failed: {btn_e}")
            # Last resort: dispatch JS KeyboardEvent
            driver.execute_script(
                """
                var input = arguments[0];
                var ev = new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true});
                input.dispatchEvent(ev);
            """,
                chat_input,
            )

    print("[*] Prompt sent. Waiting for generation to start...")
    time.sleep(wait_seconds)

    print("[*] Waiting for generation to complete...")
    generation_wait = WebDriverWait(driver, 300)  # Increased from 120 to 300 seconds
    try:
        # Wait for the stop generation button to disappear or the send button to become re-enabled
        generation_wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "#send-message-button:not([disabled]), button[aria-label*='end']:not([disabled]), button[type='submit']:not([disabled])",
                )
            )
        )
        time.sleep(3)
        print("[*] Generation finished.")
    except TimeoutException:
        raise RuntimeError(
            "Timeout waiting for AI response to complete (send button did not become re-enabled)"
        )

    containers = driver.find_elements(
        By.CSS_SELECTOR, "#response-content-container, .response-content"
    )
    if not containers:
        raise RuntimeError("No #response-content-container found")

    latest_container = containers[-1]
    response_html = latest_container.get_attribute("innerHTML") or ""
    response_text = latest_container.text or ""

    return ChatResult(
        chat_url=driver.current_url,
        response_html=response_html,
        response_text=response_text,
    )


def to_preview_url(chat_url: str) -> str:
    marker = "/c/"
    if marker not in chat_url:
        raise ValueError(f"Cannot transform non-chat URL: {chat_url}")
    uuid = chat_url.split(marker, 1)[1].split("?", 1)[0]
    return f"https://preview-chat-{uuid}.space.z.ai/"
