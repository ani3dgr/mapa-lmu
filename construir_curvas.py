# -*- coding: utf-8 -*-
"""
Detecta las curvas de cada circuito y les pone numero y nombre.

Se ejecuta UNA VEZ (o al anadir circuitos nuevos). No necesita el juego.
Escribe la lista de curvas dentro de la carpeta circuitos/.

Las curvas se detectan por GEOMETRIA del trazado, no de una lista a mano: se
mide cuanto gira el coche por metro recorrido y se agrupan los tramos que giran
de verdad. Se numeran desde la linea de meta, que es donde empieza el trazado
(la vuelta se recorta por el contador de vueltas del juego).

Los nombres salen de dos fuentes que ya estaban en el proyecto:
  - curvas_circuitos.json  (nombres propios, con coordenadas X/Z)
  - curvas_crewchief.json  (base de CrewChief, por distancia de vuelta)
"""
import json
import math
import os
import re

import circuitos as almacen

CARPETA = os.path.dirname(os.path.abspath(__file__))
PADRE = os.path.dirname(CARPETA)
CURVAS_PROPIAS = os.path.join(PADRE, "curvas_circuitos.json")
CURVAS_CREWCHIEF = os.path.join(PADRE, "curvas_crewchief.json")

# Un tramo cuenta como curva si gira mas cerrado que este radio...
RADIO_MAX = 250.0          # m
# ...y si en total cambia de direccion mas que esto (filtra kinks de recta)
GIRO_MIN = math.radians(20)
SUAVIZADO = 3              # puntos de media movil sobre la curvatura
PUNTOS_DETECCION = 2000    # resolucion para detectar (el mapa dibuja con 500)
HUECO_MAX = 6              # puntos de recta que se toleran dentro de una curva

# Palabras que identifican un circuito aunque el nombre completo no coincida
CLAVES = {
    "sebring": "sebring", "fuji": "fuji", "bahrain": "bahrain",
    "imola": "imola", "enzoedinoferrari": "imola",
    "interlagos": "interlagos", "josecarlospace": "interlagos",
    "carlospace": "interlagos", "portimao": "algarve", "algarve": "algarve",
    "lagunaseca": "lagunaseca", "paulricard": "paulricard",
    "losail": "losail", "lusail": "losail", "qatar": "losail",
    "americas": "cota", "cota": "cota", "monza": "monza",
    "silverstone": "silverstone", "spa": "spa", "francorchamps": "spa",
    "barcelona": "barcelona", "catalunya": "barcelona",
    "sarthe": "lemans", "lemans": "lemans", "daytona": "daytona",
}


