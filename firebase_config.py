import firebase_admin
from firebase_admin import credentials

# Inicializa Firebase con la clave de servicio
cred = credentials.Certificate("serviceAccountKey.json")  # Asegúrate de que el nombre del archivo JSON es correcto
firebase_admin.initialize_app(cred)
