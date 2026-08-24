# -*- coding: utf-8 -*-
"""
Encuentra donde esta instalado Le Mans Ultimate.

El juego se puede comprar en Steam o en la Epic Games Store, y cada tienda lo
pone en un sitio distinto. Ademas en Steam se pueden tener varias bibliotecas
(otro disco duro, por ejemplo). Con la ruta escrita a mano el programa solo
funcionaria en el ordenador donde se escribio.

Se busca en este orden:
  1. Lo que haya guardado en la configuracion (si alguien lo puso a mano)
  2. Las bibliotecas de Steam, leidas del propio Steam
  3. Lo que tenga apuntado la Epic Games Store
  4. El registro de programas instalados de Windows
  5. Sitios habituales, por si todo lo anterior falla

Lo encontrado se guarda para no repetir la busqueda en cada arranque.
"""
import json
import os
import re

import rutas

CARPETA = rutas.carpeta()
MEMORIA = os.path.join(CARPETA, "ruta_juego.txt")
NOMBRE = "Le Mans Ultimate"
SENAL = os.path.join("Installed", "Locations")   # lo que confirma que es el juego

_ruta = None


def _vale(carpeta):
    return bool(carpeta) and os.path.isdir(os.path.join(carpeta, SENAL))


def _de_steam():
    """Todas las bibliotecas de Steam, no solo la de la unidad C."""
    rutas = []
    bases = []
    try:
        import winreg
        for vista in (winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY):
            try:
                k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam",
                                   0, winreg.KEY_READ | vista)
                bases.append(winreg.QueryValueEx(k, "InstallPath")[0])
            except OSError:
                pass
    except ImportError:
        pass
    bases += [r"C:\Program Files (x86)\Steam", r"C:\Program Files\Steam"]

    for base in bases:
        vdf = os.path.join(base, "steamapps", "libraryfolders.vdf")
        biblioteca = [base]
        try:
            with open(vdf, encoding="utf-8", errors="replace") as f:
                # el archivo es de Valve, no JSON: se sacan las rutas a pelo
                biblioteca += re.findall(r'"path"\s*"([^"]+)"', f.read())
        except OSError:
            pass
        for b in biblioteca:
            rutas.append(os.path.join(b.replace("\\\\", "\\"),
                                      "steamapps", "common", NOMBRE))
    return rutas


def _de_epic():
    """La Epic guarda un indice de lo instalado en ProgramData."""
    rutas = []
    indice = os.path.join(os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
                          "Epic", "UnrealEngineLauncher", "LauncherInstalled.dat")
    try:
        with open(indice, encoding="utf-8", errors="replace") as f:
            for item in json.load(f).get("InstallationList", []):
                sitio = item.get("InstallLocation", "")
                if NOMBRE.lower().replace(" ", "") in (
                        item.get("AppName", "") + sitio).lower().replace(" ", ""):
                    rutas.append(sitio)
    except (OSError, ValueError):
        pass
    return rutas


def _del_registro():
    """Programas instalados, por si el juego llego por otra via."""
    rutas = []
    try:
        import winreg
        for raiz, rama in ((winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                           (winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                           (winreg.HKEY_CURRENT_USER,
                            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")):
            try:
                k = winreg.OpenKey(raiz, rama)
            except OSError:
                continue
            for i in range(winreg.QueryInfoKey(k)[0]):
                try:
                    sub = winreg.OpenKey(k, winreg.EnumKey(k, i))
                    nombre = winreg.QueryValueEx(sub, "DisplayName")[0]
                    if NOMBRE.lower() in nombre.lower():
                        rutas.append(winreg.QueryValueEx(sub, "InstallLocation")[0])
                except OSError:
                    continue
    except ImportError:
        pass
    return rutas


def _habituales():
    sitios = []
    for letra in "CDEFGH":
        for medio in (r"\Program Files (x86)\Steam\steamapps\common",
                      r"\Program Files\Epic Games",
                      r"\Games", r"\SteamLibrary\steamapps\common"):
            sitios.append("%s:%s\\%s" % (letra, medio, NOMBRE))
    return sitios


def carpeta():
    """Donde esta el juego, o cadena vacia si no se encuentra."""
    global _ruta
    if _ruta is not None:
        return _ruta

    candidatas = []
    try:
        with open(MEMORIA, encoding="utf-8") as f:
            candidatas.append(f.read().strip())
    except OSError:
        pass
    candidatas += _de_steam() + _de_epic() + _del_registro() + _habituales()

    for c in candidatas:
        if _vale(c):
            _ruta = c
            recordar(c)
            return _ruta
    _ruta = ""
    return _ruta


def recordar(ruta):
    """Guarda la ruta para no volver a buscarla, o para ponerla a mano."""
    global _ruta
    try:
        with open(MEMORIA, "w", encoding="utf-8") as f:
            f.write(ruta)
        _ruta = ruta if _vale(ruta) else None
        return True
    except OSError:
        return False


def subcarpeta(*partes):
    """Ruta dentro del juego, o cadena vacia si el juego no aparece."""
    base = carpeta()
    return os.path.join(base, *partes) if base else ""
