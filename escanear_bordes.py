# -*- coding: utf-8 -*-
"""
Escanea los BORDES de un circuito: la linea izquierda y la derecha.

Sirve para dibujar la pista con su anchura real, que es lo que hace falta para
comparar trazadas: sobre una linea sola no se ve si vas por dentro o por fuera.

COMO SE HACE (el programa te va guiando, no hace falta memorizarlo):

  1. Sal de boxes y da una vuelta de transicion para colocarte.
  2. Al pasar por meta, empieza la vuelta del LADO IZQUIERDO: la rueda
     izquierda pisando la linea blanca, despacio, sin levantarla en ningun
     momento.
  3. Al cruzar meta otra vez, da otra vuelta de transicion.
  4. Al pasar por meta, la vuelta del LADO DERECHO, igual pero con la rueda
     derecha sobre la linea.
  5. Al cruzar meta, termina y se guarda solo.

El juego da la posicion del CENTRO del coche, asi que a cada punto se le suma
medio ancho de coche hacia el lado correspondiente para quedarse con la linea
de verdad.
"""
import json
import math
import os
import sys
import time

import circuitos as almacen
import idiomas
import lector_lmu as lmu

# La consola de Windows habla cp1252 por defecto y se cae al imprimir una
# letra que no sea de las suyas (una polaca, por ejemplo). Con esto se le dice
# que hable UTF-8, y si algo no lo entiende que ponga un signo en vez de
# reventar.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HZ = 10.0
SEMIANCHO = 1.0          # m del centro del coche a la rueda (LMP/GT rondan 1 m)
PUNTOS = 600             # puntos por borde tras remuestrear
VELOCIDAD_AVISO = 70.0   # km/h; por encima se avisa de que se va muy rapido

# el texto se pide al vuelo para que salga en el idioma elegido
FASES = [
    ("transicion", "sc.bo.fase_transicion"),
    ("izquierda",  "sc.bo.fase_izquierda"),
    ("transicion", "sc.bo.fase_transicion2"),
    ("derecha",    "sc.bo.fase_derecha"),
]


def busca_jugador(sco, n):
    for v in range(n):
        if lmu.u1(sco.sco, lmu.SCO_BASE + v * lmu.SCO_STRIDE + lmu.OFF_YO):
            return v
    return None


def desplazar(puntos, lado):
    """
    Aparta cada punto medio coche hacia el lado indicado.

    Se usa la direccion de avance en cada punto y su perpendicular: asi el
    desplazamiento sigue el trazado aunque el circuito gire.
    """
    n = len(puntos)
    salida = []
    for i in range(n):
        x0, z0 = puntos[i]
        x1, z1 = puntos[(i + 1) % n]
        dx, dz = x1 - x0, z1 - z0
        largo = math.hypot(dx, dz) or 1.0
        # perpendicular a la marcha; el signo decide izquierda o derecha
        salida.append((round(x0 + (-dz / largo) * SEMIANCHO * lado, 2),
                       round(z0 + (dx / largo) * SEMIANCHO * lado, 2)))
    return salida


def remuestrear(puntos, n):
    acum, total = [0.0], 0.0
    for a, b in zip(puntos, puntos[1:]):
        total += math.dist(a, b)
        acum.append(total)
    if total <= 0:
        return puntos
    salida, j = [], 0
    for k in range(n):
        objetivo = total * k / n
        while j < len(acum) - 2 and acum[j + 1] < objetivo:
            j += 1
        tramo = acum[j + 1] - acum[j]
        t = 0.0 if tramo <= 0 else (objetivo - acum[j]) / tramo
        salida.append((puntos[j][0] + (puntos[j + 1][0] - puntos[j][0]) * t,
                       puntos[j][1] + (puntos[j + 1][1] - puntos[j][1]) * t))
    return salida


