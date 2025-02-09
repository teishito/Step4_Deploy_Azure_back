import os
import urllib.parse
from fastapi import FastAPI, HTTPException
from flask_cors import CORS
import mysql.connector

app = FastAPI()
CORS(app, resources={r"/*": {"origins": "*"}})

# データベース接続情報
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = urllib.parse.quote_plus(os.getenv('DB_PASSWORD'))  # エンコード処理
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

# MySQLのURL構築
if not DB_USER or not DB_PASSWORD or not DB_HOST or not DB_PORT or not DB_NAME:
    raise ValueError(
        "環境変数が不足しています。.env ファイルを確認してください。"
    )

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 商品検索API
@app.get("/item/{code}")
async def get_item(code: str):
    try:
        conn = mysql.connector.connect(
            user=DB_USER,
            password=os.getenv('DB_PASSWORD'),
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE code = %s", (code,))
        product = cursor.fetchone()
        conn.close()

        if product:
            return product
        return {"message": "商品がマスタ未登録です"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 購入処理API
@app.post("/purchase")
async def purchase(items: list[dict]):
    try:
        conn = mysql.connector.connect(
            user=DB_USER,
            password=os.getenv('DB_PASSWORD'),
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        cursor = conn.cursor()
        total = sum(item['price'] for item in items)

        # データベースへの登録
        for item in items:
            cursor.execute(
                "INSERT INTO transactions (prd_code, prd_name, prd_price) VALUES (%s, %s, %s)",
                (item['code'], item['name'], item['price'])
            )
        conn.commit()
        conn.close()

        return {"message": "購入完了", "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
