"""moa 오케스트레이션: 작업 언어에 따라 워커를 동적 선발 → 가중 종합."""
import asyncio
import httpx
from config import (MOCK, OPENROUTER_API_KEY, OPENROUTER_BASE, MODELS,
                    THINKER, VERIFIER, SYNTHESIZER, N_WORKERS)


async def _call(model: str, messages: list, temperature: float = 0.7) -> str:
    """단일 모델 호출. mock 모드면 실제 네트워크 없이 더미 응답."""
    if MOCK:
        last = messages[-1]["content"][:60].replace("\n", " ")
        return f"[mock:{model}] '{last}' 응답"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/stanlee7/moa",
    }
    payload = {"model": model, "messages": messages, "temperature": temperature}
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(OPENROUTER_BASE, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


# ── 작업 프로파일링 & 워커 선발 (= "한국어 가중치" 가 작동하는 곳) ──────────────
def korean_ratio(text: str) -> float:
    """전체 글자 중 한글 비율. 높을수록 한국어 작업."""
    chars = [c for c in text if not c.isspace()]
    if not chars:
        return 0.0
    han = sum(1 for c in chars if "가" <= c <= "힣")
    return han / len(chars)


def is_code_task(text: str) -> bool:
    t = text.lower()
    return any(k in text for k in ("코드", "함수", "버그")) or \
        any(k in t for k in ("code", "function", "bug", "def ", "class "))


def select_workers(task: str) -> list[tuple[str, float]]:
    """작업 언어/유형에 맞춰 모델을 점수화 → 상위 N개와 정규화 신뢰가중치 반환.

    score = general + ko*(한글비율) + code*(코딩이면 0.6)
    → 한글 비율이 높을수록 ko 강점 모델(EXAONE/SOLAR)의 점수가 올라가 선발됨.
    """
    ko = korean_ratio(task)
    code_w = 0.6 if is_code_task(task) else 0.0
    scored = [
        (m, s["general"] + s["ko"] * ko + s["code"] * code_w)
        for m, s in MODELS.items()
    ]
    scored.sort(key=lambda x: -x[1])
    top = scored[:N_WORKERS]
    total = sum(sc for _, sc in top) or 1.0
    return [(m, round(sc / total, 3)) for m, sc in top]  # (모델, 신뢰가중치)


# ── 역할(role)별 에이전트 ───────────────────────────────────────────────
async def think(task: str) -> str:
    msg = [
        {"role": "system", "content": "너는 Thinker다. 작업을 짧은 계획으로 분해하고 "
                                      "어떤 전문성이 필요한지 한국어로 간결히 적어라."},
        {"role": "user", "content": task},
    ]
    return await _call(THINKER, msg, 0.3)


async def work(task: str, plan: str, workers: list[tuple[str, float]]) -> list[dict]:
    async def one(model: str, weight: float) -> dict:
        msg = [
            {"role": "system", "content": f"너는 Worker다. 계획:\n{plan}\n계획에 따라 작업을 끝까지 완수하라."},
            {"role": "user", "content": task},
        ]
        return {"model": model, "weight": weight, "answer": await _call(model, msg, 0.7)}

    return list(await asyncio.gather(*[one(m, w) for m, w in workers]))


async def verify(task: str, answers: list[dict]) -> str:
    joined = "\n\n".join(f"[{a['model']}]\n{a['answer']}" for a in answers)
    msg = [
        {"role": "system", "content": "너는 Verifier다. 후보 답변들을 교차검증해 오류·합의·빈틈을 "
                                      "짧게 비평하라. 해결이 불충분하면 첫 줄에 'INSUFFICIENT'를 적어라."},
        {"role": "user", "content": f"작업:\n{task}\n\n후보들:\n{joined}"},
    ]
    return await _call(VERIFIER, msg, 0.2)


async def synthesize(task: str, answers: list[dict], critique: str) -> str:
    # 신뢰가중치를 명시해 종합 시 더 신뢰할 답을 알려줌 (= 종합 단계의 한국어 가중치)
    joined = "\n\n".join(
        f"[{a['model']} | 신뢰도 {a['weight']}]\n{a['answer']}" for a in answers
    )
    msg = [
        {"role": "system", "content": "너는 Synthesizer다. 후보들과 Verifier 비평을 근거로 "
                                      "단 하나의 최종 답을 만들어라. 신뢰도가 높은 후보를 더 비중 있게 "
                                      "반영하되 맹신하지는 마라. 내부 과정은 언급하지 마라."},
        {"role": "user", "content": f"작업:\n{task}\n\n후보들:\n{joined}\n\n비평:\n{critique}"},
    ]
    return await _call(SYNTHESIZER, msg, 0.4)


# ── 라우터 + 오케스트레이터 ─────────────────────────────────────────────
def route(task: str) -> str:
    """휴리스틱 라우팅: 어려운 작업은 full 파이프라인, 가벼운 건 단일 모델."""
    t = task.lower()
    hard = len(task) > 200 or any(k in task for k in ("분석", "비교", "설계", "증명", "코드")) \
        or any(k in t for k in ("analyze", "design", "prove", "compare", "code"))
    return "full" if hard else "fast"


async def orchestrate(task: str, depth: int = 0, max_depth: int = 1) -> dict:
    """반환: {"answer": 최종답변, "used": [참여 모델·역할 목록]}"""
    workers = select_workers(task)

    if route(task) == "fast":
        ans = await _call(workers[0][0], [{"role": "user", "content": task}])
        return {"answer": ans, "used": [{"role": "단독 응답", "model": workers[0][0]}]}

    plan = await think(task)
    answers = await work(task, plan, workers)
    critique = await verify(task, answers)
    final = await synthesize(task, answers, critique)

    if depth < max_depth and critique.strip().upper().startswith("INSUFFICIENT"):
        return await orchestrate(f"{task}\n\n[이전 시도 비평]\n{critique}", depth + 1, max_depth)

    used = [{"role": "🧠 계획", "model": THINKER}]
    used += [{"role": "👥 작업", "model": a["model"], "weight": a["weight"]} for a in answers]
    used += [{"role": "🔍 검증", "model": VERIFIER}, {"role": "✍️ 종합", "model": SYNTHESIZER}]
    return {"answer": final, "used": used}
