from neo4j import GraphDatabase

# Conexión Neo4j
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

def crear_usuario(tx, dni, nombre, apellido, fechaNacimiento, mail, telefono, rol, sexo):
    tx.run("""
        MERGE (u:Usuario {
            dni: $dni,
            nombre: $nombre,
            apellido: $apellido,
            fechaNacimiento: $fechaNacimiento,
            mail: $mail,
            telefono: $telefono,
            rol: $rol,
            sexo: $sexo
        })
    """, dni=dni, nombre=nombre, apellido=apellido,
         fechaNacimiento=fechaNacimiento, mail=mail,
         telefono=telefono, rol=rol, sexo=sexo)


def seguir(tx, dni_medico, dni_paciente):
    tx.run("""
        MATCH (m:Usuario {dni: $dni_medico}), (p:Usuario {dni: $dni_paciente})
        MERGE (m)-[:SIGUE]->(p)
    """, dni_medico=dni_medico, dni_paciente=dni_paciente)

def mostrar_red(tx):
    result = tx.run("MATCH (m:Usuario)-[:SIGUE]->(p:Usuario) RETURN m.nombre, p.nombre")
    for r in result:
        print(f"👨‍⚕️ {r['m.nombre']} sigue a 🧑‍⚕️ {r['p.nombre']}")

# Ejemplo
if __name__ == "__main__":
    with driver.session() as session:
        session.write_transaction(crear_usuario, "999", "Dr. Pérez", "medico")
        session.write_transaction(crear_usuario, "12345678", "Lucía Gómez", "paciente")
        session.write_transaction(seguir, "999", "12345678")
        session.read_transaction(mostrar_red)
