# -*- coding: utf-8 -*-
"""
Lo que sabe de mecanica: comparar dos reglajes, adivinar para que es uno
que viene sin nombre, y aprender de los reglajes que haya en el ordenador.

Igual que biblioteca.py, aqui no hay ninguna ventana.

POR QUE NO HAY UNA IA AQUI DENTRO
Porque no hace falta y seria peor. Que menos aleron trasero suelta el coche
en curva rapida es fisica, se sabe desde hace decadas y vale igual en LMU
que en un coche de verdad. Una IA pequena, de las que caben en un ordenador
normal, no sabe de Le Mans Ultimate y se inventaria los numeros con mucho
aplomo; para un reglaje eso es peligroso. Lo que hace falta es una tabla de
reglas que se pueda leer, corregir y discutir, y que ademas pueda explicar
por que propone cada cambio. Eso es lo que hay aqui y en reglas.json.

Y hay algo que ninguna IA generica tiene: los reglajes hechos por
ingenieros que estan en el propio ordenador. De ahi sale la calibracion, o
sea CUANTO mover cada cosa. Las reglas dicen QUE tocar; los reglajes de
verdad dicen cuanto.
"""
import json
import os
import re

import biblioteca as B
import rutas

RUTA_REGLAS = rutas.datos("reglas.json")
RUTA_CALIBRACION = rutas.datos("calibracion.json")

# Las cuatro ruedas y el eje al que pertenece cada una.
EJES = {"FRONTLEFT": "del", "FRONTRIGHT": "del",
        "REARLEFT": "tras", "REARRIGHT": "tras"}

# Nombre en cristiano de cada ajuste. Solo estan los que se tocan de
# verdad; lo que el juego no deja mover en ningun coche no hace falta
# traducirlo. La clave es el nombre tecnico tal cual aparece en el .svm.
NOMBRES = {
    # aerodinamica
    "RWSetting": "Aleron trasero",
    "FWSetting": "Aleron delantero",
    "WaterRadiatorSetting": "Radiador de agua",
    "OilRadiatorSetting": "Radiador de aceite",
    "BrakeDuctSetting": "Conductos de freno delanteros",
    "BrakeDuctRearSetting": "Conductos de freno traseros",
    # suspension
    "FrontAntiSwaySetting": "Barra estabilizadora delantera",
    "RearAntiSwaySetting": "Barra estabilizadora trasera",
    "FrontToeInSetting": "Convergencia delantera",
    "RearToeInSetting": "Convergencia trasera",
    "Front3rdSpringSetting": "Tercer muelle delantero",
    "Rear3rdSpringSetting": "Tercer muelle trasero",
    "Front3rdPackerSetting": "Tope del tercer elemento delantero",
    "Rear3rdPackerSetting": "Tope del tercer elemento trasero",
    "SpringSetting": "Muelle",
    "RideHeightSetting": "Altura",
    "CamberSetting": "Caida",
    "PressureSetting": "Presion de neumatico",
    "PackerSetting": "Tope de suspension",
    "SlowBumpSetting": "Compresion lenta",
    "SlowReboundSetting": "Rebote lento",
    "FastBumpSetting": "Compresion rapida",
    "FastReboundSetting": "Rebote rapido",
    "CompoundSetting": "Compuesto de neumatico",
    # frenos y volante
    "RearBrakeSetting": "Reparto de frenada",
    "BrakePressureSetting": "Presion de freno",
    "BrakeMigrationSetting": "Migracion de frenada",
    "BrakeDiscSetting": "Disco de freno",
    "BrakePadSetting": "Pastillas de freno",
    "SteerLockSetting": "Angulo de volante",
    # motor y electronica
    "TractionControlMapSetting": "Control de traccion",
    "TCPowerCutMapSetting": "Corte de potencia del control de traccion",
    "TCSlipAngleMapSetting": "Angulo de deslizamiento del control de traccion",
    "ABSSetting": "ABS",
    "AntilockBrakeSystemMapSetting": "Mapa de ABS",
    "EngineMixtureSetting": "Mezcla del motor",
    "EngineBrakingMapSetting": "Freno motor",
    "RevLimitSetting": "Limitador de revoluciones",
    "RegenerationMapSetting": "Recuperacion de energia",
    "ElectricMotorMapSetting": "Motor electrico",
    # transmision
    "DiffPowerSetting": "Diferencial en aceleracion",
    "DiffCoastSetting": "Diferencial en retencion",
    "DiffPreloadSetting": "Precarga del diferencial",
    "FinalDriveSetting": "Grupo final",
    "RatioSetSetting": "Juego de relaciones",
    # deposito
    "FuelSetting": "Capacidad de combustible",
    "FuelCapacitySetting": "Combustible cargado",
    "VirtualEnergySetting": "Energia virtual",
    "NumPitstopsSetting": "Paradas previstas",
}
for _n in range(1, 9):
    NOMBRES["Gear%dSetting" % _n] = "Marcha %d" % _n

