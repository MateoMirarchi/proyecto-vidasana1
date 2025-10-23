from pymongo import MongoClient
import redis
import datetime
import json

# Conexión MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["vidasana"]
pacientes = db["pacientes"]

# Conexión Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def validar_paciente(data):
    campos = ["nombre", "dni", "fechaNacimiento", "mail", "telefono", "rol", "sexo", "historiaClinica"]
    return all(c in data for c in campos) and data["rol"] in ["paciente", "medico"]

def guardar_paciente(data):
    if not validar_paciente(data):
        print("Datos inválidos")
        return
    pacientes.insert_one(data)
    redis_client.setex(f"acceso:{data['dni']}", 3600, "activo")  # TTL 1 hora
    print(f"Paciente {data['nombre']} guardado")
    print(f"Control de acceso habilitado por 1 hora para DNI {data['dni']}")

def consultar_paciente(dni):
    paciente = pacientes.find_one({"dni": dni})
    if paciente:
        print(json.dumps(paciente, default=str, indent=2))
    else:
        print("❌ Paciente no encontrado")

# Ejemplo de inserción
if __name__ == "__main__":
    nuevo = {
        "nombre": "Lucía Gómez",
        "dni": "12345678",
        "fechaNacimiento": "1990-05-12",
        "mail": "lucia@example.com",
        "telefono": "1122334455",
        "rol": "paciente",
        "sexo": "femenino",
        "historiaClinica": [
            {"fecha": "2025-10-01", "diagnostico": "Hipertensión", "tratamiento": "Ejercicio y dieta"}
        ]
    }
    guardar_paciente(nuevo)
    consultar_paciente("12345678")