def normaliza(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def familia(nombre):
    """Reduce un nombre de circuito a una palabra clave comparable."""
    n = normaliza(nombre)
    for clave, fam in CLAVES.items():
        if clave in n:
            return fam
    return n


def detectar_curvas(puntos):
    """
    Devuelve [{'n':1,'x':..,'z':..,'giro_grados':..,'frac':..}, ...]
    numeradas desde el principio del trazado (la linea de meta).
    """
    n = len(puntos)
    # longitud de cada tramo y rumbo
    largos, rumbos = [], []
    for i in range(n):
        x0, z0 = puntos[i]
        x1, z1 = puntos[(i + 1) % n]
        largos.append(math.hypot(x1 - x0, z1 - z0))
        rumbos.append(math.atan2(z1 - z0, x1 - x0))

    # cuanto gira en cada tramo, normalizado a radianes por metro
    curvatura = []
    for i in range(n):
        giro = rumbos[i] - rumbos[i - 1]
        giro = (giro + math.pi) % (2 * math.pi) - math.pi
        paso = max(largos[i - 1], 0.5)
        curvatura.append(giro / paso)

    # media movil circular: quita el ruido del muestreo
    suave = []
    mitad = SUAVIZADO // 2
    for i in range(n):
        trozo = [curvatura[(i + k) % n] for k in range(-mitad, mitad + 1)]
        suave.append(sum(trozo) / len(trozo))

    umbral = 1.0 / RADIO_MAX
    engirando = [abs(c) > umbral for c in suave]

    # agrupar tramos seguidos que giran hacia el mismo lado
    grupos = []
    i = 0
    while i < n:
        if not engirando[i]:
            i += 1
            continue
        signo = 1 if suave[i] > 0 else -1
        j, hueco = i, 0
        while j + 1 < n:
            k = j + 1
            mismo = engirando[k] and (1 if suave[k] > 0 else -1) == signo
            if mismo:
                j, hueco = k, 0
            elif hueco < HUECO_MAX:
                hueco += 1
                j = k
            else:
                break
        grupos.append((i, j))
        i = j + 1

    # unir la primera y la ultima si la curva cruza la linea de meta
    if len(grupos) > 1 and grupos[0][0] == 0 and grupos[-1][1] == n - 1:
        s0 = 1 if suave[0] > 0 else -1
        s1 = 1 if suave[n - 1] > 0 else -1
        if s0 == s1:
            grupos[0] = (grupos[-1][0] - n, grupos[0][1])
            grupos.pop()

    curvas = []
    for ini, fin in grupos:
        idx = [(k % n) for k in range(ini, fin + 1)]
        giro = sum(suave[k] * max(largos[k - 1], 0.5) for k in idx)
        if abs(giro) < GIRO_MIN:
            continue                       # un quiebro de recta, no una curva
        apex = max(idx, key=lambda k: abs(suave[k]))
        curvas.append({
            "x": puntos[apex][0],
            "z": puntos[apex][1],
            "giro_grados": round(math.degrees(giro), 1),
            "frac": apex / float(n),       # posicion en la vuelta, 0 = meta
        })

    curvas.sort(key=lambda c: c["frac"])
    for i, c in enumerate(curvas, 1):
        c["n"] = i
    return curvas


def nombres_propios(nombre_pista):
    """Nombres de curvas.json del proyecto ingeniero: vienen con X/Z."""
    try:
        with open(CURVAS_PROPIAS, encoding="utf-8") as f:
            datos = json.load(f)
    except (OSError, ValueError):
        return []
    fam = familia(nombre_pista)
    for clave, v in datos.items():
        if familia(clave) == fam or any(familia(a) == fam for a in v.get("alias", [])):
            return [c for c in v.get("curvas", []) if c.get("nombre")]
    return []


def nombres_crewchief(nombre_pista):
    """Nombres de la base de CrewChief: vienen por distancia de vuelta."""
    try:
        with open(CURVAS_CREWCHIEF, encoding="utf-8") as f:
            datos = json.load(f)["TrackLandmarksData"]
    except (OSError, ValueError, KeyError):
        return []
    fam = familia(nombre_pista)
    for d in datos:
        candidatos = list(d.get("rf2TrackNames", []))
        candidatos += list(d.get("rf1TrackNames", []))
        for extra in ("pcarsTrackName", "pcars2TrackName", "irTrackName"):
            if d.get(extra):
                candidatos.append(d[extra])
        if any(familia(c) == fam for c in candidatos if c):
            return d.get("trackLandmarks", [])
    return []


def bonito(nombre):
    """'hell_corner' -> 'Hell Corner'"""
    return re.sub(r"[_\-]+", " ", nombre).strip().title()


def poner_nombres(curvas, nombre_pista, largo_vuelta):
    """
    Asigna cada nombre a UNA sola curva.

    Emparejar cada curva con el nombre mas cercano reparte el mismo nombre entre
    varias curvas vecinas ("Les Combes" salia en la 4 y en la 11). Aqui se
    ordenan todas las parejas posibles por distancia y se van cerrando de la
    mejor a la peor, gastando cada nombre y cada curva una unica vez.
    """
    for c in curvas:
        c["nombre"] = ""

    # 1) nombres propios: emparejamiento por cercania en el plano
    parejas = []
    for i, c in enumerate(curvas):
        for j, p in enumerate(nombres_propios(nombre_pista)):
            dist = math.hypot(p["x"] - c["x"], p["z"] - c["z"])
            if dist < 120:
                parejas.append((dist, i, j, p["nombre"]))

    curvas_usadas, nombres_usados = set(), set()
    for _, i, j, nombre in sorted(parejas):
        if i in curvas_usadas or j in nombres_usados:
            continue
        curvas[i]["nombre"] = nombre
        curvas_usadas.add(i)
        nombres_usados.add(j)

    # 2) CrewChief para las que sigan sin nombre: por distancia de vuelta,
    #    quedandose con la curva mas centrada en el tramo de cada nombre
    if largo_vuelta:
        for lm in nombres_crewchief(nombre_pista):
            ini, fin = lm.get("distanceRoundLapStart"), lm.get("distanceRoundLapEnd")
            nombre = bonito(lm.get("landmarkName", ""))
            if ini is None or fin is None or not nombre or nombre in nombres_usados:
                continue
            medio = (ini + fin) / 2.0
            dentro = [(abs(c["frac"] * largo_vuelta - medio), i)
                      for i, c in enumerate(curvas)
                      if not c["nombre"] and ini <= c["frac"] * largo_vuelta <= fin]
            if dentro:
                curvas[min(dentro)[1]]["nombre"] = nombre
                nombres_usados.add(nombre)

    return sum(1 for c in curvas if c["nombre"])


def largo_del_trazado(puntos):
    return sum(math.hypot(puntos[(i + 1) % len(puntos)][0] - puntos[i][0],
                          puntos[(i + 1) % len(puntos)][1] - puntos[i][1])
               for i in range(len(puntos)))


def puntos_detallados(clave):
    """
    Trazado en alta resolucion desde el escaneo crudo, si existe.

    El mapa guarda solo 500 puntos porque le sobran para dibujar, pero a esa
    resolucion las curvas cortas desaparecen: en Monza son 11,5 m por punto y
    una chicane entera son cuatro puntos. Con el CSV original a 2000 puntos
    Monza da sus 11 curvas exactas.
    """
    import construir_circuitos as cc
    for carpeta in cc.CARPETAS_ESCANEOS:
        if not os.path.isdir(carpeta):
            continue
        for archivo in sorted(os.listdir(carpeta), reverse=True):
            if not archivo.lower().endswith(".csv"):
                continue
            base = re.sub(r"_\d{8}_\d{4}$", "", os.path.splitext(archivo)[0])
            if normaliza(base) != clave:
                continue
            elegida, _ = cc.elegir_vuelta(cc.leer_csv(os.path.join(carpeta, archivo)))
            if elegida:
                return cc.remuestrear(elegida[1], PUNTOS_DETECCION)
    return None


def main():
    circuitos = almacen.cargar(recargar=True)

    print("%-42s %7s %7s %9s %s" % ("circuito", "curvas", "nombres", "longitud", "detalle"))
    sin_detalle = []
    for clave, v in sorted(circuitos.items(), key=lambda kv: kv[1]["nombre"]):
        largo = largo_del_trazado(v["puntos"])
        finos = puntos_detallados(clave)
        if finos is None:
            finos, marca = v["puntos"], "APROXIMADO (sin escaneo crudo)"
            sin_detalle.append(v["nombre"])
        else:
            marca = "%d pts" % len(finos)
        curvas = detectar_curvas(finos)
        con_nombre = poner_nombres(curvas, v["nombre"], largo)
        v["curvas"] = curvas
        print("%-42s %7d %7d %7.0f m  %s"
              % (v["nombre"][:42], len(curvas), con_nombre, largo, marca))

    if sin_detalle:
        print("\nOJO: estos circuitos no tienen escaneo crudo, sus curvas son")
        print("aproximadas. Vuelve a escanearlos para numerarlas bien:")
        for nombre in sin_detalle:
            print("  - %s" % nombre)

    almacen.guardar_todos(circuitos)
    print("\nGuardado en %s" % almacen.CARPETA)


if __name__ == "__main__":
    main()
