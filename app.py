from fastapi import FastAPI
from flask_cors import CORS
import mysql.connector
from pydantic import BaseModel
import os

app = FastAPI()
CORS(app, resources={r"/*": {"origins": "*"}})

# データベース接続設定
db_config = {
    "host": "tech0-gen-8-step4-db-3.mysql.database.azure.com",
    "user": "Tech0Gen8TA3",
    "password": "gen8-1-ta@3",
    "database": "pos_db_teishito",
    "ssl_ca": "/path/to/DigiCertGlobalRootCA.crt.pem"
}

# 購入アイテムのスキーマ
class PurchaseItem(BaseModel):
    prd_id: int
    prd_code: str
    prd_name: str
    prd_price: int
    quantity: int

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
    except Exception as e:
        return {"error": str(e)}

# 購入処理API
@app.post("/purchase")
async def purchase(items: list[PurchaseItem]):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # トランザクションを開始
        cursor.execute("INSERT INTO transactions (TOTAL_AMT) VALUES (%s)", (0,))
        conn.commit()
        transaction_id = cursor.lastrowid

        total_amount = 0
        for item in items:
            total_price = item.prd_price * item.quantity
            total_amount += total_price

            cursor.execute("""
                INSERT INTO transaction_details (TRD_ID, PRD_ID, PRD_CODE, PRD_NAME, PRD_PRICE, QUANTITY)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (transaction_id, item.prd_id, item.prd_code, item.prd_name, item.prd_price, item.quantity))
        
        # トランザクションテーブルの合計金額を更新
        cursor.execute("UPDATE transactions SET TOTAL_AMT = %s WHERE TRD_ID = %s", (total_amount, transaction_id))
        conn.commit()

        conn.close()
        return {"message": "購入完了", "total": total_amount}
    except Exception as e:
        return {"error": str(e)}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
