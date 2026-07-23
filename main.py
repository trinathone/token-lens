from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
import math
from typing import Optional

app = FastAPI()

MODEL_PRICING = {
    "gpt-4o":          {"name": "GPT-4o",               "provider": "OpenAI",     "input_per_1m": 5.00,   "output_per_1m": 15.00},
    "gpt-4o-mini":     {"name": "GPT-4o Mini",          "provider": "OpenAI",     "input_per_1m": 0.15,   "output_per_1m": 0.60},
    "gpt-4-1":         {"name": "GPT-4.1",              "provider": "OpenAI",     "input_per_1m": 2.00,   "output_per_1m": 8.00},
    "gpt-4-mini":      {"name": "GPT-4.1 Mini",         "provider": "OpenAI",     "input_per_1m": 0.40,   "output_per_1m": 1.60},
    "claude-sonnet-4": {"name": "Claude Sonnet 4",      "provider": "Anthropic",  "input_per_1m": 3.00,   "output_per_1m": 15.00},
    "claude-haiku-3":  {"name": "Claude Haiku 3.5",     "provider": "Anthropic",  "input_per_1m": 0.80,   "output_per_1m": 4.00},
    "gemini-2-flash":  {"name": "Gemini 2.0 Flash",     "provider": "Google",     "input_per_1m": 0.075,  "output_per_1m": 0.30},
    "gemini-1-5-pro":  {"name": "Gemini 1.5 Pro",       "provider": "Google",     "input_per_1m": 1.25,   "output_per_1m": 5.00},
    "deepseek-v3":     {"name": "DeepSeek V3",          "provider": "DeepSeek",   "input_per_1m": 0.27,   "output_per_1m": 1.10},
    "deepseek-r1":     {"name": "DeepSeek R1",          "provider": "DeepSeek",   "input_per_1m": 0.55,   "output_per_1m": 2.19},
    "llama-3-3-70b":   {"name": "Llama 3.3 70B",        "provider": "Meta/OR",    "input_per_1m": 0.59,   "output_per_1m": 0.79},
    "mistral-large":   {"name": "Mistral Large 2",      "provider": "Mistral",    "input_per_1m": 2.00,   "output_per_1m": 6.00},
    "qwen3-235b":      {"name": "Qwen3 235B",           "provider": "Alibaba",    "input_per_1m": 0.50,   "output_per_1m": 1.50},
    "nova-pro":        {"name": "Amazon Nova Pro",      "provider": "AWS",        "input_per_1m": 0.80,   "output_per_1m": 3.20},
}

class AnalyzeRequest(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    model: str
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

@app.post("/parse-response")
async def parse_response(request: ParseRequest):
    try:
        data = json.loads(request.raw_json)
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "model": "gpt-4o",
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
    total_cost = input_cost + output_cost

    comparison = []
    for model_id, model_pricing in MODEL_PRICING.items():
        model_input_cost = (request.prompt_tokens / 1_000_000) * model_pricing["input_per_1m"]
        model_output_cost = (request.completion_tokens / 1_000_000) * model_pricing["output_per_1m"]
        model_total_cost = model_input_cost + model_output_cost

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
        },
        "current_model": {
            "name": pricing["name"],
            "cost_usd": round(total_cost, 6),
            "prompt_cost_usd": round(input_cost, 6),
            "completion_cost_usd": round(output_cost, 6),
        },
        "comparison": comparison,
        "cheapest": cheapest,
        "savings_vs_current": f"{savings_vs_current_pct}%",
        "monthly_projection": monthly_projection,
    }

@app.post("/explain")
async def explain_cost(analysis: dict):
    try:
        from keys.api_keys import NVIDIA_NIM_KEY
    except ImportError:
        raise HTTPException(status_code=500, detail="NVIDIA NIM key not configured")

    import httpx

    prompt = f"""Summarize this token cost analysis in 2 sentences, plain English.

Current model: {analysis['current_model']['name']}
Current cost: ${analysis['current_model']['cost_usd']}
Cheapest alternative: {analysis['cheapest']}
Savings: {analysis['savings_vs_current']}

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

app.mount("/", StaticFiles(directory="static", html=True), name="static")
