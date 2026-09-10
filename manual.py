# -*- coding: utf-8 -*-
"""
El manual: leerlo, buscarlo y encontrar la ficha de un ajuste.

EL PROBLEMA QUE RESUELVE
El programa ya sabe DECIR que hay que tocar cuando el coche hace algo raro
(el ingeniero de sintomas, reglas.json), pero no explica POR QUE ni que se
estropea al hacerlo. Quien empieza necesita eso mas que la receta.

Asi que el manual va aparte y en un archivo suelto, igual que los circuitos,
los idiomas y la tabla del ingeniero: manual_reglajes.json al lado del
programa. Cualquiera que sepa de reglajes puede corregirlo o ampliarlo sin
tocar codigo y sin recompilar, y pasarselo a otro por WhatsApp.

COMO ESTA ORGANIZADO POR DENTRO
El archivo son capitulos, y cada capitulo lleva una de estas tres cosas:

  temas   : texto normal, un titulo y sus parrafos.
  grupos  : fichas de ajustes (que es, si subes, si bajas, con que se toca).
  recetas : problemas del coche, con los pasos para arreglarlos por orden.

Aqui dentro los tres se aplanan a una misma lista de NODOS, para que la
ventana no tenga que saber de que tipo es cada cosa: pide el indice, pide un
nodo y lo pinta.

HAY DOS TOMOS. El de reglajes y el de conduccion. Si el archivo de uno de
ellos no esta, ese tomo simplemente no sale, y el programa funciona igual.
"""
import io
import json
import os

import idiomas
import rutas

# (id del tomo, archivo). El orden es el que sale en la ventana.
TOMOS = [
    ("reglajes", "manual_reglajes.json"),
    ("conduccion", "manual_conduccion.json"),
]

_cache = {}


def _codigo():
    """El idioma que hay puesto ahora mismo."""
    try:
        return idiomas.actual()
    except Exception:
        return "es"


def texto(cosa):
    """
    Saca la frase en el idioma del programa.

    Los textos del manual son grupos {"es": ...} con un idioma por linea. Si
    falta el idioma que tengas puesto se cae al ingles, y si tampoco esta, al
    espanol, que es el original y nunca falta. Vale tanto para una frase
    suelta como para una lista de parrafos.
    """
    if cosa is None:
        return ""
    if isinstance(cosa, (str, bytes)):
        return cosa
    if isinstance(cosa, list):
        return cosa
    for c in (_codigo(), "en", "es"):
        if c in cosa:
            return cosa[c]
    return ""


def parrafos(cosa):
    """Lo mismo, pero devolviendo siempre una lista de parrafos."""
    t = texto(cosa)
    if isinstance(t, list):
        return t
    return [t] if t else []


def cargar(tomo):
    """El archivo de un tomo, o None si no esta puesto."""
    if tomo in _cache:
        return _cache[tomo]
    archivo = dict(TOMOS).get(tomo)
    d = None
    if archivo:
        ruta = rutas.datos(archivo)
        if os.path.isfile(ruta):
            try:
                with io.open(ruta, encoding="utf-8-sig") as f:
                    d = json.load(f)
            except (OSError, ValueError):
                d = None
    _cache[tomo] = d
    return d


def hay(tomo):
    return cargar(tomo) is not None


def tomos():
    """Los tomos que estan puestos, en orden."""
    return [t for t, _ in TOMOS if hay(t)]


def _nodo(tomo, capitulo, grupo, cosa):
    """
    Aplana una entrada del archivo a algo que la ventana pueda pintar igual
    venga de donde venga.
    """
    if "claves" in cosa:
        tipo = "ficha"
    elif "pasos" in cosa:
        tipo = "receta"
    else:
        tipo = "tema"
    return {
        "tomo": tomo,
        "capitulo": capitulo["id"],
        "grupo": grupo["id"] if grupo else None,
        "id": cosa.get("id") or (cosa.get("claves") or [""])[0],
        "tipo": tipo,
        "titulo": texto(cosa.get("titulo") or cosa.get("nombre")),
        "dato": cosa,
    }


