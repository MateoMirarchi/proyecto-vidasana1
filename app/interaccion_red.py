import db


def seguir(tx, dni_medico, dni_paciente, m_nombre=None, m_apellido=None, p_nombre=None, p_apellido=None):
    """Crea/asegura nodos Usuario para médico y paciente y la relación SIGUE.

    Si los nodos no existen, se crean y se les asignan nombre/apellido (si se proveen).
    """
    query = (
        "MERGE (m:Usuario {dni: $dni_medico}) "
        "ON CREATE SET m.nombre = coalesce($m_nombre, m.nombre), m.apellido = coalesce($m_apellido, m.apellido) "
        "MERGE (p:Usuario {dni: $dni_paciente}) "
        "ON CREATE SET p.nombre = coalesce($p_nombre, p.nombre), p.apellido = coalesce($p_apellido, p.apellido) "
        "MERGE (m)-[:SIGUE]->(p)"
    )
    tx.run(
        query,
        dni_medico=dni_medico,
        dni_paciente=dni_paciente,
        m_nombre=m_nombre,
        m_apellido=m_apellido,
        p_nombre=p_nombre,
        p_apellido=p_apellido,
    )


def mostrar_red(tx, dni_medico: str):
    """Muestra los pacientes que sigue el médico identificado por dni_medico.

    Retorna una lista de diccionarios con nombre, apellido y dni de cada paciente.
    """
    query = (
        "MATCH (m:Usuario {dni: $dni_medico})-[:SIGUE]->(p:Usuario) "
        "RETURN p.nombre AS nombre, p.apellido AS apellido, p.dni AS dni"
    )
    result = tx.run(query, dni_medico=dni_medico)
    pacientes = []
    for r in result:
        pacientes.append({
            "nombre": r.get("nombre"),
            "apellido": r.get("apellido"),
            "dni": r.get("dni")
        })
    # Imprimir la lista de pacientes seguida por el médico
    if not pacientes:
        print(f"El médico con DNI {dni_medico} no sigue a ningún paciente.")
    else:
        print(f"Pacientes seguidos por el médico (DNI {dni_medico}):")
        for p in pacientes:
            print(f" - {p['nombre']} {p['apellido']} (DNI: {p['dni']})")
    return pacientes


if __name__ == "__main__":
    if not db.driver:
        print("Neo4j driver no disponible (configurar NEO4J_URI/credentials).")
    else:
        # Solo crear relación entre usuarios que ya existen en MongoDB
        medico = db.pacientes.find_one({"dni": "999"})
        paciente = db.pacientes.find_one({"dni": "12345678"})
        if medico and paciente:
            with db.driver.session() as session:
                session.write_transaction(seguir, "999", "12345678")
                session.read_transaction(mostrar_red)
        else:
            print("Usuarios deben existir en MongoDB antes de crear relaciones")
