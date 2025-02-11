import os
import urllib.parse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# =======================
# Azure 環境変数から取得
# =======================
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = urllib.parse.quote_plus(os.getenv("DB_PASSWORD"))  # パスワードをURLエンコード
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT", "3306")  # デフォルト 3306
PORT = int(os.getenv("PORT", 8080))  # デフォルト 8080

# MySQL接続情報
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SQLAlchemy セッション作成
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"ssl": {"ssl_ca": None}})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# =======================
# モデル定義（テーブル名を `products` に修正）
# =======================
class Product(Base):
    __tablename__ = 'products' 
    PRD_ID = Column(Integer, primary_key=True, index=True)
    CODE = Column(String(13), unique=True, index=True)
    NAME = Column(String(50))
    PRICE = Column(Integer)

# =======================
# FastAPI 初期化 & CORS 設定
# =======================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://tech0-gen8-step4-pos-app-71.azurewebsites.net"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =======================
# ルートエンドポイントの追加
# =======================
@app.get("/")
async def home():
    return {"message": "Welcome to the FastAPI API!"}

# =======================
# 商品取得 API
# =======================
class ProductResponse(BaseModel):
    PRD_ID: int
    CODE: str
    NAME: str
    PRICE: int

@app.get("/api/products/{code}", response_model=ProductResponse)
async def get_product(code: str):
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.CODE == code).first()
        if product:
            return {
                "PRD_ID": product.PRD_ID,
                "CODE": product.CODE,
                "NAME": product.NAME,
                "PRICE": product.PRICE
            }
        raise HTTPException(status_code=404, detail="商品が見つかりません")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# =======================
# アプリ起動
# =======================
if __name__ == "__main__":
    import uvicorn
    print(f"Starting FastAPI on port {PORT} with DB {DB_NAME}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
