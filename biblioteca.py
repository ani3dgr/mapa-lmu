# -*- coding: utf-8 -*-
"""
La biblioteca de reglajes: leer, entender y ordenar los .svm.

Aqui no hay ni una ventana. Solo esta la parte que sabe de reglajes, para
que se pueda probar sola y para que manana se pueda usar desde otro sitio
del programa sin arrastrar la interfaz detras.

QUE ES UN .SVM
Un reglaje de Le Mans Ultimate es un archivo de texto. Cada linea es un
ajuste y tiene esta forma:

    RWSetting=2//9.0 deg

El numero de la izquierda es el que guarda el juego (un indice, empieza en
0). Lo de detras de las dos barras es el valor de verdad, escrito para que
lo lea una persona. Esa segunda parte es oro: es la unica manera de saber
que "2" significa nueve grados de aleron en ESTE coche, porque la escala
cambia de un coche a otro.

Las tres primeras lineas del archivo dicen de que coche es. La carpeta
donde vive el archivo dice de que circuito es: eso NO esta escrito dentro.
"""
import os
import re
import time
import zipfile

import coches

# El juego escribe los comentarios en el idioma que tenga puesto quien
# guardo el reglaje, asi que hay archivos con "laps", con "Vueltas" y con
# "Runden". Por eso las vueltas se buscan por la forma "(numero palabra)" y
# no por la palabra, que seria perseguir siete idiomas para siempre.
_VUELTAS = re.compile(r"\(\s*([\d]+[.,]?[\d]*)\s*[A-Za-z]")
_NUMERO = re.compile(r"^\s*([\d]+[.,]?[\d]*)")

# Las webs de reglajes se reconocen por lo que firman en la nota interna.
# Si manana aparece una nueva, se anade una linea aqui y ya esta.
FIRMAS = [
    ("gosetups", "GO"),
    ("go setups", "GO"),
    ("hymo", "HYMO"),
    ("coach dave", "CDA"),
    ("cda", "CDA"),
]

# Cuanto puede faltar de gasolina antes de dar la alarma. Un 5% es el
# margen de un error de redondeo; por debajo de eso ya es que el reglaje
# esta mal cuadrado y el coche se va a parar en pista.
MARGEN = 0.05

# Al cuadrar el combustible se echa un pelin de mas. La vuelta de
# formacion y la de salida de boxes gastan gasolina y no cuentan como
# vuelta, asi que ir al milimetro es quedarse corto.
COLCHON = 1.03

# Palabras que son la clase del coche y no su nombre. Se usan para dos
# cosas: saber la categoria y quitarlas del nombre del archivo.
CLASES = ("HYPERCAR", "LMDH", "LMH", "LMP2", "LMP3", "GTE", "LMGT3", "GT3")


# ------------------------------------------------------------------- leer

def _numero(texto):
    """El primer numero de un texto, con coma o con punto. None si no hay."""
    if not texto:
        return None
    m = _NUMERO.match(texto)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None


def _vueltas(comentario):
    """Las vueltas de un comentario tipo '16.0L (4.5 laps)'."""
    m = _VUELTAS.search(comentario or "")
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None


