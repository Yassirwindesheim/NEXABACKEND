from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.routers import employees, workorders, tasks, portal

def get_origins():
    raw = os.getenv("CORS_ORIGINS", "")
    return [o.strip() for o in raw.split(",") if o.strip()] or ["*"]

app = FastAPI(title="NEXA API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(employees.router)
app.include_router(workorders.router)
app.include_router(tasks.router)
app.include_router(portal.router)

@app.get("/")
def root():
    return {"status": "ok", "service": "nexa-backend"}