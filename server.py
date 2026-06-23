"""OpenAI 호환 단일 엔드포인트 + 일반인용 웹 화면(/)."""
import time
import uuid
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from orchestrator import orchestrate

app = FastAPI(title="moa", description="오픈모델 오케스트레이션 게이트웨이")

_INDEX = Path(__file__).with_name("index.html")


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = "moa"
    messages: list[Message]


@app.get("/", response_class=HTMLResponse)
async def home():
    return _INDEX.read_text(encoding="utf-8")


@app.get("/health")
async def health():
    return {"name": "moa", "status": "ok"}


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    task = req.messages[-1].content
    result = await orchestrate(task)
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "moa",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": result["answer"]},
            "finish_reason": "stop",
        }],
        "moa_models": result["used"],  # 참여 모델·역할 (비표준 확장 필드)
    }
