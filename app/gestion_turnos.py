from pymongo import MongoClient
import redis
import datetime

# Conexión MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["vidasana"]
turnos = db["turnos"]
pacientes = db["pacientes"]

# Conexión Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def registrar_turno(dni, fecha, especialidad):
    turno = {
        "dni": dni,
        "fecha": fecha,
        "especialidad": especialidad
    }
    turnos.insert_one(turno)
    redis_client.setex(f"recordatorio:{dni}:{fecha}", 600, f"Turno de {especialidad} el {fecha}")
    print(f"📅 Turno registrado para DNI {dni}")
    print(f"⏰ Recordatorio activo por 10 minutos")

def evaluar_riesgo(dni):
    paciente = pacientes.find_one({"dni": dni})
    if not paciente:
        print("❌ Paciente no encontrado")
        return

    score = 0
    for hc in paciente.get("historiaClinica", []):
        if "hipertensión" in hc["diagnostico"].lower():
            score += 2
        if "diabetes" in hc["diagnostico"].lower():
            score += 3

    if score >= 3:
        print(f"⚠️ Riesgo alto detectado para {paciente['nombre']}")
        print(f"📧 Simulación de envío de email a {paciente['mail']}: 'Se recomienda consulta urgente.'")
    else:
        print(f"✅ Riesgo bajo para {paciente['nombre']}")

# Ejemplo
if __name__ == "__main__":
    registrar_turno("12345678", "2025-10-25", "cardiología")
    evaluar_riesgo("12345678")
