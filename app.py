from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
from pydantic import BaseModel
import os

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 全てのオリジンを許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# データベース接続設定
db_config = {
    "host": "tech0-gen-8-step4-db-3.mysql.database.azure.com",
    "user": "Tech0Gen8TA3",
    "password": "gen8-1-ta@3",  # パスワードを設定
    "database": "pos_db_teishito",
    "ssl_ca": "/path/to/DigiCertGlobalRootCA.crt.pem",
}

# 商品検索API
@app.get("/item/{code}")
async def get_item(code: str):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT name, price FROM products WHERE code = %s", (code,))
        product = cursor.fetchone()
        conn.close()

        if product:
            return product
        return {"message": "商品がマスタ未登録です"}
    except Exception as e:
        return {"error": f"データベース接続に失敗しました: {str(e)}"}

# 購入データモデル
class PurchaseItem(BaseModel):
    code: str
    name: str
    price: float
    quantity: int

@app.post("/purchase")
async def purchase(items: list[PurchaseItem]):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        total = 0
        for item in items:
            total += item.price * item.quantity
            # 購入データを保存
            cursor.execute(
                "INSERT INTO purchases (code, name, price, quantity) VALUES (%s, %s, %s, %s)",
                (item.code, item.name, item.price, item.quantity),
            )

        conn.commit()
        conn.close()

        return {"message": "購入完了", "total": total}
    except Exception as e:
        return {"error": f"購入処理に失敗しました: {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # 環境変数PORTが設定されていない場合、デフォルトで8000を使用
    app.run(host="0.0.0.0", port=port)