def leer(ruta):
    """
    Abre un .svm y devuelve todo lo que se puede saber de el.

    Se lee en latin-1 a proposito. Algunos reglajes traen la firma del
    ingeniero con caracteres raros (aparece un byte suelto en medio del
    nombre) y en latin-1 ningun byte falla nunca. Como luego hay que
    reescribir el archivo casi igual, lo que importa es que lo que entra
    pueda volver a salir sin romperse.
    """
    try:
        with open(ruta, encoding="latin-1") as f:
            lineas = f.read().splitlines()
    except OSError:
        return None

    ficha = {
        "ruta": ruta,
        "nombre": os.path.splitext(os.path.basename(ruta))[0],
        "circuito": os.path.basename(os.path.dirname(ruta)),
        "clase": "", "nota": "", "veh": "", "codigo": "", "familia": "",
        # La clave lleva delante la seccion: "FRONTLEFT/CamberSetting". Hace
        # falta porque la caida se llama igual en las cuatro ruedas y en un
        # diccionario a secas se pisan unas a otras: quedaba la ultima y el
        # programa creia que el coche llevaba el mismo camber delante y
        # detras. Para lo que solo existe una vez (la gasolina, el aleron)
        # se puede seguir preguntando por el nombre a secas.
        "ajustes": {},        # "SECCION/Clave" -> {"seccion","indice","texto"}
        "lineas": lineas,
    }

    seccion = "GENERAL"
    for linea in lineas:
        pelada = linea.strip()
        if pelada.startswith("[") and pelada.endswith("]"):
            seccion = pelada[1:-1].strip().upper()
            continue

        if pelada.startswith("//VEH="):
            ficha["veh"] = pelada[6:].strip()
            trozos = ficha["veh"].replace("/", "\\").split("\\")
            if trozos:
                ficha["codigo"] = os.path.splitext(trozos[-1])[0]
            if len(trozos) >= 3:
                ficha["familia"] = trozos[-3]        # LexusRCF_GT3_2024
            continue
        if pelada.startswith("//") or pelada.startswith("[") or "=" not in pelada:
            continue

        clave, resto = pelada.split("=", 1)
        clave = clave.strip()
        if "//" in resto:
            crudo, texto_valor = resto.split("//", 1)
        else:
            crudo, texto_valor = resto, ""

        if clave == "VehicleClassSetting":
            ficha["clase"] = crudo.strip().strip('"')
            continue
        if clave == "Notes":
            ficha["nota"] = crudo.strip().strip('"')
            continue

        ficha["ajustes"]["%s/%s" % (seccion, clave)] = {
            "seccion": seccion, "clave": clave,
            "indice": _numero(crudo), "texto": texto_valor.strip()}
    return ficha


def buscar(ficha, clave):
    """
    Un ajuste, por su nombre completo ('REARWING/RWSetting') o a secas
    ('RWSetting'), que devuelve el primero que aparezca. Vale para todo lo
    que solo existe una vez; para las ruedas hay que decir cual.
    """
    a = ficha["ajustes"].get(clave)
    if a:
        return a
    if "/" not in clave:
        for llave, dato in ficha["ajustes"].items():
            if dato["clave"] == clave:
                return dato
    return None


def valor(ficha, clave):
    """El indice guardado de un ajuste, o None."""
    a = buscar(ficha, clave)
    return a["indice"] if a else None


def texto(ficha, clave):
    """El valor legible de un ajuste ('9.0 deg'), o cadena vacia."""
    a = buscar(ficha, clave)
    return a["texto"] if a else ""


# --------------------------------------------------------------- el coche

def _limpiar_modelo(modelo):
    """
    'RCF LMGT3' -> 'RCF'. Quita la coletilla de la clase, que ya va aparte
    en la categoria y solo alarga el nombre del archivo.
    """
    for sobra in CLASES:
        if modelo.upper().endswith(sobra) and len(modelo) > len(sobra) + 1:
            modelo = modelo[: -len(sobra)]
    return modelo.strip(" -_")


def _pegar(marca, modelo):
    """'Lexus' + 'RCF' -> 'LexusRCF'. Lo que va delante del nombre."""
    junto = re.sub(r"[^0-9A-Za-z]", "", "%s%s" % (marca, modelo))
    return junto or "Coche"


# Como se llama cada clase en el programa. Se mira en este orden porque
#'LMGT3' contiene 'GT3' y ganaria la corta, y porque un Hypercar puede
# venir escrito de tres maneras distintas segun el coche.
NOMBRE_CLASE = [("HYPERCAR", "Hypercar"), ("LMDH", "Hypercar"),
                ("LMH", "Hypercar"), ("LMP2", "LMP2"), ("LMP3", "LMP3"),
                ("GTE", "GTE"), ("LMGT3", "GT3"), ("GT3", "GT3")]


def _categoria_de(clase):
    arriba = (clase or "").upper()
    for pista, nombre in NOMBRE_CLASE:
        if pista in arriba:
            return nombre
    return ""


