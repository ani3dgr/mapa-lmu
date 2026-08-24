# -*- coding: utf-8 -*-
"""
Convierte los escaneos CSV de telemetria en trazados de circuito para el mapa.
Se ejecuta UNA VEZ (o cuando se anada un circuito nuevo). No necesita el juego abierto.

Lee:   IngenieroLMU/escaneos/*.csv   (t;vuelta;x;y;z;vel_kmh;acel;freno;volante;enboxes;flag2)
Crea:  IngenieroLMU/mapa/circuitos/*.json  (un archivo por circuito)
"""
import csv
import json
import math
import os
import re

import circuitos as almacen

AQUI = os.path.dirname(os.path.abspath(__file__))
CARPETA = os.path.dirname(AQUI)

# Los escaneos crudos pueden estar en dos sitios: dentro de la carpeta del
# programa (lo normal ahora) o en la de al lado (donde los dejaba la version
# antigua). Se miran los dos para no perder los que ya habia.
CARPETAS_ESCANEOS = [os.path.join(AQUI, "escaneos"),
                     os.path.join(CARPETA, "escaneos")]
ESCANEOS = CARPETAS_ESCANEOS[0]
SALIDA = almacen.CARPETA

PUNTOS_TRAZADO = 500   # puntos por circuito tras remuestrear


def normaliza(s):
    """Nombre comparable: minusculas, solo letras y numeros."""
    return re.sub(r"[^a-z0-9]", "", s.lower())


def leer_csv(ruta):
    """Devuelve lista de dicts con vuelta, x, z, enboxes."""
    filas = []
    with open(ruta, "r", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter=";"):
            try:
                filas.append({
                    "vuelta": int(float(r["vuelta"])),
                    "x": float(r["x"]),
                    "y": float(r["y"]),
                    "z": float(r["z"]),
                    "boxes": int(float(r.get("enboxes", 0) or 0)),
                })
            except (ValueError, TypeError, KeyError):
                continue
    return filas


def elegir_vuelta(filas):
    """
    La vuelta mas util para dibujar: una vuelta completa (cierra el bucle) y con
    el maximo de puntos, que es la que mas detalle da del trazado.
    Nota: la columna 'enboxes' de los escaneos quedo mal calibrada (siempre 1),
    asi que la vuelta buena se detecta por geometria, no por esa columna.
    """
    EXTENSION_MIN = 300.0   # m; descarta garaje y trozos sueltos
    CIERRE_MAX = 60.0       # m; una vuelta completa vuelve a su punto de partida

    por_vuelta = {}
    for f in filas:
        por_vuelta.setdefault(f["vuelta"], []).append(f)

    candidatas = []
    for vuelta, pts in por_vuelta.items():
        if len(pts) < 300:
            continue
        xs = [p["x"] for p in pts]
        zs = [p["z"] for p in pts]
        if max(max(xs) - min(xs), max(zs) - min(zs)) < EXTENSION_MIN:
            continue
        cierre = math.dist((pts[0]["x"], pts[0]["z"]), (pts[-1]["x"], pts[-1]["z"]))
        if cierre > CIERRE_MAX:
            continue
        candidatas.append((len(pts), vuelta, pts, cierre))

    if not candidatas:
        return None, None
    _, vuelta, pts, cierre = max(candidatas)
    return (vuelta, pts), cierre


def remuestrear(pts, n):
    """Reparte n puntos a distancia constante a lo largo del trazado."""
    xs = [(p["x"], p["z"]) for p in pts]
    acum, total = [0.0], 0.0
    for a, b in zip(xs, xs[1:]):
        total += math.dist(a, b)
        acum.append(total)
    if total <= 0:
        return xs

    salida, j = [], 0
    for k in range(n):
        objetivo = total * k / n
        while j < len(acum) - 2 and acum[j + 1] < objetivo:
            j += 1
        tramo = acum[j + 1] - acum[j]
        t = 0.0 if tramo <= 0 else (objetivo - acum[j]) / tramo
        x = xs[j][0] + (xs[j + 1][0] - xs[j][0]) * t
        z = xs[j][1] + (xs[j + 1][1] - xs[j][1]) * t
        salida.append((round(x, 1), round(z, 1)))
    return salida


def main():
    if not os.path.isdir(ESCANEOS):
        print("No encuentro la carpeta de escaneos:", ESCANEOS)
        return

    circuitos = {}
    for archivo in sorted(os.listdir(ESCANEOS)):
        if not archivo.lower().endswith(".csv"):
            continue

        # "Circuit_de_Spa_Francorchamps_20260712_1935.csv" -> "Circuit de Spa Francorchamps"
        base = re.sub(r"_\d{8}_\d{4}$", "", os.path.splitext(archivo)[0])
        nombre = base.replace("_", " ").strip()

        filas = leer_csv(os.path.join(ESCANEOS, archivo))
        elegida, cierre = elegir_vuelta(filas)
        if not elegida:
            print("  [salto] %-52s sin vuelta limpia" % archivo)
            continue

        vuelta, pts = elegida
        trazado = remuestrear(pts, PUNTOS_TRAZADO)
        xs = [p[0] for p in trazado]
        zs = [p[1] for p in trazado]

        ys = [p["y"] for p in pts]
        circuitos[normaliza(base)] = {
            "nombre": nombre,
            "vuelta_usada": vuelta,
            "puntos": trazado,
            "limites": [min(xs), min(zs), max(xs), max(zs)],
            # rango de altura real del circuito: sirve para descartar en la
            # calibracion los huecos de memoria que no son posiciones (velocidades,
            # aceleraciones... que valen casi cero y se amontonan en el origen)
            "altura": [round(min(ys), 1), round(max(ys), 1)],
        }
        print("  %-52s vuelta %-3d  %4d pts  cierre %5.1f m  %.0fx%.0f m"
              % (nombre, vuelta, len(trazado), cierre, max(xs) - min(xs), max(zs) - min(zs)))

    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(circuitos, f, ensure_ascii=False, separators=(",", ":"))

    print("\n%d circuitos -> %s (%.0f KB)"
          % (len(circuitos), SALIDA, os.path.getsize(SALIDA) / 1024))


if __name__ == "__main__":
    main()
