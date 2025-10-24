from gestion_pacientes import guardar_paciente, consultar_paciente
from seguimiento_habitos import registrar_habito, consultar_habitos
import interaccion_red as red
from gestion_turnos import registrar_turno, evaluar_riesgo
import db

def crear_usuario_console():
    print("Creación de usuario")
    # Normalizar entradas básicas (strip y lower donde aplica)
    nombre = input("Nombre: ").strip()
    apellido = input("Apellido: ").strip()
    dni = ''.join(filter(str.isdigit, input("DNI: ").strip()))
    fechaNacimiento_raw = input("Fecha de nacimiento (YYYY-MM-DD o YYYYMMDD): ").strip()
    # Aceptar YYYYMMDD compacto y convertir a YYYY-MM-DD
    if fechaNacimiento_raw.isdigit() and len(fechaNacimiento_raw) == 8:
        fechaNacimiento = f"{fechaNacimiento_raw[0:4]}-{fechaNacimiento_raw[4:6]}-{fechaNacimiento_raw[6:8]}"
    else:
        # Normalizar barras a guiones y usar el valor tal cual (la validación comprobará el formato)
        fechaNacimiento = fechaNacimiento_raw.replace('/', '-').strip()
    mail = input("Email: ").strip()
    password = input("Contraseña (mínimo 8 caracteres): ").strip()
    telefono = input("Teléfono: ").strip()
    rol = input("Rol (paciente/medico): ").strip().lower()
    sexo = input("Sexo: ").strip()

    data = {
        "nombre": nombre,
        "apellido": apellido,
        "dni": dni,
        "fechaNacimiento": fechaNacimiento,
        "mail": mail,
        "password": password,
        "telefono": telefono,
        "rol": rol,
        "sexo": sexo,
        "historiaClinica": []
    }
    # Guardar usuario solo en MongoDB
    guardar_paciente(data)

def iniciar_sesion():
    dni = input("Ingrese su DNI: ")
    password = input("Ingrese su contraseña: ")

    usuario = db.find_one(db.pacientes, {"dni": dni})
    if not usuario:
        print("Usuario no encontrado")
        return None

    # Validar contraseña (la contraseña almacenada está hasheada)
    if db.check_password(password, usuario.get("password")):
        # Establecer token en Redis con TTL (1 hora)
        if db.set_access_token(dni):
            ttl = db.get_access_ttl(dni)
            if ttl is not None:
                mins, secs = divmod(ttl, 60)
                print(f"Sesión iniciada correctamente. Tiempo de sesión: {mins}m {secs}s")
                # Iniciar watcher en background para mostrar decremento de TTL
                import threading, time

                def _watch_ttl(dni_watch: str):
                    while True:
                        t = db.get_access_ttl(dni_watch)
                        if t is None or t <= 0:
                            print(f"\n⏰ Sesión para DNI {dni_watch} expirada.")
                            break
                        m, s = divmod(t, 60)

                th = threading.Thread(target=_watch_ttl, args=(dni,), daemon=True)
                th.start()
            else:
                print("✅ Sesión iniciada correctamente (TTL no disponible)")
        else:
            print("⚠️ Sesión iniciada pero no se pudo establecer token en Redis")
        return usuario
    else:
        print("Contraseña incorrecta")
        return None

def consultar_usuario(dni):
    # Usar la función de gestion_pacientes que ya hace pretty-print del documento
    return consultar_paciente(dni)


def registrar_habito_console(usuario):
    print("Registro de hábitos")
    sueño = input("Horas de sueño: ")
    alimentacion = input("Tipo de alimentación: ")
    sintomas = input("Síntomas: ")
    registrar_habito(usuario["dni"], sueño, alimentacion, sintomas)

