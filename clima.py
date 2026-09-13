# -*- coding: utf-8 -*-
"""
El tiempo que hace y el que va a hacer.

DE DONDE SALE CADA COSA. Son dos fuentes distintas y conviene tenerlo claro:

1. **Lo que hace AHORA** sale de la memoria compartida, igual que las
   posiciones de los coches: temperatura del aire y del asfalto, si llueve,
   cuanto esta mojada la pista, el agarre, el estado del cielo y la hora del
   dia. Se refresca a la vez que el resto del mapa (5 veces por segundo) y no
   cuesta nada, porque el buffer ya esta abierto.

2. **El PRONOSTICO** no esta en la memoria compartida. No lo publica. Esta en
   la API web que el juego levanta en su propio ordenador para su interfaz
   (`http://localhost:6397/rest/sessions/weather`), la misma de la que la
   pantalla del garaje saca el pronostico que se mira en carrera. Y trae mas
   de lo que esa pantalla ensena: **las tres sesiones a la vez**, asi que en
   los libres ya se puede ver lo que va a caer EN LA CARRERA.

   Viene en cinco puntos por sesion -salida, 25 %, 50 %, 75 % y final- con el
   estado del cielo, la probabilidad de lluvia, la temperatura, la humedad y
   el viento de cada uno. Y lo da ya traducido al idioma del juego, aunque
   aqui se usan los textos del programa para que la traduccion sea la del
   programa y no la del juego, que no siempre es el mismo idioma.

   Se consulta en un hilo aparte y despacio (cada 20 segundos): es una
   peticion HTTP, y aunque sea a la propia maquina, JAMAS puede hacerse en el
   bucle del mapa. Si el juego tardara en contestar se quedaria el mapa
   congelado en medio de una curva.

LOS ESTADOS DEL CIELO van del 0 al 10 y son los del propio juego, con los
nombres de su diccionario de idiomas (`Support/Languages/spanish.dic`):

    0 Despejado              5 Nublado y llovizna
    1 Ligeramente nublado    6 Nublado y lluvia ligera
    2 Parcialmente nublado   7 Cubierto y lluvia ligera
    3 Mayormente nublado     8 Cubierto y lluvia moderada
    4 Cubierto               9 Cubierto y lluvia intensa
                            10 Tormenta

El `WNV_SKY` de la API usa esos numeros tal cual, y ademas trae el nombre
escrito, asi que ahi no hay nada que adivinar.

**Lo que NO vale es leer el cielo del momento en `mCloudCoverage`.** Ese campo
de la memoria compartida da el estado del PUNTO del pronostico en el que va la
sesion, o sea el numero redondeado, y el juego no ensena eso: va pasando de un
punto al siguiente poco a poco. Comprobado contra la pantalla del juego el
12/09/2026 en Barcelona (ver `cielo_ahora`): la pantalla decia "Ligeramente
nublado" y `mCloudCoverage` ya decia 0, Despejado. Interpolando entre los dos
puntos que rodean el momento sale lo mismo que lee el jugador.

Y OJO CON EL AGARRE: `mTrackGripLevel` empieza a contar en 1 y no en cero (ver
AGARRE). Contando desde cero salia siempre un nivel mas de lo que hay.
"""
import json
import threading
import time
import urllib.request

import idiomas

T = idiomas.t

# La API local del juego. El puerto es fijo y es el que usa su propia
# interfaz; 6398 es el hermano en modo websocket y no nos sirve.
#
# **127.0.0.1 y NO "localhost".** Medido el 12/09/2026: en este Windows
# "localhost" resuelve primero a IPv6 (::1) y el juego solo escucha en IPv4,
# asi que cada intento se comia la espera entera en el ::1 antes de probar la
# direccion buena -tardaba el doble en darse por vencido (4 s en vez de 2)- y
# con el juego lento podia no llegar nunca a preguntar por IPv4.
_API = "http://127.0.0.1:6397"
URL_PRONOSTICO = _API + "/rest/sessions/weather"
# Antes de creerse un pronostico hay que preguntar si hay sesion cargada. Ver
# el porque en `Pronostico._bucle`: sin sesion, el juego contesta al de clima
# con restos de lo anterior.
URL_SESION = _API + "/rest/watch/sessionInfo"
CADA = 20.0                 # segundos entre consultas
ESPERA = 3.0                # segundos de paciencia con la API. Tres y no dos:
                            # el servidor web del juego es suyo y en carrera,
                            # con veinticuatro coches, tarda mas que en el
                            # garaje. Da igual esperar: esto va en su hilo.

