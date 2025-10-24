from datetime import datetime, timedelta
from typing import Dict, List, Optional
import db

def validar_turno(data: Dict) -> bool:
    """Valida los datos de un turno médico."""
    campos = ["dni", "fecha", "especialidad", "medico_dni"]
    if not all(c in data for c in campos):
        return False
        
    try:
        fecha_turno = datetime.strptime(data["fecha"], "%Y-%m-%d %H:%M")
        if fecha_turno < datetime.now():
            return False
    except ValueError:
        return False
        
    return True

def registrar_turno(dni: str, fecha: str, especialidad: str, medico_dni: str) -> Optional[str]:
    """Registra un turno médico y configura recordatorio.
    
    Args:
        dni: DNI del paciente
        fecha: Fecha y hora del turno (formato: YYYY-MM-DD HH:MM)
        especialidad: Especialidad médica
        medico_dni: DNI del médico
        
    Returns:
        str: ID del turno si se registra correctamente
        None: Si hay error
    """
    # Verificar que existan paciente y médico
    paciente = db.find_one(db.pacientes, {"dni": dni, "rol": "paciente"})
    medico = db.find_one(db.pacientes, {"dni": medico_dni, "rol": "medico"})
    
    if not paciente or not medico:
        print("Paciente o médico no encontrado")
        return None
        
    turno = {
        "dni": dni,
        "fecha": fecha,
        "especialidad": especialidad,
        "medico_dni": medico_dni,
        "estado": "programado",
        "creado": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if not validar_turno(turno):
        print("Datos del turno inválidos")
        return None

    try:
        # Guardar en MongoDB
        _id = db.insert_one(db.turnos, turno)
        
        # Configurar recordatorio en Redis
        mensaje = (f"Recordatorio: Turno de {especialidad}\n"
                  f"Fecha: {fecha}\n"
                  f"Dr/a. {medico['nombre']}")
        
        db.set_reminder(dni, fecha, mensaje)
        
        # Simular email de confirmación
        db.simular_email(
            paciente["mail"],
            "Turno Médico Confirmado",
            mensaje
        )
        
        print(f"Turno registrado exitosamente")
        print(f"Recordatorio configurado para 10 minutos antes")
        return _id
        
    except Exception as e:
        print(f"Error al registrar turno: {str(e)}")
        return None

def evaluar_riesgo(dni: str) -> Optional[int]:
    """Evalúa el riesgo de un paciente según su historia clínica.
    
    Args:
        dni: DNI del paciente
        
    Returns:
        int: Puntaje de riesgo (0-10)
        None: Si hay error o no existe el paciente
    """
    paciente = db.find_one(db.pacientes, {"dni": dni})
    if not paciente:
        print("Paciente no encontrado")
        return None

    score = 0
    diagnosticos_riesgo = {
        "hipertension": 2,
        "diabetes": 3,
        "obesidad": 2,
        "cardio": 2,
        "cancer": 3,
        "fiebre alta": 1,
        "dificultad respirar": 2,
        "angina": 1
    }

    for hc in paciente.get("historiaClinica", []):
        diag = hc.get("diagnostico", "").lower()
        for keyword, points in diagnosticos_riesgo.items():
            if keyword in diag:
                score += points

    score = min(10, score)  # Cap at 10
    
    mensaje = ""
    if score >= 7:
        mensaje = "RIESGO ALTO - Se requiere atención inmediata"
    elif score >= 4:
        mensaje = "RIESGO MEDIO - Se recomienda chequeo preventivo"
    else:
        mensaje = "RIESGO BAJO - Mantener controles de rutina"

    print(f"\nEvaluación de Riesgo para {paciente['nombre']}")
    print(f"Puntaje: {score}/10")
    print(mensaje)

    # Si el riesgo es alto, enviar alerta
    if score >= 7:
        db.simular_email(
            paciente["mail"],
            "Alerta Médica - Riesgo Detectado",
            f"Estimado/a {paciente['nombre']},\n\n"
            f"Se ha detectado un nivel de riesgo alto en su perfil médico.\n"
            f"Por favor, contacte a su médico de cabecera a la brevedad.\n\n"
            f"Nivel de Riesgo: {score}/10\n"
            f"Recomendación: Solicitar turno urgente para evaluación completa."
        )

    return score

def consultar_turnos_paciente(dni: str) -> List[Dict]:
    """Consulta todos los turnos de un paciente ordenados por fecha."""
    turnos = list(db.turnos.find(
        {"dni": dni},
        sort=[("fecha", 1)]
    ))
    
    if not turnos:
        print("No se encontraron turnos")
    else:
        for t in turnos:
            medico = db.find_one(db.pacientes, {"dni": t["medico_dni"]})
            print(f"\n Turno {t['especialidad']}")
            print(f"Fecha: {t['fecha']}")
            print(f"Médico: {medico['nombre'] if medico else 'No disponible'}")
            
    return turnos

if __name__ == "__main__":
    # Ejemplo: registrar turno
    turno_id = registrar_turno(
        "40123456",  # DNI paciente
        "2025-10-25 15:30",  # Fecha y hora
        "Cardiología",
        "30123456"  # DNI médico
    )
    
    if turno_id:
        # Consultar turnos del paciente
        consultar_turnos_paciente("40123456")
        
        # Evaluar riesgo
        evaluar_riesgo("40123456")
