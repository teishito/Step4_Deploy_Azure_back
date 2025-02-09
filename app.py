from fastapi import FastAPI
import mysql.connector

app = FastAPI()

# データベース接続設定
db_config = {
    "host": "tech0-gen-8-step4-db-3.mysql.database.azure.com",
    "user": "Tech0Gen8TA3",
    "password": "gen8-1-ta@3",  # パスワードを設定
    "database": "pos_db_teishito",
    "ssl_ca": "/path/to/DigiCertGlobalRootCA.crt.pem"
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
        return {"message": "商品がマスタ未登録です"}
    except Exception as e:
        return {"error": str(e)}

# 購入処理API
@app.post("/purchase")
async def purchase(items: list[dict]):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        total = sum(item['price'] for item in items)
        conn.close()

        return {"message": "購入完了", "total": total}
    except Exception as e:
        return {"error": str(e)}
