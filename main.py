import os
import mysql.connector.pooling
from mysql.connector import Error
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import hashlib

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

# Función para hashear contraseñas
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Endpoint para registro
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

# Funcionalidades de la base de datos de usuarios
@app.get("/users")
async def get_users():
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        return users
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error al obtener usuarios: {err}")

@app.post("/add_user")
async def add_user(name: str, email: str, country: str):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        query = "INSERT INTO users (name, email, country) VALUES (%s, %s, %s)"
        cursor.execute(query, (name, email, country))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "Usuario añadido exitosamente"}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error al añadir usuario: {err}")

@app.delete("/delete_user/{user_id}")
async def delete_user(user_id: int):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        query = "DELETE FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "Usuario eliminado exitosamente"}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error al eliminar usuario: {err}")

# Funcionalidades de Fintto Chat
@app.post("/fintto_chat")
async def fintto_chat(question: str):
    try:
        response = f"Fintto Chat dice: La respuesta a tu pregunta '{question}' está en proceso de desarrollo."
        return {"question": question, "response": response}
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Error en Fintto Chat: {err}")

# Funcionalidades de DeFintt Loans
@app.post("/apply_loan")
async def apply_loan(user_id: int, amount: float, duration_months: int):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        query = """
        INSERT INTO loans (user_id, amount, duration_months, status)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, amount, duration_months, "pending"))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "Solicitud de préstamo enviada exitosamente", "loan_id": cursor.lastrowid}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error al solicitar préstamo: {err}")

@app.get("/loans/{user_id}")
async def get_loans(user_id: int):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM loans WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        loans = cursor.fetchall()
        cursor.close()
        conn.close()
        return loans
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error al obtener préstamos: {err}")

# Funcionalidades de Fintt Broker
@app.post("/invest")
async def invest(user_id: int, asset: str, amount: float):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        query = """
        INSERT INTO investments (user_id, asset, amount)
        VALUES (%s, %s, %s)
        """
        cursor.execute(query, (user_id, asset, amount))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "Inversión realizada exitosamente", "investment_id": cursor.lastrowid}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error al realizar inversión: {err}")

@app.get("/investments/{user_id}")
async def get_investments(user_id: int):
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM investments WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        investments = cursor.fetchall()
        cursor.close()
        conn.close()
        return investments
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error al obtener inversiones: {err}")
