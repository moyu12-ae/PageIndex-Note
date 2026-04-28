"""
Unit tests for server/services/shared.py utilities.

Run with: PYTHONPATH=. python -m pytest tests/test_shared.py -v
"""

import sys
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from server.services.shared import (
    normalize_base_url,
    is_placeholder_api_key,
    extract_http_status,
    strip_provider_prefix,
    ensure_provider_prefix,
)


# ============================================================================
# normalize_base_url
# ============================================================================

class TestNormalizeBaseUrl:
    def test_adds_v1_suffix(self):
        assert normalize_base_url("https://api.deepseek.com") == "https://api.deepseek.com/v1"

    def test_preserves_existing_v1(self):
        assert normalize_base_url("https://api.deepseek.com/v1") == "https://api.deepseek.com/v1"

    def test_strips_trailing_slash_before_adding_v1(self):
        assert normalize_base_url("https://api.deepseek.com/") == "https://api.deepseek.com/v1"

    def test_handles_v1_with_trailing_slash(self):
        assert normalize_base_url("https://api.deepseek.com/v1/") == "https://api.deepseek.com/v1"

    def test_handles_custom_port(self):
        assert normalize_base_url("http://localhost:8080") == "http://localhost:8080/v1"

    def test_handles_other_providers(self):
        assert normalize_base_url("https://api.openai.com") == "https://api.openai.com/v1"

    def test_double_v1_not_added(self):
        # '/v1/v1' should not happen — function only checks ends_with('/v1')
        assert normalize_base_url("https://api.deepseek.com/v1") == "https://api.deepseek.com/v1"


# ============================================================================
# is_placeholder_api_key
# ============================================================================

class TestIsPlaceholderApiKey:
    def test_empty_string_is_placeholder(self):
        assert is_placeholder_api_key("") is True

    def test_none_is_placeholder(self):
        assert is_placeholder_api_key(None) is True

    def test_sk_xxx_prefix_is_placeholder(self):
        assert is_placeholder_api_key("sk-XXXXXXXXXXXXXXXXXXXXXXXX") is True

    def test_sk_xxx_short_is_placeholder(self):
        assert is_placeholder_api_key("sk-XXX") is True

    def test_contains_xxxx_is_placeholder(self):
        assert is_placeholder_api_key("mykey-with-XXXX-inside") is True

    def test_real_looking_key_is_not_placeholder(self):
        assert is_placeholder_api_key("sk-a1b2c3d4e5f6g7h8i9j0") is False

    def test_whitespace_only_is_placeholder(self):
        assert is_placeholder_api_key("   ") is True

    def test_startswith_sk_followed_by_real_chars(self):
        # "sk-" alone is not a placeholder — must be "sk-XXX..."
        assert is_placeholder_api_key("sk-real-key-value") is False


# ============================================================================
# extract_http_status
# ============================================================================

class FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code


class FakeExceptionWithStatus:
    def __init__(self, status_code):
        self.status_code = status_code


class FakeExceptionWithResponse:
    def __init__(self, status_code):
        self.response = FakeResponse(status_code)


class FakeExceptionNoStatus:
    pass


class TestExtractHttpStatus:
    def test_direct_status_code(self):
        exc = FakeExceptionWithStatus(401)
        assert extract_http_status(exc) == "401"

    def test_status_code_via_response(self):
        exc = FakeExceptionWithResponse(500)
        assert extract_http_status(exc) == "500"

    def test_no_status_code(self):
        exc = FakeExceptionNoStatus()
        assert extract_http_status(exc) is None

    def test_regular_exception(self):
        exc = ValueError("something broke")
        assert extract_http_status(exc) is None

    def test_zero_status_code(self):
        # status_code=0 is technically a value, and the function returns it
        exc = FakeExceptionWithStatus(0)
        result = extract_http_status(exc)
        assert result == "0"


# ============================================================================
# strip_provider_prefix
# ============================================================================

class TestStripProviderPrefix:
    def test_strips_openai_prefix(self):
        assert strip_provider_prefix("openai/deepseek-v4-flash") == "deepseek-v4-flash"

    def test_strips_litellm_prefix(self):
        assert strip_provider_prefix("litellm/deepseek-v4-flash") == "deepseek-v4-flash"

    def test_preserves_plain_model(self):
        assert strip_provider_prefix("deepseek-v4-flash") == "deepseek-v4-flash"

    def test_preserves_other_prefixes(self):
        assert strip_provider_prefix("anthropic/claude-sonnet") == "anthropic/claude-sonnet"

    def test_only_first_prefix_removed(self):
        # Model name containing 'openai/' in the middle should not be affected
        assert strip_provider_prefix("openai/deepseek/openai-v4") == "deepseek/openai-v4"

    def test_empty_string(self):
        assert strip_provider_prefix("") == ""


# ============================================================================
# ensure_provider_prefix
# ============================================================================

class TestEnsureProviderPrefix:
    def test_adds_prefix_to_plain_model(self):
        assert ensure_provider_prefix("deepseek-v4-flash") == "openai/deepseek-v4-flash"

    def test_idempotent_with_existing_openai_prefix(self):
        assert ensure_provider_prefix("openai/deepseek-v4-flash") == "openai/deepseek-v4-flash"

    def test_idempotent_with_litellm_prefix(self):
        assert ensure_provider_prefix("litellm/deepseek-v4-flash") == "openai/deepseek-v4-flash"

    def test_empty_string(self):
        assert ensure_provider_prefix("") == "openai/"
