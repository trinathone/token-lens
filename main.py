from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
import math
from typing import Optional, Any

app = FastAPI()

# cache_read_multiplier: fraction of input_per_1m charged for cached reads (None = no cache pricing)
# cache_write_multiplier: fraction of input_per_1m charged for cache writes (None = same as regular input)
MODEL_PRICING = {
    # OpenAI
    "gpt-4o":           {"name": "GPT-4o",               "provider": "OpenAI",     "input_per_1m": 2.50,   "output_per_1m": 10.00,  "cache_read_multiplier": 0.50,  "cache_write_multiplier": None},
    "gpt-4o-mini":      {"name": "GPT-4o Mini",          "provider": "OpenAI",     "input_per_1m": 0.15,   "output_per_1m": 0.60,   "cache_read_multiplier": 0.50,  "cache_write_multiplier": None},
    "gpt-4-1":          {"name": "GPT-4.1",              "provider": "OpenAI",     "input_per_1m": 2.00,   "output_per_1m": 8.00,   "cache_read_multiplier": 0.25,  "cache_write_multiplier": None},
    "gpt-4-1-mini":     {"name": "GPT-4.1 Mini",         "provider": "OpenAI",     "input_per_1m": 0.40,   "output_per_1m": 1.60,   "cache_read_multiplier": 0.25,  "cache_write_multiplier": None},
    "o4-mini":          {"name": "o4-mini",              "provider": "OpenAI",     "input_per_1m": 1.10,   "output_per_1m": 4.40,   "cache_read_multiplier": 0.275, "cache_write_multiplier": None},
    "o3":               {"name": "o3",                   "provider": "OpenAI",     "input_per_1m": 10.00,  "output_per_1m": 40.00,  "cache_read_multiplier": 0.25,  "cache_write_multiplier": None},
    # Anthropic — cache write = 1.25x input, cache read = 0.10x input
    "claude-opus-4":    {"name": "Claude Opus 4",        "provider": "Anthropic",  "input_per_1m": 15.00,  "output_per_1m": 75.00,  "cache_read_multiplier": 0.10,  "cache_write_multiplier": 1.25},
    "claude-sonnet-4-5":{"name": "Claude Sonnet 4.5",   "provider": "Anthropic",  "input_per_1m": 3.00,   "output_per_1m": 15.00,  "cache_read_multiplier": 0.10,  "cache_write_multiplier": 1.25},
    "claude-sonnet-4":  {"name": "Claude Sonnet 4",      "provider": "Anthropic",  "input_per_1m": 3.00,   "output_per_1m": 15.00,  "cache_read_multiplier": 0.10,  "cache_write_multiplier": 1.25},
    "claude-haiku-3":   {"name": "Claude Haiku 3.5",     "provider": "Anthropic",  "input_per_1m": 0.80,   "output_per_1m": 4.00,   "cache_read_multiplier": 0.10,  "cache_write_multiplier": 1.25},
    # Google — cache read = 0.25x input
    "gemini-2-5-pro":   {"name": "Gemini 2.5 Pro",       "provider": "Google",     "input_per_1m": 1.25,   "output_per_1m": 10.00,  "cache_read_multiplier": 0.25,  "cache_write_multiplier": None},
    "gemini-2-5-flash": {"name": "Gemini 2.5 Flash",     "provider": "Google",     "input_per_1m": 0.15,   "output_per_1m": 0.60,   "cache_read_multiplier": 0.25,  "cache_write_multiplier": None},
    "gemini-2-flash":   {"name": "Gemini 2.0 Flash",     "provider": "Google",     "input_per_1m": 0.075,  "output_per_1m": 0.30,   "cache_read_multiplier": 0.25,  "cache_write_multiplier": None},
    "gemini-1-5-pro":   {"name": "Gemini 1.5 Pro",       "provider": "Google",     "input_per_1m": 1.25,   "output_per_1m": 5.00,   "cache_read_multiplier": 0.25,  "cache_write_multiplier": None},
    # DeepSeek
    "deepseek-v3-0324": {"name": "DeepSeek V3 0324",     "provider": "DeepSeek",   "input_per_1m": 0.27,   "output_per_1m": 1.10,   "cache_read_multiplier": 0.07,  "cache_write_multiplier": None},
    "deepseek-v3":      {"name": "DeepSeek V3",          "provider": "DeepSeek",   "input_per_1m": 0.27,   "output_per_1m": 1.10,   "cache_read_multiplier": 0.07,  "cache_write_multiplier": None},
    "deepseek-r1":      {"name": "DeepSeek R1",          "provider": "DeepSeek",   "input_per_1m": 0.55,   "output_per_1m": 2.19,   "cache_read_multiplier": 0.14,  "cache_write_multiplier": None},
    # Others
    "llama-3-3-70b":    {"name": "Llama 3.3 70B",        "provider": "Meta/OR",    "input_per_1m": 0.59,   "output_per_1m": 0.79,   "cache_read_multiplier": None,  "cache_write_multiplier": None},
    "mistral-large":    {"name": "Mistral Large 2",      "provider": "Mistral",    "input_per_1m": 2.00,   "output_per_1m": 6.00,   "cache_read_multiplier": None,  "cache_write_multiplier": None},
    "qwen3-235b":       {"name": "Qwen3 235B",           "provider": "Alibaba",    "input_per_1m": 0.50,   "output_per_1m": 1.50,   "cache_read_multiplier": None,  "cache_write_multiplier": None},
    "nova-pro":         {"name": "Amazon Nova Pro",      "provider": "AWS",        "input_per_1m": 0.80,   "output_per_1m": 3.20,   "cache_read_multiplier": None,  "cache_write_multiplier": None},
    "nova-lite":        {"name": "Amazon Nova Lite",     "provider": "AWS",        "input_per_1m": 0.06,   "output_per_1m": 0.24,   "cache_read_multiplier": None,  "cache_write_multiplier": None},
    "nova-micro":       {"name": "Amazon Nova Micro",    "provider": "AWS",        "input_per_1m": 0.035,  "output_per_1m": 0.14,   "cache_read_multiplier": None,  "cache_write_multiplier": None},
    # New 2025 models
    "gpt-4-1-nano":          {"name": "GPT-4.1 Nano",              "provider": "OpenAI",     "input_per_1m": 0.10,   "output_per_1m": 0.40,   "cache_read_multiplier": 0.25,  "cache_write_multiplier": None},
    "claude-sonnet-4-6":     {"name": "Claude Sonnet 4.6",         "provider": "Anthropic",  "input_per_1m": 3.00,   "output_per_1m": 15.00,  "cache_read_multiplier": 0.10,  "cache_write_multiplier": 1.25},
    "claude-opus-4-5":       {"name": "Claude Opus 4.5",           "provider": "Anthropic",  "input_per_1m": 15.00,  "output_per_1m": 75.00,  "cache_read_multiplier": 0.10,  "cache_write_multiplier": 1.25},
    "llama-4-scout":         {"name": "Llama 4 Scout",             "provider": "Meta/OR",    "input_per_1m": 0.11,   "output_per_1m": 0.34,   "cache_read_multiplier": None,  "cache_write_multiplier": None},
    "llama-4-maverick":      {"name": "Llama 4 Maverick",          "provider": "Meta/OR",    "input_per_1m": 0.50,   "output_per_1m": 0.77,   "cache_read_multiplier": None,  "cache_write_multiplier": None},
    "gemini-2-5-flash-lite": {"name": "Gemini 2.5 Flash-Lite",     "provider": "Google",     "input_per_1m": 0.10,   "output_per_1m": 0.40,   "cache_read_multiplier": 0.25,  "cache_write_multiplier": None},
    # OpenAI reasoning
    "o1":                    {"name": "o1",                         "provider": "OpenAI",     "input_per_1m": 15.00,  "output_per_1m": 60.00,  "cache_read_multiplier": 0.50,  "cache_write_multiplier": None},
    "o1-mini":               {"name": "o1-mini",                    "provider": "OpenAI",     "input_per_1m": 1.10,   "output_per_1m": 4.40,   "cache_read_multiplier": 0.50,  "cache_write_multiplier": None},
    "o3-mini":               {"name": "o3-mini",                    "provider": "OpenAI",     "input_per_1m": 1.10,   "output_per_1m": 4.40,   "cache_read_multiplier": 0.55,  "cache_write_multiplier": None},
    # OpenAI GPT-4.5
    "gpt-4-5":               {"name": "GPT-4.5",                    "provider": "OpenAI",     "input_per_1m": 75.00,  "output_per_1m": 150.00, "cache_read_multiplier": 0.50,  "cache_write_multiplier": None},
    # xAI Grok
    "grok-3":                {"name": "Grok 3",                     "provider": "xAI",        "input_per_1m": 3.00,   "output_per_1m": 15.00,  "cache_read_multiplier": None,  "cache_write_multiplier": None},
    "grok-3-mini":           {"name": "Grok 3 Mini",                "provider": "xAI",        "input_per_1m": 0.30,   "output_per_1m": 0.50,   "cache_read_multiplier": None,  "cache_write_multiplier": None},
    "grok-2":                {"name": "Grok 2",                     "provider": "xAI",        "input_per_1m": 2.00,   "output_per_1m": 10.00,  "cache_read_multiplier": None,  "cache_write_multiplier": None},
    # DeepSeek updated
    "deepseek-r1-0528":      {"name": "DeepSeek R1 0528",           "provider": "DeepSeek",   "input_per_1m": 0.55,   "output_per_1m": 2.19,   "cache_read_multiplier": 0.14,  "cache_write_multiplier": None},
    # Anthropic Claude 3.5 Sonnet (classic)
    "claude-3-5-sonnet":     {"name": "Claude 3.5 Sonnet",          "provider": "Anthropic",  "input_per_1m": 3.00,   "output_per_1m": 15.00,  "cache_read_multiplier": 0.10,  "cache_write_multiplier": 1.25},
}

