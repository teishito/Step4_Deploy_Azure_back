from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

app = FastAPI()

# CORS (必要に応じてドメイン制限可)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Azure App Service に保存した環境変数から取得
openai.api_key = os.getenv("AZURE_API_KEY")

class AnalysisRequest(BaseModel):
    savedAnswers: dict

@app.post("/api/analyze")
async def analyze(data: AnalysisRequest):
    prompt = f"""以下は地方中小企業向けの経営診断アンケートの結果です。この内容をもとにPEST分析・4C分析・SWOT分析・STP分析・4P分析を実施し、業界トレンドを踏まえた経営戦略を提案してください。:

{data.savedAnswers}

それぞれのフレームワークごとに整理して、分かりやすく箇条書きまたは表形式で出力してください。"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-2024-08-06",  # GPT-4モデルを使用
            messages=[
                {"role": "system", "content": "あなたは地方中小企業の経営コンサルタントです。中小企業診断士の視点で分析してください。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        result = response.choices[0].message.content
        return {"result": result}

    except Exception as e:
        return {"error": str(e)}