def indice(tomo):
    """
    El arbol entero: [(capitulo, [(grupo o None, [nodos])])].

    Los capitulos que no tienen grupos devuelven un solo grupo a None, para
    que la ventana pueda recorrerlo todo igual sin preguntar.
    """
    d = cargar(tomo)
    if not d:
        return []
    salida = []
    for cap in d.get("capitulos", []):
        ramas = []
        sueltos = list(cap.get("temas", [])) + list(cap.get("recetas", []))
        if sueltos:
            ramas.append((None, [_nodo(tomo, cap, None, c) for c in sueltos]))
        for g in cap.get("grupos", []):
            # "ajustes" en los capitulos de fichas, "temas" en los de texto
            # (por coche, por ejemplo). Es lo mismo para quien lo pinta.
            dentro = g.get("ajustes") or g.get("temas") or []
            ramas.append((g, [_nodo(tomo, cap, g, c) for c in dentro]))
        salida.append((cap, ramas))
    return salida


def todos(tomo):
    """Todos los nodos del tomo, en el orden en el que estan escritos."""
    lista = []
    for _, ramas in indice(tomo):
        for _, nodos in ramas:
            lista.extend(nodos)
    return lista


_por_clave = None


def _mapa_claves():
    """
    Clave del .svm -> ficha. Se monta una sola vez.

    Se hace asi porque el editor de reglajes pregunta por cada una de las
    cien lineas de la pantalla cada vez que se pinta: recorrer el manual
    entero cien veces por pintada se notaria.
    """
    global _por_clave
    if _por_clave is None:
        _por_clave = {}
        for tomo in tomos():
            for n in todos(tomo):
                if n["tipo"] != "ficha":
                    continue
                for c in n["dato"]["claves"]:
                    _por_clave.setdefault(c, n)
    return _por_clave


def por_clave(clave):
    """
    La ficha que habla de un ajuste del .svm, para poder llegar al manual
    desde el editor de reglajes.

    Busca la clave tal cual ('EJE_del/SpringSetting') y tambien las de rueda
    suelta ('FRONTLEFT/SpringSetting'), porque el editor unas veces habla por
    eje y otras por rueda.
    """
    if not clave:
        return None
    mapa = _mapa_claves()
    if clave in mapa:
        return mapa[clave]
    trozos = clave.split("/", 1)
    if len(trozos) == 2:
        seccion, resto = trozos
        if seccion in ("FRONTLEFT", "FRONTRIGHT"):
            return mapa.get("EJE_del/" + resto)
        if seccion in ("REARLEFT", "REARRIGHT"):
            return mapa.get("EJE_tras/" + resto)
    return None


def _texto_entero(nodo):
    """Todo lo que se lee de un nodo, junto, para poder buscar dentro."""
    d = nodo["dato"]
    trozos = [nodo["titulo"], texto(d.get("pagina"))]
    for campo in ("que_es", "subir", "bajar", "donde", "ojo", "sintoma"):
        trozos.append(texto(d.get(campo)))
    trozos.extend(parrafos(d.get("texto")))
    trozos.extend(parrafos(d.get("pasos")))
    for c in d.get("combina", []):
        trozos.append(texto(c))
    trozos.extend(d.get("claves", []))
    return " ".join(x for x in trozos if isinstance(x, str)).lower()


def _sin_tildes(s):
    """Para que 'aerodinamica' encuentre 'aerodinámica' y al reves."""
    pares = ((u"á", "a"), (u"é", "e"), (u"í", "i"), (u"ó", "o"),
             (u"ú", "u"), (u"ü", "u"), (u"ñ", "n"))
    for de, a in pares:
        s = s.replace(de, a)
    return s


def buscar(tomo, texto_buscado):
    """
    Los nodos que contienen TODAS las palabras que se escriban.

    Se buscan palabras sueltas y no la frase entera a proposito: quien busca
    'barra trasera' quiere las dos palabras, esten juntas o no.
    """
    palabras = [_sin_tildes(p) for p in texto_buscado.lower().split() if p]
    if not palabras:
        return None            # None es "no hay busqueda", distinto de []
    salida = []
    for n in todos(tomo):
        entero = _sin_tildes(_texto_entero(n))
        if all(p in entero for p in palabras):
            salida.append(n)
    return salida
