from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


STATE_ORDER = [
    "INIT",
    "LOAD_OPENVPN_PROFILES",
    "CONNECT_OPENVPN",
    "VERIFY_PUBLIC_IP",
    "MAIL_BOOTSTRAP",
    "OPEN_VERIFY_AND_RESEND",
    "WAIT_VERIFY_EMAIL",
    "COMPLETE_REGISTRATION",
    "SAVE_CREDENTIALS",
    "CHAT_PARALLEL_GENERATE",
    "FINALIZE",
]


STAGE_TO_LAST_STATE = {
    "vpn": "VERIFY_PUBLIC_IP",
    "mail": "SAVE_CREDENTIALS",
    "chat": "CHAT_PARALLEL_GENERATE",
    "full": "FINALIZE",
}


@dataclass
class Settings:
    base_dir: Path
    max_retries: int = 3
    base_token: str = "60182646-1be4-414c-b697-99543c8cc974"
    groq_model: str = "llama-3.3-70b-versatile"
    openvpn_profiles_env: str | None = None
    openvpn_username: str | None = None
    openvpn_password: str | None = None
    groq_api_key: str | None = None
    chrome_binary: str = "/usr/bin/google-chrome-stable"
    chromedriver_path: str = (
        "/tmp/chromedriver-linux64/chromedriver-linux64/chromedriver"
    )
    eval_max_attempts: int = 4
    response_timeout_sec: int = 480
    openvpn_connect_timeout_sec: int = 120
    keep_browser_open_default: bool = True

    @property
    def data_dir(self) -> Path:
        return self.base_dir / "data"

    @property
    def prompts_dir(self) -> Path:
        return self.data_dir / "prompts"

    @property
    def full_prompt_path(self) -> Path:
        return self.prompts_dir / "full_prompt.txt"

    @property
    def openvpn_profiles_dir(self) -> Path:
        if self.openvpn_profiles_env:
            return Path(self.openvpn_profiles_env)
        external_profiles = Path("/mnt/vault/Downloads/vpns")
        if external_profiles.exists():
            return external_profiles
        return self.data_dir / "openvpn" / "profiles"

    @property
    def openvpn_auth_path(self) -> Path:
        return self.data_dir / "openvpn" / "auth.txt"

    @property
    def credentials_path(self) -> Path:
        return self.data_dir / "credentials.json"

    @property
    def run_state_path(self) -> Path:
        return self.data_dir / "run_state.json"

    @property
    def js_dir(self) -> Path:
        return self.base_dir / "js"

    @property
    def artifacts_dir(self) -> Path:
        return self.base_dir / "artifacts"

    @property
    def logs_dir(self) -> Path:
        return self.artifacts_dir / "logs"

    @property
    def screenshots_dir(self) -> Path:
        return self.artifacts_dir / "screenshots"

    @property
    def html_dumps_dir(self) -> Path:
        return self.artifacts_dir / "html_dumps"


def default_settings(base_dir: Path | None = None) -> Settings:
    resolved = base_dir if base_dir is not None else Path(__file__).resolve().parent
    return Settings(
        base_dir=resolved,
        openvpn_profiles_env=os.environ.get("OPENVPN_PROFILES_DIR"),
        openvpn_username=os.environ.get("OPENVPN_USERNAME"),
        openvpn_password=os.environ.get("OPENVPN_PASSWORD"),
        groq_api_key=os.environ.get("GROQ_API_KEY"),
        chrome_binary=os.environ.get("CHROME_BINARY", "/usr/bin/google-chrome-stable"),
        chromedriver_path=os.environ.get(
            "CHROMEDRIVER_PATH",
            "/tmp/chromedriver-linux64/chromedriver-linux64/chromedriver",
        ),
        eval_max_attempts=int(os.environ.get("EVAL_MAX_ATTEMPTS", "4")),
        response_timeout_sec=int(os.environ.get("RESPONSE_TIMEOUT_SEC", "480")),
        openvpn_connect_timeout_sec=int(
            os.environ.get("OPENVPN_CONNECT_TIMEOUT_SEC", "120")
        ),
        keep_browser_open_default=(
            os.environ.get("KEEP_BROWSER_OPEN_DEFAULT", "true").lower() == "true"
        ),
    )
