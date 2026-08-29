# -*- coding: utf-8 -*-
"""
Las fichas de los coches, abiertas para que las pueda ampliar cualquiera.

EL PROBLEMA QUE RESUELVE
Lo que es cada coche (motor, cilindrada, potencia, donde va el motor, que
ruedas mueve) no lo publica el juego por ningun lado: esta escrito a mano.
El programa trae escritos los treinta y cinco coches que habia cuando se
hizo, pero el juego va sacando coches nuevos. Si las fichas solo pudieran
tocarlas los que hicimos el programa, el dia que dejemos de mantenerlo los
coches nuevos se quedarian en blanco para siempre.

Asi que funciona como los circuitos y los idiomas: hay un archivo suelto,
fichas_coches.json, al lado del programa. Lo que este ahi manda sobre lo
que trae el programa dentro. Cualquiera puede rellenar un coche desde la
propia pestana, y ese archivo se puede pasar por WhatsApp igual que un
circuito escaneado: el que lo reciba lo copia en su carpeta y ya tiene las
fichas que hizo otro.

Nadie depende de nosotros para nada.
"""
import json
import os
import re

import reglajes
import rutas

RUTA = rutas.datos("fichas_coches.json")

CAMPOS = ["motor", "cilindrada", "potencia", "posicion", "traccion", "resumen"]

# Valores de los que se eligen de una lista, para que no acabe cada uno
# escribiendo lo mismo de siete maneras distintas.
POSICIONES = ["Delantero", "Central", "Trasero", "Central-trasero"]
TRACCIONES = ["Trasera", "Total", "Delantera"]

_mias = None


def _leer():
    global _mias
    if _mias is None:
        try:
            with open(RUTA, encoding="utf-8-sig") as f:
                d = json.load(f)
            _mias = d.get("fichas", d) if isinstance(d, dict) else {}
        except (OSError, ValueError):
            _mias = {}
    return _mias


def _escribir():
    try:
        with open(RUTA, "w", encoding="utf-8") as f:
            json.dump({"_ayuda": "Fichas de coches anadidas o corregidas. "
                                 "Manda sobre las que trae el programa. Se "
                                 "puede pasar a quien quieras: copiando este "
                                 "archivo en su carpeta, tendra las mismas.",
                       "fichas": _mias}, f, ensure_ascii=False, indent=1)
        return True
    except OSError:
        return False


def clave(modelo):
    """El mismo apano que usa reglajes.py, para que casen las dos listas."""
    return reglajes.clave(modelo)


# Las coletillas de clase que el juego pega al final del nombre y la tabla
# del programa no siempre lleva.
_COLAS = ("lmgt3", "lmdh", "lmh", "lmp2", "lmp3", "gte", "gt3", "lm")


def _norm(k):
    """Solo letras y numeros. Fuera guiones, puntos y espacios."""
    return re.sub(r"[^a-z0-9]", "", (k or "").lower())


def _pelada(k):
    """'astonmartinvantageamrlmgt3' -> 'astonmartinvantageamr'."""
    k = _norm(k)
    for cola in _COLAS:
        if k.endswith(cola) and len(k) > len(cola) + 3:
            return k[: -len(cola)]
    return k


def _candidatas():
    """
    Cada ficha con todas las maneras de escribirla que conocemos.

    Se mira tanto la clave con la que esta guardada ("911gt3r") como su
    nombre bonito ("Porsche 911 GT3 R (992)"), porque el juego usa uno u
    otro segun el coche y la mitad de las veces no coinciden.
    """
    salida = {}
    for c in set(reglajes.FICHAS) | set(_leer()):
        formas = {_pelada(c), _norm(c)}
        bonito = reglajes.NOMBRES.get(c)
        if bonito:
            formas |= {_pelada(bonito), _norm(bonito)}
        salida[c] = {f for f in formas if f}
    return salida


