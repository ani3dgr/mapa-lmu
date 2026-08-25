# -*- coding: utf-8 -*-
"""
Que coche lleva cada equipo.

En vivo, el juego solo da el nombre del equipo con su dorsal ("Manthey DK
Engineering 2026 #91:WEC") y un codigo interno del coche ("91_26_MANT..."),
y los archivos de los coches van cifrados y no se pueden abrir.

Pero al TERMINAR una sesion el juego escribe un XML con la marca y el modelo de
cada coche, y con ese mismo codigo. De eso se ocupa resultados.py, que monta el
catalogo. Aqui solo se consulta, y por eso ya casi nunca hay que teclear nada.

Lo que queda a mano es solo para corregir o para un coche que no haya terminado
ninguna sesion todavia. Lo escrito a mano manda sobre el catalogo, para poder
arreglar cualquier cosa que el juego escriba raro.

Ojo con identificar por EQUIPO: offline contra la IA son los equipos oficiales,
pero online cada jugador le pone a su coche el nombre que quiere. En una prueba
con 828 sesiones salieron 1.267 nombres de equipo distintos para 34 modelos de
coche. Por eso se busca primero por codigo, que si es exacto.
"""
import json
import os
import re

import resultados
import rutas

RUTA = rutas.datos("coches.json")

CATEGORIAS = ["Hypercar", "LMP2", "LMP3", "GT3", "GTE"]

# LMP2 es monomarca: no hace falta que nadie lo rellene
POR_CLASE = {"lmp2": ("Oreca", "07")}

_cache = None

# de donde salen los modelos que trae el juego instalados
VEHICULOS = ""      # se resuelve al vuelo: el juego puede estar en cualquier sitio

MARCAS = ["Aston Martin", "Isotta Fraschini", "Isotta", "Lamborghini",
          "Mercedes-AMG", "Mercedes", "Chevrolet", "Corvette", "McLaren",
          "Porsche", "Ferrari", "Toyota", "Cadillac", "Peugeot", "Alpine",
          "Genesis", "Lexus", "Ford", "BMW", "Oreca", "Ligier", "Duqueine",
          "Ginetta", "Glickenhaus", "Vanwall", "Vandervell", "ADESS", "SGC"]


def modelos_instalados():
    """
    Los modelos de coche que hay, para elegirlos de una lista en vez de
    escribirlos a mano.

    Se prefieren los nombres que da el propio juego en sus resultados
    ("Lexus RCF LMGT3"), que son los buenos. Si todavia no se ha leido ningun
    resultado se tira de los nombres de carpeta de Installed/Vehicles, que
    valen para salir del paso pero son mas toscos ("LexusRCF GT3").
    """
    import juego
    del_juego = resultados.modelos()
    if del_juego:
        return del_juego
    base = juego.subcarpeta("Installed", "Vehicles")
    salida = []
    try:
        for carpeta in sorted(os.listdir(base)):
            nombre = re.sub(r"_\d{4}$", "", carpeta).replace("_", " ")
            nombre = re.sub(r"\s+", " ", nombre).strip()
            if nombre and nombre not in salida:
                salida.append(nombre)
    except OSError:
        pass
    return salida


def partir_modelo(texto):
    """
    'BMW M4 LMGT3' -> ('BMW', 'M4 LMGT3')

    Se prueban las marcas de la mas larga a la mas corta: si no, "Mercedes-AMG
    LMGT3" cazaria con "Mercedes" y el modelo quedaria en "-AMG LMGT3".
    """
    for marca in sorted(MARCAS, key=len, reverse=True):
        if texto.lower().startswith(marca.lower()):
            return marca, texto[len(marca):].strip(" -")
    trozos = texto.split(" ", 1)
    return trozos[0], (trozos[1] if len(trozos) > 1 else "")


def _vacio():
    return {"coches": {}, "sin_identificar": {}}


def cargar():
    global _cache
    if _cache is None:
        try:
            with open(RUTA, encoding="utf-8-sig") as f:
                d = json.load(f)
            _cache = {"coches": d.get("coches", {}),
                      "sin_identificar": d.get("sin_identificar", {})}
        except (OSError, ValueError):
            _cache = _vacio()
    return _cache


