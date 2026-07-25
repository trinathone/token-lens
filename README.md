<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=180&section=header&text=TOKEN-LENS&fontSize=42&fontColor=fff&animation=twinkling&fontAlignY=32&desc=Paste%20any%20LLM%20response%20→%20see%20exact%20token%20cost%20across%2015%20models&descAlignY=55&descSize=14"/>

[![Live Demo](https://img.shields.io/badge/▶_Live_Demo-Visit_Now-6366f1?style=for-the-badge&logoColor=white)](https://token-lens-three.vercel.app)
[![GitHub Stars](https://img.shields.io/github/stars/trinathone/token-lens?style=for-the-badge&color=f59e0b)](https://github.com/trinathone/token-lens)
[![License](https://img.shields.io/badge/license-MIT-22c55e?style=for-the-badge)](LICENSE)

</div>

---

# token-lens

Ever finish a feature, look at your OpenAI bill, and have no idea which API call ate $40?

token-lens is a tiny tool that tells you exactly what any LLM call cost — and what it would have cost on every other major model.

## The problem it solves

You're building with GPT-4o. You paste a system prompt, get a response. Was that call 5 cents? 50 cents? You have no idea without opening a spreadsheet, looking up the pricing page, doing the math yourself. And you definitely don't know that the same call on Gemini 2.0 Flash would've cost 97% less.

token-lens does that math instantly. Paste the raw API response JSON, or just type in token counts manually, and it shows you a full breakdown.

## Real use cases

1. You shipped a feature last night and want to know if the LLM calls are going to be affordable at scale. Paste a sample response, see monthly cost at 10K calls/month.

2. Your team is using GPT-4o but someone suggests switching to Claude or DeepSeek. Paste a real call, see the exact savings side by side.

3. You're building a cost budget for a client. Enter estimated token counts, screenshot the comparison table for the proposal.

4. You notice your bill spiked this month. Paste recent API responses to find which model/call type is the culprit.

## How it works

1. Paste your raw API response JSON into the box (or just type prompt/completion token counts)
2. Hit Analyze
3. See the cost for that call on your current model
4. See a table of 15 models sorted cheapest first, with % savings vs your current model
5. See monthly projections at 1K / 10K / 100K calls
6. Click any row to see: "switching from GPT-4o to DeepSeek V3 saves $X/month at Y calls/mo"

## Quick start

```bash
git clone https://github.com/trinathone/token-lens
cd token-lens
pip install -r requirements.txt
uvicorn main:app --port 8008
# open http://localhost:8008
```

## API

- `GET /health` — health check
- `GET /models` — all supported models + pricing
- `POST /analyze` — cost breakdown + comparison (pass prompt_tokens, completion_tokens, model)
- `POST /parse-response` — extract token counts from raw JSON string
- `POST /explain` — plain-English summary via LLM (optional, needs NVIDIA NIM key)

## Models covered

OpenAI (GPT-4o, GPT-4o Mini, GPT-4.1, GPT-4.1 Mini), Anthropic (Claude Sonnet 4, Haiku 3.5), Google (Gemini 2.0 Flash, Gemini 1.5 Pro), DeepSeek (V3, R1), Meta (Llama 3.3 70B), Mistral Large 2, Qwen3 235B, Amazon Nova Pro. Pricing as of July 2026.
