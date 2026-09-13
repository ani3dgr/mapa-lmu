# -*- coding: utf-8 -*-
"""
Apunta en un archivo todo lo que el juego dice del clima, segundo a segundo.

PARA QUE. Hay tres cosas del clima que no se pueden averiguar mirando: hacen
falta horas de sesion y comparar numeros. Esta herramienta las graba solas
mientras se juega, y luego se leen con calma:

1. **Como se llama cada estado del cielo.** El juego tiene once, del despejado
   a la tormenta, y en una carrera normal salen dos o tres. Con una carrera
   preparada a proposito salen todos, y aqui quedan apuntados con su numero.

2. **En que numero cambia el nombre del asfalto mojado.** El juego publica la
   humedad de la pista como un numero de 0 a 1 pero no dice donde empieza a
   llamarlo "Humedo", "Poco mojado" o "Mojado extremo". Los cortes de
   `clima.MOJADO` estan puestos a ojo. Con este registro basta con que alguien
   diga por el chat "ahora pone Mojado" y mirar aqui que numero habia a esa
   hora.

3. **Si el pronostico cambia durante la sesion o es fijo.** Cada vez que
   alguno de los cinco puntos cambie, queda escrito en grande con la hora.

COMO SE USA. Con el juego abierto y dentro de una sesion:

    python registrar_clima.py

Se queda apuntando hasta que se cierra con Ctrl+C. Escribe en
`registro_clima.txt`, al lado del programa. No hace falta conducir: la
meteorologia avanza igual mirando desde el monitor.

    python registrar_clima.py 2          apunta cada 2 segundos (por defecto 5)
    python registrar_clima.py 5 otro.txt en otro archivo

Es una herramienta de taller, de las que se lanzan a mano, asi que va en
castellano y sin ventanas.
"""
import datetime
import io
import os
import sys
import time

import clima
import lector_lmu as lmu
import rutas

CADA = 5.0
ARCHIVO = os.path.join(rutas.carpeta(), "registro_clima.txt")


def marca():
    return datetime.datetime.now().strftime("%H:%M:%S")


def foto_del_pronostico():
    """Los tres bloques en una sola cadena, para ver si alguno cambia."""
    d = clima.pronostico.datos()
    if not d:
        return None
    trozos = []
    for cual in ("PRACTICE", "QUALIFY", "RACE"):
        for n in clima.pronostico.sesion(cual):
            trozos.append("%s:%d%%=%d/%d%%/%s" % (cual[0], n["parte"] * 100,
                                                  n["cielo"], n["lluvia"],
                                                  n["temp"]))
    return " ".join(trozos)


def escribe_pronostico(f, cuando, motivo):
    f.write("\n%s  ===== EL PRONOSTICO %s =====\n" % (cuando, motivo))
    for cual in ("PRACTICE", "QUALIFY", "RACE"):
        nodos = clima.pronostico.sesion(cual)
        if not nodos:
            continue
        f.write("  %-9s" % cual)
        for n in nodos:
            f.write(" | %3d%% cielo %2d %-22s lluvia %3d%% %2dC"
                    % (n["parte"] * 100, n["cielo"],
                       clima.nombre_cielo(n["cielo"]), n["lluvia"], n["temp"]))
        f.write("\n")
    f.write("\n")


