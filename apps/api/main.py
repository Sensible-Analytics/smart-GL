from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from routers import transactions, journal, reports, basiq, accounts

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("smartgl_api_starting")
    yield
    logger.info("smartgl_api_stopped")


app = FastAPI(title="Smart GL API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(journal.router, prefix="/journal", tags=["journal"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(basiq.router, prefix="/basiq", tags=["basiq"])
app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
