# -*- coding: utf-8 -*-
"""
Graba lo que publica el juego cuando hay bandera amarilla.

El juego avisa de que hay amarilla pero no dice que coche la ha provocado, y
la deteccion actual es una deduccion. Esto sirve para dejar de suponer: se
queda mirando el buffer y apunta CADA CAMBIO de los campos relacionados con
banderas, junto con quien estaba fuera de pista o parado en ese momento.

Se ejecuta con el juego abierto y se deja corriendo. Cuando ocurra una
amarilla (provocala tu mismo saliendote y parando en la escapatoria, o espera
a que la lie la IA), se apunta todo. Ctrl+C para terminar.

Escribe: mapa/monitor_amarilla.txt
"""
import os
import sys
import time

import lector_lmu as lmu

SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "monitor_amarilla.txt")
HZ = 5.0
PARADO = 20.0        # km/h


def main():
    try:
        sco = lmu.Scoring()
    except OSError as e:
        print("No encuentro el juego: %s" % e)
        return 1
    sco.off_pos = lmu.OFF_POS

    lineas = []
    ultimo_volcado = [0.0]

    def guardar():
        with open(SALIDA, "w", encoding="utf-8") as f:
            f.write("\n".join(lineas))

    def apunta(txt):
        try:
            print(txt.encode("ascii", "replace").decode("ascii"))
        except Exception:
            pass
        lineas.append(txt)
        # se vuelca cada pocos segundos: asi el archivo se puede leer en
        # cualquier momento sin tener que parar el monitor
        ahora = time.time()
        if ahora - ultimo_volcado[0] > 3.0:
            ultimo_volcado[0] = ahora
            guardar()

    apunta("MONITOR DE BANDERA AMARILLA")
    apunta("circuito: %s   sesion: %d   coches: %d"
           % (sco.circuito(), sco.sesion(), sco.n_coches()))
    apunta("")
    apunta("Se apunta cada cambio. Provoca una amarilla y deja esto corriendo.")
    apunta("Ctrl+C para terminar y guardar.")
    apunta("")
    apunta("%-9s %s" % ("tiempo", "que ha cambiado"))
    apunta("-" * 78)

    t0 = time.time()
    antes = {}
    dist_antes = {}
    t_antes = {}
    try:
        while True:
            time.sleep(1.0 / HZ)
            ahora = time.time()
            marca = "%8.1fs" % (ahora - t0)

            # --- cabecera: fase del juego y estado de amarilla ---
            cab = (sco.fase_juego(), lmu.u1(sco.sco, 121),
                   lmu.u1(sco.sco, 122), lmu.u1(sco.sco, 123), lmu.u1(sco.sco, 124))
            if cab != antes.get("cab"):
                if "cab" in antes:
                    apunta("%s CABECERA  mGamePhase=%d  mYellowFlagState=%d  "
                           "mSectorFlag=%d,%d,%d" % ((marca,) + cab))
                antes["cab"] = cab

            # --- por coche: fase individual, bandera, boxes ---
            coches = sco.coches()
            for c in coches:
                nombre = c["nombre"]
                clave = (c["fase"], c["bandera"], c["en_boxes"])
                if clave != antes.get(nombre):
                    if nombre in antes:
                        apunta("%s %-22s fase=%-3d bandera=%-3d boxes=%d"
                               % (marca, nombre[:22], c["fase"], c["bandera"],
                                  int(c["en_boxes"])))
                    antes[nombre] = clave

                # velocidad y si esta fuera de pista
                d = c["dist"]
                if nombre in dist_antes and d != dist_antes[nombre]:
                    dt = ahora - t_antes[nombre]
                    avance = d - dist_antes[nombre]
                    kmh = avance / dt * 3.6 if 0 < avance < 500 and dt > 0 else None
                    fuera = abs(c["lateral"]) > abs(c["borde"]) if c["borde"] else False
                    estado = (fuera, kmh is not None and kmh < PARADO)
                    if estado != antes.get(nombre + "|est") and any(estado):
                        apunta("%s %-22s %s%s  (lateral %.1f de borde %.1f%s)"
                               % (marca, nombre[:22],
                                  "FUERA DE PISTA " if fuera else "",
                                  "PARADO" if estado[1] else "",
                                  c["lateral"], c["borde"],
                                  "" if kmh is None else ", %.0f km/h" % kmh))
                    antes[nombre + "|est"] = estado
                if nombre not in dist_antes or d != dist_antes[nombre]:
                    dist_antes[nombre] = d
                    t_antes[nombre] = ahora
    except KeyboardInterrupt:
        apunta("")
        apunta("--- fin ---")

    guardar()
    print()
    print("Guardado en: %s" % SALIDA)
    print("Pasaselo a Claude para que vea que hizo el juego.")
    return 0


def _esperar_cierre(codigo):
    """
    La ventana se abre desde el mapa y al terminar se cerraria sola, asi que un
    error se veria un instante y desapareceria. Aqui se espera al usuario.
    """
    print()
    try:
        input("Pulsa INTRO para cerrar esta ventana...")
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
