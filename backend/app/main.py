from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .core.config import settings
from .core.database import engine, Base
from .models import *
from .api import image as image_router
from .api import classification as classification_router
from .api import stats as stats_router
from .api import grad_cam as grad_cam_router
from .ml.inference import get_inference_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    if settings.app_env != "testing":
        try:
            _ = get_inference_service()
            print("ML model initialized successfully")
        except Exception as e:
            print(f"Warning: Failed to initialize ML model: {e}")

    yield
    print("Shutting down...")


app = FastAPI(
    title=settings.app_name,
    description="Side-scan Sonar Image Seabed Classification System API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(image_router.router)
app.include_router(classification_router.router)
app.include_router(stats_router.router)
app.include_router(grad_cam_router.router)


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    return {
        "message": "Sonar Classification System API",
        "docs": "/docs",
        "health": "/api/health"
    }