def coche_de(ficha):
    """
    De que coche es el reglaje: {"marca", "modelo", "categoria", "corto"}.

    Se intenta por dos caminos distintos y por ese orden:

      1. El catalogo del juego, buscando por el codigo del coche. Es el
         bueno, pero solo lo tiene quien ya haya corrido alguna carrera:
         el catalogo se llena leyendo los resultados.
      2. El propio archivo. La linea de la clase y la carpeta del coche
         llevan el nombre escrito, asi que esto funciona SIEMPRE, tambien
         en un programa recien instalado. Es mas basto pero nunca falla.
    """
    codigo = ficha.get("codigo") or ""
    clase = ficha.get("clase") or ""

    if codigo:
        try:
            hallado = coches.buscar("", clase, codigo)
        except Exception:
            hallado = None
        if hallado and hallado.get("modelo"):
            marca = hallado.get("marca", "")
            modelo = _limpiar_modelo(hallado.get("modelo", ""))
            return {"marca": marca, "modelo": modelo,
                    "categoria": hallado.get("categoria") or _categoria_de(clase),
                    "corto": _pegar(marca, modelo)}

    # Camino 2: 'GT3 Lexus_RCF_GT3 WEC2025' o 'Ford_Mustang_LMGT3 GT3 WEC2026'.
    # El orden de las palabras cambia segun quien monto el coche, asi que no
    # se puede ir por posicion: se descartan las que se sabe que NO son el
    # coche (la clase y el ano de la temporada) y lo que sobrevive es el
    # modelo.
    resto = []
    for palabra in clase.split():
        if palabra.upper() in CLASES:
            continue
        if re.match(r"^(WEC|ELMS|IMSA)\d{2,4}$", palabra, re.I):
            continue
        resto.append(palabra)

    crudo = (resto[0] if resto else "") or ficha.get("familia", "")
    crudo = re.sub(r"_(19|20)\d{2}$", "", crudo)          # LexusRCF_GT3_2024
    trozos = [t for t in crudo.split("_") if t]
    marca = trozos[0] if trozos else ""
    modelo = _limpiar_modelo(" ".join(trozos[1:]))
    return {"marca": marca, "modelo": modelo,
            "categoria": _categoria_de(clase),
            "corto": _pegar(marca, modelo)}


# --------------------------------------------------------- el combustible

def combustible(ficha):
    """
    Lo mas importante de todo: mira si la gasolina llega hasta donde dice
    la barra de energia.

    En LMU hay dos depositos y la pantalla solo ensena uno. La barra grande
    cuenta ENERGIA; la gasolina va aparte y puede acabarse mucho antes. Un
    reglaje de clasificacion mal montado carga gasolina para vuelta y media
    mientras la barra promete seis vueltas, y el coche se para en pista sin
    que nada haya avisado.

    Devuelve None si el coche no gasta energia virtual (un LMP2, por
    ejemplo, va solo con gasolina y aqui no hay nada que cuadrar).
    """
    ve = buscar(ficha, "VirtualEnergySetting")
    cap = buscar(ficha, "FuelCapacitySetting")
    fuel = buscar(ficha, "FuelSetting")
    if not ve or not cap or not fuel:
        return None

    gasolina = _vueltas(cap["texto"])
    energia = _vueltas(ve["texto"])
    if gasolina is None or energia is None or not energia:
        return None

    sobra = gasolina - energia
    if sobra < -energia * MARGEN:
        estado = "malo"
    elif sobra > energia * 0.20:
        estado = "sobra"
    else:
        estado = "bien"

    return {"gasolina": gasolina, "energia": energia,
            "litros": _numero(cap["texto"]), "ratio": _numero(fuel["texto"]),
            "energia_pct": ve["indice"], "estado": estado,
            "faltan": max(0.0, -sobra)}


