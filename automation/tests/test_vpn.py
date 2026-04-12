from pathlib import Path

import pytest

from automation.modules.vpn import (
    VPNError,
    ensure_auth_file,
    load_profiles,
    mock_connect,
    validate_auth_file,
)


def test_load_profiles_reads_ovpn_files(tmp_path: Path):
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    (profiles_dir / "a.ovpn").write_text("client\n", encoding="utf-8")
    (profiles_dir / "b.ovpn").write_text("client\n", encoding="utf-8")
    profiles = load_profiles(profiles_dir)
    assert len(profiles) == 2


def test_validate_auth_file_requires_two_lines(tmp_path: Path):
    auth = tmp_path / "auth.txt"
    auth.write_text("only-user\n", encoding="utf-8")
    with pytest.raises(VPNError):
        validate_auth_file(auth)


def test_mock_connect_returns_metadata(tmp_path: Path):
    profile = tmp_path / "node.ovpn"
    profile.write_text("client\n", encoding="utf-8")
    auth = tmp_path / "auth.txt"
    auth.write_text("name\npass\n", encoding="utf-8")
    out = mock_connect(profile, auth)
    assert out["connected"] == "true"
    assert out["vpn_user"] == "name"


def test_ensure_auth_file_creates_from_env_values(tmp_path: Path):
    auth = tmp_path / "auth.txt"
    user, password = ensure_auth_file(auth, "u", "p")
    assert user == "u"
    assert password == "p"
    assert auth.read_text(encoding="utf-8") == "u\np\n"


def test_ensure_auth_file_raises_without_any_creds(tmp_path: Path):
    auth = tmp_path / "auth.txt"
    with pytest.raises(VPNError):
        ensure_auth_file(auth, None, None)
