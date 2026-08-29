# -*- coding: utf-8 -*-
"""
Anade un circuito nuevo al mapa grabando una vuelta en pista.

Se ejecuta con el juego abierto y rodando. Graba la posicion del coche del
jugador, detecta las vueltas completas y guarda el trazado directamente en
la carpeta circuitos/. No hace falta pasar por los CSV de escaneos.

    1. Entra en pista con el circuito nuevo.
    2. Lanza esto.
    3. Da 2 o 3 vueltas limpias (sin salirte ni cortar).
    4. Se para solo al completar 3 vueltas, o pulsa Ctrl+C cuando quieras.
"""
import csv
import datetime
import json
import math
import os
import sys
import time

import rutas
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
from construir_circuitos import PUNTOS_TRAZADO, elegir_vuelta, remuestrear

VUELTAS_OBJETIVO = 3
HZ = 10.0                # el buffer solo da 5 Hz; con 10 sobra
OFF_VUELTAS = 100        # mTotalLaps dentro de la ficha del coche (short)


def busca_jugador(sco, n):
    for v in range(n):
        if lmu.u1(sco.sco, lmu.SCO_BASE + v * lmu.SCO_STRIDE + lmu.OFF_YO):
            return v
    return None


def guardar_escaneo(pista, filas):
    """
    Guarda la grabacion cruda en la carpeta "escaneos", al lado del programa.
    Hace falta para detectar las curvas con detalle: el trazado del mapa se
    guarda remuestreado a 500 puntos y eso se queda corto.

    Va dentro de la carpeta del programa a proposito, no fuera: quien se baje
    esto de internet tiene solo esta carpeta, y escribir en la de al lado seria
    ensuciarle el disco con algo que no espera.
    """
    carpeta = rutas.datos("escaneos")
    try:
        os.makedirs(carpeta, exist_ok=True)
        limpio = "".join(ch if ch.isalnum() else "_" for ch in pista).strip("_")
        sello = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        ruta = os.path.join(carpeta, "%s_%s.csv" % (limpio, sello))
        with open(ruta, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["t", "vuelta", "x", "y", "z", "vel_kmh",
                        "acel", "freno", "volante", "enboxes", "flag2"])
            for i, r in enumerate(filas):
                w.writerow(["%.2f" % (i / HZ), r["vuelta"],
                            "%.2f" % r["x"], "%.2f" % r["y"], "%.2f" % r["z"],
                            "", "", "", "", 0, 0])
        return ruta
    except OSError:
        return None


# Cuanto se pueden llevar dos medidas del mismo trazado. El largo lo publica
# el juego y para un trazado dado sale siempre igual, asi que con diez metros
# sobra: dos variantes distintas se llevan mucho mas (Silverstone WEC y ELMS,
# veintidos).
MARGEN_LARGO = 10.0


def _clave_para(circuitos, pista, largo_juego):
    """
    Con que nombre se guarda este escaneo.

    Normalmente, el nombre del circuito y ya esta. Pero hay circuitos con
    dos trazados a los que el juego llama IGUAL (Portimao, en su version
    normal y en la de ELMS). Si se guardaran los dos con el mismo nombre,
    el segundo pisaria al primero y siempre faltaria uno.

    Asi que cuando ya hay un trazado guardado con ese nombre y mide otra
    cosa, este se guarda aparte, con su largo pegado detras. El programa
    despues elige solo el que cuadra con el circuito que se este corriendo.
    """
    base = lmu.normaliza(pista)
    anterior = circuitos.get(base)
    if not anterior or not largo_juego:
        return base
    largo_viejo = anterior.get("largo")
    if not largo_viejo:
        return base            # el de antes no lleva medida: se actualiza
    if abs(largo_viejo - largo_juego) <= MARGEN_LARGO:
        return base            # es el mismo trazado, se rehace encima
    aparte = "%s__%d" % (base, round(largo_juego))
    print(idiomas.t("sc.tz.otra_variante") % (largo_viejo, largo_juego))
    return aparte


def main():
    try:
        sco = lmu.Scoring()
    except OSError as e:
        print(idiomas.t("sc.sin_juego") % e)
        print(idiomas.t("sc.abre_lmu"))
        return 1

    n = sco.n_coches()
    if n == 0:
        print(idiomas.t("sc.sin_coches"))
        return 1

    pista = sco.circuito()
    largo_juego = sco.largo_pista()
    print(idiomas.t("sc.tz.detectado") % pista)
    if largo_juego:
        print(idiomas.t("sc.tz.largo") % largo_juego)

    circuitos = lmu.cargar_circuitos()
    clave = _clave_para(circuitos, pista, largo_juego)
    if clave in circuitos:
        anterior = circuitos[clave]
        tiene = [n for n, hay in (("bordes", anterior.get("bordes")),
                                  ("boxes", anterior.get("boxes")))
                 if hay]
        print()
        print(idiomas.t("sc.tz.ya_escaneado"))
        print(idiomas.t("sc.tz.se_sustituye"))
        if tiene:
            print(idiomas.t("sc.tz.se_conserva") % " y ".join(tiene))
        if input(idiomas.t("sc.continuar")).strip().lower() not in ("s", "si", "y"):
            print(idiomas.t("sc.cancelado"))
            return 1

    yo = busca_jugador(sco, n)
    if yo is None:
        print(idiomas.t("sc.sin_jugador"))
        return 1
    base = lmu.SCO_BASE + yo * lmu.SCO_STRIDE
    print(idiomas.t("sc.tz.tu_coche")
          % lmu.txt(sco.sco, base + lmu.OFF_NOMBRE, 32))
    print()
    print("=" * 66)
    print(idiomas.t("sc.tz.titulo"))
    print("=" * 66)
    print(idiomas.t("sc.tz.instrucciones") % VUELTAS_OBJETIVO)
    print("=" * 66)
    print()

    filas = []
    vuelta0 = None
    ultima_info = 0.0
    try:
        while True:
            vuelta = lmu.i2(sco.sco, base + OFF_VUELTAS)
            x = lmu.d(sco.sco, base + lmu.OFF_POS)
            y = lmu.d(sco.sco, base + lmu.OFF_POS + 8)
            z = lmu.d(sco.sco, base + lmu.OFF_POS + 16)
            if all(map(math.isfinite, (x, y, z))):
                filas.append({"vuelta": vuelta, "x": x, "y": y, "z": z})
                if vuelta0 is None:
                    vuelta0 = vuelta

            ahora = time.time()
            if ahora - ultima_info > 2.0:
                ultima_info = ahora
                hechas = (vuelta - vuelta0) if vuelta0 is not None else 0
                print(idiomas.t("sc.tz.vuelta") % (hechas + 1, len(filas)))

            if vuelta0 is not None and vuelta - vuelta0 >= VUELTAS_OBJETIVO:
                print(idiomas.t("sc.tz.completadas") % VUELTAS_OBJETIVO)
                break
            time.sleep(1.0 / HZ)
    except KeyboardInterrupt:
        print(idiomas.t("sc.tz.detenida"))

    if len(filas) < 300:
        print(idiomas.t("sc.tz.pocos_puntos") % len(filas))
        return 1

    elegida, cierre = elegir_vuelta(filas)
    if not elegida:
        print(idiomas.t("sc.tz.ninguna_entera"))
        return 1

    vuelta, pts = elegida
    trazado = remuestrear(pts, PUNTOS_TRAZADO)
    csv_guardado = guardar_escaneo(pista, filas)
    xs = [p[0] for p in trazado]
    zs = [p[1] for p in trazado]
    ys = [p["y"] for p in pts]

    # Se actualiza solo lo del trazado. Los bordes y la calle de boxes son
    # escaneos aparte y no tienen por que perderse por rehacer este: son
    # coordenadas del mundo y siguen siendo validas.
    entrada = circuitos.get(clave, {})
    # Se guarda cuanto mide el circuito segun el juego. Es el unico dato
    # que distingue dos trazados que se llaman IGUAL: Portimao publica
    # "Algarve International Circuit" tanto en su version normal como en la
    # de ELMS, asi que por el nombre no hay manera de saber cual es. Con el
    # largo, el mapa puede avisar de que el trazado dibujado no es el que se
    # esta corriendo, en vez de pintar mal y dejar que uno se vuelva loco.
    entrada.update({
        "nombre": pista,
        "largo": round(largo_juego, 1) if largo_juego else None,
        "vuelta_usada": vuelta,
        "puntos": trazado,
        "limites": [min(xs), min(zs), max(xs), max(zs)],
        "altura": [round(min(ys), 1), round(max(ys), 1)],
    })
    entrada.pop("curvas", None)      # se recalculan con el trazado nuevo
    circuitos[clave] = entrada
    almacen.guardar_uno(clave, entrada)

    print()
    print(idiomas.t("sc.tz.guardado") % pista)
    print(idiomas.t("sc.tz.vuelta_usada") % (vuelta, cierre))
    print(idiomas.t("sc.tz.dimensiones")
          % (max(xs) - min(xs), max(zs) - min(zs)))
    print(idiomas.t("sc.tz.altura") % (min(ys), max(ys)))
    if csv_guardado:
        print(idiomas.t("sc.tz.crudo") % os.path.basename(csv_guardado))
    print()
    print(idiomas.t("sc.tz.ya_puedes"))
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
