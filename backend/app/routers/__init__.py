from app.routers.candidates import router as candidates_router
from app.routers.evaluations import router as evaluations_router
from app.routers.health import router as health_router

__all__ = ["candidates_router", "evaluations_router", "health_router"]
