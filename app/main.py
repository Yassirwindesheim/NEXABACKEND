# app/main.py (or main.py)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
import traceback # <--- Add this import
from app.routers import customers

# Import your routers
from app.routers import auth, employees, portal, tasks, workorders

app = FastAPI(title="Your App Name", version="1.0.0")

@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        # Print the full traceback directly to the console
        print("-" * 60)
        print("INTERNAL SERVER ERROR TRACEBACK (FOR DEBUGGING):")
        traceback.print_exc()
        print("-" * 60)
        
        # Return a generic 500 response
        return Response("Internal Server Error", status_code=500)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(customers.router)
app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(portal.router)
app.include_router(tasks.router)
app.include_router(workorders.router)
# Don't include pycache - that's just Python cache files

@app.get("/")
async def root():
    return {"message": "API is running"}