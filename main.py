import os
import mysql.connector.pooling
from mysql.connector import Error
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import hashlib
from datetime import datetime
from fastapi import APIRouter

# Carga variables de entorno desde Render o un archivo .env
load_dotenv()

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia "*" por tu dominio de Netlify si quieres restringirlo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración directa con los datos de tu base de datos en Amazon RDS
db_config = {
    "host": os.getenv("DB_HOST", "fint-db.ctkokc288j85.us-east-2.rds.amazonaws.com"),
    "user": os.getenv("DB_USER", "fint_user"),
    "password": os.getenv("DB_PASSWORD", "JesusismyLord33!"),
    "database": os.getenv("DB_NAME", "fint_db"),
}

# Crea un pool de conexiones
db_pool = mysql.connector.pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **db_config)

@app.on_event("startup")
async def startup_event():
    try:
        conn = db_pool.get_connection()
        if conn.is_connected():
            print("Conexión exitosa a la base de datos con pool de conexiones")
            conn.close()
    except Error as err:
        raise Exception(f"Error conectando a MySQL: {err}")

@app.get("/")
async def root():
    return {"message": "FINTT Backend is running with connection pool!"}

# Modelo para el login
class LoginData(BaseModel):
    email: str
    password: str

# Modelo para el registro
class RegisterData(BaseModel):
    name: str
    email: str
    password: str
    country: str

# Modelo para suscripciones
class SubscriptionData(BaseModel):
    user_id: int
    plan: str

# Función para hashear contraseñas
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Endpoints para registro
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
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado")
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error al registrar usuario: {err}")

# Endpoint para login
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
        raise HTTPException(status_code=500, detail=f"Error al iniciar sesión: {err}")

# Router para Fintto Chat
chat_router = APIRouter()

class ChatMessage(BaseModel):
    question: str

@chat_router.post("/chat")
async def fintto_chat(data: ChatMessage):
    try:
        user_question = data.question.lower()

        # Lógica básica para respuestas
        if "bolsa" in user_question:
            response = "Para invertir en la bolsa, necesitas abrir una cuenta con un broker y elegir tus activos."
        elif "criptomonedas" in user_question:
            response = "Las criptomonedas son activos digitales que puedes adquirir en plataformas como Binance o Coinbase."
        else:
            response = f"Fintto Chat dice: La respuesta a tu pregunta '{data.question}' será más detallada en el futuro."

        return {"question": data.question, "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en Fintto Chat: {str(e)}")

app.include_router(chat_router, prefix="/api")

# Endpoint para suscripciones
@app.post("/api/subscribe")
async def subscribe(data: SubscriptionData):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        query = "INSERT INTO subscriptions (user_id, plan, created_at) VALUES (%s, %s, %s)"
        cursor.execute(query, (data.user_id, data.plan, datetime.now()))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "Suscripción creada exitosamente"}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error al crear suscripción: {err}")

@app.get("/api/subscriptions/{user_id}")
async def get_subscriptions(user_id: int):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM subscriptions WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        subscriptions = cursor.fetchall()
        cursor.close()
        conn.close()
        return subscriptions
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error al obtener suscripciones: {err}")