def registrar_turno_console(usuario):
    print("Registro de turno")
    # Fecha en formato compacto YYYYMMDD o con guiones
    fecha_raw = input("Fecha del turno (YYYYMMDD o YYYY-MM-DD): ").strip()
    hora_raw = input("Hora del turno (HH:MM, 24h): ").strip()
    # Aceptar formato compacto y convertir
    if fecha_raw.isdigit() and len(fecha_raw) == 8:
        fecha_iso = f"{fecha_raw[0:4]}-{fecha_raw[4:6]}-{fecha_raw[6:8]}"
    else:
        fecha_iso = fecha_raw.replace('/', '-').strip()

    # Validar hora simple
    if len(hora_raw) == 4 and hora_raw.isdigit():
        # aceptar HMM or HHMM? prefer HHMM -> insert colon
        hora = f"{hora_raw[0:2]}:{hora_raw[2:4]}"
    else:
        hora = hora_raw

    especialidad = input("Especialidad: ").strip()
    # Solicitar nombre y apellido del médico, buscar su DNI en la colección de pacientes
    medico_nombre = input("Nombre del médico: ").strip()
    medico_apellido = input("Apellido del médico: ").strip()

    # Buscar médicos que coincidan (case-insensitive). Solo considerar documentos con rol 'medico'
    posibles = list(db.pacientes.find({
        "nombre": {"$regex": f"^{medico_nombre}$", "$options": "i"},
        "apellido": {"$regex": f"^{medico_apellido}$", "$options": "i"},
        "rol": "medico"
    }))

    if not posibles:
        print(f"No se encontró médico con nombre {medico_nombre} {medico_apellido}")
        return
    elif len(posibles) == 1:
        medico_dni = posibles[0].get("dni")
    else:
        print("Se encontraron varios médicos con ese nombre:")
        for i, m in enumerate(posibles, 1):
            print(f"{i}. {m.get('nombre')} {m.get('apellido')} - DNI: {m.get('dni')}")
        choice = input("Seleccione el número del médico (o ingrese DNI): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(posibles):
            medico_dni = posibles[int(choice) - 1].get("dni")
        else:
            # Si ingresaron un DNI, normalizarlo
            chosen_dni = ''.join(filter(str.isdigit, choice))
            if chosen_dni:
                medico_dni = chosen_dni
            else:
                print("Selección inválida")
                return

    paciente_dni = ''.join(filter(str.isdigit, input("DNI del paciente: ").strip()))

    if not paciente_dni:
        print("DNI de paciente inválido")
        return
    if not medico_dni:
        print("DNI de médico inválido")
        return

    fecha_hora = f"{fecha_iso} {hora}"

    # Intentar registrar el turno en la lógica de negocio
    turno_id = registrar_turno(paciente_dni, fecha_hora, especialidad, medico_dni)
    if turno_id:
        # Mensaje local (simulado) de notificación
        print(f"Turno registrado (id={turno_id}).")
        print(f"Se envió una notificación al mail del paciente.")
    else:
        print("No se pudo registrar el turno. Revise los datos e intente nuevamente.")

def mostrar_red_console():
    print("\n Red médico-paciente")
    try:
            if db.driver:
                dni = input("Ingrese su DNI de médico para ver su red: ").strip()
                with db.driver.session() as session:
                    session.read_transaction(red.mostrar_red, dni)
            else:
                print("Neo4j no disponible: no se puede mostrar la red")
    except Exception as e:
        print(f" Error al consultar red: {e}")

def seguir_paciente_console(usuario):
    print("\n Seguir paciente")
    dni_paciente_raw = input("DNI del paciente a seguir: ")
    # Normalizar: mantener solo dígitos
    dni_paciente = ''.join(filter(str.isdigit, str(dni_paciente_raw).strip()))

    if not dni_paciente:
        print("DNI de paciente inválido (debe contener dígitos)")
        return

    try:
        if not db.driver:
            print("Neo4j no disponible: no se puede crear la relación")
            return

        # Verificar existencia en MongoDB antes de crear la relación en Neo4j
        medico_doc = db.find_one(db.pacientes, {"dni": usuario.get("dni")})
        paciente_doc = db.find_one(db.pacientes, {"dni": dni_paciente})

        if not medico_doc:
            print(f"Médico con DNI {usuario.get('dni')} no encontrado en la base de datos. No se crea la relación.")
            return

        if not paciente_doc:
            print(f"Paciente con DNI {dni_paciente} no encontrado. No se puede seguir a un paciente inexistente.")
            return

        # Obtener nombres para almacenar en Neo4j al crear nodos (si aplica)
        m_nombre = medico_doc.get("nombre")
        m_apellido = medico_doc.get("apellido")
        p_nombre = paciente_doc.get("nombre")
        p_apellido = paciente_doc.get("apellido")

        with db.driver.session() as session:
            session.write_transaction(
                red.seguir,
                usuario.get("dni"),
                dni_paciente,
                m_nombre,
                m_apellido,
                p_nombre,
                p_apellido,
            )
        print(f"Ahora sigue al paciente {dni_paciente}")
    except Exception as e:
        print(f"Error al seguir paciente: {e}")

def consultar_habitos_console(usuario):
    consultar_habitos(usuario["dni"])

def evaluar_riesgo_console(usuario):
    evaluar_riesgo(usuario["dni"])
