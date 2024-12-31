import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from firebase_admin import credentials, initialize_app, auth
import mysql.connector

# Cargar variables de entorno
load_dotenv()

# Inicializar Firebase
firebase_credentials_path = "/etc/secrets/firebase_credentials.json"
try:
    cred = credentials.Certificate(firebase_credentials_path)
    initialize_app(cred)
except Exception as e:
    raise Exception(f"Error inicializando Firebase: {e}")

# Inicializar conexión a MySQL
try:
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306))
    )
except mysql.connector.Error as err:
    raise Exception(f"Error conectando a MySQL: {err}")

# Inicializar FastAPI
app = FastAPI()

# Modelos de datos
class User(BaseModel):
    email: str
    name: str

class LoanRequest(BaseModel):
    user_id: int
    amount: float
    duration: int  # en meses

class Trade(BaseModel):
    user_id: int
    crypto: str
    amount: float
    trade_type: str  # "buy" o "sell"

# Rutas de ejemplo

@app.get("/")
async def root():
    return {"message": "FINTT Backend is running successfully!"}

# Registro de usuarios
@app.post("/register")
async def register_user(user: User):
    try:
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (email, name) VALUES (%s, %s)", (user.email, user.name))
        db.commit()
        return {"message": "User registered successfully!"}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error registrando usuario: {err}")

# Obtener todos los usuarios
@app.get("/users")
async def get_users():
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        return {"users": users}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error obteniendo usuarios: {err}")

# Solicitar préstamo
@app.post("/loans/request")
async def request_loan(loan: LoanRequest):
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO loans (user_id, amount, duration) VALUES (%s, %s, %s)",
            (loan.user_id, loan.amount, loan.duration)
        )
        db.commit()
        return {"message": "Loan request submitted successfully!"}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error solicitando préstamo: {err}")

# Obtener préstamos de un usuario
@app.get("/loans/{user_id}")
async def get_user_loans(user_id: int):
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM loans WHERE user_id = %s", (user_id,))
        loans = cursor.fetchall()
        return {"loans": loans}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error obteniendo préstamos: {err}")

# Realizar trading (Broker Portal)
@app.post("/broker/trade")
async def broker_trade(trade: Trade):
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO trades (user_id, crypto, amount, trade_type) VALUES (%s, %s, %s, %s)",
            (trade.user_id, trade.crypto, trade.amount, trade.trade_type)
        )
        db.commit()
        return {"message": f"Trade {'bought' if trade.trade_type == 'buy' else 'sold'} successfully!"}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error realizando trading: {err}")

# Obtener transacciones del Broker Portal
@app.get("/broker/trades/{user_id}")
async def get_user_trades(user_id: int):
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM trades WHERE user_id = %s", (user_id,))
        trades = cursor.fetchall()
        return {"trades": trades}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error obteniendo transacciones: {err}")

# Asesor financiero (ejemplo básico con respuesta fija)
@app.get("/advisor")
async def financial_advisor():
    advice = "Diversifica tus inversiones en activos seguros y de mayor riesgo según tu perfil."
    return {"advice": advice}
