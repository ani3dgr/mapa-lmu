# -*- coding: utf-8 -*-
"""
Lectura del buffer de scoring de LMU (posiciones de todos los coches en pista).

Reutiliza la base ya calibrada en ingeniero_ia.py:
    SCO_BASE = 560, SCO_STRIDE = 584, numVehicles en offset 116, trackName en 12.

Lo que NO estaba calibrado (posicion X/Z, quien es el jugador, clase del coche)
se autodetecta comparando contra el trazado real del circuito: solo hay un sitio
del buffer que coloca a TODOS los coches encima de la pista.
"""
import ctypes
import json
import math
import os
import re
import struct
import time

import rutas

CARPETA = rutas.carpeta()

SCO_MAP = "$rFactor2SMMP_Scoring$"
SCO_BASE = 560          # primer coche
SCO_STRIDE = 584        # bytes por coche
OFF_TRACK = 12          # nombre del circuito (64 bytes)
OFF_NUMVEH = 116        # numero de coches (int)
OFF_JUGADOR = 128       # mPlayerName en la cabecera: tu nombre de piloto
OFF_SESION = 76         # mSession: 0 = sin empezar, 1-4 practicas,
                        # 5-8 clasificacion, 9 warmup, 10-13 carrera
OFF_NOMBRE = 4          # driverName dentro de la ficha del coche (32 bytes)
OFF_VEHICULO = 36       # mVehicleName: "Heart of Racing Team 2026 #23:WEC"
OFF_CODIGO = 544        # mVehFilename: codigo interno del coche, "91_26_MANT..."
                        # Lleva el ano dentro, asi que cambia cada temporada:
                        # sirve de referencia, no como identificador estable.

# Verificados en pista el 23/08/2026 (Silverstone, 18 coches). Coinciden con el
# header oficial de Studio 397 salvo la posicion, que en el buffer del plugin
# cae 8 bytes antes de lo que dice el struct (por eso el stride es 584 y no 592).
OFF_POS = 264           # posicion en el mundo: 3 dobles X, Y, Z
OFF_YO = 196            # mIsPlayer: vale 1 solo en el coche del jugador
OFF_PUESTO = 199        # mPlace: puesto en carrera, 1..N
OFF_CLASE = 200         # mVehicleClass: texto (Hypercar / LMP2 / LMGT3)
OFF_VUELTAS = 100       # mTotalLaps: vueltas completadas (short)
OFF_DIST = 104          # mLapDist: metros recorridos en la vuelta actual
OFF_LATERAL = 112       # mPathLateral: separacion del centro de la pista (m)
OFF_BORDE = 120         # mTrackEdge: donde queda el borde POR ESE LADO. Viene
                        # con signo, del mismo lado que el coche, asi que para
                        # saber si esta fuera hay que comparar valores absolutos
OFF_MEJOR = 144         # mBestLapTime: mejor vuelta en segundos
OFF_ULTIMA = 168        # mLastLapTime: ultima vuelta cerrada, en segundos
OFF_SEC1 = 152          # mLastSector1: sector 1 de la ultima vuelta
OFF_SEC2 = 160          # mLastSector2: sectores 1+2 de la ultima vuelta
OFF_BOXES = 198         # mInPits: 1 si esta en la calle de boxes
OFF_FASE = 459          # mIndividualPhase: 5 = verde, 10 = bajo amarilla,
                        # 11 = bajo azul. Es lo que avisa de que hay amarilla.
OFF_BANDERA = 504       # mFlag: 0 = verde, 6 = azul (le estan doblando)
OFF_PENAS = 194         # mNumPenalties: sanciones pendientes (short). En
                        # CARRERA el juego no anula la vuelta, sanciona, asi
                        # que este es el aviso que cuenta ahi.
OFF_VALIDA = 506        # mCountLapFlag: veredicto del JUEGO sobre la vuelta.
                        # 2 = cuenta vuelta y tiempo (todo en orden)
                        # 1 = cuenta la vuelta pero no el tiempo
                        # 0 = no cuenta ninguna de las dos
                        # Baja de 2 en cuanto el juego invalida por salirse.

MAX_COCHES = 128

# ---------------- acceso a memoria compartida ----------------
_k32 = ctypes.windll.kernel32
_k32.OpenFileMappingW.restype = ctypes.c_void_p
_k32.OpenFileMappingW.argtypes = (ctypes.c_uint32, ctypes.c_int, ctypes.c_wchar_p)
_k32.MapViewOfFile.restype = ctypes.c_void_p
_k32.MapViewOfFile.argtypes = (ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32,
                               ctypes.c_uint32, ctypes.c_size_t)
_FILE_MAP_READ = 0x0004


