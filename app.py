import os
import urllib.parse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

app = FastAPI()

# CORSの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 環境変数からデータベース情報を取得
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = urllib.parse.quote_plus(os.getenv('DB_PASSWORD'))  # URLエンコード
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME')
SSL_CERT = os.getenv('SSL_CERT', 'DigiCertGlobalRootCA.crt.pem')  # SSL証明書のパス

# 環境変数が不足している場合のエラーチェック
if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    raise ValueError("環境変数が不足しています。全ての環境変数を設定してください。")

# MySQLの接続関数
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            ssl_ca=SSL_CERT
        )
        return conn
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")

# 商品情報を取得するAPI
@app.get("/item/{code}")
async def get_item(code: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE code = %s", (code,))
        product = cursor.fetchone()
        conn.close()

        if product:
            return product
        return {"message": "商品がマスタ未登録です"}
    except mysql.connector.Error as db_err:
        raise HTTPException(status_code=500, detail=f"Database error: {db_err}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

# 購入処理API
@app.post("/purchase")
async def purchase(items: list[dict]):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        total = sum(item['price'] for item in items)

        # トランザクション開始
        for item in items:
            cursor.execute(
                "INSERT INTO transactions (prd_code, prd_name, prd_price) VALUES (%s, %s, %s)",
                (item['code'], item['name'], item['price'])
            )
        conn.commit()
        conn.close()

        return {"message": "購入完了", "total": total}
    except mysql.connector.Error as db_err:
        raise HTTPException(status_code=500, detail=f"Database error: {db_err}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

# 起動用コード
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