# Lo que no vale la pena ensenar al comparar: son iguales en todos los
# reglajes o el juego no los deja tocar.
#
# Van en dos listas y no en una sola por una razon de peso: el .svm tiene
# una linea que se llama "Ride" a secas, que va vacia, y otra que se llama
# "RideHeightSetting", que es la altura del coche y es de lo mas importante
# que hay. Filtrando por el principio del nombre, la primera se llevaba por
# delante a la segunda y la altura no salia nunca al comparar.
IGNORAR_EXACTOS = {"Balance", "Custom", "Downforce", "Gearing", "Ride",
                   "Symmetric", "UpgradeSetting", "WedgeSetting"}
IGNORAR_EMPIEZAN = re.compile(
    r"^(ChassisAdj|Pitstop\d|CG[A-Z]|LeftTrackBar|RightTrackBar|LeftCaster|"
    r"RightCaster|FrontWheelTrack|RearWheelTrack|FenderFlare|GearAuto|"
    r"Reverse|Handbrake|Handfrontbrake)")


def se_ignora(clave):
    return clave in IGNORAR_EXACTOS or bool(IGNORAR_EMPIEZAN.match(clave))


def nombre_de(seccion, clave):
    """'REARLEFT' + 'SpringSetting' -> 'Muelle trasero'."""
    base = NOMBRES.get(clave, clave)
    eje = EJES.get(seccion)
    if not eje:
        return base
    return base + (" delantero" if eje == "del" else " trasero")


# ------------------------------------------------------------- comparar

def _agrupar(ficha):
    """
    Junta las dos ruedas de un eje cuando llevan lo mismo, que es casi
    siempre. Asi la comparacion dice 'Muelle trasero' una vez en vez de
    'trasero izquierdo' y 'trasero derecho' con el mismo numero.
    """
    sueltos = {}
    for llave, a in ficha["ajustes"].items():
        if se_ignora(a["clave"]):
            continue
        eje = EJES.get(a["seccion"])
        grupo = ("EJE_" + eje, a["clave"]) if eje else (a["seccion"], a["clave"])
        sueltos.setdefault(grupo, []).append(a)

    salida = {}
    for grupo, lista in sueltos.items():
        indices = set(x["indice"] for x in lista)
        if len(indices) == 1:
            salida[grupo] = lista[0]
        else:
            # Las dos ruedas van distintas: el coche esta descompensado a
            # proposito y hay que ensenar cada lado por separado.
            for a in lista:
                salida[(a["seccion"], a["clave"])] = a
    return salida


def comparar(uno, otro):
    """
    En que se diferencian dos reglajes.

    Devuelve una lista de diccionarios con el nombre en cristiano, lo que
    pone cada uno y cuantos puntos de diferencia hay. Ordenada poniendo
    delante lo que mas cambia el coche, que es como lo miraria un
    ingeniero: el aleron primero y el disco de freno el ultimo.
    """
    a, b = _agrupar(uno), _agrupar(otro)
    filas = []
    for grupo in set(a) | set(b):
        x, y = a.get(grupo), b.get(grupo)
        if not x or not y or x["indice"] == y["indice"]:
            continue
        seccion, clave = grupo
        eje = seccion[4:] if seccion.startswith("EJE_") else None
        nombre = NOMBRES.get(clave, clave)
        if eje:
            nombre += " delantero" if eje == "del" else " trasero"
        elif seccion in EJES:
            nombre = nombre_de(seccion, clave)
        filas.append({
            "clave": clave, "nombre": nombre,
            "de": x["texto"] or ("%g" % x["indice"] if x["indice"] is not None else "?"),
            # Los dos reglajes pueden venir guardados en idiomas distintos.
            # Se ensena el segundo como lo escribe el primero para que las
            # dos columnas se puedan comparar de un vistazo.
            "a": con_el_formato_de(x["texto"], y["texto"])
                 or ("%g" % y["indice"] if y["indice"] is not None else "?"),
            "saltos": abs((y["indice"] or 0) - (x["indice"] or 0)),
            "peso": PESO.get(clave, 5),
        })
    filas.sort(key=lambda f: (-f["peso"], f["nombre"]))
    return filas


