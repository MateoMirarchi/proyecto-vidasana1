from gestion_pacientes import guardar_paciente, consultar_paciente
from seguimiento_habitos import registrar_habito, consultar_habitos
from interaccion_red import crear_usuario, seguir, mostrar_red
from gestion_turnos import registrar_turno, evaluar_riesgo
from pymongo import MongoClient
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["vidasana"]
turnos = db["turnos"]

def crear_usuario_console():
    print("Creación de usuario")
    data = {
        "nombre": input("Nombre: "),
        "apellido": input("Apellido: "),
        "dni": input("DNI: "),
        "fechaNacimiento": input("Fecha de nacimiento (YYYY-MM-DD): "),
        "mail": input("Email: "),
        "telefono": input("Teléfono: "),
        "rol": input("Rol (paciente/medico): "),
        "sexo": input("Sexo: "),
        "historiaClinica": []
    }
    guardar_paciente(data)
    try:
        crear_usuario(None, data["dni"], data["nombre"], data["apellido"],
                       data["fechaNacimiento"], data["mail"],
                       data["telefono"], data["rol"], data["sexo"])
    except Exception as e:
        print(f"Error al crear usuario: {e}")

def iniciar_sesion():
    dni = input("Ingrese su DNI: ")
    acceso = redis_client.get(f"acceso:{dni}")
    if acceso:
        print("Sesión iniciada")
        return consultar_usuario(dni)
    else:
        print("Acceso expirado o no registrado")
        return None

def consultar_usuario(dni):
    mongo_client = MongoClient("mongodb://localhost:27017/")
    db = mongo_client["vidasana"]
    return db["pacientes"].find_one({"dni": dni})

def registrar_habito_console(usuario):
    print("Registro de hábitos")
    sueño = input("Horas de sueño: ")
    alimentacion = input("Tipo de alimentación: ")
    sintomas = input("Síntomas: ")
    registrar_habito(usuario["dni"], sueño, alimentacion, sintomas)

def registrar_turno_console(usuario):
    print("Registro de turno")
    fecha = input("Fecha del turno (YYYY-MM-DD): ")
    especialidad = input("Especialidad: ")
    medico = input("DNI del médico: ")
    registrar_turno(usuario["dni"], fecha, especialidad, medico)

def mostrar_red_console():
    print("\n🔗 Red médico-paciente")
    try:
        mostrar_red(None)
    except Exception as e:
        print(f"⚠️ Error al consultar red: {e}")

def seguir_paciente_console(usuario):
    print("\n➕ Seguir paciente")
    dni_paciente = input("DNI del paciente a seguir: ")
    try:
        seguir(None, usuario["dni"], dni_paciente)
        print(f"✅ Ahora sigue al paciente {dni_paciente}")
    except Exception as e:
        print(f"⚠️ Error al seguir paciente: {e}")

def consultar_habitos_console(usuario):
    consultar_habitos(usuario["dni"])

def evaluar_riesgo_console(usuario):
    evaluar_riesgo(usuario["dni"])