def guardar():
    d = cargar()
    try:
        with open(RUTA, "w", encoding="utf-8") as f:
            json.dump({
                "_ayuda": "Se edita desde el programa: opciones -> pestana Coches. "
                          "La clave es el nombre del equipo en minusculas.",
                "coches": d["coches"],
                "sin_identificar": d["sin_identificar"],
            }, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def equipo_de(nombre_vehiculo):
    """'Heart of Racing Team 2026 #23:WEC' -> 'Heart of Racing Team'"""
    return re.split(r"\s+\d{4}\s*#|\s*#", nombre_vehiculo or "")[0].strip()


def dorsal_de(nombre_vehiculo):
    """'Heart of Racing Team 2026 #23:WEC' -> '#23'"""
    hallado = re.search(r"#\s*(\d+)", nombre_vehiculo or "")
    return "#" + hallado.group(1) if hallado else ""


def _cuadra_la_clase(ficha, clase):
    """
    Que la ficha sea de la categoria en la que va ese coche ahora mismo.

    Es la red que evita el fallo de antes: si en la tabla pone que AF Corse
    lleva un Ferrari 296 (GT3) y el coche que tenemos delante va en Hypercar,
    esa ficha no vale y mas vale no decir nada que decir una mentira.

    Sin clase (no siempre llega) se da por buena, que es como funcionaba antes.
    """
    categoria = (ficha.get("categoria") or "").strip().lower()
    if not clase or not categoria:
        return True
    return categoria == (resultados.categoria_de(clase) or "").strip().lower()


def _del_catalogo(ficha):
    """Pasa una ficha del catalogo del juego al formato de aqui."""
    marca, modelo = partir_modelo(ficha.get("modelo", ""))
    return {"marca": marca, "modelo": modelo,
            "categoria": ficha.get("categoria") or "GT3", "origen": "juego"}


def buscar(nombre_vehiculo, clase="", codigo=""):
    """
    Devuelve {"marca", "modelo", "categoria"} o None si no se sabe que coche es.

    Se mira en este orden:
      1. El codigo del coche en el catalogo leido de los resultados del juego.
         Este es el bueno: es exacto y lo rellena el juego solo.
      2. Lo que haya puesto el usuario a mano, para un coche que el juego no
         haya escrito todavia en ningun resultado.
      3. El nombre del equipo en el catalogo, por si el codigo cambio de
         temporada pero el equipo sigue llamandose igual.
      4. La clase, para lo que es monomarca (LMP2 siempre es un Oreca 07).

    El codigo va PRIMERO, por delante de lo puesto a mano, porque el equipo no
    identifica un coche: un equipo de verdad corre en varias categorias a la
    vez. United Autosports lleva un McLaren en GT3 y un Oreca en LMP2; AF Corse
    lleva un Ferrari 296 en GT3 y el 499P en Hypercar. Preguntando solo por el
    equipo salia el coche equivocado, y pasaba de verdad.
    """
    equipo = equipo_de(nombre_vehiculo)

    if codigo:
        ficha = resultados.por_codigo(codigo)
        if ficha:
            return _del_catalogo(ficha)

    ficha = cargar()["coches"].get(equipo.lower())
    if ficha and _cuadra_la_clase(ficha, clase):
        return dict(ficha)

    if equipo:
        ficha = resultados.por_equipo(equipo)
        if ficha and _cuadra_la_clase(ficha, clase):
            return _del_catalogo(ficha)

    for pista, (marca, modelo) in POR_CLASE.items():
        if pista in (clase or "").lower():
            return {"marca": marca, "modelo": modelo, "categoria": "LMP2"}
    return None


def texto(nombre_vehiculo, clase="", codigo=""):
    """'Porsche 911 GT3 R' o, si no se sabe, el nombre del equipo."""
    ficha = buscar(nombre_vehiculo, clase, codigo)
    if ficha:
        return ("%s %s" % (ficha.get("marca", ""), ficha.get("modelo", ""))).strip()
    return equipo_de(nombre_vehiculo)


def anotar_desconocido(nombre_vehiculo, clase, circuito, fecha, codigo=""):
    """
    Apunta un equipo que no esta en la tabla, con donde y cuando se vio.

    Con el catalogo de los resultados del juego esto casi nunca salta: solo
    para un coche que no haya terminado ni una sesion todavia. En cuanto se
    acabe una carrera con el, el juego escribe su archivo, el catalogo lo lee
    y desaparece de aqui solo.
    """
    equipo = equipo_de(nombre_vehiculo)
    if not equipo or buscar(nombre_vehiculo, clase, codigo):
        return False
    d = cargar()
    clave = equipo.lower()
    if clave in d["sin_identificar"]:
        return False
    d["sin_identificar"][clave] = {
        "equipo": equipo, "clase": clase or "", "codigo": codigo,
        "visto_en": circuito or "", "visto_el": fecha or "",
    }
    guardar()
    return True


def definir(equipo, categoria, marca, modelo):
    """Da de alta o corrige un coche, y lo quita de los pendientes."""
    if not equipo or not (marca or modelo):
        return False
    d = cargar()
    d["coches"][equipo.lower()] = {"equipo": equipo, "categoria": categoria,
                                   "marca": marca, "modelo": modelo}
    d["sin_identificar"].pop(equipo.lower(), None)
    return guardar()


def borrar(equipo):
    d = cargar()
    quitado = d["coches"].pop(equipo.lower(), None) is not None
    quitado = d["sin_identificar"].pop(equipo.lower(), None) is not None or quitado
    if quitado:
        guardar()
    return quitado


def por_categoria():
    """{'GT3': [ficha, ...], ...} ordenado, para pintar el arbol."""
    salida = {c: [] for c in CATEGORIAS}
    for ficha in cargar()["coches"].values():
        salida.setdefault(ficha.get("categoria") or "GT3", []).append(ficha)
    for lista in salida.values():
        lista.sort(key=lambda f: (f.get("marca", ""), f.get("modelo", ""),
                                  f.get("equipo", "")))
    return salida


def traer_de_la_sesion():
    """
    Mete en la lista de pendientes todos los equipos de la sesion que hay
    ahora mismo en el juego.

    Asi se rellenan de una sentada mirando la clasificacion en pantalla, que es
    donde salen los logos de las marcas, en vez de ir descubriendolos de uno en
    uno segun aparezcan.

    Devuelve (anadidos, total_en_pista) o (None, 0) si el juego no esta.
    """
    try:
        import lector_lmu as lmu
        sco = lmu.Scoring()
    except OSError:
        return None, 0
    n = sco.n_coches()
    if not n:
        return 0, 0
    anadidos = 0
    for v in range(n):
        b = lmu.SCO_BASE + v * lmu.SCO_STRIDE
        vehiculo = lmu.txt(sco.sco, b + lmu.OFF_VEHICULO, 64)
        clase = lmu.txt(sco.sco, b + lmu.OFF_CLASE, 32)
        codigo = lmu.txt(sco.sco, b + lmu.OFF_CODIGO, 32)
        if anotar_desconocido(vehiculo, clase, sco.circuito(), "", codigo):
            anadidos += 1
    return anadidos, n


def limpiar_resueltos():
    """
    Quita de los pendientes los que el catalogo del juego ya sabe identificar.

    Hace falta porque los pendientes se guardaron en su dia, cuando la marca
    habia que ponerla a mano. Segun se van leyendo resultados del juego, esa
    lista se vacia sola en vez de quedarse ahi dando la lata.
    """
    d = cargar()
    resueltos = [clave for clave, f in d["sin_identificar"].items()
                 if buscar(f.get("equipo", ""), f.get("clase", ""),
                           f.get("codigo", ""))]
    for clave in resueltos:
        d["sin_identificar"].pop(clave, None)
    if resueltos:
        guardar()
    return len(resueltos)


def pendientes():
    """Los equipos vistos en pista que nadie ha identificado todavia."""
    limpiar_resueltos()
    return sorted(cargar()["sin_identificar"].values(),
                  key=lambda f: f.get("equipo", ""))
