"""
Shared utilities for PageIndex server services.

URL handling, API key validation, error extraction, and model name prefix
conversion that multiple modules depend on.
"""


def normalize_base_url(url: str) -> str:
    """Ensure base URL ends with /v1 for OpenAI-compatible API.

    The OpenAI Python client (v1.x) appends paths like /chat/completions
    to base_url, so the base must include the API version prefix.
    Example: https://api.deepseek.com -> https://api.deepseek.com/v1
    """
    url = url.rstrip("/")
    if not url.endswith("/v1"):
        url = url + "/v1"
    return url


def is_placeholder_api_key(api_key: str) -> bool:
    """Check if the API key is empty or a placeholder value."""
    if not api_key or not api_key.strip():
        return True
    if api_key.startswith("sk-XXX"):
        return True
    if "XXXX" in api_key:
        return True
    return False


def extract_http_status(exc: Exception) -> str | None:
    """Try to extract HTTP status code from an OpenAI / httpx exception.

    Returns a string like '401' or None if no status code is found.
    """
    status = getattr(exc, "status_code", None)
    if status is not None:
        return str(status)

    response = getattr(exc, "response", None)
    if response is not None:
        status = getattr(response, "status_code", None)
        if status is not None:
            return str(status)

    return None


# ---------------------------------------------------------------------------
# Model name prefix helpers
# - config.yaml stores model names with a litellm provider prefix (e.g. "openai/deepseek-v4-flash")
# - AsyncOpenAI (chat_service, test-connection) needs the plain name (e.g. "deepseek-v4-flash")
# - The frontend sees and sends the plain name
# ---------------------------------------------------------------------------

LITELLM_PROVIDER_PREFIX = "openai/"


def strip_provider_prefix(model: str) -> str:
    """Remove litellm provider prefix for direct API calls."""
    for prefix in ("openai/", "litellm/"):
        if model.startswith(prefix):
            return model[len(prefix):]
    return model


def ensure_provider_prefix(model: str) -> str:
    """Add litellm provider prefix for config.yaml storage (idempotent)."""
    model = strip_provider_prefix(model)
    return f"{LITELLM_PROVIDER_PREFIX}{model}"
