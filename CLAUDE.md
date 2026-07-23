# CLAUDE.md — token-lens

## What it is
A single-page tool where you paste any LLM API response (or describe your usage) and instantly see the token cost breakdown + what it would cost across 10+ major models side by side.

## Why it exists
HN "Ask HN: How are you controlling Token Costs?" — devs are flying blind on LLM spend. No easy way to paste an API response and say "how much did that cost across models?" You have to manually look up pricing per model, do math, repeat. Engineers waste time and burn budget without visibility.

Real evidence:
- HN thread: "Ask HN: How are you controlling Token Costs?" (multiple replies)
- LiteLLM GitHub: "DeepSeek V4 reasoning_content stripped in multi-turn" (25 reactions)
- LiteLLM GitHub: Dark Mode request (68 reactions — devs live in this tool constantly)

## Stack
- FastAPI + Python 3.11
- Single-page HTML UI (no frameworks, vanilla JS)
- Dark theme: background #0d1117, card #161b22, accent #58a6ff, green #3fb950, border #30363d
- Port: 8008

## File Structure
```
token-lens/
├── main.py
├── requirements.txt
├── static/
│   └── index.html
├── README.md
└── CLAUDE.md
```

## API Endpoints

### GET /health
Returns: `{"status": "ok", "service": "token-lens"}`

### POST /analyze
Analyze token cost from raw usage data.

Request body:
```json
{
  "prompt_tokens": 1234,
  "completion_tokens": 567,
  "model": "gpt-4o",
  "raw_response": ""  // optional — if provided, parse usage from it
}
```

Response:
```json
{
  "input": {
    "prompt_tokens": 1234,
    "completion_tokens": 567
  },
  "current_model": {
    "name": "gpt-4o",
    "cost_usd": 0.0185,
    "prompt_cost_usd": 0.0062,
    "completion_cost_usd": 0.0113
  },
  "comparison": [
    {
      "model": "gpt-4o",
      "provider": "OpenAI",
      "prompt_cost_usd": 0.0062,
      "completion_cost_usd": 0.0113,
      "total_cost_usd": 0.0175,
      "cheaper_by_pct": 0,
      "tokens_per_dollar": 47000
    }
    // ... more models
  ],
  "cheapest": "deepseek-v3",
  "savings_vs_current": "82%",
  "monthly_projection": {
    "calls_1000": 0.185,
    "calls_10000": 1.85,
    "calls_100000": 18.5
  }
}
```

### POST /parse-response
Parse token counts from a raw OpenAI-format JSON response string.

Request body:
```json
{
  "raw_json": "{\"usage\": {\"prompt_tokens\": 100, \"completion_tokens\": 50}}"
}
```

Response:
```json
{
  "prompt_tokens": 100,
  "completion_tokens": 50,
  "model": "gpt-4o",
  "found": true
}
```

### GET /models
Returns all supported models and their pricing.

Response:
```json
{
  "models": [
    {
      "id": "gpt-4o",
      "name": "GPT-4o",
      "provider": "OpenAI",
      "input_per_1m": 5.0,
      "output_per_1m": 15.0
    }
  ]
}
```

## Pricing Data (hardcoded, as of July 2026)

Build this as a dict in main.py (no API calls during build):

```python
MODEL_PRICING = {
    "gpt-4o":          {"name": "GPT-4o",               "provider": "OpenAI",     "input_per_1m": 5.00,   "output_per_1m": 15.00},
    "gpt-4o-mini":     {"name": "GPT-4o Mini",           "provider": "OpenAI",     "input_per_1m": 0.15,   "output_per_1m": 0.60},
    "gpt-4.1":         {"name": "GPT-4.1",               "provider": "OpenAI",     "input_per_1m": 2.00,   "output_per_1m": 8.00},
    "gpt-4.1-mini":    {"name": "GPT-4.1 Mini",          "provider": "OpenAI",     "input_per_1m": 0.40,   "output_per_1m": 1.60},
    "claude-sonnet-4": {"name": "Claude Sonnet 4",       "provider": "Anthropic",  "input_per_1m": 3.00,   "output_per_1m": 15.00},
    "claude-haiku-3":  {"name": "Claude Haiku 3.5",      "provider": "Anthropic",  "input_per_1m": 0.80,   "output_per_1m": 4.00},
    "gemini-2.0-flash":{"name": "Gemini 2.0 Flash",      "provider": "Google",     "input_per_1m": 0.075,  "output_per_1m": 0.30},
    "gemini-1.5-pro":  {"name": "Gemini 1.5 Pro",        "provider": "Google",     "input_per_1m": 1.25,   "output_per_1m": 5.00},
    "deepseek-v3":     {"name": "DeepSeek V3",           "provider": "DeepSeek",   "input_per_1m": 0.27,   "output_per_1m": 1.10},
    "deepseek-r1":     {"name": "DeepSeek R1",           "provider": "DeepSeek",   "input_per_1m": 0.55,   "output_per_1m": 2.19},
    "llama-3.3-70b":   {"name": "Llama 3.3 70B",         "provider": "Meta/OR",    "input_per_1m": 0.59,   "output_per_1m": 0.79},
    "mistral-large":   {"name": "Mistral Large 2",       "provider": "Mistral",    "input_per_1m": 2.00,   "output_per_1m": 6.00},
    "qwen3-235b":      {"name": "Qwen3 235B",            "provider": "Alibaba",    "input_per_1m": 0.50,   "output_per_1m": 1.50},
    "nova-pro":        {"name": "Amazon Nova Pro",       "provider": "AWS",        "input_per_1m": 0.80,   "output_per_1m": 3.20},
}
```