def main():
    try:
        sco = lmu.Scoring()
    except OSError as e:
        print(idiomas.t("sc.sin_juego") % e)
        return 1

    n = sco.n_coches()
    if n == 0:
        print(idiomas.t("sc.sin_coches2"))
        return 1
    yo = busca_jugador(sco, n)
    if yo is None:
        print(idiomas.t("sc.sin_jugador2"))
        return 1

    base = lmu.SCO_BASE + yo * lmu.SCO_STRIDE
    pista = sco.circuito()
    largo = sco.largo_pista()
    print("=" * 68)
    print(idiomas.t("sc.bo.titulo") % (pista, largo))
    print("=" * 68)
    print(idiomas.t("sc.bo.como"))
    print("=" * 68)
    print()

    circuitos_previos = lmu.cargar_circuitos()
    if (circuitos_previos.get(lmu.normaliza(pista)) or {}).get("bordes"):
        print(idiomas.t("sc.bo.ya_escaneado"))
        respuesta = input(idiomas.t("sc.bo.se_sustituyen"))
        if respuesta.strip().lower() not in ("s", "si", "y"):
            print(idiomas.t("sc.cancelado"))
            return 1
        print()

    fase = 0
    puntos = []
    dist_antes = lmu.d(sco.sco, base + lmu.OFF_DIST)
    bordes = {}
    ultimo_aviso = 0.0
    print(">>> %s" % idiomas.t(FASES[fase][1]))

    try:
        while fase < len(FASES):
            time.sleep(1.0 / HZ)
            dist = lmu.d(sco.sco, base + lmu.OFF_DIST)
            if dist == dist_antes:
                continue

            if dist < dist_antes - largo * 0.5:          # ha cruzado meta
                nombre = FASES[fase][0]
                if nombre != "transicion":
                    if len(puntos) < 200:
                        print(idiomas.t("sc.bo.corta")
                              % len(puntos))
                    else:
                        lado = 1.0 if nombre == "izquierda" else -1.0
                        bordes[nombre] = desplazar(remuestrear(puntos, PUNTOS), lado)
                        print(idiomas.t("sc.bo.lado_guardado") % (nombre, PUNTOS))
                        fase += 1
                else:
                    fase += 1
                puntos = []
                if fase < len(FASES):
                    print()
                    print(">>> %s" % idiomas.t(FASES[fase][1]))
            elif dist > dist_antes:
                if FASES[fase][0] != "transicion":
                    x = lmu.d(sco.sco, base + lmu.OFF_POS)
                    z = lmu.d(sco.sco, base + lmu.OFF_POS + 16)
                    if math.isfinite(x) and math.isfinite(z):
                        puntos.append((x, z))
                    kmh = (dist - dist_antes) * HZ * 3.6
                    ahora = time.time()
                    if kmh > VELOCIDAD_AVISO and ahora - ultimo_aviso > 3.0:
                        ultimo_aviso = ahora
                        print(idiomas.t("sc.bo.despacio") % kmh)
            dist_antes = dist
    except KeyboardInterrupt:
        print(idiomas.t("sc.cancelado_ctrlc"))
        return 1

    if "izquierda" not in bordes or "derecha" not in bordes:
        print(idiomas.t("sc.bo.faltan_lados"))
        return 1

    anchos = [math.dist(a, b) for a, b in zip(bordes["izquierda"], bordes["derecha"])]
    anchos.sort()
    mediana = anchos[len(anchos) // 2]

    circuitos = lmu.cargar_circuitos()
    clave = lmu.normaliza(pista)
    entrada = circuitos.get(clave)
    if entrada is None:
        print(idiomas.t("sc.bo.sin_trazado"))
        return 1

    entrada["bordes"] = {"izquierda": bordes["izquierda"], "derecha": bordes["derecha"]}
    almacen.guardar_uno(clave, entrada)

    print()
    print(idiomas.t("sc.bo.guardado") % pista)
    print(idiomas.t("sc.bo.anchura")
          % (mediana, anchos[0], anchos[-1]))
    if not 6.0 < mediana < 25.0:
        print(idiomas.t("sc.bo.cuidado"))
    return 0


def _esperar_cierre(codigo):
    """
    La ventana se abre desde el mapa y al terminar se cerraria sola, asi que un
    error se veria un instante y desapareceria. Aqui se espera al usuario.
    """
    print()
    try:
        input(idiomas.t("sc.cerrar"))
    except Exception:
        pass
    return codigo


if __name__ == "__main__":
    try:
        sys.exit(_esperar_cierre(main()))
    except KeyboardInterrupt:
        sys.exit(_esperar_cierre(0))
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(_esperar_cierre(1))
