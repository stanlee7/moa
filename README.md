# fugu-kr 🐡🇰🇷

**하나의 API처럼 보이지만, 뒤에서는 오픈모델 팀이 움직이는** 오케스트레이션 게이트웨이.
일본 Sakana의 Fugu 아이디어를, 한국에서 **오픈웨이트만으로** 재현한 최소 구현체.

> 핵심 명제: 프런티어 모델을 직접 훈련하지 않아도, **여러 오픈모델을 잘 지휘하면**
> 단일 프런티어 모델급 경험을 만들 수 있다. 모델이 아니라 **오케스트레이션이 경쟁력**.

## 구조

```
            ┌─────────────────────────────────────────────┐
 client ──▶ │  /v1/chat/completions  (OpenAI 호환 단일 API) │
            └───────────────────────┬─────────────────────┘
                                    ▼
              router(휴리스틱) ─ fast │ full
                                    ▼
        Thinker(계획) ▶ Workers(N개 모델 병렬) ▶ Verifier(교차검증) ▶ Synthesizer(종합)
                                    │
                                    └─▶ (필요시) 재귀 호출로 1회 정제
```

- **Thinker / Worker / Verifier** 역할은 Fugu와 동일한 분담.
- Fugu가 "오케스트레이션을 학습"한 것과 달리, 여기선 **휴리스틱 라우팅**으로 대체 (솔로 현실판).
- 기본 풀은 **OpenRouter 무료(:free) US 오픈모델** — NVIDIA Nemotron·Poolside 등. 카드 등록 불필요.
- 더 강한 유료 모델/자체 키를 원하는 사람은 `config.py` 슬러그만 갈아끼우면 됨 (본인 키로).
- 원하면 전부 자가호스팅 가능 → 규제/데이터주권에서 자유.

## 실행

```bash
pip install -r requirements.txt

# 1) 키 없이 바로 체험 (mock 모드, 기본값)
uvicorn server:app --reload --port 8080

# 2) 무료 US 오픈모델로 (OpenRouter 키만 — 카드 등록 불필요)
cp .env.example .env   # OPENROUTER_API_KEY 입력, FUGU_MOCK=0
uvicorn server:app --reload --port 8080
```

호출 (OpenAI SDK 그대로):

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"fugu-kr","messages":[{"role":"user","content":"한국이 오픈소스로 프런티어급 서비스를 만들 수 있을까? 근거와 함께 분석해줘"}]}'
```

## 일반인에게 배포 (Render 무료)

브라우저에서 누구나 쓰게 하려면 — `/` 에 웹 화면이 내장돼 있어 서버만 띄우면 끝.

1. [render.com](https://render.com) 가입(GitHub 로그인) → **New → Blueprint**
2. 이 repo 선택 → `render.yaml` 자동 인식 → **Apply**
3. 환경변수 **OPENROUTER_API_KEY** 에 본인 키 입력 (한 번)
4. 몇 분 뒤 `https://fugu-kr.onrender.com` 같은 주소 생성 → 끝

> 무료 플랜은 15분 미사용 시 잠들어 첫 접속이 ~50초 느림(콜드스타트). 무료 모델 호출 한도도 공유됨.

## 다음 단계 (해자 만들기)

1. **한국어 해자**: 무료 풀엔 한국어 특화 모델이 없음 → EXAONE/SOLAR를 유료 또는 자가호스팅으로 Worker에 추가
2. **학습된 라우터**: 휴리스틱 → 작은 분류 모델로 교체 (Fugu의 Conductor 방향)
3. **자가호스팅**: vLLM으로 직접 서빙 → API 의존·데이터주권 완전 해결 (SELFHOST.md)
4. **eval 하니스**: 라우팅 품질을 측정해야 진짜 성능이 올라감

MIT License.
