import os
import openai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
model = os.getenv("OPENAI_MODEL", "gpt-4o-2024-08-06")

print("✅ APIキー:", openai.api_key[:8] + "..." if openai.api_key else "None")
print("✅ API BASE:", openai.api_base)
print("✅ 使用モデル:", model)

class AnalysisRequest(BaseModel):
    prompt: str

@app.post("/api/analyze")
async def analyze(req: AnalysisRequest):
    try:
        completion = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "あなたは地方中小企業の経営コンサルタントです。"},
                {"role": "user", "content": req.prompt}
            ]
        )
        return {"result": completion.choices[0].message.content}
    except Exception as e:
        print("❌ Server Error:", str(e))
        return {"error": f"Internal Server Error: {str(e)}"}
