from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from firebase_admin import auth, credentials, initialize_app
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
import mysql.connector
import jwt
import datetime
import openai

# Inicializa Firebase
cred = credentials.Certificate("C:\\Users\\Salaz\\Videos\\FINTT\\backend\\serviceAccountKey.json")
initialize_app(cred)

# Configuración de OpenAI
openai.api_key = "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"

# Conexión a MySQL
db = mysql.connector.connect(
    host="localhost",
    user="fint_user",
    password="casattiel",
    database="fint_db"
)

# Inicializa FastAPI
app = FastAPI()

# Configuración JWT
SECRET_KEY = "YOUR_SECRET_KEY"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos
class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ChatRequest(BaseModel):
    message: str

# Función auxiliar: Crear JWT
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
def fintto_chat(request: ChatRequest):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=request.message,
            max_tokens=100,
            temperature=0.7
        )
        return {"response": response.choices[0].text.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error with Fintto Chat: {str(e)}")
