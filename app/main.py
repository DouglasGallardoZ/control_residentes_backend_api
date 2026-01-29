from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.interfaces.routers import (
    qr_router, cuentas_router, residentes_router, 
    propietarios_router, miembros_router, accesos_router
)
from app.infrastructure.db import Base, engine

# Crear tablas (comentar en producción si usas Alembic)
Base.metadata.create_all(bind=engine)

settings = get_settings()

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(qr_router.router)
app.include_router(cuentas_router.router)
app.include_router(residentes_router.router)
app.include_router(propietarios_router.router)
app.include_router(miembros_router.router)
app.include_router(accesos_router.router)


@app.get("/", tags=["Health"])
def root():
    """Endpoint raíz para verificar que la API está en funcionamiento"""
    return {
        "mensaje": "API de Control de Acceso Residencial",
        "version": settings.API_VERSION,
        "estado": "operacional"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Endpoint para verificar salud de la aplicación"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