def cuadrar(ficha):
    """
    Calcula que indice hay que poner en FuelSetting para que la gasolina
    dure lo mismo que la energia. Devuelve (indice_nuevo, ratio_nuevo) o
    None si no hace falta o no se puede.

    La cuenta es simple. Del propio archivo se saca cuanto gasta el coche
    por vuelta (los litros cargados entre las vueltas que dan), y con eso
    se sabe cuantos litros hacen falta para las vueltas de energia. Lo que
    no se sabe de antemano es como se convierte ese numero en el indice del
    juego, porque la escala cambia de un coche a otro; asi que la
    equivalencia se deduce del propio reglaje, comparando el indice que
    trae con el valor que dice traer.
    """
    c = combustible(ficha)
    if not c or c["estado"] != "malo":
        return None
    if not c["litros"] or not c["gasolina"] or not c["ratio"]:
        return None
    pct = c["energia_pct"]
    indice = valor(ficha, "FuelSetting")
    if not pct or indice is None:
        return None

    por_vuelta = c["litros"] / c["gasolina"]
    vueltas = c["energia"] * COLCHON
    litros_quiero = por_vuelta * vueltas
    ratio_quiero = litros_quiero / pct

    desfase = c["ratio"] * 100.0 - indice        # casi siempre 1
    nuevo = max(0, int(round(ratio_quiero * 100.0 - desfase)))
    return {"indice": nuevo, "ratio": ratio_quiero,
            "litros": litros_quiero, "vueltas": vueltas}


# El renglon de la capacidad tiene esta forma: '16.0L (4.5 laps)'. La unidad
# y la palabra de las vueltas cambian con el idioma del juego, asi que se
# cambian solo los dos numeros y todo lo demas se deja como estaba.
_CAPACIDAD = re.compile(r"^\s*([\d]+[.,]?[\d]*)\s*([A-Za-z]*)\s*"
                        r"\(\s*([\d]+[.,]?[\d]*)\s*([^)]*)\)")


def _rehacer_capacidad(viejo, litros, vueltas):
    """
    Reescribe '16.0L (4.5 laps)' con los litros y las vueltas nuevos.

    Esta linea la escribe el juego para que la lea una persona, y el juego
    no la va a rehacer hasta que alguien vuelva a guardar el reglaje desde
    el garaje. Si se cambia la gasolina y esto se queda como estaba, el
    archivo dice dos cosas distintas: el reglaje esta bien pero el papel
    sigue poniendo lo de antes, y el propio programa vuelve a dar la alarma
    sobre algo que ya arreglo.
    """
    m = _CAPACIDAD.match(viejo or "")
    if not m:
        return viejo
    coma = "," in m.group(1) or "," in m.group(3)
    def num(v):
        t = "%.1f" % v
        return t.replace(".", ",") if coma else t
    return "%s%s (%s %s)" % (num(litros), m.group(2), num(vueltas),
                             m.group(4).strip())


def guardar_cuadrado(ficha, destino=None):
    """
    Reescribe el .svm con el combustible cuadrado.

    Se tocan DOS lineas y las demas se copian tal cual. Nada de volver a
    generar el archivo desde cero: si el juego guardo ahi algo que este
    programa todavia no entiende, tiene que seguir estando cuando lo abra.

    Las dos lineas son la gasolina y el renglon de al lado que dice cuanta
    entra y para cuantas vueltas da. La segunda es solo texto y el juego no
    la mira, pero si se deja como estaba el archivo se queda diciendo dos
    cosas distintas.
    """
    a = cuadrar(ficha)
    if not a:
        return None
    capacidad = _rehacer_capacidad(texto(ficha, "FuelCapacitySetting"),
                                   a["litros"], a["vueltas"])
    salida = []
    for linea in ficha["lineas"]:
        pelada = linea.strip()
        if pelada.startswith("FuelSetting="):
            salida.append("FuelSetting=%d//%.2f" % (a["indice"], a["ratio"]))
        elif pelada.startswith("FuelCapacitySetting="):
            salida.append("FuelCapacitySetting=%s//%s"
                          % (int(valor(ficha, "FuelCapacitySetting") or 0),
                             capacidad))
        else:
            salida.append(linea)

    destino = destino or ficha["ruta"]
    try:
        with open(destino, "w", encoding="latin-1", newline="\r\n") as f:
            f.write("\n".join(salida) + "\n")
    except OSError:
        return None
    return destino


# ------------------------------------------------------------ que tipo es