class AnalyzeRequest(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    model: str
    cache_read_tokens: Optional[int] = 0
    cache_write_tokens: Optional[int] = 0
    raw_response: Optional[str] = None

class ParseRequest(BaseModel):
    raw_json: str

@app.get("/health")
async def health():
    return {"status": "ok", "service": "token-lens"}

@app.get("/models")
async def get_models():
    models = []
    for model_id, pricing in MODEL_PRICING.items():
        models.append({
            "id": model_id,
            "name": pricing["name"],
            "provider": pricing["provider"],
            "input_per_1m": pricing["input_per_1m"],
            "output_per_1m": pricing["output_per_1m"],
        })
    return {"models": models}

# Maps common model name substrings (from API responses) to token-lens model IDs
# Order matters — more specific keys must come before shorter ones
MODEL_NAME_MAP = {
    # More specific keys MUST precede shorter prefixes they'd shadow
    "gpt-4o-mini": "gpt-4o-mini",
    "gpt-4.1-nano": "gpt-4-1-nano",
    "gpt-4.1-mini": "gpt-4-1-mini",
    "gpt-4.1": "gpt-4-1",
    "gpt-4o": "gpt-4o",
    "o4-mini": "o4-mini",
    "o3-mini": "o3-mini",  # must precede "o3"
    "o3": "o3",
    "claude-opus-4-5": "claude-opus-4-5",
    "claude-opus-4": "claude-opus-4",
    "claude-sonnet-4-6": "claude-sonnet-4-6",
    "claude-sonnet-4.6": "claude-sonnet-4-6",  # Bedrock variant
    "claude-sonnet-4-5": "claude-sonnet-4-5",
    "claude-sonnet-4.5": "claude-sonnet-4-5",  # Bedrock variant
    "claude-sonnet-4": "claude-sonnet-4",
    "claude-3-5-haiku": "claude-haiku-3",
    "claude-haiku": "claude-haiku-3",
    "gemini-2.5-flash-lite": "gemini-2-5-flash-lite",
    "gemini-2.5-pro": "gemini-2-5-pro",
    "gemini-2.5-flash": "gemini-2-5-flash",
    "gemini-2.0-flash": "gemini-2-flash",
    "gemini-1.5-pro": "gemini-1-5-pro",
    "deepseek-v3-0324": "deepseek-v3-0324",
    "deepseek-r1-0528": "deepseek-r1-0528",  # must precede "deepseek-r1"
    "deepseek-r1": "deepseek-r1",
    "deepseek-v3": "deepseek-v3",
    "llama-4-maverick": "llama-4-maverick",
    "llama-4-scout": "llama-4-scout",
    "llama-3.3-70b": "llama-3-3-70b",
    "mistral-large": "mistral-large",
    "qwen3-235b": "qwen3-235b",
    "nova-pro": "nova-pro",
    "nova-lite": "nova-lite",
    "nova-micro": "nova-micro",
    # xAI Grok
    "grok-3-mini": "grok-3-mini",
    "grok-3": "grok-3",
    "grok-2": "grok-2",
    # OpenAI o1 — more specific BEFORE shorter keys
    "o1-mini": "o1-mini",
    "o1": "o1",
    # OpenAI GPT-4.5
    "gpt-4.5": "gpt-4-5",
    "gpt-4-5": "gpt-4-5",
    # Anthropic Claude 3.5 Sonnet classic
    "claude-3-5-sonnet": "claude-3-5-sonnet",
    "claude-3.5-sonnet": "claude-3-5-sonnet",
}

def _resolve_model(raw_model: Optional[str]) -> str:
    """Map a raw model string from an API response to a token-lens model ID.

    Handles:
    - Standard model names: 'gpt-4o', 'claude-sonnet-4-6'
    - Bedrock cross-region IDs: 'us.anthropic.claude-sonnet-4-6-20250717-v1:0'
    - Versioned model IDs: 'claude-3-5-haiku-20241022'
    """
    if not raw_model:
        return "gpt-4o"
    lower = raw_model.lower()
    # Strip Bedrock cross-region prefix (us., eu., ap.) and provider namespace
    # e.g. "us.anthropic.claude-sonnet-4-6-20250717-v1:0" -> "claude-sonnet-4-6-20250717-v1:0"
    stripped_bedrock = False
    for prefix in ("us.", "eu.", "ap."):
        if lower.startswith(prefix):
            lower = lower[len(prefix):]
            stripped_bedrock = True
            break
    # Only strip provider namespace (e.g. "anthropic.claude-...") when a Bedrock prefix was removed
    if stripped_bedrock and "." in lower:
        lower = lower.split(".", 1)[1]
    for key, model_id in MODEL_NAME_MAP.items():
        if key in lower:
            return model_id
    return "gpt-4o"

@app.post("/parse-response")
async def parse_response(request: ParseRequest):
    try:
        data = json.loads(request.raw_json)
        usage = data.get("usage", {})

        # OpenAI format: prompt_tokens / completion_tokens
        # Anthropic format: input_tokens / output_tokens
        prompt_tokens = (
            usage.get("prompt_tokens")
            or usage.get("input_tokens")
            or 0
        )
        completion_tokens = (
            usage.get("completion_tokens")
            or usage.get("output_tokens")
            or 0
        )

        # Cache tokens — OpenAI: prompt_tokens_details.cached_tokens
        # Anthropic: cache_read_input_tokens / cache_creation_input_tokens
        cache_read_tokens = (
            (usage.get("prompt_tokens_details") or {}).get("cached_tokens")
            or usage.get("cache_read_input_tokens")
            or 0
        )
        cache_write_tokens = usage.get("cache_creation_input_tokens") or 0

        # Extract model from response JSON if present
        raw_model = data.get("model")
        resolved_model = _resolve_model(raw_model)

        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cache_read_tokens": cache_read_tokens,
            "cache_write_tokens": cache_write_tokens,
            "model": resolved_model,
            "raw_model": raw_model,
            "found": prompt_tokens > 0 or completion_tokens > 0
        }
    except (json.JSONDecodeError, KeyError):
        raise HTTPException(status_code=400, detail="Invalid JSON format")

