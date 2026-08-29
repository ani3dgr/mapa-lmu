# -*- coding: utf-8 -*-
"""
El aviso de coche parado, con antelacion.

QUE HACE Y EN QUE SE DIFERENCIA DE UN SPOTTER
Un spotter normal avisa por proximidad: te dice que tienes a alguien al
lado cuando ya lo tienes al lado. Esto es otra cosa: como el programa sabe
por donde va cada coche EN EL TRAZADO, puede avisar de un coche parado
mientras todavia estas a diez segundos, que es cuando aun se puede hacer
algo. Es la diferencia entre "cuidado" y "ya te lo has llevado por
delante".

POR QUE SE MIDE EN SEGUNDOS Y NO EN METROS
Porque trescientos metros no son lo mismo en la recta de Le Mans que
entrando a una horquilla: en un sitio son tres segundos y en el otro
quince. Al que conduce le importan los segundos, no los metros. Los metros
se miden por el trazado (no en linea recta) y se convierten a segundos con
la velocidad de cada momento.

Medir POR EL TRAZADO tambien evita un error tonto: un coche parado al otro
lado de una horquilla puede estar a treinta metros en linea recta y a medio
kilometro de pista. Ese no es un peligro, y avisar de el seria ruido.

POR QUE NO SE QUEDA PILLADO EL AVISO
Se recalcula en cada lectura, veinte veces por segundo. En cuanto el coche
arranca, deja de estar en la lista de parados y el aviso se va solo. Lo que
si hace falta es lo contrario: que no PARPADEE cuando el coche esta justo
en el limite del margen. Para eso el aviso, una vez encendido, aguanta un
minimo en pantalla y no se apaga hasta que el peligro se aleja bastante mas
de lo que hizo falta para encenderlo.
"""

# Un coche a menos de esto se considera parado; lo decide comparador.py, que
# es quien lleva la cuenta de las lecturas seguidas.

# Cuanto mas lejos tiene que irse el peligro para que el aviso se apague, en
# proporcion a lo que hizo falta para encenderlo. Sin esto, un coche justo en
# el limite hace que el cartel parpadee y eso distrae mas que ayuda.
HISTERESIS = 1.4

# Lo que aguanta el aviso en pantalla como minimo, en segundos. Da tiempo a
# leerlo aunque el peligro desaparezca al instante.
MINIMO = 1.5

# Por debajo de esta velocidad no se avisa: si vas parado o rodando muy
# despacio, cualquier cosa queda "a muchisimos segundos" y el aviso no dice
# nada util. En metros por segundo (unos 40 km/h).
VELOCIDAD_MINIMA = 11.0

# Mas alla de esto no se mira, por mucho que se configure: avisar de algo que
# esta a un minuto no sirve para nada y en circuitos cortos acabaria avisando
# de un coche que tienes DETRAS, dando la vuelta entera.
TOPE = 30.0


def _por_delante(mi_dist, su_dist, largo):
    """
    Metros de pista que hay hasta un coche que va por delante.

    Se mide siempre hacia adelante y dando la vuelta al circuito si hace
    falta, porque las distancias del juego se reinician en la linea de meta
    y sin esto un coche cien metros mas alla de la meta parece estar a un
    circuito entero de distancia.
    """
    if not largo or largo <= 0:
        return None
    hueco = (su_dist - mi_dist) % largo
    return hueco


def peligros(coches, parados, largo, mi_kmh, margen_seg):
    """
    Los coches parados que tienes por delante, del mas cercano al mas lejano.

    Devuelve [{"nombre", "metros", "segundos", "clase"}, ...] ya filtrado
    por el margen que se haya configurado.

    `parados` es lo que devuelve comparador.parados(): los que llevan varias
    lecturas seguidas sin moverse y no estan en boxes.
    """
    if not parados or not largo:
        return []
    if mi_kmh is None or mi_kmh / 3.6 < VELOCIDAD_MINIMA:
        return []

    yo = next((c for c in coches if c.get("es_yo")), None)
    if yo is None or yo.get("dist") is None:
        return []

    mi_ms = mi_kmh / 3.6
    limite = min(margen_seg, TOPE)
    salida = []
    for c in coches:
        if c.get("es_yo") or c.get("nombre") not in parados:
            continue
        if c.get("dist") is None:
            continue
        metros = _por_delante(yo["dist"], c["dist"], largo)
        if metros is None:
            continue
        segundos = metros / mi_ms
        if segundos <= limite:
            salida.append({"nombre": c.get("nombre") or "",
                           "clase": c.get("clase") or "",
                           "metros": metros, "segundos": segundos})
    salida.sort(key=lambda p: p["segundos"])
    return salida


class Vigia:
    """
    Lleva la cuenta de si hay que ensenar el aviso o no.

    Se le va dando lo que se ve en cada lectura y el responde con el peligro
    que toca ensenar, o None. La histeresis y el minimo en pantalla viven
    aqui dentro para que quien dibuja no tenga que saber de esto.
    """

    def __init__(self):
        self.encendido = False
        self.desde = 0.0
        self.ultimo = None

    def mirar(self, ahora, coches, parados, largo, mi_kmh, margen_seg):
        """Devuelve el peligro a ensenar, o None si no hay que ensenar nada."""
        limite = margen_seg * (HISTERESIS if self.encendido else 1.0)
        lista = peligros(coches, parados, largo, mi_kmh, limite)

        if lista:
            if not self.encendido:
                self.encendido = True
                self.desde = ahora
            self.ultimo = lista[0]
            return self.ultimo

        # Ya no hay peligro. Se mantiene lo ultimo un momento para que de
        # tiempo a leerlo, y luego se apaga.
        if self.encendido and ahora - self.desde < MINIMO:
            return self.ultimo
        self.encendido = False
        self.ultimo = None
        return None

    def acaba_de_encenderse(self, ahora):
        """True solo en la lectura en que se enciende: para tocar el sonido."""
        return self.encendido and ahora - self.desde < 0.001
