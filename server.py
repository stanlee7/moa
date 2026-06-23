"""OpenAI 호환 단일 엔드포인트. 클라이언트는 '하나의 모델'로 인식한다."""
import time
import uuid
from fastapi import FastAPI
from pydantic import BaseModel
from orchestrator import orchestrate

app = FastAPI(title="fugu-kr", description="오픈모델 오케스트레이션 게이트웨이")


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = "fugu-kr"
    messages: list[Message]


@app.get("/")
async def root():
    return {"name": "fugu-kr", "status": "ok", "endpoint": "/v1/chat/completions"}


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    task = req.messages[-1].content
    answer = await orchestrate(task)
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "fugu-kr",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": answer},
            "finish_reason": "stop",
        }],
    }
