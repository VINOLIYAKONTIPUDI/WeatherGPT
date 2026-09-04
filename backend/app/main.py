from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import weather, chat, alerts, location

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

# Register routes
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
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