# Los cinco puntos de cada sesion, en orden y con su parte de la sesion.
NODOS = [("START", 0.0), ("NODE_25", 0.25), ("NODE_50", 0.50),
         ("NODE_75", 0.75), ("FINISH", 1.0)]

# Los once estados del cielo del juego, del 0 al 10, cada uno con el dibujo
# que le toca. El dibujo lo pinta clima_gui; aqui solo se dice cual.
#
#   nubes: 0 nada, 1 poca, 2 media, 3 mucha, 4 cubierto oscuro
#   gotas: cuantas gotas caen (0 = ninguna)
#   rayo:  si lleva relampago
CIELO = [
    #  clave de texto      nubes gotas rayo
    ("cielo.despejado",        0,   0, False),   # 0
    ("cielo.poco_nublado",     1,   0, False),   # 1
    ("cielo.parcial",          2,   0, False),   # 2
    ("cielo.mayormente",       3,   0, False),   # 3
    ("cielo.cubierto",         4,   0, False),   # 4
    ("cielo.llovizna",         3,   2, False),   # 5
    ("cielo.lluvia_ligera",    3,   3, False),   # 6
    ("cielo.cub_ligera",       4,   3, False),   # 7
    ("cielo.cub_moderada",     4,   5, False),   # 8
    ("cielo.cub_intensa",      4,   7, False),   # 9
    ("cielo.tormenta",         4,   5, True),    # 10
]

# Como de mojada esta la pista, y cuanto llueve. **No son numeros continuos:
# el juego solo usa seis escalones en cada cosa, y cada escalon tiene nombre.**
#
# Esto salio de una sesion preparada a proposito el 13/09/2026 en Interlagos
# (Manuel programo el tiempo para que fuera de despejado a tormenta y se grabo
# todo con `registrar_clima.py`). En 45 minutos de sesion, la humedad de la
# pista tomo EXACTAMENTE seis valores y la lluvia otros seis, ni uno mas:
#
#     mojado : 0   0,05   0,125   0,4   0,6   1
#     lluvia : 0   0,05   0,15    0,3   0,5   1
#
# Y hay exactamente seis nombres de cada cosa. O sea que no hay cortes que
# adivinar: es una correspondencia uno a uno. Cuatro de ellos se comprobaron
# contra la pantalla del juego en marcha (0,05 "Humedo", 0,125 "Poco mojado",
# 1 "Mojado extremo", y en la lluvia 0,05 "Chispeando", 0,15 "Lluvia ligera",
# 1 "Tormenta"); los demas caen solos por su sitio en la lista.
#
# Antes esto eran cortes puestos a ojo, y por suerte daban el mismo resultado.
# Ahora son los valores del juego.
#
# Se busca el escalon MAS CERCANO y no el de debajo, por si alguna version
# publicara valores intermedios: asi nunca se va mas de medio escalon.
MOJADO = [
    (0.000, "pista.seco"),
    (0.050, "pista.humedo"),
    (0.125, "pista.poco_mojado"),
    (0.400, "pista.mojado"),
    (0.600, "pista.bastante_mojado"),
    (1.000, "pista.mojado_extremo"),
]

# Lo mismo para la lluvia que cae. El cero no tiene nombre: no llueve.
LLUVIA = [
    (0.05, "lluvia.chispeando"),
    (0.15, "lluvia.ligera"),
    (0.30, "lluvia.normal"),
    (0.50, "lluvia.moderada"),
    (1.00, "lluvia.tormenta"),
]

# El agarre. **Son CINCO niveles y empieza a contar en cero**, y esto costo
# dos intentos:
#
# El 12/09/2026 en Barcelona la memoria decia 3 y el juego ponia "Alta
# adherencia", el tercero de los cuatro que yo tenia. Se dio por hecho que la
# cuenta empezaba en 1 y se resto uno. Cuadraba, pero por casualidad.
#
# El 13/09/2026 en Interlagos, con la pista recien estrenada, la memoria dijo
# 0 y el juego puso **"Pista limpia"**, un nombre que no estaba en la lista.
# Ahi salio la verdad: en el diccionario del juego, antes de #TG_LOW, hay un
# **#TG_GREEN** que se me habia pasado. Con los cinco nombres y contando desde
# cero cuadran los dos casos: el 0 es "Pista limpia" y el 3 es "Alta
# adherencia". Lo caza Manuel conduciendo, no mirando el codigo.
AGARRE = ["agarre.limpia", "agarre.baja", "agarre.media", "agarre.alta",
          "agarre.optima"]
