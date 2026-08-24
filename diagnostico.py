# -*- coding: utf-8 -*-
"""
Vuelca a un archivo de texto lo que hay ahora mismo en el buffer de scoring,
para poder localizar a mano donde estan las posiciones de los coches.

Ejecutar CON EL JUEGO EN PISTA (mejor rodando, no parado en boxes).
Escribe: mapa/diagnostico.txt
"""
import os
import sys
import time

import lector_lmu as lmu

SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagnostico.txt")


def main():
    lineas = []

    def apunta(txt=""):
        # algunos nombres de piloto traen caracteres que la consola de Windows
        # no sabe imprimir; si reventara aqui perderiamos todo el informe
        try:
            print(txt.encode("ascii", "replace").decode("ascii"))
        except Exception:
            pass
        lineas.append(txt)

    try:
        sco = lmu.Scoring()
    except OSError as e:
        apunta("ERROR: %s" % e)
        apunta("El juego tiene que estar abierto y con una sesion cargada.")
        volcar(lineas)
        return

    n = sco.n_coches()
    pista = sco.circuito()
    apunta("circuito segun el juego : %r" % pista)
    apunta("coches en sesion        : %d" % n)

    circuitos = lmu.cargar_circuitos()
    clave, datos = lmu.buscar_circuito(circuitos, pista)
    apunta("trazado emparejado      : %s" % (datos["nombre"] if datos else "NINGUNO"))
    if datos:
        x0, z0, x1, z1 = datos["limites"]
        apunta("limites del trazado     : X %.0f..%.0f   Z %.0f..%.0f   altura %.1f..%.1f"
               % (x0, x1, z0, z1, datos["altura"][0], datos["altura"][1]))
    apunta()

    if n == 0:
        apunta("No hay coches: entra en pista y vuelve a ejecutarlo.")
        volcar(lineas)
        return

    apunta("--- pilotos ---")
    for v in range(min(n, 24)):
        b = lmu.SCO_BASE + v * lmu.SCO_STRIDE
        apunta("  %2d  %s" % (v, lmu.txt(sco.sco, b + lmu.OFF_NOMBRE, 32)))
    apunta()

    # dos lecturas separadas para ver que se mueve
    apunta("--- ternas de dobles en cada offset (coche 0, 1 y 2) ---")
    apunta("    offset |            coche 0            |   movimiento coche 0 en 0,5 s")
    m1 = {}
    for off in range(0, lmu.SCO_STRIDE - 24, 8):
        try:
            m1[off] = lmu.muestra(sco.sco, off, min(n, 3))
        except Exception:
            pass
    time.sleep(0.5)
    for off in sorted(m1):
        try:
            m2 = lmu.muestra(sco.sco, off, min(n, 3))
        except Exception:
            continue
        a, b = m1[off][0], m2[0]
        mov = ((a[0] - b[0]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5
        marca = ""
        if datos:
            dist = lmu._dist_al_trazado(a[0], a[2], datos["puntos"])
            ymin, ymax = datos["altura"]
            if dist < 150 and ymin - 30 <= a[1] <= ymax + 30:
                marca = "  <== ENCAJA CON EL TRAZADO (a %.0f m)" % dist
        apunta("    %6d | %10.1f %8.1f %10.1f | %8.2f m%s"
               % (off, a[0], a[1], a[2], mov, marca))
    apunta()

    if datos:
        off, informe = lmu.calibrar(sco.sco, datos, n, verboso=True)
        apunta("--- veredicto de la autocalibracion ---")
        apunta("  %s" % informe)
        if off is not None:
            apunta()
            apunta("--- posiciones con ese offset ---")
            for v in range(min(n, 24)):
                bb = lmu.SCO_BASE + v * lmu.SCO_STRIDE
                x = lmu.d(sco.sco, bb + off)
                z = lmu.d(sco.sco, bb + off + 16)
                apunta("  %2d  %-22s X %9.1f   Z %9.1f   (a %.0f m del trazado)"
                       % (v, lmu.txt(sco.sco, bb + lmu.OFF_NOMBRE, 32)[:22], x, z,
                          lmu._dist_al_trazado(x, z, datos["puntos"])))
        apunta()

    apunta("--- otros campos ---")
    apunta("  posibles 'soy yo' (byte a 1 en un solo coche): %s"
           % lmu.calibrar_jugador(sco.sco, n))
    apunta("  offset de la clase del coche                 : %s"
           % lmu.calibrar_clase(sco.sco, n))
    apunta("  offset del puesto en carrera                 : %s"
           % lmu.calibrar_puesto(sco.sco, n))

    volcar(lineas)


def volcar(lineas):
    with open(SALIDA, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))
    print()
    print("Informe guardado en: %s" % SALIDA)


if __name__ == "__main__":
    main()
