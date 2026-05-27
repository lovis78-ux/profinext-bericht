from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS, ORIGINALS_DIR, OPTIMIZED_DIR
from database import init_db
from routes.upload import router as upload_router
from routes.reports import router as reports_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure storage directories exist (important on Railway with a fresh volume)
    ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
    OPTIMIZED_DIR.mkdir(parents=True, exist_ok=True)
    await init_db()
    yield


app = FastAPI(
    title="Projektbericht Optimizer",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(reports_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