AGARRE_BASE = 0         # el primer valor que usa el juego

# Que bloque del pronostico le toca a cada sesion del juego. El numero de
# sesion es el de siempre: 0 sin empezar, 1-4 libres, 5-8 clasificacion,
# 9 warmup, 10-13 carrera.
def bloque_de_sesion(sesion):
    try:
        s = int(sesion)
    except (TypeError, ValueError):
        return "RACE"
    if s >= 10:
        return "RACE"
    if s == 9:
        return "RACE"          # el warmup va con el tiempo de la carrera
    if s >= 5:
        return "QUALIFY"
    return "PRACTICE"


def nombre_cielo(valor):
    """El nombre del estado del cielo. Fuera de rango, lo mas parecido."""
    try:
        v = max(0, min(len(CIELO) - 1, int(valor)))
    except (TypeError, ValueError):
        return ""
    return T(CIELO[v][0])


def dibujo_cielo(valor, de_noche=False):
    """
    (nubes, gotas, rayo, de_noche) para que clima_gui sepa que pintar.

    La noche solo cambia una cosa: el sol se convierte en luna. Las nubes y la
    lluvia se pintan igual, que de noche tambien llueve.
    """
    try:
        v = max(0, min(len(CIELO) - 1, int(valor)))
    except (TypeError, ValueError):
        v = 0
    _, nubes, gotas, rayo = CIELO[v]
    return nubes, gotas, rayo, bool(de_noche)


def _mas_cercano(valor, tabla):
    """El nombre del escalon mas proximo al valor que publica el juego."""
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return None
    return min(tabla, key=lambda par: abs(par[0] - v))[1]


def nombre_mojado(humedad):
    clave = _mas_cercano(humedad, MOJADO)
    return T(clave) if clave else ""


def nombre_lluvia(cuanto):
    """
    Como llama el juego a la lluvia que esta cayendo, o "" si no llueve.

    Son las palabras que escribe en su pantalla ("Mayormente nublado,
    Chispeando"), que no son las mismas que las del pronostico: alli van
    juntas con el cielo ("Nublado y llovizna") y aqui van sueltas.
    """
    try:
        v = float(cuanto)
    except (TypeError, ValueError):
        return ""
    if v < 0.025:
        return ""
    return T(_mas_cercano(v, LLUVIA))


def nombre_agarre(nivel):
    try:
        i = int(nivel) - AGARRE_BASE
    except (TypeError, ValueError):
        return ""
    return T(AGARRE[max(0, min(len(AGARRE) - 1, i))])


def cielo_ahora(nodos, ahora):
    """
    El estado del cielo de ESTE instante, interpolando el pronostico.

    POR QUE NO SE USA `mCloudCoverage` A SECAS. El juego publica en la memoria
    compartida el estado del cielo del tramo en el que va, o sea el numero
    redondeado del punto del pronostico. Pero su pantalla no ensena eso: el
    juego va pasando de un punto al siguiente poco a poco, y lo que escribe en
    "clima actual" es el estado intermedio.

    Medido el 12/09/2026 en Barcelona, al 87,6 % de los libres, entre el punto
    del 75 % (Parcialmente nublado, el 2) y el final (Despejado, el 0):

        2 + (0 - 2) x 0,504 = 0,99  ->  Ligeramente nublado

    Y "Ligeramente nublado" era exactamente lo que ponia la pantalla del juego,
    mientras `mCloudCoverage` ya decia 0. Asi que interpolando sale lo mismo
    que lee el jugador, y con el numero de la memoria salia un paso adelantado.

    Si no hay pronostico de esta sesion, o el juego no dice cuanto dura, se
    devuelve lo que traiga la memoria, que es mejor que nada.
    """
    respaldo = (ahora or {}).get("cielo")
    if not nodos or not ahora:
        return respaldo
    fin = ahora.get("fin_sesion") or 0.0
    et = ahora.get("reloj_sesion") or 0.0
    if fin <= 0 or not 0 <= et <= fin * 1.02:
        return respaldo
    parte = max(0.0, min(1.0, et / fin))
    anterior = nodos[0]
    for n in nodos:
        if n["parte"] <= parte:
            anterior = n
        else:
            hueco = n["parte"] - anterior["parte"]
            if hueco <= 0:
                return anterior["cielo"]
            t = (parte - anterior["parte"]) / hueco
            return int(round(anterior["cielo"]
                             + (n["cielo"] - anterior["cielo"]) * t))
    return anterior["cielo"]


