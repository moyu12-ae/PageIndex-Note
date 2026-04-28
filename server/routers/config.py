import os
import json
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from dotenv import load_dotenv, set_key
import yaml

router = APIRouter(prefix="/api/config", tags=["config"])

PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
CONFIG_YAML_PATH = PROJECT_ROOT / "pageindex" / "config.yaml"


def _load_env():
    load_dotenv(ENV_PATH, override=True)


def _read_config_yaml():
    with open(CONFIG_YAML_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _write_config_yaml(data: dict):
    with open(CONFIG_YAML_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


# Model name handling:
# - config.yaml stores model with litellm prefix: "openai/deepseek-v4-flash"
# - AsyncOpenAI (chat_service, test-connection) needs plain name: "deepseek-v4-flash"
# - Frontend should see/use the plain name
LITELLM_PROVIDER_PREFIX = "openai/"

def _strip_provider_prefix(model: str) -> str:
    """Remove litellm provider prefix for direct API calls."""
    for prefix in ("openai/", "litellm/"):
        if model.startswith(prefix):
            return model[len(prefix):]
    return model

def _ensure_provider_prefix(model: str) -> str:
    """Add litellm provider prefix for config.yaml storage."""
    model = _strip_provider_prefix(model)  # strip any existing prefix first
    return f"{LITELLM_PROVIDER_PREFIX}{model}"


@router.get("")
async def get_config():
    """Get current LLM and processing configuration."""
    _load_env()
    cfg = _read_config_yaml()

    api_key = os.getenv("CHATGPT_API_KEY", "")
    api_key_preview = f"...{api_key[-4:]}" if len(api_key) > 4 else ""

    # Strip litellm provider prefix for frontend display / test-connection
    raw_model = cfg.get("model", "deepseek-v4-flash")
    display_model = _strip_provider_prefix(raw_model)

    return {
        "llm": {
            "model": display_model,
            "api_base_url": os.getenv("API_BASE_URL", "https://api.deepseek.com"),
            "api_key_set": bool(api_key),
            "api_key_preview": api_key_preview,
        },
        "processing": {
            "toc_check_page_num": cfg.get("toc_check_page_num", 20),
            "max_page_num_each_node": cfg.get("max_page_num_each_node", 10),
            "max_token_num_each_node": cfg.get("max_token_num_each_node", 20000),
            "if_add_node_id": cfg.get("if_add_node_id", "yes"),
            "if_add_node_summary": cfg.get("if_add_node_summary", "yes"),
            "if_add_doc_description": cfg.get("if_add_doc_description", "no"),
            "if_add_node_text": cfg.get("if_add_node_text", "no"),
        }
    }


@router.patch("")
async def update_config(request: Request):
    """Update configuration (partial update)."""
    body = await request.json()

    # Update LLM settings
    llm = body.get("llm", {})
    if "api_key" in llm and llm["api_key"]:
        set_key(str(ENV_PATH), "CHATGPT_API_KEY", llm["api_key"])
    if "api_base_url" in llm:
        set_key(str(ENV_PATH), "API_BASE_URL", llm["api_base_url"])

    # Update config.yaml (store with litellm provider prefix)
    cfg = _read_config_yaml()
    if "model" in llm:
        cfg["model"] = _ensure_provider_prefix(llm["model"])

    processing = body.get("processing", {})
    for key in ["toc_check_page_num", "max_page_num_each_node", "max_token_num_each_node",
                "if_add_node_id", "if_add_node_summary", "if_add_doc_description", "if_add_node_text"]:
        if key in processing:
            cfg[key] = processing[key]

    _write_config_yaml(cfg)

    # Reload env
    _load_env()

    return await get_config()


@router.post("/test-connection")
async def test_connection(request: Request):
    """Test the LLM API connection."""
    body = await request.json()

    api_key = body.get("api_key", os.getenv("CHATGPT_API_KEY", ""))
    base_url = body.get("api_base_url", os.getenv("API_BASE_URL", "https://api.deepseek.com"))
    # Strip litellm provider prefix for direct AsyncOpenAI call
    model = _strip_provider_prefix(body.get("model", "deepseek-v4-flash"))

    if not api_key:
        return {"success": False, "error": "API Key 未设置"}
    if "XXXX" in api_key or api_key.startswith("sk-XXX"):
        return {"success": False, "error": "API Key 是占位符，请填入有效的 DeepSeek API Key"}

    # Normalize base URL: DeepSeek API requires /v1 prefix for OpenAI-compatible endpoints
    base_url = base_url.rstrip("/")
    if not base_url.endswith("/v1"):
        base_url = base_url + "/v1"

    try:
        from openai import AsyncOpenAI
        import time

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        start = time.time()
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hello, respond with just 'OK'."}],
            max_tokens=10,
            timeout=15,
        )
        latency = int((time.time() - start) * 1000)

        return {
            "success": True,
            "latency_ms": latency,
            "model_name": model,
            "response": response.choices[0].message.content,
        }
    except Exception as e:
        error_detail = str(e)
        status_code = getattr(e, "status_code", None) or getattr(getattr(e, "response", None), "status_code", None)
        if status_code:
            error_detail = f"HTTP {status_code}: {error_detail}"
        return {"success": False, "error": error_detail}
