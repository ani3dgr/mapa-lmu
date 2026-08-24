# -*- coding: utf-8 -*-
"""
Saca los bordes de pista de los escaneos antiguos.

Aquellas sesiones de escaneo llevaban dentro, ademas de las vueltas normales,
una vuelta pegada a la linea izquierda y otra a la derecha. Aqui se detectan
por geometria (cual se desvia mas a cada lado del trazado medio) y se guardan
como bordes en la carpeta circuitos/.

Se ejecuta UNA VEZ. Para circuitos nuevos esta escanear_bordes.py, que graba
los dos lados a proposito.
"""
import json
import math
import os
import re

import construir_circuitos as cc
import escanear_bordes as eb
import circuitos as almacen
import lector_lmu as lmu

PUNTOS = 600
ANCHURA_MIN = 5.0        # m; por debajo el escaneo no es de bordes
ANCHURA_MAX = 30.0       # m; por encima algo se torcio
COINCIDENCIA_MIN = 0.90  # fraccion de puntos en que un lado queda del lado bueno


def vueltas_completas(archivo, n=400):
    filas = cc.leer_csv(os.path.join(cc.ESCANEOS, archivo))
    por = {}
    for f in filas:
        por.setdefault(f["vuelta"], []).append(f)
    salida = {}
    for v, pts in por.items():
        if len(pts) < 300:
            continue
        xs = [p["x"] for p in pts]
        zs = [p["z"] for p in pts]
        if max(max(xs) - min(xs), max(zs) - min(zs)) < 300:
            continue
        if math.dist((pts[0]["x"], pts[0]["z"]), (pts[-1]["x"], pts[-1]["z"])) < 60:
            salida[v] = [(p[0], p[1]) for p in cc.remuestrear(pts, n)]
    return salida


def desvios(lap, medio):
    """Separacion con signo de una vuelta respecto al trazado medio."""
    n = len(medio)
    out = []
    for i in range(n):
        dx = medio[(i + 1) % n][0] - medio[i][0]
        dz = medio[(i + 1) % n][1] - medio[i][1]
        largo = math.hypot(dx, dz) or 1.0
        out.append(((lap[i][0] - medio[i][0]) * dz
                    - (lap[i][1] - medio[i][1]) * dx) / largo)
    return out


def main():
    circuitos = lmu.cargar_circuitos()
    print("%-40s %8s %10s %s" % ("circuito", "anchura", "coincide", "resultado"))

    for archivo in sorted(os.listdir(cc.ESCANEOS)):
        if not archivo.lower().endswith(".csv"):
            continue
        base = re.sub(r"_\d{8}_\d{4}$", "", os.path.splitext(archivo)[0])
        clave = lmu.normaliza(base)
        entrada = circuitos.get(clave)
        nombre = entrada["nombre"] if entrada else base.replace("_", " ")

        laps = vueltas_completas(archivo)
        if entrada is None or len(laps) < 3:
            print("%-40s %8s %10s %s" % (nombre[:40], "-", "-", "sin datos suficientes"))
            continue

        claves = sorted(laps)
        n = len(laps[claves[0]])
        medio = [(sum(laps[k][i][0] for k in claves) / len(claves),
                  sum(laps[k][i][1] for k in claves) / len(claves)) for i in range(n)]
        d = {k: desvios(laps[k], medio) for k in claves}

        # los dos extremos son las vueltas de borde
        uno = min(claves, key=lambda k: sum(d[k]) / n)
        otro = max(claves, key=lambda k: sum(d[k]) / n)
        coincide = sum(1 for i in range(n) if d[uno][i] < d[otro][i]) / float(n)

        # se aparta cada lado medio coche, igual que en el escaneo en vivo
        izq = eb.desplazar(cc.remuestrear([{"x": x, "z": z} for x, z in laps[uno]], PUNTOS), 1.0)
        der = eb.desplazar(cc.remuestrear([{"x": x, "z": z} for x, z in laps[otro]], PUNTOS), -1.0)
        # La anchura es la diferencia de SEPARACION LATERAL entre los dos
        # lados, no la distancia entre puntos: si una vuelta va desfasada
        # respecto a la otra, la distancia directa se dispara y da anchuras
        # imposibles (Silverstone llegaba a marcar 79 m).
        anchos = sorted(d[otro][i] - d[uno][i] for i in range(n))
        mediana = anchos[len(anchos) // 2] + 2 * eb.SEMIANCHO

        vale = (coincide >= COINCIDENCIA_MIN and ANCHURA_MIN < mediana < ANCHURA_MAX)
        if vale:
            entrada["bordes"] = {"izquierda": [(round(x, 2), round(z, 2)) for x, z in izq],
                                 "derecha": [(round(x, 2), round(z, 2)) for x, z in der]}
        print("%-40s %6.1f m %9.0f%% %s"
              % (nombre[:40], mediana, coincide * 100,
                 "GUARDADO" if vale else "descartado, mejor reescanear"))

    almacen.guardar_todos(circuitos)
    con = sum(1 for v in circuitos.values() if v.get("bordes"))
    print("\n%d de %d circuitos con bordes -> %s"
          % (con, len(circuitos), almacen.CARPETA))


if __name__ == "__main__":
    main()
