import os
import urllib.parse
import pymysql
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# favicon.ico の提供
app.mount("/static", StaticFiles(directory="static"), name="static")

# 環境変数からデータベース情報を取得
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = urllib.parse.quote_plus(os.getenv('DB_PASSWORD'))  # URLエンコード
DB_HOST = os.getenv('DB_HOST')
DB_PORT = int(os.getenv('DB_PORT', '3306'))
DB_NAME = os.getenv('DB_NAME')
SSL_CERT = "DigiCertGlobalRootCA.crt.pem"  # SSL証明書

# 環境変数チェック
if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    raise ValueError("環境変数が不足しています。")

# MySQL接続関数（pymysql使用）
def get_db_connection():
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT,
            ssl={"ssl": {"ca": SSL_CERT}},
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except pymysql.MySQLError as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")

# 商品情報取得 API
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

# 購入処理 API
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

# Faviconのエンドポイント
@app.get("/favicon.ico")
async def favicon():
    return {"message": "Favicon not found"}

# アプリケーション起動
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
