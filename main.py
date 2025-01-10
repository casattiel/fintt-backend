from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.auth_routes import router as auth_router
from utils.db import init_db

# Configurar la app FastAPI
app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia esto en producción para mayor seguridad
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar conexión con la base de datos al arrancar
@app.on_event("startup")
async def startup_event():
    init_db()
    print("Database initialized.")

# Rutas principales
@app.get("/")
async def root():
    return {"message": "FINTT Backend is running!"}

# Incluir rutas de autenticación
app.include_router(auth_router, prefix="", tags=["Authentication"])