def abrir(nombre):
    """Abre el mapa del juego SOLO si existe (nunca crea uno falso)."""
    h = _k32.OpenFileMappingW(_FILE_MAP_READ, False, nombre)
    if not h:
        raise OSError("no existe el mapa %s (juego cerrado o plugin desactivado)" % nombre)
    ptr = _k32.MapViewOfFile(h, _FILE_MAP_READ, 0, 0, 0)
    if not ptr:
        _k32.CloseHandle(h)
        raise OSError("no se pudo mapear %s" % nombre)
    return ptr


def d(base, off):
    return struct.unpack("<d", ctypes.string_at(base + off, 8))[0]


def i4(base, off):
    return struct.unpack("<i", ctypes.string_at(base + off, 4))[0]


def i2(base, off):
    return struct.unpack("<h", ctypes.string_at(base + off, 2))[0]


def u1(base, off):
    return ctypes.string_at(base + off, 1)[0]


def txt(base, off, n):
    """
    Texto del buffer. Los nombres de piloto llevan acentos (Francois Heriau,
    Jose Maria Lopez): se prueba UTF-8 y se cae a latin-1 si no cuadra.
    """
    crudo = ctypes.string_at(base + off, n).split(b"\x00")[0]
    try:
        return crudo.decode("utf-8")
    except UnicodeDecodeError:
        return crudo.decode("latin-1", "replace")


def normaliza(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


# ---------------- circuitos ----------------
def cargar_circuitos(recargar=False):
    """Los circuitos medidos. Cada uno vive en su propio archivo, dentro de
    la carpeta 'circuitos', para poder compartirlos sueltos."""
    import circuitos
    return circuitos.cargar(recargar)


def buscar_circuito(circuitos, nombre_juego):
    """Empareja el nombre que da el juego con uno de los trazados guardados."""
    n = normaliza(nombre_juego)
    if not n:
        return None, None
    if n in circuitos:
        return n, circuitos[n]
    # coincidencia parcial en cualquiera de los dos sentidos
    mejor, mejor_len = None, 0
    for clave, datos in circuitos.items():
        if (n in clave or clave in n) and len(clave) > mejor_len:
            mejor, mejor_len = clave, len(clave)
    return (mejor, circuitos[mejor]) if mejor else (None, None)


# ---------------- autocalibracion ----------------
MARGEN_XZ = 150.0     # m que un coche puede estar fuera del trazado (boxes, escapatorias)
MARGEN_Y = 30.0       # m fuera del rango de altura conocido del circuito
SALTO_MAX = 250.0     # m maximos que puede recorrer un coche entre dos lecturas
DISPERSION_MIN = 25.0  # m que como minimo separan al primer coche del ultimo


def _dist_al_trazado(x, z, puntos):
    return min(math.hypot(x - px, z - pz) for px, pz in puntos)


def muestra(sco, off, n_coches):
    """Lee la terna (X,Y,Z) de ese offset para todos los coches."""
    salida = []
    for v in range(n_coches):
        b = SCO_BASE + v * SCO_STRIDE
        salida.append((d(sco, b + off), d(sco, b + off + 8), d(sco, b + off + 16)))
    return salida


def _evaluar(ternas, puntos, altura):
    """
    Devuelve (desvio maximo al trazado, dispersion entre coches) si la muestra
    puede ser posiciones de coches, o None si no lo es.
    """
    ymin, ymax = altura
    peor = 0.0
    for x, y, z in ternas:
        if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(z)):
            return None
        if not (ymin - MARGEN_Y <= y <= ymax + MARGEN_Y):
            return None          # altura imposible en este circuito
        dist = _dist_al_trazado(x, z, puntos)
        if dist > MARGEN_XZ:
            return None          # ese coche no esta en el circuito
        peor = max(peor, dist)

    xs = [t[0] for t in ternas]
    zs = [t[2] for t in ternas]
    return peor, math.hypot(max(xs) - min(xs), max(zs) - min(zs))


