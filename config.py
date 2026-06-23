import os
from pathlib import Path

# .env 파일이 있으면 자동 로드 (추가 설치 없이 직접 파싱)
_env = Path(__file__).with_name(".env")
if _env.exists():
    for _line in _env.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        _k, _v = _line.split("=", 1)
        os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

# 기본은 mock — 키 없이도 전체 파이프라인이 돌아감 (구조 학습용)
MOCK = os.getenv("FUGU_MOCK", "1") == "1"

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
# 기본은 OpenRouter. 자가호스팅(vLLM) 시 LLM_BASE_URL 만 바꾸면 코드 수정 0.
OPENROUTER_BASE = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")

# ── 모델 카탈로그: OpenRouter "무료(:free)" 모델만 ─────────────────────────
#   ko=한국어, code=코딩, general=범용(0~1). 워커는 매 요청마다 이 점수로 동적 선발.
#   전부 무료라 카드 등록 없이 OpenRouter 키만 있으면 됨 (무료는 분당/일일 호출 제한 있음).
#   ※ 무료 슬러그는 자주 바뀜 → https://openrouter.ai/models?max_price=0 에서 최신값 확인.
#   더 강한 유료 모델을 쓰고 싶은 사람은 본인 키로 슬러그만 갈아끼우면 됨.
MODELS = {
    "nvidia/nemotron-3-ultra-550b-a55b:free":              {"ko": 0.60, "code": 0.82, "general": 0.90},  # 🇺🇸 NVIDIA(라마 기반, 대형)
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free":  {"ko": 0.45, "code": 0.75, "general": 0.80},  # 🇺🇸 NVIDIA(추론)
    "poolside/laguna-m.1:free":                            {"ko": 0.40, "code": 0.85, "general": 0.78},  # 🇺🇸 Poolside(코딩)
    "poolside/laguna-xs.2:free":                           {"ko": 0.38, "code": 0.78, "general": 0.72},  # 🇺🇸 Poolside(소형)
    "cohere/north-mini-code:free":                         {"ko": 0.45, "code": 0.80, "general": 0.74},  # 🇨🇦 Cohere(코딩, 선택)
}

# 고정 역할 (계획 / 검증 / 종합) — 무료 US 모델
THINKER = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"   # 추론 모델로 계획
VERIFIER = "poolside/laguna-m.1:free"
SYNTHESIZER = "nvidia/nemotron-3-ultra-550b-a55b:free"           # 종합은 가장 큰 모델로

N_WORKERS = 3  # 매 요청마다 카탈로그에서 점수 상위 N개를 워커로 선발
