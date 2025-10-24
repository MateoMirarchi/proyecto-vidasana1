import db


def list_invalid_nodes():
    print("\nListado de nodos Usuario con dni no numérico:")
    invalid = []
    if not db.driver:
        print("Neo4j driver no disponible. No se puede listar.")
        return invalid
    with db.driver.session() as s:
        res = s.run(r"MATCH (p:Usuario) WHERE NOT p.dni =~ '^\\d+$' RETURN p.nombre AS nombre, p.apellido AS apellido, p.dni AS dni, id(p) AS nodeId LIMIT 100")
        rows = list(res)
        if not rows:
            print(" Ningún nodo inválido encontrado.")
            return invalid
        for r in rows:
            nombre = r.get("nombre")
            apellido = r.get("apellido")
            dni = r.get("dni")
            nodeId = r.get("nodeId")
            print(f" - nodeId={nodeId} | {nombre} {apellido} | dni={dni}")
            invalid.append({"nodeId": nodeId, "dni": dni, "nombre": nombre, "apellido": apellido})
    return invalid


def delete_invalid_relationships():
    if not db.driver:
        print("Neo4j driver no disponible. No se puede eliminar relaciones.")
        return 0
    with db.driver.session() as s:
        # Eliminar relaciones SIGUE que apunten a nodos con dni no numérico
        q = r"MATCH (m:Usuario)-[r:SIGUE]->(p:Usuario) WHERE NOT p.dni =~ '^\\d+$' DELETE r RETURN count(r) AS deleted"
        res = s.run(q)
        row = list(res)
        if row:
            deleted = row[0].get("deleted", 0)
        else:
            deleted = 0
        print(f"\nRelaciones SIGUE eliminadas: {deleted}")
        return deleted


if __name__ == '__main__':
    invalid = list_invalid_nodes()
    if invalid:
        confirm = input('\nSe encontraron nodos inválidos. Eliminar RELACIONES SIGUE hacia estos nodos? (s/n): ').strip().lower()
        if confirm == 's':
            delete_invalid_relationships()
            print('\nListado después de la limpieza:')
            list_invalid_nodes()
        else:
            print('Operación cancelada por el usuario. No se eliminó nada.')
    else:
        print('\nNo hay nodos inválidos, nada que limpiar.')