@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    if request.model not in MODEL_PRICING:
        raise HTTPException(status_code=400, detail=f"Model '{request.model}' not found")

    pricing = MODEL_PRICING[request.model]
    input_cost = (request.prompt_tokens / 1_000_000) * pricing["input_per_1m"]
    output_cost = (request.completion_tokens / 1_000_000) * pricing["output_per_1m"]

    # Cache costs
    cache_read_cost = 0.0
    cache_write_cost = 0.0
    cache_read_tokens = request.cache_read_tokens or 0
    cache_write_tokens = request.cache_write_tokens or 0
    if cache_read_tokens and pricing.get("cache_read_multiplier") is not None:
        cache_read_cost = (cache_read_tokens / 1_000_000) * pricing["input_per_1m"] * pricing["cache_read_multiplier"]
    if cache_write_tokens:
        write_mult = pricing.get("cache_write_multiplier") or 1.0
        cache_write_cost = (cache_write_tokens / 1_000_000) * pricing["input_per_1m"] * write_mult

    total_cost = input_cost + output_cost + cache_read_cost + cache_write_cost

    comparison = []
    for model_id, model_pricing in MODEL_PRICING.items():
        model_input_cost = (request.prompt_tokens / 1_000_000) * model_pricing["input_per_1m"]
        model_output_cost = (request.completion_tokens / 1_000_000) * model_pricing["output_per_1m"]

        m_cache_read_cost = 0.0
        m_cache_write_cost = 0.0
        if cache_read_tokens and model_pricing.get("cache_read_multiplier") is not None:
            m_cache_read_cost = (cache_read_tokens / 1_000_000) * model_pricing["input_per_1m"] * model_pricing["cache_read_multiplier"]
        if cache_write_tokens:
            w_mult = model_pricing.get("cache_write_multiplier") or 1.0
            m_cache_write_cost = (cache_write_tokens / 1_000_000) * model_pricing["input_per_1m"] * w_mult

        model_total_cost = model_input_cost + model_output_cost + m_cache_read_cost + m_cache_write_cost

        if total_cost > 0:
            cheaper_by_pct = round(((total_cost - model_total_cost) / total_cost) * 100)
        else:
            cheaper_by_pct = 0

        total_tokens = request.prompt_tokens + request.completion_tokens
        tokens_per_dollar = round(total_tokens / model_total_cost) if model_total_cost > 0 else 0

        comparison.append({
            "model": model_id,
            "name": model_pricing["name"],
            "provider": model_pricing["provider"],
            "prompt_cost_usd": round(model_input_cost, 6),
            "completion_cost_usd": round(model_output_cost, 6),
            "cache_read_cost_usd": round(m_cache_read_cost, 6),
            "cache_write_cost_usd": round(m_cache_write_cost, 6),
            "total_cost_usd": round(model_total_cost, 6),
            "cheaper_by_pct": cheaper_by_pct,
            "tokens_per_dollar": tokens_per_dollar
        })

    comparison.sort(key=lambda x: x["total_cost_usd"])
    cheapest = comparison[0]["model"] if comparison else request.model

    if total_cost > 0:
        savings_vs_current_pct = round(((total_cost - comparison[0]["total_cost_usd"]) / total_cost) * 100)
    else:
        savings_vs_current_pct = 0

    monthly_projection = {
        "calls_1000": round(total_cost * 1000, 2),
        "calls_10000": round(total_cost * 10000, 2),
        "calls_100000": round(total_cost * 100000, 2),
    }

    return {
        "input": {
            "prompt_tokens": request.prompt_tokens,
            "completion_tokens": request.completion_tokens,
            "cache_read_tokens": cache_read_tokens,
            "cache_write_tokens": cache_write_tokens,
        },
        "current_model": {
            "name": pricing["name"],
            "cost_usd": round(total_cost, 6),
            "prompt_cost_usd": round(input_cost, 6),
            "completion_cost_usd": round(output_cost, 6),
            "cache_read_cost_usd": round(cache_read_cost, 6),
            "cache_write_cost_usd": round(cache_write_cost, 6),
        },
        "comparison": comparison,
        "cheapest": cheapest,
        "savings_vs_current": f"{savings_vs_current_pct}%",
        "monthly_projection": monthly_projection,
    }