# Como se dice "mojado" en los siete idiomas en los que se juega a LMU. El
# compuesto de neumatico lo escribe el juego traducido al idioma de quien
# guardo el reglaje, asi que buscar solo "wet" dejaba fuera los reglajes
# guardados en espanol, que ponen "Mojado".
_MOJADO_GOMA = re.compile(r"(wet|mojad|lluvia|pluie|mouill|bagnat|nass|"
                          r"regen|molhad|chuva|mokr|deszcz)", re.I)
# Y en el nombre del archivo, que es la otra via. HYMO abrevia la lluvia
# con una W delante de la sesion (WQ, WR).
_MOJADO_NOMBRE = re.compile(r"(wet|rain|lluvia|pluie|regen|bagnat|chuva)", re.I)


def mojado(ficha):
    """
    Si el reglaje es de lluvia, y de que fiarse para decirlo.

    Devuelve (True/False, seguro). Hay dos vias y no siempre coinciden:

      - El compuesto de neumatico. Si pone mojado, es que si, sin discusion.
      - El nombre del archivo. Es una pista, no una prueba.

    Hace falta mirar las dos porque hay reglajes de lluvia que dejan
    puestas las gomas de seco: cambian el aleron, las barras y el control
    de traccion, pero el compuesto lo elige el piloto en el garaje y el
    ingeniero no lo toco. Mirando solo la goma, esos pasaban por secos.
    """
    a = buscar(ficha, "CompoundSetting")
    if a and _MOJADO_GOMA.search(a["texto"] or ""):
        return True, True
    if _MOJADO_NOMBRE.search(ficha["nombre"]):
        return True, False
    m = _CODIGO_HYMO.search(ficha["nombre"])
    if m and m.group(1).upper() == "W":
        return True, False
    return False, True


def sesion(ficha):
    """
    'Qualy', 'Race' o 'Endu'.

    Clasificacion y carrera salen de la carga que lleva el coche, y eso es
    fiable: nadie sale a clasificar con el deposito lleno. Lo que no se
    puede saber mirando el archivo es si una carrera es de las largas, asi
    que de momento se mira lo que ponga el nombre. El detector que adivine
    eso solo es el siguiente paso del programa.
    """
    if re.search(r"(endu|enduro|endurance)", ficha["nombre"], re.I):
        return "Endu"

    c = combustible(ficha)
    if c:
        if c["energia_pct"] and c["energia_pct"] <= 40:
            return "Qualy"
        if c["gasolina"] and c["gasolina"] < 10:
            return "Qualy"
        return "Race"

    if re.search(r"(qual|hotlap)", ficha["nombre"], re.I):
        return "Qualy"
    return "Race"


# Cada web abrevia a su manera y hay que conocerlas una por una. GoSetups
# escribe la palabra entera ("Esport", "Safe"); HYMO usa dos letras al
# final del nombre, la primera para el estilo y la segunda para la sesion:
# ER es Esport de carrera, CQ es la version comoda de clasificacion, WR es
# la de lluvia. Sin esto, dos reglajes distintos del mismo pack acababan
# con el mismo nombre y uno se comia al otro.
_FAST = re.compile(r"(esport|e-?sport|fast|aggr|attack|quick|hotlap)", re.I)
_CODIGO_HYMO = re.compile(r"(?:^|[\s_-])([CEW])([QR])(?:$|[\s_.-])")


def estilo(ficha):
    """
    'Safe' o 'Fast'. Esto NO esta escrito en el archivo, asi que solo se
    puede mirar lo que diga el nombre de origen y, si no dice nada,
    dejarlo en Safe: entre equivocarse hacia un coche comodo y
    equivocarse hacia uno que da trompos, el error barato es el primero.
    """
    n = ficha["nombre"]
    if _FAST.search(n):
        return "Fast"
    m = _CODIGO_HYMO.search(n)
    if m and m.group(1).upper() == "E":
        return "Fast"
    return "Safe"


def fuente(ficha):
    """De que web viene. Primero la firma interna, que se falsea menos."""
    donde = ("%s %s" % (ficha.get("nota", ""), ficha["nombre"])).lower()
    for pista, nombre in FIRMAS:
        if pista in donde:
            return nombre
    return "Propio"


