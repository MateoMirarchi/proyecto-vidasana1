from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import db

def validar_habito(data: Dict) -> bool:
    """Valida los datos de un registro de hábitos."""
    campos = ["dni", "fecha", "sueno", "alimentacion", "sintomas", "ejercicio", "estres", "frecuencia_ejercicio"]
    if not all(c in data for c in campos):
        return False
        
    try:
        # Validar horas de sueño
        horas_sueno = float(data["sueno"].split()[0])
        if not 0 <= horas_sueno <= 24:
            return False
            
        # Validar frecuencia de ejercicio
        frecuencia = int(data["frecuencia_ejercicio"])
        if not 0 <= frecuencia <= 7:
            return False
            
        # Validar fecha
        datetime.strptime(data["fecha"], "%Y-%m-%d")
        return True
        
    except (ValueError, IndexError):
        return False

def registrar_habito(
    dni: str,
    sueno: str,
    alimentacion: str,
    sintomas: str,
    ejercicio: str = "No realizado",
    estres: int = 5,
    frecuencia_ejercicio: int = 0
) -> Optional[str]:
    
    # Verificar que existe el paciente
    paciente = db.find_one(db.pacientes, {"dni": dni})
    if not paciente:
        print("Paciente no encontrado")
        return None
        
    registro = {
        "dni": dni,
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "sueno": sueno,
        "alimentacion": alimentacion,
        "sintomas": sintomas,
        "ejercicio": ejercicio,
        "frecuencia_ejercicio": max(0, min(7, frecuencia_ejercicio)),  # Clamp entre 0-7
        "estres": max(1, min(10, estres)),  # Clamp entre 1-10
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if not validar_habito(registro):
        print("Datos inválidos")
        return None
        
    try:
        # Verificar si ya existe registro hoy
        hoy = datetime.now().strftime("%Y-%m-%d")
        if db.find_one(db.habitos, {"dni": dni, "fecha": hoy}):
            print("Ya existe un registro para hoy")
            return None
            
        _id = db.insert_one(db.habitos, registro)
        
        # Analizar síntomas y alertar si es necesario
        sintomas_alerta = ["dolor intenso", "fiebre", "dificultad respirar", 
                          "mareo", "desmayo", "pérdida conciencia"]
                          
        if any(s in sintomas.lower() for s in sintomas_alerta):
            db.simular_email(
                paciente["mail"],
                "Alerta: Síntomas Reportados",
                f"Se han detectado síntomas que requieren atención:\n{sintomas}\n\n"
                f"Por favor, contacte a su médico si los síntomas persisten."
            )
            
        print(f"Registro de hábitos guardado exitosamente")
        return _id
        
    except Exception as e:
        print(f"Error al guardar registro: {str(e)}")
        return None

def consultar_habitos(
    dni: str,
    desde: Optional[str] = None,
    hasta: Optional[str] = None
) -> List[Dict]:
    
    query = {"dni": dni}
    
    if desde:
        query["fecha"] = {"$gte": desde}
    if hasta:
        query.setdefault("fecha", {})["$lte"] = hasta
        
    registros = list(db.habitos.find(
        query,
        sort=[("fecha", -1)]
    ))
    
    if not registros:
        print("No se encontraron registros")
        return []
        
    print("\n Resumen de Hábitos:")
    for r in registros:
        print(f"\n Fecha: {r['fecha']}")
        print(f" Sueño: {r['sueno']}")
        print(f" Alimentación: {r['alimentacion']}")
        print(f" Ejercicio: {r['ejercicio']}")
        print(f" Frecuencia semanal: {r['frecuencia_ejercicio']} veces")
        print(f" Nivel de estrés: {r['estres']}/10")
        if r['sintomas']:
            print(f" Síntomas: {r['sintomas']}")
            
    if len(registros) >= 7:
        print("\n Análisis de la última semana:")
        ultima_semana = registros[:7]
        horas_sueno = []
        niveles_estres = []
        
        for r in ultima_semana:
            try:
                horas_sueno.append(float(r['sueno'].split()[0]))
                niveles_estres.append(r['estres'])
            except (ValueError, IndexError):
                continue
                
        if horas_sueno:
            print(f"Promedio de sueño: {sum(horas_sueno)/len(horas_sueno):.1f} horas")
        if niveles_estres:
            print(f"Promedio de estrés: {sum(niveles_estres)/len(niveles_estres):.1f}/10")
            
    return registros

if __name__ == "__main__":
    # Ejemplo: registrar hábitos
    habito_id = registrar_habito(
        "40123456",  # DNI paciente
        "8 horas",  # Sueño
        "Dieta balanceada, sin excesos",  # Alimentación
        "Leve dolor de cabeza por la tarde",  # Síntomas
        "Caminata 30 minutos",  # Ejercicio
        6,  # Nivel de estrés
        3   # Frecuencia de ejercicio semanal
    )
    
    if habito_id:
        # Consultar última semana
        consultar_habitos(
            "40123456",
            desde=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        )
