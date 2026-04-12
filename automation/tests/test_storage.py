import json

from automation.modules.storage import load_credentials, upsert_credential


def test_upsert_creates_and_updates_record(tmp_path):
    path = tmp_path / "credentials.json"
    upsert_credential(path, {"email": "a@test.dev", "username": "u1"})
    first = load_credentials(path)
    assert len(first) == 1
    assert first[0]["username"] == "u1"

    upsert_credential(path, {"email": "a@test.dev", "status": "completed"})
    second = load_credentials(path)
    assert len(second) == 1
    assert second[0]["status"] == "completed"
    assert second[0]["username"] == "u1"


def test_load_credentials_accepts_dict_format(tmp_path):
    path = tmp_path / "credentials.json"
    path.write_text(json.dumps({"email": "one@test.dev"}), encoding="utf-8")
    loaded = load_credentials(path)
    assert loaded == [{"email": "one@test.dev"}]