def casar(modelo):
    """
    Encuentra la ficha de un coche aunque el nombre no cuadre letra a letra.

    Hace falta porque el juego llama a los coches de una manera y la tabla
    del programa de otra: el juego dice "Lexus RCF LMGT3" y la tabla pone
    "lexusrcfgt3"; el juego dice "Toyota GR010" y la tabla "toyotagr10";
    el juego dice "Vanwall 680" y la tabla "vandervell680". Comparando
    letra a letra, veintitres coches de treinta y cuatro se quedaban sin
    ficha teniendola escrita.

    Se prueba en cuatro pasadas, de la mas segura a la mas atrevida: tal
    cual, quitando la coletilla de la clase, dejando que uno empiece por el
    otro, y por ultimo por parecido. Lo del parecido tiene un liston alto
    (75%) para que no acabe emparejando un Ferrari con otro Ferrari
    distinto: es mejor quedarse sin ficha, que se rellena en un minuto, que
    ensenar la del coche equivocado.
    """
    k = _norm(clave(modelo))
    cand = _candidatas()
    for c, formas in cand.items():
        if k in formas:
            return c

    base = _pelada(modelo)
    for c, formas in cand.items():
        if base in formas:
            return c

    cerca = [c for c, formas in cand.items()
             if any(f.startswith(base) or base.startswith(f) for f in formas)]
    if cerca:
        return min(cerca, key=lambda c: abs(len(_norm(c)) - len(base)))

    import difflib
    mejor, punto = None, 0.75
    for c, formas in cand.items():
        for f in formas:
            r = difflib.SequenceMatcher(None, base, f).ratio()
            if r > punto:
                mejor, punto = c, r
    return mejor


def de(modelo):
    """
    La ficha de un coche, o None si nadie la ha escrito todavia.

    Primero se mira el archivo suelto: si alguien ha corregido un dato,
    manda su version sobre la que venia dentro del programa.
    """
    k = casar(modelo)
    if not k:
        return None
    mia = _leer().get(k)
    if mia:
        junta = dict(reglajes.FICHAS.get(k) or {})
        junta.update({c: v for c, v in mia.items() if v})
        return junta
    return reglajes.FICHAS.get(k)


def traducida(modelo):
    """La ficha en el idioma que este puesto, si viene con el programa."""
    k = casar(modelo)
    if not k or k in _leer():
        return None            # las escritas a mano van en su idioma
    return reglajes.ficha_traducida(k)


def es_mia(modelo):
    """Si la ficha esta en el archivo suelto y no dentro del programa."""
    return (casar(modelo) or clave(modelo)) in _leer()


def guardar(modelo, datos):
    """Escribe o corrige la ficha de un coche."""
    _leer()
    # Se guarda con la clave que ya usa la tabla del programa si el coche
    # esta en ella, para que corregir un dato no cree una ficha suelta que
    # convive con la de dentro y luego nadie sepa cual manda.
    _mias[casar(modelo) or clave(modelo)] = {
        c: (datos.get(c) or "").strip() for c in CAMPOS}
    return _escribir()


def borrar(modelo):
    """Quita lo anadido a mano. Vuelve a mandar la ficha del programa."""
    _leer()
    if _mias.pop(casar(modelo) or clave(modelo), None) is not None:
        return _escribir()
    return True


def categoria_de(modelo):
    """
    A que clase corre un coche.

    Los que trae el programa estan en su tabla. Para uno nuevo se mira lo
    que diga su nombre, que suele bastar: los coches llevan la clase en el
    nombre (LMGT3, LMP2, GT3). Y si no se saca nada, GT3, que es la clase
    con mas coches.
    """
    k = clave(modelo)
    if k in reglajes.CLASE_DE:
        return reglajes.CLASE_DE[k]
    arriba = (modelo or "").upper()
    for pista, nombre in (("HYPERCAR", "Hypercar"), ("LMDH", "Hypercar"),
                          ("LMH", "Hypercar"), ("LMP2", "LMP2"),
                          ("LMP3", "LMP3"), ("GTE", "GTE"),
                          ("LMGT3", "GT3"), ("GT3", "GT3"),
                          ("CUP", "Copa"), ("CHALLENGE", "Copa")):
        if pista in arriba:
            return nombre
    return "GT3"


def por_categoria():
    """
    {'GT3': ['Lexus RCF LMGT3', ...], ...}

    Salen TODOS los coches que tenga instalados el juego, tengan ficha
    escrita o no. Antes solo salian los que venian en la tabla del
    programa, asi que un coche nuevo no aparecia en ninguna parte y no
    habia manera de rellenarle la ficha. Ahora aparece, vacio, con el boton
    para escribirla.
    """
    import coches
    modelos = coches.modelos_instalados()
    if not modelos:
        modelos = sorted(set(list(reglajes.FICHAS) + list(_leer())))

    salida = {c: [] for c in reglajes.CATEGORIAS}
    vistos = set()
    for m in modelos:
        k = clave(m)
        if k in vistos:
            continue
        vistos.add(k)
        salida.setdefault(categoria_de(m), []).append(m)
    for lista in salida.values():
        lista.sort(key=reglajes.bonito)
    return salida


def sin_rellenar():
    """Los coches instalados que todavia no tienen ficha."""
    faltan = []
    for lista in por_categoria().values():
        for m in lista:
            if not de(m):
                faltan.append(m)
    return faltan
