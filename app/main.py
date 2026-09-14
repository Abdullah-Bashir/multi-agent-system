from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.mongodb import MongoDB
from routes import leads, services, chat

app = FastAPI(
    title="AI Lead Management System",
    description="Multi-agent system for lead qualification and customer support",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(leads.router)
app.include_router(services.router)
app.include_router(chat.router) 

@app.get("/")
async def root():
    return {
        "message": "AI Lead Management System API",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}


@app.on_event("startup")
async def startup():
    await MongoDB.connect()
    print("🚀 Server started on http://localhost:8000")


@app.on_event("shutdown")
async def shutdown():
    await MongoDB.disconnect()
    print("👋 Shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )