# -*- coding: utf-8 -*-
"""
Sigue el camino EXACTO que usa el mapa y apunta que pasa con los avisos de
salida de pista. Sirve para ver donde se pierde la deteccion cuando en el mapa
no aparece el triangulo.

Se ejecuta con el juego abierto y rodando. Sal de pista una vez y mira el
archivo. Ctrl+C para terminar.

Escribe: mapa/prueba_salidas.txt
"""
import os
import sys
import time

import comparador as comp
import mapa_pista as mp

SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prueba_salidas.txt")


def main():
    cfg = mp.cargar_config()
    fuente = mp.Juego()
    comparador = None
    lineas = []
    t0 = time.time()
    ultimo_volcado = [0.0]
    creaciones = [0]

    def guardar():
        with open(SALIDA, "w", encoding="utf-8") as f:
            f.write("\n".join(lineas))

    def apunta(txt):
        try:
            print(txt.encode("ascii", "replace").decode("ascii"))
        except Exception:
            pass
        lineas.append(txt)
        ahora = time.time()
        if ahora - ultimo_volcado[0] > 2.0:
            ultimo_volcado[0] = ahora
            guardar()

    apunta("PRUEBA DE AVISOS DE SALIDA")
    apunta("salidas_segun_juego (la casilla) = %s" % cfg["salidas_segun_juego"])
    apunta("ver_salidas                      = %s" % cfg["ver_salidas"])
    apunta("MARGEN_SALIDA = %.1f m   LECTURAS_SALIDA = %d"
           % (comp.MARGEN_SALIDA, comp.LECTURAS_SALIDA))
    apunta("")
    apunta("Sal de pista una vez. Se apunta cada lectura en que estes fuera,")
    apunta("y cada vez que se registre o se borre un aviso.")
    apunta("")

    antes_salidas = -1
    try:
        while True:
            time.sleep(0.1)
            coches = fuente.leer()
            largo = getattr(fuente, "largo", 0.0)
            if not largo:
                continue
            sesion = getattr(fuente, "sesion", None)
            if (comparador is None
                    or abs(comparador.largo - largo) > 50
                    or comparador.sesion != sesion):
                comparador = comp.Comparador(largo, sesion)
                creaciones[0] += 1
                apunta("%7.1fs  COMPARADOR CREADO DE NUEVO (van %d)  sesion=%s largo=%.0f"
                       % (time.time() - t0, creaciones[0], sesion, largo))
            comparador.usar_flag_juego = cfg["salidas_segun_juego"]
            if coches:
                comparador.actualiza(coches, time.monotonic())

            marca = "%7.1fs" % (time.time() - t0)
            yo = next((c for c in coches if c["es_yo"]), None)
            if yo and yo.get("borde"):
                exceso = abs(yo["lateral"]) - abs(yo["borde"])
                if exceso > 0.3:
                    apunta("%s  fuera %+.2f m  (lateral %.1f borde %.1f)  "
                           "seguidas=%d  avisos=%d"
                           % (marca, exceso, yo["lateral"], yo["borde"],
                              comparador._fuera_seguidas, len(comparador.salidas)))
            if len(comparador.salidas) != antes_salidas:
                antes_salidas = len(comparador.salidas)
                apunta("%s  >>> AVISOS REGISTRADOS: %d  %s"
                       % (marca, antes_salidas,
                          {k: v["motivo"] for k, v in comparador.salidas.items()}))
    except KeyboardInterrupt:
        apunta("")
        apunta("--- fin ---")

    guardar()
    print()
    print("Guardado en: %s" % SALIDA)
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
