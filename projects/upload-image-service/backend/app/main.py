from app.api.endpoints import contract, submission
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="契約書類アップロードシステム", description="エルダーズギルド品質基準準拠", version="2.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(contract.router, prefix="/api/v1/contract", tags=["contract"])
app.include_router(submission.router, prefix="/api/v1/submission", tags=["submission"])


@app.get("/")
async def root():
    return {"message": "契約書類アップロードシステム API", "version": "2.0.0", "elder_guild": "品質基準準拠"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
