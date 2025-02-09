from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
import os

app = FastAPI()

# CORS設定（全てのオリジンを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    "ssl_ca": "DigiCertGlobalRootCA.crt.pem",  # 証明書ファイルのパス（相対パス）
}

# 商品検索API
@app.get("/item/{code}")
async def get_item(code: str):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE CODE = %s", (code,))
        product = cursor.fetchone()
        conn.close()

        if product:
            return product
        return {"message": "商品がマスタ未登録です"}
    except mysql.connector.Error as e:
        return {"error": f"Database error: {e}"}
    except Exception as e:
        return {"error": str(e)}

# 購入処理API
@app.post("/purchase")
async def purchase(items: list[dict]):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # トランザクション開始
        conn.start_transaction()

        # 購入情報を保存
        cursor.execute(
            "INSERT INTO transactions (DATETIME, TOTAL_AMT) VALUES (NOW(), %s)",
            (sum(item["price"] for item in items),),
        )
        transaction_id = cursor.lastrowid

        # 購入詳細を保存
        for item in items:
            cursor.execute(
                "INSERT INTO transaction_details (TRD_ID, PRD_ID, PRD_CODE, PRD_NAME, PRD_PRICE) "
                "VALUES (%s, %s, %s, %s, %s)",
                (transaction_id, item["id"], item["code"], item["name"], item["price"]),
            )

        # トランザクションをコミット
        conn.commit()
        conn.close()

        return {"message": "購入完了", "total": sum(item["price"] for item in items)}
    except mysql.connector.Error as e:
        return {"error": f"Database error: {e}"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # デフォルトのポート番号を8000に設定
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