## UI Design

Single HTML page. No React. Vanilla JS only.

Layout (dark theme #0d1117):
```
┌─────────────────────────────────────────────┐
│  🔍 token-lens                               │
│  see what your LLM calls actually cost       │
├─────────────────────────────────────────────┤
│  PASTE API RESPONSE  [textarea]              │
│  — OR manually enter —                      │
│  Prompt tokens: [____]  Model: [dropdown]   │
│  Completion tokens: [____]                  │
│  [  ANALYZE COST  ]                         │
├─────────────────────────────────────────────┤
│  RESULTS PANEL (shows after analyze):        │
│                                             │
│  This call: $0.0185  (GPT-4o)               │
│  Cheapest alternative: DeepSeek V3 $0.0032  │
│  You'd save 82% per call                    │
│                                             │
│  Monthly projection:                        │
│  1K calls/mo → $18.50 | $3.20 (cheapest)   │
│  10K calls/mo → $185  | $32                 │
│                                             │
│  MODEL COMPARISON TABLE:                    │
│  Model          | Provider  | Cost   | vs   │
│  GPT-4o         | OpenAI    | $0.018 | —    │
│  DeepSeek V3    | DeepSeek  | $0.003 | -82% │
│  Gemini Flash   | Google    | $0.002 | -88% │
│  ...            |           |        |      │
│  (sorted by cost, cheapest first)           │
│                                             │
│  Token breakdown:                           │
│  Prompt: 1234 tokens × $5/1M = $0.0062     │
│  Completion: 567 tokens × $15/1M = $0.0085 │
└─────────────────────────────────────────────┘
```

Color coding:
- Green (#3fb950) = cheaper than current
- Red (#f85149) = more expensive
- Yellow (#e3b341) = within 20% of current

Features:
1. Paste raw JSON into textarea → auto-parse usage fields → fill in token counts
2. Manual entry fallback (prompt + completion + model dropdown)
3. Model comparison table sorted by cost (cheapest first)
4. Monthly projection (1K / 10K / 100K calls)
5. Copy token counts button
6. "What if I switch?" — click any model row to see projected monthly savings vs current

The table rows are clickable: clicking a model row shows an inline "savings calculator" below that row: "At X calls/mo, switching from GPT-4o → DeepSeek V3 saves $Y/mo"

## NVIDIA NIM Usage
This project does NOT need NIM for the core functionality (it's pure math on pricing data). 

However, add one optional endpoint: POST /explain which takes the analysis result and returns a plain-English summary. Use NIM inside the function only:

```python
async def explain_cost(analysis: dict):
    from keys.api_keys import NVIDIA_NIM_KEY  # import inside function only
    # Use nim_api_key with openai client pointed at https://integrate.api.nvidia.com/v1
    # Model: meta/llama-3.3-70b-instruct
    # Prompt: summarize the cost analysis in 2 sentences, plain English
```

## Rules
- DO NOT start the server
- DO NOT make any real API calls during build
- Syntax check must pass: `python3 -m py_compile main.py`
- All imports at top of file EXCEPT api_keys imports (those go inside functions)
- requirements.txt must include: fastapi, uvicorn, httpx, pydantic
- static/index.html must exist and be complete
- README.md must exist
- No placeholder comments — all code must be real and complete
