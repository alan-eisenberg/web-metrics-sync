from automation.config import STAGE_TO_LAST_STATE


def test_stage_mapping_is_exact():
    assert STAGE_TO_LAST_STATE["vpn"] == "VERIFY_PUBLIC_IP"
    assert STAGE_TO_LAST_STATE["mail"] == "SAVE_CREDENTIALS"
    assert STAGE_TO_LAST_STATE["chat"] == "SAVE_PREVIEW_LINKS"
    assert STAGE_TO_LAST_STATE["full"] == "FINALIZE"