def main():
    cada = CADA
    archivo = ARCHIVO
    if len(sys.argv) > 1:
        try:
            cada = max(1.0, float(sys.argv[1]))
        except ValueError:
            pass
    if len(sys.argv) > 2:
        archivo = sys.argv[2]

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    print("=" * 70)
    print("  REGISTRO DEL CLIMA")
    print("=" * 70)
    print("  apuntando cada %.0f s en %s" % (cada, archivo))
    print("  se para con Ctrl+C")
    print()

    try:
        sco = lmu.Scoring()
    except OSError:
        print("  El juego no esta abierto (o no publica todavia). Abrelo,")
        print("  entra en una sesion y vuelve a lanzar esto.")
        return 1

    clima.pronostico.arrancar()
    anterior = None
    ultimo_nombre = None
    version = None
    vivo = None
    n = 0

    with io.open(archivo, "a", encoding="utf-8") as f:
        f.write("\n\n" + "=" * 78 + "\n")
        f.write("%s  EMPIEZA EL REGISTRO  (cada %.0f s)\n"
                % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), cada))
        f.write("=" * 78 + "\n")
        f.write("hora      sesion  reloj    cielo                    aire asf"
                "  moj.med moj.max lluv nub agarre\n")
        f.flush()
        try:
            while True:
                # Solo se apunta cuando el juego esta publicando de verdad.
                # Que la memoria compartida se pueda leer no basta: al cerrar
                # el juego se queda ahi con lo ultimo, o a ceros, y el archivo
                # se llenaba de renglones inutiles mientras uno prepara la
                # sesion. El contador de version es lo unico que lo delata.
                v = sco.version()
                publicando = (version is not None and v != version)
                version = v
                if publicando != vivo:
                    if vivo is not None or not publicando:
                        f.write("%s  --- %s ---\n"
                                % (marca(), "EMPIEZAN A LLEGAR DATOS"
                                   if publicando else "DEJAN DE LLEGAR DATOS "
                                   "(juego cerrado, en el menu o en pausa)"))
                        f.flush()
                    print("  %s  %s" % (marca(), "el juego esta publicando"
                                        if publicando else "esperando al juego..."))
                    vivo = publicando
                if not publicando:
                    time.sleep(min(cada, 2.0))
                    continue

                c = sco.clima()
                if c is None:
                    time.sleep(cada)
                    continue
                nodos = clima.pronostico.sesion(
                    clima.bloque_de_sesion(sco.sesion()))
                cielo = clima.cielo_ahora(nodos, c)
                # La MEDIA del trazado, no el maximo. Comprobado el
                # 13/09/2026 en Interlagos: con la media en 0,05 y el maximo
                # ya en 0,125, el juego seguia escribiendo "Humedo", que es
                # lo que toca por la media. Apuntando por el maximo, este
                # registro marcaba cambios de nombre que el juego no hacia.
                nombre = clima.nombre_mojado(c["mojado"])
                cuando = marca()

                # el pronostico, la primera vez y cada vez que cambie
                foto = foto_del_pronostico()
                if foto and foto != anterior:
                    escribe_pronostico(
                        f, cuando,
                        "SE LEE POR PRIMERA VEZ" if anterior is None
                        else "HA CAMBIADO")
                    anterior = foto

                # el aviso gordo: justo cuando cambia el nombre del asfalto
                if ultimo_nombre is not None and nombre != ultimo_nombre:
                    f.write("%s  >>> EL ASFALTO PASA DE '%s' A '%s' con "
                            "humedad media %.4f y maxima %.4f <<<\n"
                            % (cuando, ultimo_nombre, nombre, c["mojado"],
                               c["mojado_max"]))
                    print("  %s  el asfalto pasa a %s (%.4f)"
                          % (cuando, nombre, c["mojado"]))
                ultimo_nombre = nombre

                f.write("%s  %-6s  %6.0f  %2d %-22s %4.1f %4.1f  %.5f %.5f "
                        "%.3f %.3f  %d\n"
                        % (cuando, sco.sesion(), c["reloj_sesion"], cielo,
                           clima.nombre_cielo(cielo), c["aire"], c["asfalto"],
                           c["mojado"], c["mojado_max"], c["lluvia"],
                           c["nubes"], c["agarre"]))
                f.flush()

                n += 1
                if n % 12 == 0:
                    print("  %s  %s, %.0f grados de asfalto, %s  (%d apuntes)"
                          % (cuando, clima.nombre_cielo(cielo), c["asfalto"],
                             nombre, n))
                time.sleep(cada)
        except KeyboardInterrupt:
            f.write("%s  FIN DEL REGISTRO (%d apuntes)\n" % (marca(), n))
            print("\n  Parado. %d apuntes en %s" % (n, archivo))
    return 0


if __name__ == "__main__":
    sys.exit(main())
