# -*- coding: utf-8 -*-
"""
Que circuitos y variantes tiene instalados el juego, y cuales estan escaneados.

El juego guarda cada circuito en Installed/Locations, y dentro de la version mas
nueva hay un archivo layout*.mas por variante. De ahi sale la lista completa:
Silverstone tiene cuatro (WEC, ELMS, International y National), Spa tres, Paul
Ricard cinco... Asi que si sale un circuito nuevo en una actualizacion aparece
solo en la lista, sin tocar nada.

De cada trazado se mira que partes estan escaneadas:
    pista    - los dos bordes, que es lo que da la anchura real
    trazada  - el recorrido de referencia (lo que dibuja el mapa)
    boxes    - la calle de boxes
"""
import os
import re

import juego
import lector_lmu as lmu

# La ruta ya no va escrita a mano: el juego puede estar en Steam, en Epic o en
# otro disco, y con una ruta fija esto solo funcionaria en un ordenador.
LOCALIZACIONES = juego.subcarpeta("Installed", "Locations")

# Palabras por las que se reconoce cada circuito en el nombre que da el juego.
# Hacen falta porque la carpeta y el nombre en pista no coinciden: la carpeta
# es "LeMans_2023" y el juego lo llama "Circuit de la Sarthe".
PALABRAS = {
    "BahrainWEC": ["bahrain"],
    "Barcelona": ["barcelona", "catalunya"],
    "CotAWEC": ["americas", "cota"],
    "Daytona": ["daytona"],
    "FujiWEC": ["fuji"],
    "ImolaWEC": ["imola", "enzoedinoferrari"],
    "Interlagos": ["interlagos", "carlospace"],
    "LagunaSeca": ["lagunaseca"],
    "LeMans": ["lemans", "sarthe"],
    "Monza": ["monza"],
    "PaulRicard": ["paulricard", "castellet"],
    "PortimaoWEC": ["portimao", "algarve"],
    "Qatar": ["qatar", "losail", "lusail"],
    "Sebring": ["sebring"],
    "Silverstone": ["silverstone"],
    "Spa": ["spa", "francorchamps"],
}


def _palabras_de(carpeta):
    base = re.sub(r"_\d{4}$", "", carpeta)
    return PALABRAS.get(base, [lmu.normaliza(base)])


def layouts_instalados():
    """[{carpeta, circuito, layout, palabras}] de todo lo que hay instalado."""
    salida = []
    if not os.path.isdir(LOCALIZACIONES):
        return salida
    for carpeta in sorted(os.listdir(LOCALIZACIONES)):
        ruta = os.path.join(LOCALIZACIONES, carpeta)
        if not os.path.isdir(ruta) or "Showroom" in carpeta:
            continue
        versiones = sorted(v for v in os.listdir(ruta)
                           if os.path.isdir(os.path.join(ruta, v)))
        layouts = []
        for v in reversed(versiones):        # la version mas nueva manda
            hallados = [re.sub(r"^layout|\.mas$", "", f, flags=re.I)
                        for f in os.listdir(os.path.join(ruta, v))
                        if f.lower().startswith("layout") and f.lower().endswith(".mas")]
            if hallados:
                layouts = sorted(hallados)
                break
        circuito = re.sub(r"_\d{4}$", "", carpeta)
        for layout in layouts or ["(unico)"]:
            salida.append({"carpeta": carpeta, "circuito": circuito,
                           "layout": layout, "palabras": _palabras_de(carpeta)})
    return salida


def variante_principal(carpeta, layouts):
    """
    La variante por defecto del circuito.

    Hace falta porque el juego solo pone la variante en el nombre a veces: dice
    "Silverstone Grand Prix Circuit - WEC", pero a Imola la llama "Autodromo
    Enzo e Dino Ferrari" a secas. Cuando el nombre no la dice, lo escaneado es
    la principal, y esa se reconoce porque su nombre esta dentro del de la
    carpeta (ImolaWEC -> Imola, CotAWEC -> Cota, Qatar -> Qatar).
    """
    base = lmu.normaliza(re.sub(r"_\d{4}$", "", carpeta))
    dentro = [l for l in layouts if base.startswith(lmu.normaliza(l))]
    if dentro:
        return max(dentro, key=len)
    return sorted(layouts)[0] if layouts else None


def _encaja(clave_escaneo, entrada, layouts_del_circuito):
    """Si un escaneo guardado corresponde a este trazado."""
    if not any(p in clave_escaneo for p in entrada["palabras"]):
        return False
    if len(layouts_del_circuito) <= 1:
        return True                          # circuito de una sola variante

    # con varias variantes, la buena es la que aparece en el nombre; se prefiere
    # la coincidencia mas larga para que "Spa" no se lleve lo de "SpaELMS"
    candidatas = [l for l in layouts_del_circuito
                  if lmu.normaliza(l) in clave_escaneo]
    if candidatas:
        return entrada["layout"] == max(candidatas, key=len)
    # el nombre no dice la variante: se da por hecho que es la principal
    return entrada["layout"] == variante_principal(entrada["carpeta"],
                                                   layouts_del_circuito)


def inventario():
    """
    Lista completa para la pantalla: cada trazado instalado con lo que tiene
    escaneado y lo que le falta.
    """
    try:
        circuitos = lmu.cargar_circuitos()
    except (OSError, ValueError):
        circuitos = {}

    entradas = layouts_instalados()
    por_circuito = {}
    for e in entradas:
        por_circuito.setdefault(e["circuito"], []).append(e["layout"])

    salida = []
    usados = set()
    for e in entradas:
        layouts = por_circuito[e["circuito"]]
        encontrado = None
        for clave, datos in circuitos.items():
            if clave in usados:
                continue
            if _encaja(clave, e, layouts):
                encontrado = (clave, datos)
                break
        if encontrado:
            usados.add(encontrado[0])
        clave, datos = encontrado if encontrado else (None, None)
        salida.append({
            "circuito": e["circuito"],
            "layout": e["layout"],
            "clave": clave,
            "nombre": datos["nombre"] if datos else "",
            "trazada": bool(datos and datos.get("puntos")),
            "pista": bool(datos and datos.get("bordes")),
            "boxes": bool(datos and datos.get("boxes")),
            "curvas": len(datos.get("curvas", [])) if datos else 0,
        })

    # escaneos que no encajan con ningun trazado instalado (circuito retirado
    # del juego, o escaneado con un nombre raro): no se pierden de vista
    for clave, datos in circuitos.items():
        if clave in usados:
            continue
        salida.append({
            "circuito": datos.get("nombre", clave), "layout": "?",
            "clave": clave, "nombre": datos.get("nombre", ""),
            "trazada": bool(datos.get("puntos")),
            "pista": bool(datos.get("bordes")),
            "boxes": bool(datos.get("boxes")),
            "curvas": len(datos.get("curvas", [])),
        })
    return salida


def borrar_escaneo(clave):
    """Quita del archivo todo lo guardado de ese trazado."""
    circuitos = lmu.cargar_circuitos()
    if clave not in circuitos:
        return False
    import circuitos as almacen
    almacen.borrar(clave)
    return True