def calibrar(sco, datos, n_coches, verboso=False):
    """
    Encuentra el offset de la posicion (X,Y,Z) dentro de la ficha de cada coche.

    No basta con que los valores caigan sobre el trazado: hay huecos del buffer
    (velocidades, aceleraciones) que valen casi cero, y el punto (0,0) del mundo
    suele quedar pegado al circuito, asi que colarian con todos los coches
    amontonados en el centro del mapa. Por eso se exige ademas altura coherente,
    que siga siendo valido en una segunda lectura y que nadie se teletransporte.

    Devuelve (offset_pos, informe) u (None, informe).
    """
    puntos, altura = datos["puntos"], datos["altura"]

    # Camino rapido: el offset ya verificado en pista. Se comprueba igualmente,
    # por si una actualizacion del juego moviera el campo de sitio.
    try:
        r = _evaluar(muestra(sco, OFF_POS, n_coches), puntos, altura)
    except (struct.error, OSError):
        r = None
    if r is not None:
        return OFF_POS, "offset posicion = %d (el conocido; desvio max %.1f m, coches separados %.0f m)" % (
            OFF_POS, r[0], r[1])

    # Busqueda completa solo si el conocido ya no vale.
    candidatos = []
    for off in range(0, SCO_STRIDE - 24, 8):
        try:
            r = _evaluar(muestra(sco, off, n_coches), puntos, altura)
        except (struct.error, OSError):
            continue
        if r is None:
            continue
        peor, dispersion = r
        if n_coches >= 3 and dispersion < DISPERSION_MIN:
            continue          # coches amontonados: es una zona de ceros, no posiciones
        candidatos.append((dispersion, off, peor))

    if not candidatos:
        # Si el trazado guardado esta mal (un escaneo torcido, por ejemplo) la
        # comprobacion falla aunque el offset sea correcto. Antes se devolvia
        # None y el mapa se quedaba en "Calibrando..." para siempre. Es mejor
        # tirar con el offset verificado: como mucho se vera el circuito raro,
        # pero los coches saldran en su sitio relativo.
        return OFF_POS, ("el trazado guardado no cuadra con las posiciones; "
                         "se usa el offset conocido (%d). Merece la pena "
                         "reescanear este circuito." % OFF_POS)

    # El criterio que de verdad separa el grano de la paja es la DISPERSION:
    # los coches de verdad estan repartidos por el circuito (cientos de metros),
    # mientras que las zonas de ceros y los tiempos de vuelta se quedan en unas
    # pocas decenas. En pista la diferencia es de un orden de magnitud.
    candidatos.sort(reverse=True)
    dispersion, off, peor = candidatos[0]
    informe = "offset posicion = %d (desvio max %.1f m, coches separados %.0f m, %d candidatos)" % (
        off, peor, dispersion, len(candidatos))
    if verboso:
        informe += "\n  descartados: " + ", ".join(
            "%d (%.0fm)" % (o, disp) for disp, o, _ in candidatos[1:6])
    return off, informe


def _solo_uno(sco, off, n_coches):
    """Cierto si en ese byte exactamente un coche vale 1 y el resto 0."""
    try:
        vals = [u1(sco, SCO_BASE + v * SCO_STRIDE + off) for v in range(n_coches)]
    except OSError:
        return False
    return sorted(vals) == [0] * (n_coches - 1) + [1]


def buscar_jugador(sco, n_coches):
    """
    Offset del byte que marca al coche del jugador.

    Se usa el verificado (196) siempre que cumpla. Solo si no cumpliera -- por
    ejemplo si una actualizacion del juego moviera el campo -- se busca a ciegas.

    Buscar a ciegas es lo que habia antes y daba problemas: con 18 coches hay
    varios bytes que por casualidad tienen un unico 1 (el 457 marca al que ha
    pedido entrar a boxes), y quedarse con el de offset mas bajo podia acabar
    siguiendo a otro piloto. Sintoma: tu circulo se convertia de repente en el
    de un rival.
    """
    if n_coches > 0 and _solo_uno(sco, OFF_YO, n_coches):
        return OFF_YO
    for off in range(0, SCO_STRIDE):
        if off != OFF_YO and _solo_uno(sco, off, n_coches):
            return off
    return OFF_YO


def calibrar_jugador(sco, n_coches):
    """Todos los offsets que cumplen la condicion. Solo para diagnostico."""
    validos = []
    for off in range(0, SCO_STRIDE):
        try:
            vals = [u1(sco, SCO_BASE + v * SCO_STRIDE + off) for v in range(n_coches)]
        except OSError:
            continue
        if sorted(vals) == [0] * (n_coches - 1) + [1]:
            validos.append(off)
    return validos


def calibrar_clase(sco, n_coches):
    """Busca el campo de texto con la clase del coche (Hypercar / LMP2 / LMGT3...)."""
    CLASES = ("hyper", "lmp", "lmgt", "gte", "gt3", "gtp")
    for off in range(0, SCO_STRIDE - 8):
        try:
            vals = [txt(sco, SCO_BASE + v * SCO_STRIDE + off, 32) for v in range(n_coches)]
        except OSError:
            continue
        # el texto tiene que EMPEZAR donde empieza el campo: un offset una
        # posicion antes tambien contendria la palabra, precedida de basura
        if not all(v[:1].isalpha() for v in vals):
            continue
        if all(any(c in v.lower() for c in CLASES) for v in vals):
            return off
    return None


