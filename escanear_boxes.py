# -*- coding: utf-8 -*-
"""
Escanea la CALLE DE BOXES de un circuito.

COMO SE HACE (el programa te va guiando):

  1. Sal de boxes y da una vuelta de transicion.
  2. Al llegar al final de esa vuelta, ENTRA a boxes.
  3. Recorre la calle entera por el centro del carril, sin pararte.
  4. Sal de nuevo a pista y se guarda solo.

Se detecta por el propio aviso del juego (mInPits), asi que no hay que acertar
con ningun punto: se empieza a grabar cuando el juego dice que estas en la
calle y se termina cuando dice que has salido.
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
PUNTOS = 300
MIN_PUNTOS = 60
VELOCIDAD_AVISO = 90.0     # km/h; por encima se avisa de que se va muy rapido


def remuestrear(puntos, n):
    """Reparte n puntos a distancia constante. Boxes es abierto, no un bucle."""
    if len(puntos) < 2:
        return puntos
    acum, total = [0.0], 0.0
    for a, b in zip(puntos, puntos[1:]):
        total += math.dist(a, b)
        acum.append(total)
    if total <= 0:
        return puntos[:1]
    salida, j = [], 0
    for k in range(n):
        objetivo = total * k / max(n - 1, 1)
        while j < len(acum) - 2 and acum[j + 1] < objetivo:
            j += 1
        tramo = acum[j + 1] - acum[j]
        t = 0.0 if tramo <= 0 else (objetivo - acum[j]) / tramo
        salida.append((round(puntos[j][0] + (puntos[j + 1][0] - puntos[j][0]) * t, 2),
                       round(puntos[j][1] + (puntos[j + 1][1] - puntos[j][1]) * t, 2)))
    return salida


def main():
    try:
        sco = lmu.Scoring()
    except OSError as e:
        print(idiomas.t("sc.sin_juego") % e)
        return 1
    sco.off_pos = lmu.OFF_POS

    n = sco.n_coches()
    if n == 0:
        print(idiomas.t("sc.sin_coches2"))
        return 1
    sco.off_jugador = lmu.buscar_jugador(sco.sco, n)
    yo = next((v for v in range(n)
               if lmu.u1(sco.sco, lmu.SCO_BASE + v * lmu.SCO_STRIDE + sco.off_jugador)), None)
    if yo is None:
        print(idiomas.t("sc.sin_jugador2"))
        return 1
    base = lmu.SCO_BASE + yo * lmu.SCO_STRIDE

    pista = sco.circuito()
    clave = lmu.normaliza(pista)
    circuitos = lmu.cargar_circuitos()
    if clave not in circuitos:
        print(idiomas.t("sc.bx.sin_trazado"))
        return 1

    print("=" * 68)
    print(idiomas.t("sc.bx.titulo") % pista)
    print("=" * 68)
    print(idiomas.t("sc.bx.como"))
    print("=" * 68)
    print()
    if circuitos[clave].get("boxes"):
        print(idiomas.t("sc.bx.ya_escaneado"))
        respuesta = input(idiomas.t("sc.bx.se_sustituye"))
        if respuesta.strip().lower() not in ("s", "si", "y"):
            print(idiomas.t("sc.cancelado"))
            return 1
        print()

    print(idiomas.t("sc.bx.empieza"))
    puntos = []
    dentro_antes = False
    ultimo_aviso = 0.0
    dist_antes = lmu.d(sco.sco, base + lmu.OFF_DIST)

    try:
        while True:
            time.sleep(1.0 / HZ)
            dentro = bool(lmu.u1(sco.sco, base + lmu.OFF_BOXES))
            dist = lmu.d(sco.sco, base + lmu.OFF_DIST)

            if dentro and not dentro_antes:
                puntos = []
                print()
                print(idiomas.t("sc.bx.dentro"))
            elif dentro_antes and not dentro:
                if len(puntos) >= MIN_PUNTOS:
                    print()
                    print(idiomas.t("sc.bx.has_salido") % len(puntos))
                    break
                print(idiomas.t("sc.bx.muy_poco") % len(puntos))
            dentro_antes = dentro

            if dentro and dist != dist_antes:
                x = lmu.d(sco.sco, base + lmu.OFF_POS)
                z = lmu.d(sco.sco, base + lmu.OFF_POS + 16)
                if math.isfinite(x) and math.isfinite(z):
                    if not puntos or math.dist(puntos[-1], (x, z)) > 0.5:
                        puntos.append((x, z))
                kmh = abs(dist - dist_antes) * HZ * 3.6
                ahora = time.time()
                if kmh > VELOCIDAD_AVISO and ahora - ultimo_aviso > 3.0:
                    ultimo_aviso = ahora
                    print(idiomas.t("sc.despacio") % kmh)
                if len(puntos) % 40 == 0 and puntos:
                    print(idiomas.t("sc.puntos") % len(puntos))
            dist_antes = dist
    except KeyboardInterrupt:
        print(idiomas.t("sc.cancelado_ctrlc"))
        return 1

    trazada = remuestrear(puntos, PUNTOS)
    largo = sum(math.dist(a, b) for a, b in zip(trazada, trazada[1:]))
    circuitos[clave]["boxes"] = trazada
    almacen.guardar_uno(clave, circuitos[clave])

    print()
    print(idiomas.t("sc.bx.guardado") % pista)
    print(idiomas.t("sc.bx.longitud") % (largo, len(trazada)))
    if largo < 150:
        print(idiomas.t("sc.bx.cuidado"))
    return 0


def _esperar_cierre(codigo):
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
