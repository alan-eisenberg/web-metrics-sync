import pytest

from automation.modules.chat import run_prompt, to_preview_url


def test_to_preview_url_transforms_chat_path():
    chat_url = "https://chat.z.ai/c/1234-abcd"
    assert to_preview_url(chat_url) == "https://preview-chat-1234-abcd.space.z.ai/"


def test_to_preview_url_rejects_non_chat_url():
    with pytest.raises(ValueError):
        to_preview_url("https://chat.z.ai/")


def test_run_prompt_returns_mock_result():
    result = run_prompt("hello", prompt_index=1)
    assert "/c/" in result.chat_url
    assert "response-content-container" in result.response_html
