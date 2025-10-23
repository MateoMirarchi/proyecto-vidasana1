import redis
import acciones

redis_client = redis.Redis(host='localhost', port=6379, db=0)
usuario_actual = None

def menu_principal():
    global usuario_actual
    while True:
        print("\n🩺 Bienvenido a VidaSana")
        print("1. Crear usuario")
        print("2. Iniciar sesión")
        print("3. Registrar hábitos diarios")
        print("4. Consultar hábitos")
        print("5. Registrar turno médico")
        print("6. Evaluar riesgo clínico")
        print("7. Ver red médico-paciente")
        print("8. Seguir paciente (solo médicos)")
        print("9. Salir")
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            acciones.crear_usuario_console()
        elif opcion == "2":
            usuario_actual = acciones.iniciar_sesion()
        elif opcion == "3":
            if validar_sesion():
                acciones.registrar_habito_console(usuario_actual)
        elif opcion == "4":
            if validar_sesion():
                acciones.consultar_habitos_console(usuario_actual)
        elif opcion == "5":
            if validar_sesion():
                acciones.registrar_turno_console(usuario_actual)
        elif opcion == "6":
            if validar_sesion():
                acciones.evaluar_riesgo_console(usuario_actual)
        elif opcion == "7":
            acciones.mostrar_red_console()
        elif opcion == "8":
            if validar_sesion() and usuario_actual["rol"] == "medico":
                acciones.seguir_paciente_console(usuario_actual)
        elif opcion == "9":
            print("👋 Gracias por usar VidaSana")
            break
        else:
            print("❌ Opción inválida")

def validar_sesion():
    if usuario_actual:
        return True
    print("⚠️ Debe iniciar sesión primero")
    return False

if __name__ == "__main__":
    menu_principal()
