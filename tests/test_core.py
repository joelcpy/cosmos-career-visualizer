import json
from unittest.mock import MagicMock, patch
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import get_occupation_and_prompt, generate_image, QUALITY_SUFFIX


# ── get_occupation_and_prompt ──────────────────────────────────────────────────

def test_no_api_key_returns_fallback(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    occ, prompt = get_occupation_and_prompt("firefighter")
    assert occ == "firefighter"
    assert QUALITY_SUFFIX in prompt


def test_allowed_career_returns_prompt():
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=json.dumps({
        "ok": True,
        "occupation": "Firefighter",
        "prompt": "A brave firefighter battling flames in a burning building"
    }))]

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("core.anthropic.Anthropic") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_msg
            occ, prompt = get_occupation_and_prompt("firefighter")

    assert occ == "Firefighter"
    assert QUALITY_SUFFIX in prompt
    assert "firefighter" in prompt.lower()


def test_blocked_career_returns_none():
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=json.dumps({"ok": False}))]

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("core.anthropic.Anthropic") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_msg
            occ, prompt = get_occupation_and_prompt("drug dealer")

    assert occ is None
    assert prompt is None


def test_anthropic_failure_returns_fallback():
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("core.anthropic.Anthropic") as mock_client:
            mock_client.return_value.messages.create.side_effect = Exception("API error")
            occ, prompt = get_occupation_and_prompt("astronaut")

    assert occ == "astronaut"
    assert QUALITY_SUFFIX in prompt


def test_quality_suffix_always_appended():
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=json.dumps({
        "ok": True,
        "occupation": "Chef",
        "prompt": "A chef cooking in a restaurant kitchen"
    }))]

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("core.anthropic.Anthropic") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_msg
            _, prompt = get_occupation_and_prompt("chef")

    assert prompt.endswith(QUALITY_SUFFIX)


# ── generate_image ─────────────────────────────────────────────────────────────

def test_generate_image_success():
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=json.dumps({
        "ok": True,
        "occupation": "Astronaut",
        "prompt": "An astronaut floating in space"
    }))]

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("core.anthropic.Anthropic") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_msg
            with patch("core.fal_client.run") as mock_fal:
                mock_fal.return_value = {"images": [{"url": "https://example.com/image.jpg"}]}
                image_url, occupation = generate_image("base64data", "astronaut")

    assert image_url == "https://example.com/image.jpg"
    assert occupation == "Astronaut"


def test_generate_image_blocked_raises():
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=json.dumps({"ok": False}))]

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("core.anthropic.Anthropic") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_msg
            with pytest.raises(ValueError, match="blocked"):
                generate_image("base64data", "violent career")


def test_generate_image_fal_failure_raises():
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=json.dumps({
        "ok": True,
        "occupation": "Doctor",
        "prompt": "A doctor in a hospital"
    }))]

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("core.anthropic.Anthropic") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_msg
            with patch("core.fal_client.run") as mock_fal:
                mock_fal.side_effect = Exception("fal.ai timeout")
                with pytest.raises(Exception, match="fal.ai timeout"):
                    generate_image("base64data", "doctor")


def test_generate_image_passes_base64_to_fal():
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=json.dumps({
        "ok": True,
        "occupation": "Chef",
        "prompt": "A chef in a kitchen"
    }))]

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("core.anthropic.Anthropic") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_msg
            with patch("core.fal_client.run") as mock_fal:
                mock_fal.return_value = {"images": [{"url": "https://example.com/img.jpg"}]}
                generate_image("mybase64string", "chef")
                args = mock_fal.call_args
                assert "mybase64string" in args[1]["arguments"]["reference_image_url"]
