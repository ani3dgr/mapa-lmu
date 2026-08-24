# -*- coding: utf-8 -*-
"""
Busca si el juego publica en algun sitio los avisos de limites de pista.

El header oficial de Studio 397 documenta unos campos, pero LMU anade cosas
propias sobre la base de rFactor 2 y podria estar guardando ahi el contador de
avisos (el que sumado tres veces acaba en drive-through). Esto vigila la ficha
ENTERA de tu coche byte a byte y apunta los que cambian pocas veces, que son
los candidatos a ser contadores o marcas.

Se ejecuta con el juego rodando. Salte de pista varias veces, a proposito, de
esas que el juego te avisa. Cuantas mas, mejor: si hay un contador, se vera
subiendo justo en esos momentos. Ctrl+C para terminar.

Escribe: mapa/buscar_aviso.txt
"""
import ctypes
import os
import sys
import time

import rutas
import idiomas
import lector_lmu as lmu

# la consola de Windows habla cp1252 y se cae con letras que no sean suyas
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SALIDA = rutas.datos("buscar_aviso.txt")
HZ = 10.0
# los que ya sabemos que cambian todo el rato: posicion, tiempos, distancia...
IGNORAR = set(range(96, 200)) | set(range(232, 300)) | set(range(456, 500))
MAX_CAMBIOS = 40      # un byte que cambia mas veces que esto es ruido, no un contador


def main():
    try:
        sco = lmu.Scoring()
    except OSError as e:
        print(idiomas.t("sc.sin_juego") % e)
        return 1
    sco.off_pos = lmu.OFF_POS

    n = sco.n_coches()
    yo = next((v for v in range(n)
               if lmu.u1(sco.sco, lmu.SCO_BASE + v * lmu.SCO_STRIDE + lmu.OFF_YO)), None)
    if yo is None:
        print(idiomas.t("sc.sin_jugador2"))
        return 1
    base = lmu.SCO_BASE + yo * lmu.SCO_STRIDE

    print("=" * 68)
    print(idiomas.t("dg.titulo"))
    print("=" * 68)
    print(idiomas.t("dg.como"))
    print("=" * 68)
    print()

    t0 = time.time()
    ficha = sco.sco + base            # direccion real de tu ficha
    antes = bytearray(ctypes.string_at(ficha, lmu.SCO_STRIDE))
    historial = {}          # offset -> [(segundo, valor viejo, valor nuevo), ...]
    fuera_en = []           # momentos en que estabas fuera de pista

    try:
        while True:
            time.sleep(1.0 / HZ)
            t = time.time() - t0
            ahora = bytearray(ctypes.string_at(ficha, lmu.SCO_STRIDE))

            lateral = lmu.d(sco.sco, base + lmu.OFF_LATERAL)
            borde = lmu.d(sco.sco, base + lmu.OFF_BORDE)
            if borde and abs(lateral) > abs(borde):
                if not fuera_en or t - fuera_en[-1] > 3.0:
                    fuera_en.append(t)
                    print(idiomas.t("dg.fuera")
                          % (t, abs(lateral) - abs(borde)))

            for off in range(lmu.SCO_STRIDE):
                if off in IGNORAR or antes[off] == ahora[off]:
                    continue
                historial.setdefault(off, []).append((t, antes[off], ahora[off]))
            antes = ahora
    except KeyboardInterrupt:
        pass

    lineas = []

    def apunta(txt):
        print(txt)
        lineas.append(txt)

    apunta("BUSQUEDA DEL CONTADOR DE AVISOS")
    apunta("duracion: %.0f s   salidas de pista detectadas: %d"
           % (time.time() - t0, len(fuera_en)))
    apunta("momentos en que estabas fuera: %s"
           % ", ".join("%.0fs" % x for x in fuera_en))
    apunta("")
    apunta("Bytes que cambiaron POCAS veces (candidatos a contador o marca):")
    apunta("")

    candidatos = [(off, camb) for off, camb in historial.items()
                  if 0 < len(camb) <= MAX_CAMBIOS]
    candidatos.sort(key=lambda x: len(x[1]))
    if not candidatos:
        apunta("  ninguno.")
    for off, cambios in candidatos:
        conocido = {194: "mNumPenalties", 196: "mIsPlayer", 197: "mControl",
                    198: "mInPits", 199: "mPlace", 504: "mFlag",
                    505: "mUnderYellow", 506: "mCountLapFlag",
                    507: "mInGarageStall"}.get(off, "")
        apunta("  offset %3d %-16s %d cambio(s)" % (off, conocido, len(cambios)))
        for t, viejo, nuevo in cambios[:12]:
            cerca = any(abs(t - f) < 6.0 for f in fuera_en)
            apunta("      %6.1fs  %3d -> %-3d %s"
                   % (t, viejo, nuevo, "<== justo al salirte" if cerca else ""))
        if len(cambios) > 12:
            apunta("      ... y %d mas" % (len(cambios) - 12))
        apunta("")

    with open(SALIDA, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))
    print(idiomas.t("dg.guardado") % SALIDA)
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
