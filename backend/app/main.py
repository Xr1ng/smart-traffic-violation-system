from fastapi import FastAPI

from app.ai.routes import internal_router
from app.api.v1.router import api_router

app = FastAPI(title="交通违章智能管理平台 API")
app.include_router(api_router)
app.include_router(internal_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
