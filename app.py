import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
from dotenv import load_dotenv

load_dotenv()  # 必要に応じて

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # セキュリティ的には適宜調整
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisRequest(BaseModel):
    prompt: str

@app.post("/api/analyze")
async def analyze(req: AnalysisRequest):
    try:
        openai.api_key = os.environ.get("AZURE_API_KEY")  # 環境変数から読み込み
        if not openai.api_key:
            return {"error": "APIキーが設定されていません"}
        
        completion = openai.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": "あなたは地方中小企業の経営コンサルタントです。中小企業診断士の視点で分析してください。"},
                {"role": "user", "content": req.prompt},
            ],
        )
        return {"result": completion.choices[0].message.content}
    except Exception as e:
        print("Server Error:", e)
        return {"error": str(e)}
