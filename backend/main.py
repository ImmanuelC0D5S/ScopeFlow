from fastapi import FastAPI

from backend.api.approvals import router as approvals_router
from backend.api.ingest import router as ingest_router
from backend.api.projects import router as projects_router

app = FastAPI(title="ScopeFlow API")
app.include_router(ingest_router)
app.include_router(projects_router)
app.include_router(approvals_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
