"""Aventura en la Isla Perdida - versión pandas (modo difícil)."""
from datetime import datetime

import pandas as pd

ARCHIVO_ESCENAS = "escenas_isla.xlsx"
ARCHIVO_ESTADO = "estado_partida.xlsx"
LETRAS = ["a", "b", "c", "d"]

# vida inicial, turnos disponibles y si se ocultan las opciones bloqueadas
DIFICULTADES = {
    "1": {"nombre": "Normal", "vida": 12, "turnos": 60, "ocultar_bloqueadas": False},
    "2": {"nombre": "EXTREMO", "vida": 8, "turnos": 45, "ocultar_bloqueadas": True},
}


# ----------------------------------------------------------------- datos
def cargar_escenas():
    """Lee el Excel con las escenas (el 'mapa' de la aventura)."""
    return pd.read_excel(ARCHIVO_ESCENAS, sheet_name="escenas")


def obtener_escena_actual(df, id_escena):
    """Devuelve la fila (Series) de la escena indicada."""
    return df[df["id_escena"] == id_escena].iloc[0]


def tiene_valor(valor):
    return pd.notna(valor) and str(valor).strip() != ""


def separar_objetos(valor):
    """'cuerda|machete' -> ['cuerda', 'machete'];  vacío -> []."""
    if not tiene_valor(valor):
        return []
    return [o.strip() for o in str(valor).split("|") if o.strip()]


def es_final(fila):
    return str(fila["es_final"]).strip().upper() in ("SI", "SÍ", "TRUE")


# ------------------------------------------------------------ inventario
def agregar_a_inventario(inventario, objetos):
    """Añade objetos sin duplicados y devuelve los que son nuevos."""
    nuevos = []
    for objeto in objetos:
        if objeto not in inventario:
            inventario.append(objeto)
            nuevos.append(objeto)
    return nuevos


def faltantes(inventario, requeridos):
    return [o for o in requeridos if o not in inventario]


# ---------------------------------------------------------------- pantalla
def mostrar_estado(vida, vida_max, turnos_restantes, inventario):
    barra = "❤️" * vida + "🖤" * (vida_max - vida)
    objetos = ", ".join(inventario) if inventario else "vacío"
    print(f"\n{barra}  Vida {vida}/{vida_max}  |  ⏳ Turnos: {turnos_restantes}")
    print(f"🎒 Inventario: {objetos}")


def obtener_opciones(fila, inventario, ocultar_bloqueadas):
    """Lista las opciones de la escena indicando si están disponibles."""
    opciones = []
    for letra in LETRAS:
        if not tiene_valor(fila.get(f"opcion_{letra}")):
            continue
        requeridos = separar_objetos(fila.get(f"requiere_{letra}"))
        falta = faltantes(inventario, requeridos)
        if falta and ocultar_bloqueadas:
            continue
        opciones.append({"letra": letra.upper(),
                         "texto": fila[f"opcion_{letra}"],
                         "destino": fila[f"destino_{letra}"],
                         "requeridos": requeridos,
                         "falta": falta})
    return opciones


def mostrar_opciones(opciones):
    print()
    for o in opciones:
        if o["falta"]:
            print(f"  🔒 {o['letra']}) {o['texto']}  (necesitas: {', '.join(o['requeridos'])})")
        else:
            print(f"  {o['letra']}) {o['texto']}")


def pedir_decision(opciones):
    """Pregunta hasta recibir una opción válida y desbloqueada."""
    while True:
        eleccion = input("\n¿Qué haces? ").strip().upper()
        elegida = next((o for o in opciones if o["letra"] == eleccion), None)
        if elegida is None:
            print("❌ Opción inválida. Elige una de las letras mostradas.")
        elif elegida["falta"]:
            print(f"🔒 No puedes hacer eso todavía. Te falta: {', '.join(elegida['falta'])}")
        else:
            return elegida


# ---------------------------------------------------------------- efectos
def aplicar_efectos(fila, id_escena, inventario, visitadas, vida, vida_max):
    """Aplica daño (siempre), curación (1ª visita) y objetos al llegar a una escena."""
    danio = int(fila["danio"]) if tiene_valor(fila["danio"]) else 0
    cura = int(fila["cura"]) if tiene_valor(fila["cura"]) else 0

    if danio:
        vida -= danio
        print(f"💥 Pierdes {danio} de vida.")
    if cura and id_escena not in visitadas:
        recuperada = min(cura, vida_max - vida)
        vida += recuperada
        if recuperada:
            print(f"💚 Recuperas {recuperada} de vida.")
    for objeto in agregar_a_inventario(inventario, separar_objetos(fila["otorga_objeto"])):
        print(f"🎒 Has conseguido: {objeto}")
    visitadas.add(id_escena)
    return vida


# ---------------------------------------------------------------- guardado
def guardar_estado(escena_final, inventario, tipo_final, vida, turnos_usados, dificultad):
    estado = {
        "escena_final": escena_final,
        "inventario": ", ".join(inventario) if inventario else "sin objetos",
        "tipo_final": tipo_final,
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "vida_restante": max(vida, 0),
        "turnos_usados": turnos_usados,
        "dificultad": dificultad,
    }
    pd.DataFrame([estado]).to_excel(ARCHIVO_ESTADO, index=False)
    print(f"\n💾 Partida guardada en {ARCHIVO_ESTADO}")


def elegir_dificultad():
    print("🌴 AVENTURA EN LA ISLA PERDIDA 🌴")
    print("1) Normal   (12 de vida, 60 turnos)")
    print("2) EXTREMO  (8 de vida, 45 turnos, opciones bloqueadas ocultas)")
    while True:
        eleccion = input("Elige dificultad: ").strip()
        if eleccion in DIFICULTADES:
            return DIFICULTADES[eleccion]
        print("❌ Escribe 1 o 2.")


# ------------------------------------------------------------------- juego
def jugar():
    df = cargar_escenas()
    dificultad = elegir_dificultad()

    escena_actual = "inicio"
    inventario = []
    juego_activo = True
    visitadas = set()
    vida_max = dificultad["vida"]
    vida = vida_max
    turnos_restantes = dificultad["turnos"]

    while juego_activo == True:
        fila = obtener_escena_actual(df, escena_actual)

        print("\n" + "=" * 60)
        print(fila["descripcion"])
        vida = aplicar_efectos(fila, escena_actual, inventario, visitadas, vida, vida_max)

        # ¿morimos por heridas?
        if vida <= 0 and not es_final(fila):
            escena_actual = "final_malo_heridas"
            continue

        if es_final(fila):
            print("\n" + str(fila["mensaje_final"]))
            juego_activo = False
            guardar_estado(escena_actual, inventario, fila["tipo_final"], vida,
                           dificultad["turnos"] - turnos_restantes, dificultad["nombre"])
            break

        mostrar_estado(vida, vida_max, turnos_restantes, inventario)
        opciones = obtener_opciones(fila, inventario, dificultad["ocultar_bloqueadas"])
        mostrar_opciones(opciones)
        elegida = pedir_decision(opciones)

        escena_actual = elegida["destino"]
        turnos_restantes -= 1
        if turnos_restantes <= 0 and not es_final(obtener_escena_actual(df, escena_actual)):
            escena_actual = "final_malo_tormenta"


if __name__ == "__main__":
    jugar()
