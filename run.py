"""프롬프트를 받아 오케스트레이션 결과를 answer.txt(UTF-8)로 저장.

사용:  python run.py "질문 내용"
콘솔 인코딩 문제 없이 결과를 파일로 안전하게 저장한다.
"""
import asyncio
import sys
from orchestrator import orchestrate

prompt = sys.argv[1] if len(sys.argv) > 1 else \
    "한국이 무료 오픈모델만으로 프런티어급 서비스를 만들 수 있을지 근거와 함께 분석해줘"

answer = asyncio.run(orchestrate(prompt))

with open("answer.txt", "w", encoding="utf-8") as f:
    f.write(f"[질문]\n{prompt}\n\n[답변]\n{answer}\n")

print("=== 완료: answer.txt 파일에 저장됨 ===")