# Cuanto cambia el coche cada cosa, de 10 a 1. Sirve para poner primero lo
# que de verdad importa cuando se comparan dos reglajes, y para que el
# ingeniero proponga antes lo gordo que lo fino.
PESO = {
    "RWSetting": 10, "FWSetting": 10,
    "RearAntiSwaySetting": 9, "FrontAntiSwaySetting": 9,
    "PressureSetting": 9, "CompoundSetting": 9,
    "RideHeightSetting": 8, "SpringSetting": 8,
    "RearToeInSetting": 7, "FrontToeInSetting": 7,
    "TractionControlMapSetting": 7, "RearBrakeSetting": 7,
    "DiffPowerSetting": 6, "DiffCoastSetting": 6, "DiffPreloadSetting": 6,
    "CamberSetting": 6, "BrakePressureSetting": 6,
    "SlowBumpSetting": 5, "SlowReboundSetting": 5,
    "FastBumpSetting": 4, "FastReboundSetting": 4,
    "TCPowerCutMapSetting": 4, "TCSlipAngleMapSetting": 4,
    "Front3rdSpringSetting": 4, "Rear3rdSpringSetting": 4,
    "WaterRadiatorSetting": 3, "OilRadiatorSetting": 3,
    "BrakeDuctSetting": 3, "BrakeDuctRearSetting": 3,
    "BrakeMigrationSetting": 3, "PackerSetting": 3,
    "EngineMixtureSetting": 3, "SteerLockSetting": 2,
    "FuelSetting": 2, "VirtualEnergySetting": 2,
}


# ------------------------------------------------------------- calibracion

def _senales(ficha):
    """
    Las tres cosas que se miden de un reglaje para adivinar de que tipo es.

    No son valores absolutos (un coche no se parece a otro) sino los
    indices tal cual, que luego se comparan contra los demas reglajes del
    MISMO coche. Comparar un Lexus con un Porsche no dice nada; comparar
    dos Lexus del mismo circuito lo dice todo.

      agarre    : cuanto apoyo lleva atras. Menos apoyo, coche mas suelto.
      ayudas    : cuanta electronica lleva puesta.
      aguante   : lo que se hace para que el coche llegue al final.
    """
    def v(clave, por_defecto=0.0):
        x = B.valor(ficha, clave)
        return por_defecto if x is None else x

    return {
        "agarre": v("REARWING/RWSetting") + v("SUSPENSION/RearToeInSetting"),
        "ayudas": v("ENGINE/TractionControlMapSetting")
                  + v("ENGINE/TCPowerCutMapSetting"),
        "aguante": (100 - v("BODYAERO/WaterRadiatorSetting", 100))
                   + (100 - v("BODYAERO/OilRadiatorSetting", 100))
                   + v("DRIVELINE/DiffPreloadSetting") / 10.0,
    }


