import os
import mysql.connector.pooling
from mysql.connector import Error
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import krakenex
from subscriptions import router as subscriptions_router
from fintto_chat import router as fintto_chat_router

# Configuración directa de claves (usando las claves proporcionadas por ti)
KRAKEN_API_KEY = "SzQ41RAGaxOFOxiqs88aQis8eCmGPJ5VpoR1Vz2ypP8kksjYUVXcWCQ7"
KRAKEN_SECRET_KEY = "20dsWMlMOkGTEtRLKUWXYmR8DJNEzWnIHZyt3u7HxtkDNlcAJD6j7IIh0t0hQHe7fEPuSYJ7XXStTzk/A=="
DB_HOST = "fint-db.ctkokc288j85.us-east-2.rds.amazonaws.com"
DB_USER = "fint_user"
DB_PASSWORD = "JesusismyLord33!"
DB_NAME = "fint_db"

# Inicializar la API de Kraken
kraken_api = krakenex.API()
kraken_api.key = KRAKEN_API_KEY
kraken_api.secret = KRAKEN_SECRET_KEY

# Configuración de la aplicación FastAPI
app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de la base de datos (pool de conexiones)
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
)

@app.on_event("startup")
async def startup_event():
    try:
        conn = db_pool.get_connection()
        if conn.is_connected():
            print("Conexión a la base de datos exitosa")
            conn.close()
    except Error as err:
        raise Exception(f"Error al conectar con MySQL: {err}")

@app.get("/")
async def root():
    return {"message": "FINTT Backend está funcionando con integración de Kraken."}

# Función para hashear contraseñas
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Modelos de datos
class LoginData(BaseModel):
    email: str
    password: str

class RegisterData(BaseModel):
    name: str
    email: str
    password: str
    country: str

class TradeData(BaseModel):
    user_id: int
    crypto_pair: str  # Ejemplo: "XXBTZUSD" para BTC/USD en Kraken
    amount: float
    action: str  # "buy" o "sell"

class SubscriptionUpgrade(BaseModel):
    user_id: int
    new_plan: str  # "basic" o "premium"

# Endpoint para registrar usuarios
@app.post("/register")
async def register(data: RegisterData):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        hashed_password = hash_password(data.password)
        query = "INSERT INTO users (name, email, password, country) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (data.name, data.email, hashed_password, data.country))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "Usuario registrado exitosamente"}
    except mysql.connector.IntegrityError:
        raise HTTPException(status_code=400, detail="Correo ya registrado")
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error al registrar usuario: {err}")

# Endpoint para iniciar sesión
@app.post("/login")
async def login(data: LoginData):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        hashed_password = hash_password(data.password)
        query = "SELECT * FROM users WHERE email = %s AND password = %s"
        cursor.execute(query, (data.email, hashed_password))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        cursor.close()
        conn.close()
        return {"message": "Inicio de sesión exitoso", "user": {"id": user["id"], "name": user["name"], "email": user["email"]}}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error durante el inicio de sesión: {err}")

# Endpoint para realizar trading con Kraken
@app.post("/trade")
async def execute_trade(data: TradeData):
    try:
        if data.action not in ["buy", "sell"]:
            raise HTTPException(status_code=400, detail="Acción inválida. Usa 'buy' o 'sell'.")

        # Ejecución de la operación
        response = kraken_api.query_private('AddOrder', {
            'pair': data.crypto_pair,
            'type': data.action,
            'ordertype': 'market',
            'volume': data.amount
        })

        if response.get("error"):
            raise HTTPException(status_code=500, detail=f"Error en Kraken API: {response['error']}")

        return {"message": "Operación ejecutada exitosamente", "details": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ejecutando la operación: {e}")

# Endpoint para actualizar suscripción
@app.post("/subscriptions/upgrade")
async def upgrade_subscription(data: SubscriptionUpgrade):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        query = "UPDATE users SET subscription_plan = %s WHERE id = %s"
        cursor.execute(query, (data.new_plan, data.user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "Suscripción actualizada exitosamente", "new_plan": data.new_plan}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error al actualizar suscripción: {err}")

# Endpoint para obtener precios de mercado
@app.get("/market/prices")
async def get_market_prices():
    try:
        response = kraken_api.query_public('Ticker', {'pair': 'XXBTZUSD'})
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener precios del mercado: {e}")

# Incluir routers adicionales
app.include_router(subscriptions_router)
app.include_router(fintto_chat_router, prefix="/api")