def version(ficha):
    """
    'V141' del nombre, y si no lo trae, la fecha del archivo.

    Sirve para que un reglaje nuevo de la misma web no machaque al viejo:
    de un mes para otro sacan otra version, y merece la pena tener las dos
    para poder compararlas.
    """
    m = re.search(r"[vV]\s*(\d)[.\s]?(\d)[.\s]?(\d)?", ficha["nombre"])
    if m:
        return "V" + "".join(t for t in m.groups() if t)
    try:
        return time.strftime("%y%m%d",
                             time.localtime(os.path.getmtime(ficha["ruta"])))
    except OSError:
        return ""


def describir(ficha):
    """Todo lo que sabemos del reglaje, junto, para pintarlo en una fila."""
    llueve, seguro = mojado(ficha)
    return {
        "coche": coche_de(ficha),
        "mojado": llueve,
        "mojado_seguro": seguro,
        "sesion": sesion(ficha),
        "estilo": estilo(ficha),
        "fuente": fuente(ficha),
        "version": version(ficha),
        "combustible": combustible(ficha),
    }


def nombre_propuesto(datos):
    """
    'LexusRCF_Dry_Race_Safe_GO_V141'.

    El coche va delante para que en la lista del juego salgan juntos todos
    los de un mismo coche, que es como se buscan. Y va SIEMPRE, aunque
    parezca repetido, porque el juego ensena en esa lista todos los
    reglajes de la carpeta del circuito sin mirar de que coche son: deja
    cargar uno del Lexus en un Ford sin avisar de nada. El nombre es lo
    unico que hay para no equivocarse.
    """
    trozos = [datos["coche"]["corto"],
              "Wet" if datos["mojado"] else "Dry",
              datos["sesion"],
              datos["estilo"],
              datos.get("fuente", ""),
              datos.get("version", "")]
    return "_".join(t for t in trozos if t)


# -------------------------------------------------------------- duplicados

def huella(ficha, con_gasolina=False):
    """
    Lo que de verdad define un reglaje.

    Por defecto se compara solo el reglaje en si y no el archivo entero,
    porque dos copias del mismo pueden traer distinta firma del ingeniero,
    distinta ruta de instalacion o distinta carga de gasolina sin ser
    reglajes distintos: el coche va exactamente igual.

    Con con_gasolina se mira TAMBIEN el deposito y las paradas. Hace falta
    para saber cual se puede borrar, que es otra pregunta: el reglaje de
    clasificacion y el de carrera de un mismo pack suelen llevar el coche
    igual y cambiar solo la gasolina, y ahi no sobra ninguno de los dos.
    """
    fuera = () if con_gasolina else (
        "FuelSetting", "FuelCapacitySetting", "VirtualEnergySetting",
        "NumPitstopsSetting")
    return "|".join("%s=%s" % (c, ficha["ajustes"][c]["indice"])
                    for c in sorted(ficha["ajustes"])
                    if ficha["ajustes"][c]["clave"] not in fuera)


def buscar_duplicados(fichas, mismo_circuito=False, con_gasolina=False):
    """
    Agrupa los que son el mismo reglaje con distinto nombre.

    Con mismo_circuito solo se juntan los que ademas viven en la misma
    carpeta, que son los que de verdad sobran. El mismo reglaje en Monza y
    en Spa no es una copia de mas: hace falta en los dos sitios, porque el
    circuito de un reglaje es la carpeta donde esta.

    Con con_gasolina se exige que sean iguales hasta en el deposito, que es
    lo que hay que pedir antes de proponerle a nadie que borre uno.
    """
    por_huella = {}
    for f in fichas:
        h = huella(f, con_gasolina)
        por_huella.setdefault((f["circuito"], h) if mismo_circuito else h,
                              []).append(f)
    return [g for g in por_huella.values() if len(g) > 1]


# ---------------------------------------------------------------- importar

def sin_pisar(ruta):
    """La misma ruta, numerada si ya existe. Nunca se machaca un archivo."""
    if not os.path.exists(ruta):
        return ruta
    base, ext = os.path.splitext(ruta)
    n = 2
    while os.path.exists("%s (%d)%s" % (base, n, ext)):
        n += 1
    return "%s (%d)%s" % (base, n, ext)


