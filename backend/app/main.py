from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import weather, chat, alerts, location, auth, notifications
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.services.notification_scheduler import start_scheduler, stop_scheduler

app = FastAPI(
    title="WeatherGPT API",
    description="Conversational Voice-First Weather Intelligence Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_db_client():
    stop_scheduler()
    await close_mongo_connection()

# Register routes
app.include_router(auth.router)
app.include_router(notifications.router)
app.include_router(weather.router)
app.include_router(chat.router)
app.include_router(alerts.router)
app.include_router(location.router)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "WeatherGPT",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8001))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
