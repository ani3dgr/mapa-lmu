# -*- coding: utf-8 -*-
"""
Donde estan los archivos del programa.

Parece una tonteria tener un archivo para esto, pero al compilar el programa
deja de serlo. Sin compilar, "la carpeta del programa" es donde esta este
archivo .py. Compilado, los .py van metidos DENTRO del ejecutable, y ese truco
apuntaria a un sitio temporal que Windows borra al cerrar: los circuitos que
escaneases y tus vueltas se perderian solas.

Asi que compilado se mira donde esta el .exe, que es la carpeta que el usuario
ve y donde tienen que vivir circuitos/, idiomas/, sesiones/ y coches.json para
que se puedan tocar, compartir y actualizar sin recompilar nada.
"""
import os
import sys


def carpeta():
    """La carpeta del programa, este compilado o no."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def datos(*partes):
    """Una ruta dentro de la carpeta del programa."""
    return os.path.join(carpeta(), *partes)


def compilado():
    return bool(getattr(sys, "frozen", False))