def calibrar(carpeta_settings, guardar=True):
    """
    Aprende de todos los reglajes del ordenador y deja lo aprendido en
    calibracion.json.

    Lo que aprende son dos cosas:

      1. El paso de cada ajuste: de cuanto en cuanto lo mueven los que
         saben. Si en veinte reglajes el aleron nunca se mueve de uno en
         uno sino de dos en dos, ese es el escalon que tiene sentido
         proponer.
      2. Como es un reglaje comodo y como es uno agresivo, para cada
         coche, mirando los que ya vienen con el nombre puesto.

    Lo que se guarda son numeros, no reglajes. Un archivo que dice que el
    paso del aleron suele ser de un grado no es de nadie, igual que decir
    que un GT3 corre a doscientos. Los .svm de las webs de pago se quedan
    donde estan.
    """
    fichas = []
    for circuito in B.circuitos_del_juego(carpeta_settings):
        carpeta = os.path.join(carpeta_settings, circuito)
        for archivo in sorted(os.listdir(carpeta)):
            if archivo.lower().endswith(".svm"):
                f = B.leer(os.path.join(carpeta, archivo))
                if f:
                    fichas.append(f)

    pasos = {}
    tipos = {}
    valores = {}
    for ficha in fichas:
        cat = B.coche_de(ficha)["categoria"] or "?"
        corto = B.coche_de(ficha)["corto"]
        for a in ficha["ajustes"].values():
            if se_ignora(a["clave"]) or a["indice"] is None:
                continue
            pasos.setdefault(cat, {}).setdefault(a["clave"], []).append(a["indice"])
            # Que significa cada numero EN ESTE COCHE. El juego escribe al
            # lado de cada indice lo que vale de verdad, y juntando los de
            # todos los reglajes sale la escala entera. Con eso el
            # ingeniero puede decir "el aleron pasa de 9 a 10 grados" en
            # vez de "sube un punto", que no le dice nada a nadie.
            #
            # Va por coche y no por categoria a proposito: la escala del
            # aleron de un Lexus no es la de un Mustang aunque los dos sean
            # GT3. Y esto es como es el coche en el juego, no el reglaje de
            # nadie: se ve entrando al garaje.
            if a["texto"] and not _NO_SE_TOCA.match(a["texto"]):
                (valores.setdefault(corto, {}).setdefault(a["clave"], {})
                 .setdefault(str(int(a["indice"])), a["texto"]))

        d = B.describir(ficha)
        clave = "%s|%s" % (corto, ficha["circuito"])
        etiqueta = "%s|%s" % (d["sesion"], d["estilo"])
        tipos.setdefault(clave, {}).setdefault(etiqueta, []).append(_senales(ficha))

    salida = {"_ayuda": "Lo escribe el programa solo, leyendo los reglajes que "
                        "tengas. Son numeros aprendidos, no reglajes: se puede "
                        "repartir sin problema.",
              "reglajes_mirados": len(fichas),
              "pasos": {}, "tipos": {}, "valores": valores}

    for cat, claves in pasos.items():
        for clave, vistos in claves.items():
            unicos = sorted(set(vistos))
            if len(unicos) < 2:
                continue
            huecos = [b - a for a, b in zip(unicos, unicos[1:])]
            huecos.sort()
            salida["pasos"].setdefault(cat, {})[clave] = {
                "paso": huecos[len(huecos) // 2],       # el hueco de en medio
                "min": unicos[0], "max": unicos[-1], "visto": len(vistos)}

    for clave, etiquetas in tipos.items():
        salida["tipos"][clave] = {
            et: {k: round(sum(s[k] for s in lista) / len(lista), 2)
                 for k in ("agarre", "ayudas", "aguante")}
            for et, lista in etiquetas.items()}

    if guardar:
        try:
            with open(RUTA_CALIBRACION, "w", encoding="utf-8") as f:
                json.dump(salida, f, ensure_ascii=False, indent=1)
        except OSError:
            pass
    return salida


def leer_calibracion():
    try:
        with open(RUTA_CALIBRACION, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"pasos": {}, "tipos": {}, "valores": {}, "reglajes_mirados": 0}


_TROZOS = re.compile(r"[\d]+[.,]?[\d]*")


def con_el_formato_de(modelo, otro):
    """
    Coge los numeros de `otro` y los escribe como estan en `modelo`.

    Hace falta porque cada reglaje se guardo con el juego en un idioma, y
    la escala aprendida acaba mezclando: el mismo aleron sale como '9.0
    deg' en uno, '10.0 Grad' en otro y '11.0 grados' en un tercero. Se
    respeta como lo tenga escrito el reglaje que el piloto esta mirando, y
    solo cambia el numero.
    """
    if not modelo or not otro:
        return otro
    nums = _TROZOS.findall(otro)
    trozos = _TROZOS.split(modelo)
    if len(nums) != len(trozos) - 1:
        return otro            # no encajan: mejor dejarlo como estaba
    coma = "," in modelo and "." not in modelo
    salida = trozos[0]
    for n, resto in zip(nums, trozos[1:]):
        salida += (n.replace(".", ",") if coma else n.replace(",", ".")) + resto
    return salida


def como_queda(calibracion, coche, clave, indice, como_ahora=""):
    """
    Que valor de verdad es un indice en este coche: 3 -> '10.0 deg'.

    Sale de la escala aprendida en calibrar(). Si ese numero no se ha visto
    nunca en ningun reglaje, no se inventa nada y se devuelve vacio.
    """
    try:
        crudo = calibracion["valores"][coche][clave][str(int(indice))]
    except (KeyError, TypeError, ValueError):
        return ""
    return con_el_formato_de(como_ahora, crudo)


def paso_de(calibracion, categoria, clave):
    """De cuanto en cuanto conviene mover un ajuste. 1 si no se sabe."""
    try:
        return max(1, int(calibracion["pasos"][categoria][clave]["paso"]))
    except (KeyError, TypeError, ValueError):
        return 1


# --------------------------------------------------------------- detector

def detectar(ficha, hermanos, calibracion=None):
    """
    Para que es un reglaje que viene sin decirlo.

    `hermanos` son los demas reglajes del mismo coche y circuito, que es
    contra lo que se compara. Devuelve el tipo y cuanta confianza hay, de 0
    a 100, y por que.

    Seco/mojado y clasificacion/carrera salen del propio archivo y son
    seguros. Comodo/agresivo y si es de carrera larga NO estan escritos en
    ningun sitio, asi que aqui hay una estimacion, y se dice que lo es. Se
    prefiere quedarse corto antes que dar por bueno un reglaje agresivo:
    equivocarse hacia un coche comodo cuesta una decima, equivocarse hacia
    el otro lado cuesta un trompo.
    """
    llueve, seguro_lluvia = B.mojado(ficha)
    ses = B.sesion(ficha)
    mias = _senales(ficha)
    porques = []

    otras = [_senales(h) for h in hermanos
             if os.path.abspath(h["ruta"]) != os.path.abspath(ficha["ruta"])]
    if not otras:
        return {"mojado": llueve, "mojado_seguro": seguro_lluvia,
                "sesion": ses, "sesion_seguro": True,
                "estilo": B.estilo(ficha), "confianza": 0,
                "porque": ["No hay otros reglajes de este coche y circuito "
                           "con los que comparar."]}

    def medio(k):
        return sum(o[k] for o in otras) / len(otras)

    puntos_fast = 0
    if mias["agarre"] < medio("agarre"):
        puntos_fast += 2
        porques.append("Lleva menos apoyo atras que los demas de este coche: "
                       "mas rapido, pero mas suelto en curva rapida.")
    if mias["ayudas"] < medio("ayudas"):
        puntos_fast += 2
        porques.append("Lleva menos control de traccion que los demas.")

    estilo = "Fast" if puntos_fast >= 3 else "Safe"
    confianza = 50 + 15 * puntos_fast if estilo == "Fast" else 55

    endu = False
    if ses == "Race" and mias["aguante"] > medio("aguante") * 1.10:
        endu = True
        porques.append("Va mas tapado y con mas precarga de diferencial que "
                       "los demas: eso es de aguantar temperatura y desgaste, "
                       "o sea de carrera larga.")
    if endu:
        ses = "Endu"

    # Lo que diga el nombre pesa, porque el que lo puso sabia de que era.
    del_nombre = B.estilo(ficha)
    if re.search(r"(esport|fast|safe|endu)", ficha["nombre"], re.I):
        estilo = del_nombre
        confianza = 95
        porques.insert(0, "El nombre del archivo ya lo dice.")

    return {"mojado": llueve, "mojado_seguro": seguro_lluvia,
            "sesion": ses, "sesion_seguro": ses != "Endu",
            "estilo": estilo, "confianza": min(95, confianza),
            "porque": porques}


# --------------------------------------------------------- el ingeniero

_reglas = None


def reglas():
    """La tabla de sintomas, leida una sola vez."""
    global _reglas
    if _reglas is None:
        try:
            with open(RUTA_REGLAS, encoding="utf-8-sig") as f:
                _reglas = json.load(f)
        except (OSError, ValueError):
            _reglas = {"donde": [], "que": [], "cuando": [],
                       "reglas": [], "nombres": {}}
    return _reglas


def en_idioma(cosa, codigo):
    """
    El texto en el idioma que toque, cayendo al ingles si no esta.

    Las reglas van en espanol e ingles porque son textos largos y muy
    tecnicos. Quien quiera su idioma solo tiene que anadir una linea mas en
    reglas.json, igual que se hace con los archivos de la carpeta idiomas.
    """
    if not isinstance(cosa, dict):
        return str(cosa or "")
    return cosa.get(codigo) or cosa.get("en") or cosa.get("es") or ""


def nombre_ajuste(clave, codigo="es"):
    """'RWSetting' -> 'Aleron trasero', en el idioma que sea."""
    n = reglas().get("nombres", {}).get(clave)
    return en_idioma(n, codigo) if n else NOMBRES.get(clave, clave)


def opciones(cual, codigo="es"):
    """Las opciones de un desplegable: [(id, texto), ...]."""
    return [(o["id"], en_idioma(o, codigo)) for o in reglas().get(cual, [])]


def diagnosticar(donde, que, cuando):
    """
    Busca la regla que mejor encaja con lo que ha contado el piloto.

    Gana la que coincida en mas cosas. Una lista vacia en la regla quiere
    decir 'en cualquier caso' y cuenta como media coincidencia: asi una
    regla general sirve cuando no hay ninguna mas fina, pero pierde contra
    la que si menciona tu caso.
    """
    mejor, mejor_punto = None, 0
    for r in reglas().get("reglas", []):
        punto = 0
        # Donde pasa y que hace el coche mandan: si no coinciden, esa regla
        # no va de esto y se descarta.
        for campo, elegido in (("donde", donde), ("que", que)):
            lista = r.get(campo) or []
            if not lista:
                punto += 0.5
            elif elegido in lista:
                punto += 1
            else:
                punto = -1
                break
        if punto < 0:
            continue
        # El cuando afina, pero no descarta. Una regla que acierta el
        # sintoma sigue valiendo aunque no mencione tu caso concreto; entre
        # dos que empatan, gana la que si lo menciona. Antes se descartaba y
        # mas de la mitad de las combinaciones se quedaban sin respuesta,
        # que es la peor manera de ayudar a alguien.
        de_cuando = r.get("cuando") or []
        if not de_cuando:
            punto += 0.5
        elif cuando in de_cuando:
            punto += 1
        if punto > mejor_punto:
            mejor, mejor_punto = r, punto
    return mejor


def es_exacta(regla, cuando):
    """
    Si la regla habla justo del caso que ha contado el piloto, o si es una
    respuesta general. Sirve para avisar en pantalla y no dar por seguro
    algo que solo se parece.
    """
    lista = (regla or {}).get("cuando") or []
    return not lista or cuando in lista


def proponer(ficha, regla, calibracion=None, codigo="es"):
    """
    Convierte una regla en cambios concretos para ESTE reglaje.

    Devuelve una lista con el ajuste, lo que pone ahora, lo que pondria y
    por que. Se calcula el indice nuevo con el paso que el programa haya
    aprendido de los reglajes del ordenador, y se recorta al rango que se
    haya visto para no pedirle al juego un valor que no existe.
    """
    if not regla:
        return []
    calibracion = calibracion or leer_calibracion()
    categoria = B.coche_de(ficha)["categoria"] or "?"
    salida = []

    for cambio in regla.get("cambios", []):
        param = cambio["param"]
        seccion, clave = param.split("/", 1)
        destinos = _donde_aplicar(ficha, seccion, clave)
        if not destinos:
            continue

        paso = paso_de(calibracion, categoria, clave) * int(cambio.get("pasos", 1))
        actual = ficha["ajustes"][destinos[0]]
        if actual["indice"] is None:
            continue
        nuevo = actual["indice"] + cambio.get("dir", 1) * paso
        nuevo = _recortar(calibracion, categoria, clave, nuevo)
        if nuevo == actual["indice"]:
            continue

        salida.append({
            "param": param, "claves": destinos, "clave": clave,
            "nombre": nombre_ajuste(clave, codigo) + _apellido(seccion, codigo),
            "ahora": actual["texto"] or "%g" % actual["indice"],
            "indice_ahora": int(actual["indice"]), "indice_nuevo": int(nuevo),
            "saltos": int(abs(nuevo - actual["indice"])),
            "sube": nuevo > actual["indice"],
            "queda": como_queda(calibracion, B.coche_de(ficha)["corto"],
                                clave, nuevo, actual["texto"]),
            "porque": en_idioma(cambio, codigo),
        })
    return salida


def _apellido(seccion, codigo):
    if seccion == "EJE_del" or seccion in ("FRONTLEFT", "FRONTRIGHT"):
        return " delantero" if codigo == "es" else " (front)"
    if seccion == "EJE_tras" or seccion in ("REARLEFT", "REARRIGHT"):
        return " trasero" if codigo == "es" else " (rear)"
    return ""


# Lo que el juego escribe cuando un ajuste existe pero ese coche no lo deja
# tocar. Aparece traducido, asi que se mira el principio de la palabra.
_NO_SE_TOCA = re.compile(r"^\s*(n/?a\b|n/?d\b|non-?adjust|no ajust|nicht|"
                         r"non regol|nao ajust|non modif|niereg)", re.I)


def _donde_aplicar(ficha, seccion, clave):
    """
    Que lineas del archivo toca un cambio. Un eje son dos ruedas.

    Si la seccion que dice la regla no existe, se busca el ajuste por su
    nombre en cualquier otra. Hace falta porque la misma cosa no vive en el
    mismo sitio en todos los coches: el control de traccion esta en
    CONTROLS en unos y en ENGINE en otros, y una regla no puede fallar por
    eso.
    """
    if seccion == "EJE_del":
        candidatas = ["FRONTLEFT/" + clave, "FRONTRIGHT/" + clave]
    elif seccion == "EJE_tras":
        candidatas = ["REARLEFT/" + clave, "REARRIGHT/" + clave]
    else:
        candidatas = ["%s/%s" % (seccion, clave)]
        if candidatas[0] not in ficha["ajustes"]:
            candidatas = [llave for llave, a in ficha["ajustes"].items()
                          if a["clave"] == clave and a["seccion"] not in EJES]

    buenas = []
    for c in candidatas:
        a = ficha["ajustes"].get(c)
        # Lo que el coche no deja tocar no se propone: el juego se comeria
        # el cambio sin decir nada y pareceria que el programa miente.
        if a and not _NO_SE_TOCA.match(a["texto"] or ""):
            buenas.append(c)
    return buenas


def _recortar(calibracion, categoria, clave, valor):
    """
    Deja el valor dentro de lo que se ha visto de verdad en reglajes de esa
    categoria. Sin esto se podria pedir un aleron que ese coche no tiene, y
    el juego se comeria el reglaje entero sin decir nada.
    """
    try:
        d = calibracion["pasos"][categoria][clave]
        return max(d["min"], min(d["max"], valor))
    except (KeyError, TypeError):
        return max(0, valor)


def aplicar(ficha, cambios, destino):
    """
    Escribe un reglaje nuevo con los cambios puestos.

    NUNCA machaca el original. El reglaje bueno de ayer tiene que seguir
    ahi manana, porque la mitad de las veces el cambio no mejora nada y hay
    que poder volver. Cada prueba es un archivo mas.
    """
    nuevos = {}
    for c in cambios:
        for llave in c["claves"]:
            nuevos[llave] = c["indice_nuevo"]

    seccion = "GENERAL"
    salida = []
    for linea in ficha["lineas"]:
        pelada = linea.strip()
        if pelada.startswith("[") and pelada.endswith("]"):
            seccion = pelada[1:-1].strip().upper()
            salida.append(linea)
            continue
        if pelada.startswith("//") or "=" not in pelada:
            salida.append(linea)
            continue
        clave = pelada.split("=", 1)[0].strip()
        llave = "%s/%s" % (seccion, clave)
        if llave in nuevos:
            # Se deja el comentario viejo entre parentesis. El juego lo
            # rehace en cuanto se guarda el reglaje desde el garaje, y
            # mientras tanto se ve de un vistazo de donde venia.
            viejo = ficha["ajustes"][llave]["texto"]
            salida.append("%s=%d//%s" % (clave, nuevos[llave],
                                         ("<- %s" % viejo) if viejo else ""))
        else:
            salida.append(linea)

    try:
        with open(destino, "w", encoding="latin-1", newline="\r\n") as f:
            f.write("\n".join(salida) + "\n")
    except OSError:
        return None
    return destino
