import os
import urllib.parse
import pymysql
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles

# FastAPIアプリの初期化
app = FastAPI()

# ミドルウェア CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tech0-gen8-step4-pos-app-71.azurewebsites.net"],  # 許可するオリジンを指定
    allow_credentials=True,
    allow_methods=["*"],  # 全てのHTTPメソッドを許可
    allow_headers=["*"],  # 全てのヘッダーを許可
)

# favicon.ico用の静的ディレクトリ設定（必要な場合）
app.mount("/static", StaticFiles(directory="static"), name="static")

# 環境変数からデータベース情報を取得
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = urllib.parse.quote_plus(os.getenv('DB_PASSWORD'))  # URLエンコード
DB_HOST = os.getenv('DB_HOST')
DB_PORT = int(os.getenv('DB_PORT', '3306'))
DB_NAME = os.getenv('DB_NAME')
SSL_CERT = "/home/site/certs/DigiCertGlobalRootCA.crt.pem"  # SSL証明書パス

# 環境変数が不足している場合のエラーチェック
if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    raise ValueError("環境変数が不足しています。")

# MySQL接続関数
def get_db_connection():
    try:
        return pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT,
            ssl={"ssl": {"ca": SSL_CERT}},
            cursorclass=pymysql.cursors.DictCursor
        )
    except pymysql.MySQLError as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")

# サンプルデータモデル
class SampleData(BaseModel):
    id: int
    name: str
    age: int

# エンドポイント定義: ルート
@app.get("/")
async def home():
    return {"message": "Welcome to the FastAPI API!"}

# エンドポイント定義: サンプルデータ取得
@app.get("/data", response_model=SampleData)
async def get_data():
    sample_data = {
        "id": 1,
        "name": "John Doe",
        "age": 30
    }
    return sample_data

# エンドポイント定義: 商品情報取得
@app.get("/item/{code}")
async def get_item(code: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE code = %s", (code,))
        product = cursor.fetchone()
        conn.close()

        if product:
            return product
        return {"message": "商品がマスタ未登録です"}
    except pymysql.MySQLError as db_err:
        raise HTTPException(status_code=500, detail=f"Database error: {db_err}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

# エンドポイント定義: 購入処理
@app.post("/purchase")
async def purchase(items: list[dict]):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        total = sum(item['price'] for item in items)

        for item in items:
            cursor.execute(
                "INSERT INTO transactions (prd_code, prd_name, prd_price) VALUES (%s, %s, %s)",
                (item['code'], item['name'], item['price'])
            )
        conn.commit()
        conn.close()

        return {"message": "購入完了", "total": total}
    except pymysql.MySQLError as db_err:
        raise HTTPException(status_code=500, detail=f"Database error: {db_err}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

# アプリケーション起動
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
