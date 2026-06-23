# 자가호스팅 가이드 (vLLM)

OpenRouter 대신 **내 GPU에서 직접 모델을 서빙**하면 외부 API 의존·데이터 유출이 0이 된다.
fugu-kr는 베이스 URL만 바꾸면 되도록 설계됨 (`LLM_BASE_URL` 환경변수).

## 1. vLLM으로 미국 오픈모델 서빙 (GPU 필요)

```bash
pip install vllm

# 예: Llama 3.3 70B (A100/H100급 권장). 작은 GPU면 gemma-2-9b-it 로 시작.
vllm serve meta-llama/Llama-3.3-70B-Instruct \
  --port 8000 \
  --api-key local-key
```

vLLM은 `http://localhost:8000/v1/chat/completions` 로 **OpenAI 호환** 엔드포인트를 연다.

## 2. fugu-kr를 자가호스팅에 연결

```bash
export LLM_BASE_URL=http://localhost:8000/v1/chat/completions
export OPENROUTER_API_KEY=local-key
export FUGU_MOCK=0
uvicorn server:app --port 8080
```

## 3. 여러 모델을 동시에 서빙하려면

워커 풀이 여러 모델이므로, 모델별로 vLLM 인스턴스를 띄우거나
[LiteLLM Proxy](https://docs.litellm.ai/docs/proxy/quick_start) 로 한 엔드포인트 뒤에 묶어
`LLM_BASE_URL` 을 LiteLLM 프록시로 지정하면 된다.

> GPU가 없으면: 1차는 OpenRouter(클라우드), 데이터주권이 필요한 워크로드만
> 자가호스팅으로 단계적 이전 — 코드 변경 없이 `LLM_BASE_URL` 토글만으로 전환된다.
