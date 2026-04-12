from automation.modules.tempmail import (
    build_verify_url,
    generate_fake_email,
    generate_username,
)


def test_generate_username_shape():
    username = generate_username()
    assert len(username) >= 6
    assert any(ch.isdigit() for ch in username)


def test_generate_fake_email_has_at():
    email = generate_fake_email()
    assert "@" in email


def test_build_verify_url_contains_params():
    url = build_verify_url("tok", "e@x.dev", "user12")
    assert "token=tok" in url
    assert "email=e@x.dev" in url
    assert "username=user12" in url
