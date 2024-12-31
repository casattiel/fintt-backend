from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from firebase_admin import auth, credentials, initialize_app
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
import mysql.connector
import jwt
import datetime
import openai
import os

# Configuración de Firebase desde el archivo secreto en Render
firebase_credentials_path = "/etc/secrets/firebase_credentials.json"
if not os.path.exists(firebase_credentials_path):
    raise FileNotFoundError(f"El archivo {firebase_credentials_path} no existe.")

cred = credentials.Certificate(firebase_credentials_path)
initialize_app(cred)

# Configuración de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("La clave de API de OpenAI no está configurada. Verifica las variables de entorno.")

# Configuración de la conexión a MySQL
db = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "fint_user"),
    password=os.getenv("DB_PASSWORD", "casattiel"),
    database=os.getenv("DB_NAME", "fint_db")
)

# Inicialización de la app FastAPI
app = FastAPI()

# Configuración JWT
SECRET_KEY = os.getenv("SECRET_KEY", "YOUR_SECRET_KEY")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambiar según el dominio permitido en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de datos
class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ChatRequest(BaseModel):
    message: str

# Función auxiliar para crear un token JWT
def create_jwt_token(user):
    payload = {
        "sub": user["uid"],
        "name": user["name"],
        "email": user["email"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# Endpoints
@app.get("/")
def root():
    return {"message": "Welcome to FINTT, your global financial advisor!"}

@app.post("/register")
def register_user(request: RegisterRequest):
    try:
        user = auth.create_user(email=request.email, password=request.password, display_name=request.name)
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (name, email, country) VALUES (%s, %s, 'Unknown')",
                       (request.name, request.email))
        db.commit()
        return {"message": f"User {request.name} registered successfully!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error registering user: {str(e)}")

@app.post("/login")
def login_user(request: LoginRequest):
    try:
        user = auth.get_user_by_email(request.email)
        token = create_jwt_token({"uid": user.uid, "name": user.display_name, "email": user.email})
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Login failed: {str(e)}")

@app.post("/chat")
def fintt_chat(request: ChatRequest):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=request.message,
            max_tokens=100,
            temperature=0.7
        )
        return {"response": response.choices[0].text.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error with Fintt Chat: {str(e)}")

# Endpoint de salud para Render
@app.get("/health")
def health_check():
    return {"status": "ok"}
