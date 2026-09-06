from database import DB
from fastapi import FastAPI
from .router.log_routes import router as log_router
from .router.chat_routes import router as chat_router
from .router.user_routes import router as user_router
from .router.cv_routes import router as cv_router
from .router.experience_routes import router as experience_router
from .router.skill_routes import router as skill_router
from .router.education_routes import router as education_router
from .router.routing import router as auth_router


def main() -> None:
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(cv_router)
    app.include_router(experience_router)
    app.include_router(skill_router)
    app.include_router(education_router)
    app.include_router(chat_router)
    app.include_router(log_router)
