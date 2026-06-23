"""게이트웨이 스모크 테스트. 서버가 떠 있어야 함 (uvicorn server:app --port 8080)."""
import sys
import httpx

PROMPT = sys.argv[1] if len(sys.argv) > 1 else \
    "한국이 미국 오픈모델만으로 프런티어급 서비스를 만들 수 있을지 근거와 함께 분석해줘"

resp = httpx.post(
    "http://localhost:8080/v1/chat/completions",
    json={"model": "moa", "messages": [{"role": "user", "content": PROMPT}]},
    timeout=180,
)
resp.raise_for_status()
print(resp.json()["choices"][0]["message"]["content"])
