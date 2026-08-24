# -*- coding: utf-8 -*-
"""
Los circuitos medidos, uno por archivo.

Antes iban todos juntos en circuitos_mapa.json, y eso hacia imposible
compartir uno suelto: habia que abrir el archivo y recortar a mano. Ahora cada
trazado es un archivo dentro de la carpeta "circuitos", asi que pasarle Spa a
un amigo es mandarle spa.json y que lo copie en su carpeta. El programa lo
detecta al arrancar, sin instalar nada.

Tambien se puede subir la carpeta entera a internet para que la gente la
descargue, o bajarse solo los circuitos que le falten.
"""
import json
import os

import rutas

CARPETA = rutas.datos("circuitos")
ANTIGUO = rutas.datos("circuitos_mapa.json")

_cache = None


def _archivo(clave):
    return os.path.join(CARPETA, "%s.json" % clave)


def migrar():
    """Parte el archivo unico de antes en uno por circuito."""
    if not os.path.isfile(ANTIGUO):
        return 0
    try:
        with open(ANTIGUO, encoding="utf-8-sig") as f:
            todos = json.load(f)
    except (OSError, ValueError):
        return 0
    os.makedirs(CARPETA, exist_ok=True)
    hechos = 0
    for clave, datos in todos.items():
        if not os.path.isfile(_archivo(clave)):
            guardar_uno(clave, datos)
            hechos += 1
    return hechos


def cargar(recargar=False):
    """Todos los circuitos, como {clave: datos}."""
    global _cache
    if _cache is not None and not recargar:
        return _cache
    if not os.path.isdir(CARPETA):
        migrar()
    salida = {}
    try:
        for nombre in sorted(os.listdir(CARPETA)):
            if not nombre.lower().endswith(".json"):
                continue
            try:
                with open(os.path.join(CARPETA, nombre), encoding="utf-8-sig") as f:
                    datos = json.load(f)
            except (OSError, ValueError):
                continue
            if isinstance(datos, dict) and datos.get("puntos"):
                salida[os.path.splitext(nombre)[0]] = datos
    except OSError:
        pass
    _cache = salida
    return salida


def guardar_uno(clave, datos):
    global _cache
    try:
        os.makedirs(CARPETA, exist_ok=True)
        with open(_archivo(clave), "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, separators=(",", ":"))
        if _cache is not None:
            _cache[clave] = datos
        return True
    except OSError:
        return False


def guardar_todos(circuitos):
    """Guarda solo lo que haya cambiado, cada uno en su archivo."""
    for clave, datos in circuitos.items():
        guardar_uno(clave, datos)
    return True


def borrar(clave):
    global _cache
    try:
        os.remove(_archivo(clave))
        if _cache is not None:
            _cache.pop(clave, None)
        return True
    except OSError:
        return False
