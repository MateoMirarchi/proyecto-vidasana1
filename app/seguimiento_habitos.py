from pymongo import MongoClient
import datetime

# Conexión MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["vidasana"]
habitos = db["habitos"]

def registrar_habito(dni, sueño, alimentacion, sintomas):
    registro = {
        "dni": dni,
        "fecha": datetime.datetime.now().strftime("%Y-%m-%d"),
        "sueño": sueño,
        "alimentacion": alimentacion,
        "sintomas": sintomas
    }
    habitos.insert_one(registro)
    print(f"✅ Registro de hábitos guardado para DNI {dni}")

def consultar_habitos(dni):
    registros = habitos.find({"dni": dni})
    for r in registros:
        print(r)

# Ejemplo
if __name__ == "__main__":
    registrar_habito("12345678", "7 horas", "Vegetariana", "Dolor de cabeza")
    consultar_habitos("12345678")
