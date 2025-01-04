import os
import mysql.connector
from mysql.connector import Error
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

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
DB_HOST = os.getenv("DB_HOST", "fint-db.ctkokc288j85.us-east-2.rds.amazonaws.com")
DB_NAME = os.getenv("DB_NAME", "fint_db")
DB_USER = os.getenv("DB_USER", "fint_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "JesusismyLord33!")

@app.on_event("startup")
async def startup_event():
    try:
        global db
        db = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )
        if db.is_connected():
            print("Conexión exitosa a la base de datos")
    except Error as err:
        raise Exception(f"Error conectando a MySQL: {err}")

@app.on_event("shutdown")
async def shutdown_event():
    if db.is_connected():
        db.close()
        print("Conexión a la base de datos cerrada")

@app.get("/")
async def root():
    return {"message": "FINTT Backend is running!"}

# Modelo para el login
class LoginData(BaseModel):
    email: str
    password: str

# Endpoint para login
@app.post("/login")
async def login(data: LoginData):
    try:
        cursor = db.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE email = %s AND password = %s"
        cursor.execute(query, (data.email, data.password))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        cursor.close()
        return {"message": "Inicio de sesión exitoso", "user": user}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error al iniciar sesión: {err}")

# Funcionalidades de la base de datos de usuarios
@app.get("/users")
async def get_users():
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        return users
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error al obtener usuarios: {err}")

@app.post("/add_user")
async def add_user(name: str, email: str, country: str):
    try:
        cursor = db.cursor()
        query = "INSERT INTO users (name, email, country) VALUES (%s, %s, %s)"
        cursor.execute(query, (name, email, country))
        db.commit()
        return {"message": "Usuario añadido exitosamente"}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error al añadir usuario: {err}")

@app.delete("/delete_user/{user_id}")
async def delete_user(user_id: int):
    try:
        cursor = db.cursor()
        query = "DELETE FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        db.commit()
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
        cursor = db.cursor()
        query = """
        INSERT INTO loans (user_id, amount, duration_months, status)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, amount, duration_months, "pending"))
        db.commit()
        return {"message": "Solicitud de préstamo enviada exitosamente", "loan_id": cursor.lastrowid}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error al solicitar préstamo: {err}")

@app.get("/loans/{user_id}")
async def get_loans(user_id: int):
    try:
        cursor = db.cursor(dictionary=True)
        query = "SELECT * FROM loans WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        loans = cursor.fetchall()
        return loans
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error al obtener préstamos: {err}")

# Funcionalidades de Fintt Broker
@app.post("/invest")
async def invest(user_id: int, asset: str, amount: float):
    try:
        cursor = db.cursor()
        query = """
        INSERT INTO investments (user_id, asset, amount)
        VALUES (%s, %s, %s)
        """
        cursor.execute(query, (user_id, asset, amount))
        db.commit()
        return {"message": "Inversión realizada exitosamente", "investment_id": cursor.lastrowid}
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error al realizar inversión: {err}")

@app.get("/investments/{user_id}")
async def get_investments(user_id: int):
    try:
        cursor = db.cursor(dictionary=True)
        query = "SELECT * FROM investments WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        investments = cursor.fetchall()
        return investments
    except Error as err:
        raise HTTPException(status_code=500, detail=f"Error al obtener inversiones: {err}")
