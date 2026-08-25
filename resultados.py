# -*- coding: utf-8 -*-
"""
La marca y el modelo de cada coche, sacados del propio juego.

Durante un tiempo se creyo que el juego no publicaba el modelo por ningun
sitio: en la memoria compartida, que es lo que se lee en vivo, solo viene el
nombre del equipo con su dorsal y un codigo interno del coche. Por eso la
pestana Coches nacio pidiendo que se rellenara la marca a mano.

Pero el juego SI lo dice, solo que en otro sitio y mas tarde: al terminar cada
sesion escribe un XML en UserData/Log/Results, y ahi viene, coche por coche:

    <VehFile>78_26_AKKO79996909.VEH</VehFile>
    <CarType>Lexus RCF LMGT3</CarType>
    <CarClass>GT3</CarClass>
    <TeamName>Akkodis ASP Team</TeamName>

Ese VehFile es EL MISMO codigo que se lee en vivo, asi que con leer esos
archivos una vez se sabe que coche lleva cada uno sin preguntarle nada a nadie.

Por que esto importa mas de lo que parece:

- El nombre del equipo NO sirve de identificador. Offline contra la IA son los
  equipos oficiales y son cuatro, pero online cada jugador le pone a su coche
  el nombre que quiere. En una prueba real salieron 1.267 nombres de equipo
  distintos para 34 modelos de coche. Identificar por equipo no acaba nunca;
  por codigo, si.
- Cuando el juego saque coches nuevos, apareceran solos aqui en cuanto se
  corra una sesion con ellos. No hay que tocar nada ni esperar a nadie.

Se guarda lo leido en catalogo_coches.json y en cada arranque solo se miran
los archivos nuevos, que la primera lectura de 828 sesiones son 0,4 segundos
pero no hace falta repetirla.
"""
import json
import os
import re

import rutas

RUTA = rutas.datos("catalogo_coches.json")

# Como llama el juego a cada clase -> como la llamamos nosotros
CLASES = {
    "HYPER": "Hypercar", "HYPERCAR": "Hypercar", "LMH": "Hypercar",
    "LMDH": "Hypercar", "LMP2": "LMP2", "LMP2_ELMS": "LMP2",
    "LMP3": "LMP3", "GT3": "GT3", "LMGT3": "GT3", "GTE": "GTE",
}

_bloque = re.compile(r"<Driver>(.*?)</Driver>", re.S)
_cache = None


def _campo(bloque, nombre):
    hallado = re.search(r"<%s>([^<]*)</%s>" % (nombre, nombre), bloque)
    return hallado.group(1).strip() if hallado else ""


def _limpiar_codigo(texto):
    """'78_26_AKKO79996909.VEH' -> '78_26_AKKO79996909'"""
    texto = (texto or "").strip().upper()
    return texto[:-4] if texto.endswith(".VEH") else texto


def categoria_de(clase_del_juego):
    """'LMP2_ELMS' -> 'LMP2'. Si no la conocemos, se devuelve tal cual."""
    clave = (clase_del_juego or "").strip().upper()
    return CLASES.get(clave, clase_del_juego or "")


def carpeta():
    """Donde deja el juego los resultados, o cadena vacia si no aparece."""
    import juego
    return juego.subcarpeta("UserData", "Log", "Results")


def _vacio():
    return {"codigos": {}, "equipos": {}, "archivos": {}}


def cargar():
    global _cache
    if _cache is None:
        try:
            with open(RUTA, encoding="utf-8-sig") as f:
                d = json.load(f)
            _cache = {"codigos": d.get("codigos", {}),
                      "equipos": d.get("equipos", {}),
                      "archivos": d.get("archivos", {})}
        except (OSError, ValueError):
            _cache = _vacio()
    return _cache


def guardar():
    d = cargar()
    try:
        with open(RUTA, "w", encoding="utf-8") as f:
            json.dump({
                "_ayuda": "Lo escribe el programa solo, leyendo "
                          "UserData/Log/Results del juego. No hace falta tocarlo.",
                "codigos": d["codigos"],
                "equipos": d["equipos"],
                "archivos": d["archivos"],
            }, f, ensure_ascii=False, indent=1)
        return True
    except OSError:
        return False


def _leer_archivo(ruta, d):
    """Saca los coches de un XML de resultados. Devuelve cuantos codigos nuevos."""
    try:
        with open(ruta, encoding="utf-8", errors="ignore") as f:
            texto = f.read()
    except OSError:
        return 0
    nuevos = 0
    for bloque in _bloque.findall(texto):
        modelo = _campo(bloque, "CarType")
        if not modelo:
            continue
        clase = categoria_de(_campo(bloque, "CarClass"))
        equipo = _campo(bloque, "TeamName")
        codigo = _limpiar_codigo(_campo(bloque, "VehFile"))
        ficha = {"modelo": modelo, "categoria": clase, "equipo": equipo}
        if codigo and codigo not in d["codigos"]:
            d["codigos"][codigo] = ficha
            nuevos += 1
        if equipo:
            # el equipo es peor identificador que el codigo (online cada uno se
            # pone el nombre que quiere), pero sirve de red por si el codigo
            # cambia de temporada
            d["equipos"][equipo.lower()] = ficha
    return nuevos


def actualizar():
    """
    Lee los resultados que aun no se habian leido.

    Devuelve (archivos_nuevos, codigos_nuevos). (0, 0) si no hay nada nuevo,
    y (None, 0) si no se encuentra la carpeta del juego.
    """
    base = carpeta()
    if not base or not os.path.isdir(base):
        return None, 0
    d = cargar()
    archivos = 0
    codigos = 0
    try:
        listado = os.listdir(base)
    except OSError:
        return None, 0
    for nombre in sorted(listado):
        if not nombre.lower().endswith(".xml") or nombre in d["archivos"]:
            continue
        codigos += _leer_archivo(os.path.join(base, nombre), d)
        d["archivos"][nombre] = 1
        archivos += 1
    if archivos:
        guardar()
    return archivos, codigos


def por_codigo(codigo):
    ficha = cargar()["codigos"].get(_limpiar_codigo(codigo))
    return dict(ficha) if ficha else None


def por_equipo(equipo):
    ficha = cargar()["equipos"].get((equipo or "").strip().lower())
    return dict(ficha) if ficha else None


def modelos():
    """Los modelos distintos que han aparecido, ordenados."""
    return sorted({f["modelo"] for f in cargar()["codigos"].values() if f.get("modelo")})


def modelos_por_categoria():
    """{'GT3': ['BMW M4 LMGT3', ...], ...}"""
    salida = {}
    for f in cargar()["codigos"].values():
        if f.get("modelo"):
            salida.setdefault(f.get("categoria") or "GT3", set()).add(f["modelo"])
    return {c: sorted(v) for c, v in salida.items()}


def resumen():
    """(modelos, decoraciones, sesiones_leidas)"""
    d = cargar()
    return len(modelos()), len(d["codigos"]), len(d["archivos"])
