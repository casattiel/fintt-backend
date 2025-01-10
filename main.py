from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials, initialize_app
from routers.auth_routes import router as auth_router
from utils.db import init_db
import os

def initialize_firebase():
    """
    Inicializa Firebase usando las variables de entorno.
    """
    try:
        # Depurar el contenido del private_key para asegurar que tiene saltos de línea reales
        private_key = os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n")
        
        if not private_key.startswith("-----BEGIN PRIVATE KEY-----"):
            print("❌ Formato incorrecto de FIREBASE_PRIVATE_KEY. Verifica los saltos de línea.")
            raise ValueError("Formato incorrecto de FIREBASE_PRIVATE_KEY.")
        
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": private_key,
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL"),
        })
        initialize_app(cred)
        print("✅ Firebase inicializado correctamente.")
    except Exception as e:
        print(f"❌ Error al inicializar Firebase: {e}")
        raise

# Inicializar Firebase
initialize_firebase()

# Crear la aplicación FastAPI
app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes (restringe en producción)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar la base de datos
@app.on_event("startup")
async def startup_event():
    try:
        init_db()
        print("✅ Base de datos inicializada correctamente.")
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {e}")
        raise

# Ruta raíz
@app.get("/")
async def root():
    return {"message": "FINTT Backend funcionando con Firebase inicializado correctamente."}

# Incluir las rutas de autenticación
app.include_router(auth_router, prefix="", tags=["Authentication"])
