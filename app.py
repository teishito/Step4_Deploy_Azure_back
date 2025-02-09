from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
import os

# FastAPI アプリケーションの作成
app = FastAPI()

# CORS ミドルウェア設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 全てのオリジンを許可（必要に応じて制限）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# データベース接続設定
db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "test_db"),
    "ssl_ca": os.getenv("SSL_CA_PATH", "")
}

# 商品検索API
@app.get("/item/{code}")
async def get_item(code: str):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE code = %s", (code,))
        product = cursor.fetchone()
        conn.close()

        if product:
            return product
        raise HTTPException(status_code=404, detail="商品がマスタ未登録です")
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"データベースエラー: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"サーバーエラー: {str(e)}")

# 購入処理API
@app.post("/purchase")
async def purchase(items: list[dict]):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # 合計金額の計算
        total = sum(item["price"] * item.get("quantity", 1) for item in items)

        # トランザクションの登録（簡略化）
        cursor.execute("INSERT INTO transactions (total_amt) VALUES (%s)", (total,))
        transaction_id = cursor.lastrowid

        # トランザクション詳細の登録
        for item in items:
            cursor.execute(
                """
                INSERT INTO transaction_details (trd_id, prd_code, prd_name, prd_price, quantity)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (transaction_id, item["code"], item["name"], item["price"], item.get("quantity", 1))
            )

        conn.commit()
        conn.close()

        return {"message": "購入完了", "total": total}
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"データベースエラー: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"サーバーエラー: {str(e)}")

# メイン関数
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
