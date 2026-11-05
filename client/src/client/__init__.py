import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.requests import Request
from .router.log_routes import router as log_router
from .router.chat_routes import router as chat_router
from .router.user_routes import router as user_router
from .router.cv_routes import router as cv_router
from .router.experience_routes import router as experience_router
from .router.skill_routes import router as skill_router
from .router.education_routes import router as education_router
from .router.routing import router as auth_router
from .router.skill_catalog_routes import router as skill_catalog_router
from .router.achievement_routes import router as achievement_router
from .router.program_routes import router as program_router
from .router.language_routes import router as language_router
from database.DB import create_all_tables

app = FastAPI(title="CvCreator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "Content-Disposition",
        "X-Export-Format",
        "X-Export-Pages",
        "X-Export-Characters",
        "X-Export-Adapted",
        "X-Export-Warnings",
    ],
)

logger = logging.getLogger("cv_creator.api")

# Orígenes permitidos: tiene que coincidir con `allow_origins` de más abajo.
ALLOWED_ORIGINS = ("http://localhost:3000",)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Los errores no controlados salen por fuera del middleware de CORS.

    Sin las cabeceras el navegador no puede leer la respuesta y muestra un
    error de red opaco (Firefox: "NetworkError when attempting to fetch
    resource.") en vez del motivo real. El detalle se registra en el servidor.
    """
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    origin = request.headers.get("origin")
    headers = {}
    if origin in ALLOWED_ORIGINS:
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor. Probá de nuevo en unos segundos."},
        headers=headers,
    )


@app.on_event("startup")
def on_startup():
    create_all_tables()
    print("Tablas creadas/verificadas correctamente")

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(cv_router)
app.include_router(experience_router)
app.include_router(skill_router)
app.include_router(education_router)
app.include_router(chat_router)
app.include_router(log_router)
app.include_router(skill_catalog_router)
app.include_router(achievement_router)
app.include_router(program_router)
app.include_router(language_router)

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