def desempaquetar(ruta_zip, destino):
    """
    Saca los .svm de un comprimido y los deja sueltos en una carpeta.

    Las webs mandan un solo archivo con el pack entero dentro, muchas veces
    con una carpeta por circuito. Aqui se sacan todos en plano; a que
    circuito va cada uno se decide despues, uno por uno.
    """
    sacados = []
    try:
        with zipfile.ZipFile(ruta_zip) as z:
            for miembro in z.namelist():
                if not miembro.lower().endswith(".svm"):
                    continue
                nombre = os.path.basename(miembro)
                if not nombre:
                    continue
                # Se guarda tambien de que carpeta salio: en un pack por
                # circuitos, esa carpeta es la mejor pista de a donde va.
                carpeta = os.path.basename(os.path.dirname(miembro))
                salida = sin_pisar(os.path.join(destino, nombre))
                with z.open(miembro) as origen, open(salida, "wb") as f:
                    f.write(origen.read())
                sacados.append((salida, carpeta))
    except (OSError, zipfile.BadZipFile, RuntimeError):
        return []
    return sacados


# ------------------------------------------------- que llevas en el juego

def asignados(carpeta_player):
    """
    Los reglajes que el juego tiene ASIGNADOS, leidos de su propio archivo.

    Devuelve [{"circuito", "clase", "ruta", "nombre", "existe"}, ...].

    De donde sale y por que este y no otro: el juego NO apunta en ningun
    sitio el reglaje que cargas en el garaje. Se comprobo uno por uno:
    cargarlo no escribe nada, salir a pista tampoco, cambiar de sesion
    tampoco, y salir al menu reescribe el archivo pero sin anadirlo. Lo
    unico que lo deja escrito, y al instante, es pulsar ASIGNAR en la
    pantalla de configuraciones.

    Por eso esto no adivina nada: es el juego diciendo la ruta exacta. Si
    alguien no ha asignado nada, aqui no sale y el programa lo dice, que es
    mejor que suponer.

    OJO AL EFECTO SECUNDARIO, que hay que avisarlo en pantalla: asignar un
    reglaje hace que el juego lo cargue solo la proxima vez que entres con
    ese coche a ese circuito. A unos les viene bien y a otros no, asi que
    es cosa suya decidirlo. El programa solo LEE este archivo; no lo
    escribe nunca.
    """
    ruta = os.path.join(carpeta_player, "FavoriteAndFixedSetups.gal")
    try:
        with open(ruta, encoding="latin-1") as f:
            texto = f.read()
    except OSError:
        return []

    salida = []
    for trozo in re.findall(r"AutoLoadEntry\s*\{(.*?)\}", texto, re.S):
        def campo(nombre):
            m = re.search(r'%s\s*=\s*"([^"]*)"' % nombre, trozo)
            return m.group(1) if m else ""
        archivo = campo("File")
        if not archivo:
            continue
        salida.append({
            "circuito": campo("Track"),
            "clase": campo("Classes"),
            "ruta": archivo,
            "nombre": os.path.splitext(os.path.basename(archivo))[0],
            "existe": os.path.isfile(archivo),
        })
    return salida


def asignado_a(carpeta_player, ficha):
    """Si un reglaje concreto es el que el juego tiene asignado."""
    mia = os.path.abspath(ficha["ruta"]).lower()
    for a in asignados(carpeta_player):
        if os.path.abspath(a["ruta"]).lower() == mia:
            return a
    return None


