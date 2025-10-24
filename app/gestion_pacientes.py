import datetime
import json
from typing import Dict, Optional, List
import db

def validar_paciente(data: Dict) -> bool:
    """Valida que un diccionario tenga todos los campos requeridos para un paciente/médico."""
    campos = ["nombre", "dni", "fechaNacimiento", "mail", "telefono", "rol", "sexo", "password"]
    faltantes = [c for c in campos if c not in data or data.get(c) is None or str(data.get(c)).strip() == ""]
    if faltantes:
        print(f" Campos faltantes o vacíos: {', '.join(faltantes)}")
        return False

    # Normalizar rol para validación flexible
    rol = str(data.get("rol")).strip().lower()
    if rol not in ["paciente", "medico"]:
        print(" Rol inválido. Debe ser 'paciente' o 'medico'")
        return False

    # Validar formato de fecha esperado
    try:
        datetime.datetime.strptime(str(data.get("fechaNacimiento")), "%Y-%m-%d")
    except ValueError:
        print(" Fecha inválida. Use el formato YYYY-MM-DD")
        return False

    # Asegurar DNI numérico
    dni_str = str(data.get("dni")).strip()
    if not dni_str.isdigit():
        print(" DNI inválido. Debe contener solo dígitos")
        return False

    # Validar longitud mínima de contraseña
    if len(str(data.get("password"))) < 8:
        print(" La contraseña debe tener al menos 8 caracteres")
        return False

    return True

def guardar_paciente(data: Dict) -> Optional[str]:
    """Guarda un paciente/médico en MongoDB y habilita su acceso en Redis.
    
    Args:
        data: Diccionario con los datos del paciente/médico
        
    Returns:
        str: ID del documento creado si es exitoso
        None: Si hay error de validación o en la inserción
    """
    # Asegurar historia clínica vacía si no existe
    if "historiaClinica" not in data:
        data["historiaClinica"] = []
        
    if not validar_paciente(data):
        print("Datos inválidos")
        return None

    try:
        # Verificar si ya existe
        if db.find_one(db.pacientes, {"dni": data["dni"]}):
            print(f"Ya existe un usuario con DNI {data['dni']}")
            return None
            
        # Hash de la contraseña antes de guardar
        password = data["password"]
        data["password"] = db.hash_password(password)
        
        # Insertar en MongoDB
        _id = db.insert_one(db.pacientes, data)
        
        # Establecer acceso en Redis
        db.set_access_token(data["dni"])
        
        print(f"{data['rol'].title()} {data['nombre']} guardado correctamente")
        return _id
        
    except Exception as e:
        print(f"Error al guardar: {str(e)}")
        return None

def actualizar_historia_clinica(dni: str, diagnostico: str, tratamiento: str) -> bool:
    """Añade una entrada a la historia clínica del paciente.
    
    Args:
        dni: DNI del paciente
        diagnostico: Diagnóstico médico
        tratamiento: Tratamiento indicado
        
    Returns:
        bool: True si se actualizó correctamente
    """
    entrada = {
        "fecha": datetime.datetime.now().strftime("%Y-%m-%d"),
        "diagnostico": diagnostico,
        "tratamiento": tratamiento
    }
    
    result = db.update_one(
        db.pacientes,
        {"dni": dni},
        {"$push": {"historiaClinica": entrada}}
    )
    
    if result:
        print(f"Historia clínica actualizada para DNI {dni}")
        return True
    else:
        print(f"No se pudo actualizar la historia clínica para DNI {dni}")
        return False

def consultar_paciente(dni: str) -> Optional[Dict]:
    """Consulta un paciente por DNI.
    
    Args:
        dni: DNI del paciente/médico
        
    Returns:
        Dict: Datos del paciente si existe
        None: Si no existe
    """
    paciente = db.find_one(db.pacientes, {"dni": dni})
    if not paciente:
        print("❌ Paciente no encontrado")
        return None

    # Imprimir paciente completo
    print(json.dumps(paciente, default=str, indent=2))

    # Consultar y mostrar turnos asociados al paciente
    try:
        turnos = list(db.turnos.find({"dni": dni}))
        if not turnos:
            print("\nNo hay turnos asignados a este paciente")
        else:
            print(f"\nTurnos asignados al paciente (DNI {dni}):")
            for t in turnos:
                # Incluir información completa del turno
                print("------------------------------")
                for k, v in t.items():
                    print(f"{k}: {v}")
            print("------------------------------")
    except Exception as e:
        print(f"⚠️ Error al consultar turnos del paciente: {e}")

    return paciente

if __name__ == "__main__":
    # Ejemplo: crear médico
    medico = {
        "nombre": "Dr. Juan Pérez",
        "dni": "30123456",
        "fechaNacimiento": "1980-05-15",
        "mail": "dr.perez@hospital.com",
        "telefono": "1155667788",
        "rol": "medico",
        "sexo": "masculino",
        "historiaClinica": []
    }
    guardar_paciente(medico)
    
    # Ejemplo: crear paciente y actualizar historia
    paciente = {
        "nombre": "María López",
        "dni": "40123456",
        "fechaNacimiento": "1990-10-20",
        "mail": "maria@gmail.com",
        "telefono": "1145678901",
        "rol": "paciente",
        "sexo": "femenino"
    }
    if guardar_paciente(paciente):
        actualizar_historia_clinica(
            paciente["dni"],
            "Hipertensión arterial",
            "Dieta hiposódica, ejercicio moderado"
        )
        consultar_paciente(paciente["dni"])
