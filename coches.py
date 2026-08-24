# -*- coding: utf-8 -*-
"""
Que coche lleva cada equipo.

El juego NO publica la marca ni el modelo por ningun sitio: solo da el nombre
del equipo con su dorsal ("Manthey DK Engineering 2026 #91:WEC") y un codigo
interno del vehiculo ("91_26_MANT12345678"). Los archivos de los coches van
comprimidos y no se pueden rastrear.

Asi que la marca hay que ponerla a mano UNA VEZ por equipo, y el programa se
encarga del resto: mientras ruedas apunta solo los equipos que no conoce, y
desde la pestana "Coches" se rellenan. No hace falta tocar ningun archivo.

Por que la clave es el EQUIPO y no el codigo del vehiculo: el codigo lleva el
ano dentro (91_**26**_MANT...), asi que cambiaria solo al llegar la temporada
siguiente aunque fuera el mismo coche. El nombre del equipo aguanta mucho mejor.
"""
import json
import os
import re

import rutas

RUTA = rutas.datos("coches.json")

CATEGORIAS = ["Hypercar", "LMP2", "LMP3", "GT3", "GTE"]

# LMP2 es monomarca: no hace falta que nadie lo rellene
POR_CLASE = {"lmp2": ("Oreca", "07")}

_cache = None

# de donde salen los modelos que trae el juego instalados
VEHICULOS = ""      # se resuelve al vuelo: el juego puede estar en cualquier sitio

MARCAS = ["Aston Martin", "Isotta", "Lamborghini", "Mercedes", "Chevrolet",
          "Corvette", "McLaren", "Porsche", "Ferrari", "Toyota", "Cadillac",
          "Peugeot", "Alpine", "Genesis", "Lexus", "Ford", "BMW", "Oreca",
          "Ligier", "Duqueine", "Ginetta", "Vandervell", "ADESS", "SGC"]


def modelos_instalados():
    """
    Los coches que trae el juego, sacados de Installed/Vehicles.

    Sirve para elegir el modelo de una lista en vez de escribirlo a mano: menos
    erratas, y ademas se ve de un vistazo que coches hay.
    """
    import juego
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
    """'BMW M4 LMGT3' -> ('BMW', 'M4 LMGT3')"""
    for marca in MARCAS:
        if texto.lower().startswith(marca.lower()):
            return marca, texto[len(marca):].strip()
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


def buscar(nombre_vehiculo, clase=""):
    """
    Devuelve {"marca", "modelo", "categoria"} o None si ese equipo no esta.
    """
    for pista, (marca, modelo) in POR_CLASE.items():
        if pista in (clase or "").lower():
            return {"marca": marca, "modelo": modelo, "categoria": "LMP2"}
    ficha = cargar()["coches"].get(equipo_de(nombre_vehiculo).lower())
    return dict(ficha) if ficha else None


def texto(nombre_vehiculo, clase=""):
    """'Porsche 911 GT3 R' o, si no se sabe, el nombre del equipo."""
    ficha = buscar(nombre_vehiculo, clase)
    if ficha:
        return ("%s %s" % (ficha.get("marca", ""), ficha.get("modelo", ""))).strip()
    return equipo_de(nombre_vehiculo)


def anotar_desconocido(nombre_vehiculo, clase, circuito, fecha, codigo=""):
    """
    Apunta un equipo que no esta en la tabla, con donde y cuando se vio.

    Es lo que permite que el mantenimiento sea automatico: si en unos meses
    meten coches nuevos, apareceran solos en la pestana Coches esperando a que
    alguien les ponga marca y modelo.
    """
    equipo = equipo_de(nombre_vehiculo)
    if not equipo or buscar(nombre_vehiculo, clase):
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


def pendientes():
    """Los equipos vistos en pista que nadie ha identificado todavia."""
    return sorted(cargar()["sin_identificar"].values(),
                  key=lambda f: f.get("equipo", ""))