def donde_estas():
    """
    En que circuito y con que coche estas ahora mismo, o None si el juego
    no esta abierto. Sale de la memoria compartida, o sea del propio juego.
    """
    try:
        import lector_lmu as L
        sco = L.Scoring()
        circuito = sco.circuito() or ""
        if not circuito:
            return None
        # El coche se lee a mano de la ficha del jugador, sin pasar por
        # Scoring.coches(). Esa funcion devuelve las posiciones en el mapa y
        # para eso necesita el circuito escaneado y calibrado; si falta algo
        # devuelve la lista vacia. Aqui no hacen falta posiciones, solo
        # saber que coche es, y ese dato esta siempre.
        corto = ""
        try:
            import coches as cat
            for i in range(min(L.MAX_COCHES, sco.n_coches())):
                b = L.SCO_BASE + i * L.SCO_STRIDE
                if not L.u1(sco.sco, b + L.OFF_YO):
                    continue
                f = cat.buscar(L.txt(sco.sco, b + L.OFF_VEHICULO, 64),
                               L.txt(sco.sco, b + L.OFF_CLASE, 32),
                               L.txt(sco.sco, b + L.OFF_CODIGO, 32))
                if f:
                    corto = _pegar(f.get("marca", ""),
                                   _limpiar_modelo(f.get("modelo", "")))
                break
        except Exception:
            pass
        return {"circuito": circuito, "coche": corto}
    except Exception:
        return None


def el_que_llevas(carpeta_player, aqui=None):
    """
    Cual de los reglajes asignados es el de AQUI y AHORA.

    Hace falta distinguirlo porque el juego guarda un reglaje asignado por
    cada combinacion de circuito y coche: quien haya corrido en seis
    circuitos tiene seis, y solo uno es el que va a cargar cuando entre a
    pista. Marcarlos todos igual no dice nada; peor todavia era senalar uno
    a boleo, que es lo que se hacia antes (se cogia el ultimo del archivo y
    acertaba de casualidad).

    Si el juego esta cerrado no se puede saber, y entonces se dice que no
    se sabe en vez de adivinar.
    """
    aqui = aqui if aqui is not None else donde_estas()
    if not aqui:
        return None
    suelto = re.sub(r"[^a-z0-9]", "", (aqui["circuito"] or "").lower())

    # Primero por circuito. El .gal escribe la carpeta ("Silverstonewec") y
    # el juego publica el nombre largo ("Silverstone Grand Prix Circuit -
    # WEC"), asi que se comparan por trozos y no letra a letra.
    candidatos = []
    for a in asignados(carpeta_player):
        if not a["existe"]:
            continue
        carpeta = re.sub(r"[^a-z0-9]", "",
                         os.path.basename(os.path.dirname(a["ruta"])).lower())
        if carpeta and (carpeta in suelto or suelto.startswith(carpeta[:8])):
            candidatos.append(a)
    if not candidatos:
        return None
    if len(candidatos) == 1:
        return candidatos[0]

    # Hay varios en el mismo circuito, uno por coche. Sin saber el coche no
    # se puede elegir, y elegir a boleo es peor que no elegir: te llevaria
    # a retocar el reglaje de otro coche creyendo que es el tuyo.
    if not aqui.get("coche"):
        return None
    for a in candidatos:
        f = leer(a["ruta"])
        if f and coche_de(f)["corto"].lower() == aqui["coche"].lower():
            return a
    return None


def circuitos_del_juego(carpeta_settings):
    """Las carpetas de circuito que tiene el juego, en orden alfabetico."""
    try:
        return sorted(d for d in os.listdir(carpeta_settings)
                      if os.path.isdir(os.path.join(carpeta_settings, d)))
    except OSError:
        return []


def adivinar_circuito(pistas, disponibles):
    """
    A que circuito suena un reglaje, mirando su nombre y su carpeta.

    Los packs abrevian: SIL es Silverstone, IMO es Imola, POR es Portimao.
    Se prueba primero el nombre entero del circuito y luego las tres
    primeras letras, que es como abrevia todo el mundo. Si no queda claro
    no se inventa nada: devuelve vacio y lo elige la persona, que es mucho
    mejor que colar un reglaje en el circuito equivocado.
    """
    limpio = re.sub(r"[^a-z]", " ", (" ".join(pistas)).lower())
    junto = limpio.replace(" ", "")
    palabras = [p for p in limpio.split() if len(p) >= 3]

    # Los nombres largos ganan: 'Silverstonewec' antes que 'Silverstone',
    # que si no siempre saldria la variante corta.
    for c in sorted(disponibles, key=len, reverse=True):
        if c.lower().replace(" ", "") in junto:
            return c
    for p in palabras:
        for c in sorted(disponibles, key=len, reverse=True):
            if c.lower().startswith(p[:3]):
                return c
    return ""
