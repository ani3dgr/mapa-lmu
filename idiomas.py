# -*- coding: utf-8 -*-
"""
El idioma del programa.

Funciona igual que la carpeta de circuitos: cada idioma es UN archivo dentro
de la carpeta "idiomas". Para anadir un idioma nuevo se copia en.json, se
traduce y se deja ahi con el nombre del idioma; el programa lo ve solo. Y si
alguien traduce mejor una frase, cambia esa linea y ya esta, sin tocar codigo.

El espanol va escrito aqui dentro (BASE) porque es el idioma original: asi el
programa nunca se queda mudo aunque falte la carpeta entera.

Si a un idioma le falta una frase, se cae al ingles, y si tampoco esta, al
espanol. Nunca sale un hueco en blanco.

QUE ESTA TRADUCIDO: todo lo que se lee en pantalla. Las pestanas, los
botones, las ayudas largas de la (i), los rotulos que salen encima del mapa y
las indicaciones de las ventanas negras de escaneo. Son unos 450 textos por
idioma.

Lo unico que sigue en castellano son las herramientas de trabajo que no se
abren desde el programa (monitor_amarilla.py, diagnostico.py y los
construir_*.py), que se lanzan a mano y no las ve un usuario normal.
"""
import json
import os

import rutas

CARPETA = rutas.datos("idiomas")
MEMORIA = rutas.datos("idioma.txt")

# Los idiomas en los que se juega a LMU: son los que trae el propio juego
# traducidos, asi que es donde esta la gente.
IDIOMAS = [
    ("es", "Español"),
    ("en", "English"),
    ("fr", "Français"),
    ("it", "Italiano"),
    ("de", "Deutsch"),
    ("pt", "Português"),
    ("pl", "Polski"),
]

# ------------------------------------------------------------------ textos
# Clave -> texto en espanol. Es la lista de todo lo que se puede traducir.
BASE = {
    # pestanas
    "tab.ver": "Que se ve",
    "tab.aspecto": "Tamanos y colores",
    "tab.tiempos": "Comparar tiempos",
    "tab.trazadas": "Comparar trazadas",
    "tab.escaneo": "Escanear pistas",
    "tab.coches": "Coches",
    "tab.reglajes": "Reglajes",
    "tab.acerca": "Acerca de",
    # pie de la ventana
    "pie.teclas": "F9 oculta o muestra el mapa   /   F10 cierra estas opciones\n"
                  "Con esta ventana abierta puedes arrastrar el mapa con el raton.",
    # acerca de
    "acerca.titulo": "Mapa de pista para Le Mans Ultimate",
    "acerca.descripcion": "Programa gratuito para la comunidad.\n"
                          "Se puede copiar, pasar a quien quieras y usar sin pagar nada.",
    "acerca.idioma": "Idioma",
    "acerca.reiniciar": "El idioma cambia del todo al volver a abrir el programa.",
    "acerca.donar.titulo": "Invitame a un cafe",
    "acerca.donar.texto": "Esto lo hago en mis ratos libres y seguira siendo gratis.\n"
                          "Si te ha servido y te apetece echar una mano, se agradece;\n"
                          "y si no, disfrutalo igual.",
    "acerca.donar.kofi": "Donar por Ko-fi",
    "acerca.donar.paypal": "Donar por PayPal",
    "acerca.proyecto": "Pagina del programa",
    "acerca.patrocinio": "Patrocinado por ciclotracker.com",
    "acerca.patrocinio.texto": "Si ademas de simracing le das al pedal de verdad,\n"
                               "ciclotracker.com lleva la cuenta de tus rutas.",
    "acerca.patrocinio.web": "Ir a ciclotracker.com",
    "acerca.patrocinio.android": "Bajarla para Android",
    "acerca.cerrar": "CERRAR EL MAPA",
    # reglajes
    "reg.aviso": "Vista previa. Todavia no funciona: se ensena para que veas por donde va.",
    "reg.sello": "PRÓXIMAMENTE",
    "reg.sub.caracteristicas": "  Caracteristicas  ",
    "reg.sub.reglaje": "  Reglaje  ",
    "reg.ejemplo": "valores de ejemplo",
    "reg.comportamiento": "COMO SE COMPORTA",
    "reg.motor": "Motor",
    "reg.cilindrada": "Cilindrada",
    "reg.potencia": "Potencia",
    "reg.posicion": "Posicion del motor",
    "reg.traccion": "Traccion",
}

