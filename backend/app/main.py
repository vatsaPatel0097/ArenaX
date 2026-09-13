from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="ArenaX - Open-Source LLM Battleground & Evaluation Platform Backend API",
    version="0.1.0",
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust allowed origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint to verify backend operational readiness."""
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "0.1.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
