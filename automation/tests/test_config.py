from pathlib import Path

from automation.config import STAGE_TO_LAST_STATE, STATE_ORDER, default_settings


def test_stage_targets_exist_in_state_order():
    for last_state in STAGE_TO_LAST_STATE.values():
        assert last_state in STATE_ORDER


def test_default_settings_derive_paths(tmp_path: Path):
    settings = default_settings(tmp_path)
    assert settings.data_dir == tmp_path / "data"
    assert settings.credentials_path == tmp_path / "data" / "credentials.json"


def test_default_settings_prefers_standard_vpn_folder_when_present(tmp_path: Path):
    settings = default_settings(tmp_path)
    assert settings.openvpn_profiles_dir in {
        Path("/mnt/vault/Downloads/vpns"),
        tmp_path / "data" / "openvpn" / "profiles",
    }