# ---------------- lectura en vivo ----------------
class Scoring:
    def __init__(self):
        self.sco = abrir(SCO_MAP)
        self.off_pos = None            # se confirma contra el trazado al entrar
        self.off_jugador = OFF_YO      # verificados en pista; la autodeteccion
        self.off_clase = OFF_CLASE     # solo hace falta si el juego los mueve

    def circuito(self):
        return txt(self.sco, OFF_TRACK, 64)

    def nombre_jugador(self):
        """Tu nombre de piloto, tal cual lo publica la cabecera."""
        return txt(self.sco, OFF_JUGADOR, 32)

    def sesion(self):
        """Que sesion se esta corriendo. Al cambiar hay que empezar de cero."""
        return i4(self.sco, OFF_SESION)

    def version(self):
        """
        Contador que el plugin sube en cada actualizacion.

        Es la forma de saber si el juego esta publicando: al salir al menu
        principal la memoria se queda con los ultimos datos (mismo circuito,
        mismos coches) y sin esto el mapa seguiria pintando una sesion que ya
        no existe.
        """
        return i4(self.sco, 0)

    def tiempo_sesion(self):
        """
        mCurrentET: segundos transcurridos de la sesion.

        Vuelve a empezar en cada sesion nueva, asi que si retrocede es que se
        ha empezado otra. Hace falta porque el codigo de sesion no distingue
        una practica de la practica siguiente: las dos valen 1.
        """
        return d(self.sco, 80)

    def en_pista(self):
        """mInRealtime: 1 conduciendo, 0 en el garaje o en la reproduccion."""
        return bool(u1(self.sco, 127))

    def fase_juego(self):
        """mGamePhase de la cabecera: 5 = verde, 6 = amarilla a todo el trazado."""
        return u1(self.sco, 120)

    def largo_pista(self):
        """Longitud del circuito en metros (cabecera del buffer)."""
        return d(self.sco, 100)

    def n_coches(self):
        n = i4(self.sco, OFF_NUMVEH)
        return n if 0 < n <= MAX_COCHES else 0

    def coches(self):
        """Lista de dicts: nombre, x, z, clase, es_yo."""
        salida = []
        if self.off_pos is None:
            return salida
        mi_nombre = self.nombre_jugador()
        for v in range(self.n_coches()):
            b = SCO_BASE + v * SCO_STRIDE
            try:
                x = d(self.sco, b + self.off_pos)
                z = d(self.sco, b + self.off_pos + 16)
            except (OSError, struct.error):
                continue
            if not (math.isfinite(x) and math.isfinite(z)):
                continue
            salida.append({
                "nombre": txt(self.sco, b + OFF_NOMBRE, 32),
                "vehiculo": txt(self.sco, b + OFF_VEHICULO, 64),
                "codigo": txt(self.sco, b + OFF_CODIGO, 32),
                "x": x,
                "z": z,
                "clase": txt(self.sco, b + self.off_clase, 32) if self.off_clase is not None else "",
                # Se cruza el byte mIsPlayer con el nombre que da la cabecera:
                # si el juego pone la marca a cero un instante (paso por boxes,
                # cumplir una sancion) el coche propio no se pierde.
                "es_yo": (bool(u1(self.sco, b + self.off_jugador))
                          if self.off_jugador is not None else False)
                         or (bool(mi_nombre)
                             and txt(self.sco, b + OFF_NOMBRE, 32) == mi_nombre),
                "dist": d(self.sco, b + OFF_DIST),        # metros de vuelta
                "lateral": d(self.sco, b + OFF_LATERAL),
                "borde": d(self.sco, b + OFF_BORDE),
                "vueltas": i2(self.sco, b + OFF_VUELTAS),
                "mejor": d(self.sco, b + OFF_MEJOR),      # s, 0 si aun no tiene
                "ultima": d(self.sco, b + OFF_ULTIMA),    # s, la que acaba de cerrar
                "sec1": d(self.sco, b + OFF_SEC1),        # sector 1 de esa vuelta
                "sec2": d(self.sco, b + OFF_SEC2),        # sectores 1+2 acumulados
                "vuelta_valida": u1(self.sco, b + OFF_VALIDA),
                "penalizaciones": i2(self.sco, b + OFF_PENAS),
                "en_boxes": bool(u1(self.sco, b + OFF_BOXES)),
                "fase": u1(self.sco, b + OFF_FASE),
                "bandera": u1(self.sco, b + OFF_BANDERA),
            })
        return salida


def calibrar_puesto(sco, n_coches):
    """
    Busca el byte con el puesto en carrera: sus valores entre todos los coches
    tienen que ser exactamente 1..N sin repetirse.
    """
    if n_coches < 2:
        return None
    esperado = list(range(1, n_coches + 1))
    for off in range(0, SCO_STRIDE):
        try:
            vals = [u1(sco, SCO_BASE + v * SCO_STRIDE + off) for v in range(n_coches)]
        except OSError:
            continue
        if sorted(vals) == esperado:
            return off
    return None