def es_de_noche(hora_dia):
    """
    Si a esa hora hay que encender los faros.

    Se toma de las NUEVE de la tarde a las seis de la manana. No es exacto
    -depende del mes y de donde este el circuito, y eso el juego no lo dice-
    pero para elegir entre un sol y una luna sobra.

    Estaba en las ocho y se corrio a las nueve: el mundial se corre en
    primavera y verano en Europa, donde a las ocho de la tarde es de dia de
    sobra. Una carrera de 6 h que acaba a las 20:03 del circuito salia con la
    luna puesta en el ultimo punto del pronostico, y por el parabrisas se veia
    el sol. Mas vale quedarse corto por este lado: equivocarse hacia el dia
    solo se nota una hora al anochecer, y equivocarse hacia la noche pinta una
    luna a pleno sol.
    """
    try:
        h = (float(hora_dia) / 3600.0) % 24.0
    except (TypeError, ValueError):
        return False
    return h >= 21.0 or h < 6.0


def reloj(segundos_del_dia):
    """Los segundos desde medianoche que publica el juego, en hh:mm."""
    try:
        s = float(segundos_del_dia) % 86400.0
    except (TypeError, ValueError):
        return "--:--"
    return "%02d:%02d" % (int(s // 3600), int(s % 3600) // 60)


def reloj_real(dentro_de=0.0):
    """
    La hora del reloj del ordenador, o la que sera dentro de un rato.

    Sirve para poner la hora de verdad debajo de la del circuito y poder
    comparar las dos. El rato se cuenta en segundos de SESION, que corren a la
    par que el reloj de pared (medido: la sesion avanza 20 s en 20 s reales).
    El del circuito no: ese va por su cuenta y puede ir a escala.
    """
    try:
        t = time.localtime(time.time() + float(dentro_de or 0.0))
    except (TypeError, ValueError, OSError):
        return ""
    return "%02d:%02d" % (t.tm_hour, t.tm_min)


def cuanto_falta(segundos, corto=False):
    """
    '1h 12m' o '14m', para decir cuanto queda para algo.

    En corto, '1h12': es lo que cabe en una columna del pronostico, que mide
    poco mas de cincuenta pixeles.
    """
    try:
        s = int(max(0, segundos))
    except (TypeError, ValueError):
        return ""
    if s >= 3600:
        return ("%dh%02d" if corto else "%dh %02dm") % (s // 3600,
                                                        (s % 3600) // 60)
    if s >= 60:
        return "%dm" % (s // 60)
    return "%ds" % s


class Pronostico:
    """
    Le pregunta el pronostico al juego cada pocos segundos, en su hilo.

    El hilo se arranca solo la primera vez que alguien pide los datos, asi que
    si nadie enciende el panel del clima el programa no hace ni una peticion.
    Y si el juego esta cerrado, falla en silencio y lo vuelve a intentar:
    `datos()` devuelve None y el panel lo dice.
    """

    def __init__(self):
        self._datos = None
        self._sello = 0.0           # cuando llego lo ultimo (reloj monotono)
        self._hilo = None
        self._fallos = 0
        self._donde = None          # (circuito, puerto) de la sala de la que
                                    # es el pronostico que tenemos guardado

    def arrancar(self):
        if self._hilo is None:
            self._hilo = threading.Thread(target=self._bucle, daemon=True)
            self._hilo.start()

    def datos(self):
        """El pronostico entero, o None si todavia no ha llegado ninguno."""
        self.arrancar()
        return self._datos

    def fresco(self):
        """Si lo ultimo que llego es reciente (menos de un minuto)."""
        return self._datos is not None and time.monotonic() - self._sello < 60.0

    def sesion(self, cual):
        """
        Los cinco puntos de una sesion, en orden, ya masticados:
        [(parte, cielo, lluvia_pct, temp, humedad, viento_kmh), ...]
        """
        d = self.datos()
        if not d:
            return []
        bloque = d.get(cual) or {}
        salida = []
        for clave, parte in NODOS:
            n = bloque.get(clave)
            if not isinstance(n, dict):
                continue
            salida.append({
                "parte": parte,
                "cielo": _num(n.get("WNV_SKY"), 0),
                "lluvia": _num(n.get("WNV_RAIN_CHANCE"), 0),
                "temp": _num(n.get("WNV_TEMPERATURE"), None),
                "humedad": _num(n.get("WNV_HUMIDITY"), None),
                "viento": _texto(n.get("WNV_WINDSPEED")),
                "viento_dir": _texto(n.get("WNV_WINDDIRECTION")),
            })
        return salida

    # ------------------------------------------------------------ el hilo
    def _bucle(self):
        """
        Pregunta primero SI HAY SESION, y solo entonces por el clima.

        Esto no es precaucion de mas, es un fallo cazado el 12/09/2026. En el
        hueco entre salir de un servidor y cargar el siguiente, la API sigue
        contestando al pronostico tan campante, **pero con restos de la sala
        anterior**. Se le dio por bueno y salio un pronostico de carrera
        inventado (cubierto y 16 grados) que no era de ninguna de las dos
        salas. `sessionInfo` en ese momento venia con el circuito y la sesion
        VACIOS, asi que preguntando antes por ahi se ve venir.

        Y ademas se apunta de QUE SALA es el pronostico guardado (circuito y
        puerto del servidor). Al cambiar de sala se tira y se vuelve a pedir,
        para no ensenar ni un segundo el tiempo del sitio de donde vienes.
        """
        while True:
            try:
                donde = self._donde_estamos()
                if donde is None:
                    # Sin sesion no hay pronostico que valga: se borra lo que
                    # hubiera, y el panel dira que espera al juego.
                    self._datos = None
                    self._donde = None
                    self._fallos += 1
                else:
                    if donde != self._donde:
                        self._datos = None      # otra sala, otro tiempo
                        self._donde = donde
                    d = self._pedir(URL_PRONOSTICO)
                    if isinstance(d, dict) and d:
                        self._datos = d
                        self._sello = time.monotonic()
                        self._fallos = 0
            except Exception:
                # El juego cerrado, en carga o sin sesion: no hay nada que
                # hacer salvo volver a preguntar luego. Nunca se propaga, que
                # este hilo no puede morirse.
                self._fallos += 1
            # Si lleva un rato sin contestar se pregunta mas de tarde en tarde,
            # para no estar llamando a una puerta que no hay.
            time.sleep(CADA if self._fallos < 5 else CADA * 3)

    def _donde_estamos(self):
        """
        (circuito, puerto del servidor) si hay sesion cargada, o None.

        El puerto es lo que distingue una sala de otra: el nombre del servidor
        viene vacio en las salas oficiales, y el circuito puede ser el mismo
        (el servidor de practicas de Le Mans y el evento son los dos
        Barcelona, y ahi solo cambio el puerto: 31604 contra 54290).
        """
        d = self._pedir(URL_SESION)
        if not isinstance(d, dict):
            return None
        pista = (d.get("trackName") or "").strip()
        sesion = (d.get("session") or "").strip()
        if not pista or not sesion:
            return None
        return (pista, d.get("serverPort"))

    def _pedir(self, url):
        pet = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(pet, timeout=ESPERA) as r:
            crudo = r.read()
        # utf-8-sig porque la API cuela el BOM delante del JSON, y con utf-8 a
        # secas el json se cae en el primer caracter.
        return json.loads(crudo.decode("utf-8-sig", "replace"))


def _num(campo, por_defecto):
    if isinstance(campo, dict):
        v = campo.get("currentValue")
        if isinstance(v, (int, float)):
            return v
    return por_defecto


def _texto(campo):
    if isinstance(campo, dict):
        v = campo.get("stringValue")
        if isinstance(v, str):
            return v
    return ""


# Una sola instancia para todo el programa: el hilo es uno y las consultas se
# comparten.
pronostico = Pronostico()
