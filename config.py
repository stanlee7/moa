import os

# 기본은 mock — 키 없이도 전체 파이프라인이 돌아감 (구조 학습용)
MOCK = os.getenv("FUGU_MOCK", "1") == "1"

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
# 기본은 OpenRouter. 자가호스팅(vLLM) 시 LLM_BASE_URL 만 바꾸면 코드 수정 0.
OPENROUTER_BASE = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")

# ── 모델 카탈로그: 미국 오픈모델 위주 (+ 한국어 보강 1개) ────────────────────
#   ko=한국어, code=코딩, general=범용(0~1). 워커는 매 요청마다 이 점수로 동적 선발.
#   중국 모델 0 / 미국 오픈모델 코어 → 신뢰·규제 우려 최소.
#   ※ 슬러그는 https://openrouter.ai/models 에서 최신값 확인 후 교체.
MODELS = {
    "meta-llama/llama-3.3-70b-instruct":  {"ko": 0.50, "code": 0.80, "general": 0.85},  # 🇺🇸 Meta
    "meta-llama/llama-3.1-405b-instruct": {"ko": 0.55, "code": 0.85, "general": 0.90},  # 🇺🇸 Meta (대형)
    "google/gemma-2-27b-it":              {"ko": 0.55, "code": 0.72, "general": 0.80},  # 🇺🇸 Google
    "microsoft/phi-4":                    {"ko": 0.40, "code": 0.82, "general": 0.80},  # 🇺🇸 Microsoft
    "lgai/exaone-3.5-32b-instruct":       {"ko": 0.95, "code": 0.70, "general": 0.78},  # 🇰🇷 한국어 보강
}

# 순수 US만 원하면 위 EXAONE 줄을 지우세요 (단, 한국어 가중치 효과는 약해짐).

# 고정 역할 (계획 / 검증 / 종합) — 전부 미국 오픈모델
THINKER = "meta-llama/llama-3.3-70b-instruct"
VERIFIER = "google/gemma-2-27b-it"
SYNTHESIZER = "meta-llama/llama-3.1-405b-instruct"   # 종합은 가장 큰 모델로

N_WORKERS = 3  # 매 요청마다 카탈로그에서 점수 상위 N개를 워커로 선발
