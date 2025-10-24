import acciones
import db

usuario_actual = None

def mostrar_estado_conexiones():
    """Muestra el estado de conexión de las bases de datos."""
    print("Estado de conexiones:")
    
    # Verificar MongoDB
    try:
        db.pacientes.find_one({})
        print("✅ MongoDB: Conectado")
    except Exception as e:
        print(f"❌ MongoDB: Error ({str(e)})")
    
    # Verificar Redis
    try:
        db.redis_client.ping()
        print("✅ Redis: Conectado")
    except Exception as e:
        print(f"❌ Redis: Error ({str(e)})")
    
    # Verificar Neo4j
    if db.driver:
        try:
            with db.driver.session() as session:
                session.run("RETURN 1")
            print("✅ Neo4j: Conectado")
        except Exception as e:
            print(f"❌ Neo4j: Error ({str(e)})")
    else:
        print("⚠️ Neo4j: No configurado")
    print()

def menu_principal():
    """Menú principal de la aplicación."""
    global usuario_actual
    
    try:
        mostrar_estado_conexiones()
    except Exception as e:
        print(f"\n❌ Error al verificar conexiones: {str(e)}")
        return
    
    while True:
        print("\n VidaSana")
        if usuario_actual:
            print(f"Usuario actual: {usuario_actual['nombre']} ({usuario_actual['rol']})")
        
        print("\nOpciones:")
        print("1. Crear usuario")
        print("2. Iniciar sesión")
        print("3. Consultar usuario por DNI")
        print("4. Registrar hábitos diarios")
        print("5. Consultar hábitos")
        print("6. Agregar historia clínica a paciente")
        print("7. Registrar turno médico")
        print("8. Evaluar riesgo clínico")
        print("9. Ver red médico-paciente")
        print("10. Seguir paciente (solo médicos)")
        print("0. Salir")
        
        try:
            opcion = input("\nSeleccione una opción: ")

            if opcion == "1":
                acciones.crear_usuario_console()
            elif opcion == "2":
                usuario_actual = acciones.iniciar_sesion()
            elif opcion == "3":
                try:
                    dni = input("Ingrese DNI a consultar: ").strip()
                    if not dni.isdigit():
                        print("El DNI debe contener solo números")
                        continue
                    consultarUsuario = acciones.consultar_usuario(dni)
                except ValueError:
                    print("DNI inválido")
            elif opcion == "4":
                if validar_sesion():
                    acciones.registrar_habito_console(usuario_actual)
            elif opcion == "5":
                if validar_sesion():
                    acciones.consultar_habitos_console(usuario_actual)
            elif opcion == "6":
                # Agregar historia clínica: solo recoger inputs aquí y delegar en la lógica
                if validar_sesion():
                    dni_hc = input("Ingrese DNI del paciente para agregar historia clínica: ").strip()
                    diagnostico = input("Diagnóstico: ").strip()
                    tratamiento = input("Tratamiento: ").strip()
                    # Llamar a la lógica existente
                    from gestion_pacientes import actualizar_historia_clinica
                    if actualizar_historia_clinica(dni_hc, diagnostico, tratamiento):
                        print("Historia clínica agregada correctamente")
                    else:
                        print("No se pudo agregar la historia clínica")
            elif opcion == "7":
                if validar_sesion():
                    acciones.registrar_turno_console(usuario_actual)
            elif opcion == "8":
                if validar_sesion():
                    acciones.evaluar_riesgo_console(usuario_actual)
            elif opcion == "9":
                acciones.mostrar_red_console()
            elif opcion == "10":
                if validar_sesion() and usuario_actual["rol"] == "medico":
                    acciones.seguir_paciente_console(usuario_actual)
                elif usuario_actual and usuario_actual["rol"] != "medico":
                    print("Esta función es solo para médicos")
            elif opcion == "0":
                print("\n ¡Gracias por usar VidaSana!")
                break
            else:
                print("Opción inválida")
        except Exception as e:
            print(f"\n Error: {str(e)}")
            print("Por favor, intente nuevamente.")

def validar_sesion() -> bool:
    """Verifica si hay un usuario con sesión activa."""
    if not usuario_actual:
        print("Debe iniciar sesión primero")
        return False
        
    # Verificar si la sesión sigue activa en Redis
    try:
        if not db.check_access(usuario_actual["dni"]):
            print("Su sesión ha expirado. Por favor, inicie sesión nuevamente.")
            return False
    except Exception as e:
        print(f"No se pudo verificar la sesión: {str(e)}")
        # Si Redis no está disponible, permitimos continuar
        pass
        
    return True

if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n Programa terminado por el usuario")
    except Exception as e:
        print(f"\n Error fatal: {str(e)}")
        print("El programa se cerrará")