_actual = None
_textos = {}


def _leer(codigo):
    try:
        with open(os.path.join(CARPETA, "%s.json" % codigo), encoding="utf-8-sig") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def actual():
    """El idioma elegido. Por defecto, espanol."""
    global _actual
    if _actual is None:
        try:
            with open(MEMORIA, encoding="utf-8-sig") as f:
                codigo = f.read().strip().lower()
        except OSError:
            codigo = ""
        _actual = codigo if codigo in dict(disponibles()) else "es"
        _cargar()
    return _actual


def _cargar():
    """
    Monta el idioma elegido por capas, de abajo arriba.

    Abajo del todo el espanol, que es el original y esta completo; encima el
    ingles, que tambien lo esta; y encima el idioma elegido. Asi, a una
    traduccion a medias le salen las frases que le faltan en ingles, y si el
    ingles tampoco las tiene, en espanol. Nunca queda un hueco en blanco.
    """
    global _textos
    _textos = dict(_leer("es"))
    if _actual != "es":
        _textos.update(_leer("en"))
        if _actual != "en":
            _textos.update(_leer(_actual))


def elegir(codigo):
    """Guarda el idioma. Lo que ya esta dibujado no cambia hasta reabrir."""
    global _actual
    if codigo not in dict(disponibles()):
        return False
    try:
        with open(MEMORIA, "w", encoding="utf-8") as f:
            f.write(codigo)
    except OSError:
        return False
    _actual = codigo
    _cargar()
    return True


def nombre(codigo):
    return dict(IDIOMAS).get(codigo, codigo)


def disponibles():
    """
    [(codigo, nombre), ...] con los idiomas que hay.

    A los que trae el programa se les suma cualquier archivo suelto que
    alguien haya dejado en la carpeta: asi un idioma nuevo aparece en la lista
    sin tocar nada, igual que pasa con los circuitos.
    """
    lista = list(IDIOMAS)
    conocidos = dict(IDIOMAS)
    try:
        for archivo in sorted(os.listdir(CARPETA)):
            codigo = os.path.splitext(archivo)[0].lower()
            if archivo.lower().endswith(".json") and codigo not in conocidos:
                lista.append((codigo, codigo.upper()))
                conocidos[codigo] = codigo.upper()
    except OSError:
        pass
    return lista


def t(clave):
    """El texto en el idioma elegido, con el ingles y el espanol por debajo."""
    actual()
    texto = _textos.get(clave)
    if texto:
        return texto
    return BASE.get(clave, clave)


def textos_es():
    """
    Todo el espanol: lo que hay en los archivos mas lo que trae el codigo.

    Es la lista completa de lo traducible, y de aqui salen las plantillas.
    """
    completo = dict(BASE)
    completo.update(_leer("es"))
    return completo


def guardar(codigo, textos):
    """Escribe un archivo de idioma. Solo lo usan las herramientas."""
    os.makedirs(CARPETA, exist_ok=True)
    with open(os.path.join(CARPETA, "%s.json" % codigo), "w", encoding="utf-8") as f:
        json.dump(textos, f, ensure_ascii=False, indent=2, sort_keys=True)
    return len(textos)


def que_falta(codigo):
    """Las frases que ese idioma todavia no tiene traducidas."""
    return sorted(set(textos_es()) - set(_leer(codigo)))