class BatchItem(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    model: str
    cache_read_tokens: Optional[int] = 0
    cache_write_tokens: Optional[int] = 0
    label: Optional[str] = None  # optional tag e.g. "summarize-call", "classify-call"

class BatchRequest(BaseModel):
    calls: list[BatchItem]

@app.post("/batch")
async def batch_analyze(request: BatchRequest):
    """Analyze multiple LLM calls at once. Returns per-call breakdown + aggregate totals."""
    if not request.calls:
        raise HTTPException(status_code=400, detail="No calls provided")
    if len(request.calls) > 500:
        raise HTTPException(status_code=400, detail="Max 500 calls per batch")

    results = []
    aggregate_total_usd = 0.0
    aggregate_prompt_tokens = 0
    aggregate_completion_tokens = 0
    per_model_spend: dict[str, float] = {}

    for i, call in enumerate(request.calls):
        if call.model not in MODEL_PRICING:
            raise HTTPException(status_code=400, detail=f"Call {i}: model '{call.model}' not found")

        pricing = MODEL_PRICING[call.model]
        input_cost = (call.prompt_tokens / 1_000_000) * pricing["input_per_1m"]
        output_cost = (call.completion_tokens / 1_000_000) * pricing["output_per_1m"]

        cache_read_tokens = call.cache_read_tokens or 0
        cache_write_tokens = call.cache_write_tokens or 0
        cache_read_cost = 0.0
        cache_write_cost = 0.0
        if cache_read_tokens and pricing.get("cache_read_multiplier") is not None:
            cache_read_cost = (cache_read_tokens / 1_000_000) * pricing["input_per_1m"] * pricing["cache_read_multiplier"]
        if cache_write_tokens:
            write_mult = pricing.get("cache_write_multiplier") or 1.0
            cache_write_cost = (cache_write_tokens / 1_000_000) * pricing["input_per_1m"] * write_mult

        call_total = input_cost + output_cost + cache_read_cost + cache_write_cost

        results.append({
            "index": i,
            "label": call.label or f"call_{i}",
            "model": call.model,
            "model_name": pricing["name"],
            "prompt_tokens": call.prompt_tokens,
            "completion_tokens": call.completion_tokens,
            "cache_read_tokens": cache_read_tokens,
            "cache_write_tokens": cache_write_tokens,
            "cost_usd": round(call_total, 6),
        })

        aggregate_total_usd += call_total
        aggregate_prompt_tokens += call.prompt_tokens
        aggregate_completion_tokens += call.completion_tokens
        per_model_spend[call.model] = per_model_spend.get(call.model, 0.0) + call_total

    # Sort per-model spend descending so biggest spenders surface first
    sorted_model_spend = sorted(
        [{"model": k, "name": MODEL_PRICING[k]["name"], "total_usd": round(v, 6)} for k, v in per_model_spend.items()],
        key=lambda x: x["total_usd"],
        reverse=True,
    )

    # What would this batch cost on the cheapest available model?
    # Use gemini-2-flash as reference (cheapest in pricing table)
    cheapest_model_id = min(MODEL_PRICING, key=lambda m: MODEL_PRICING[m]["input_per_1m"] + MODEL_PRICING[m]["output_per_1m"])
    cheapest_pricing = MODEL_PRICING[cheapest_model_id]
    cheapest_batch_cost = (
        (aggregate_prompt_tokens / 1_000_000) * cheapest_pricing["input_per_1m"]
        + (aggregate_completion_tokens / 1_000_000) * cheapest_pricing["output_per_1m"]
    )
    potential_savings_usd = round(aggregate_total_usd - cheapest_batch_cost, 6)
    potential_savings_pct = round((potential_savings_usd / aggregate_total_usd) * 100) if aggregate_total_usd > 0 else 0

    return {
        "calls": results,
        "aggregate": {
            "total_calls": len(results),
            "total_cost_usd": round(aggregate_total_usd, 6),
            "total_prompt_tokens": aggregate_prompt_tokens,
            "total_completion_tokens": aggregate_completion_tokens,
            "per_model_spend": sorted_model_spend,
            "potential_savings_usd": potential_savings_usd,
            "potential_savings_pct": f"{potential_savings_pct}%",
            "cheapest_alternative_model": cheapest_model_id,
            "cheapest_alternative_name": cheapest_pricing["name"],
        },
    }


class ExplainRequest(BaseModel):
    current_model: dict
    cheapest: str
    savings_vs_current: str

@app.post("/explain")
async def explain_cost(analysis: ExplainRequest):
    try:
        from keys.api_keys import NVIDIA_NIM_KEY
    except ImportError:
        raise HTTPException(status_code=500, detail="NVIDIA NIM key not configured")

    import httpx

    prompt = f"""Summarize this token cost analysis in 2 sentences, plain English.

Current model: {analysis.current_model.get('name', 'unknown')}
Current cost: ${analysis.current_model.get('cost_usd', 0)}
Cheapest alternative: {analysis.cheapest}
Savings: {analysis.savings_vs_current}

Keep it simple and actionable."""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {NVIDIA_NIM_KEY}"},
            json={
                "model": "meta/llama-3.3-70b-instruct",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 100,
            },
            timeout=10.0
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="NIM API error")

        data = response.json()
        summary = data["choices"][0]["message"]["content"]
        return {"summary": summary}

@app.get("/cheapest")
async def cheapest_models(
    prompt_tokens: int = 1000,
    completion_tokens: int = 500,
    top_n: int = 5,
):
    """Return the top N cheapest models for a given token count (defaults: 1K prompt, 500 completion, top 5)."""
    results = []
    for model_id, pricing in MODEL_PRICING.items():
        cost = (
            (prompt_tokens / 1_000_000) * pricing["input_per_1m"]
            + (completion_tokens / 1_000_000) * pricing["output_per_1m"]
        )
        results.append({
            "model": model_id,
            "name": pricing["name"],
            "provider": pricing["provider"],
            "cost_usd": round(cost, 8),
            "input_per_1m": pricing["input_per_1m"],
            "output_per_1m": pricing["output_per_1m"],
        })
    results.sort(key=lambda x: x["cost_usd"])
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "top_n": top_n,
        "cheapest": results[:top_n],
    }

app.mount("/", StaticFiles(directory="static", html=True), name="static")
