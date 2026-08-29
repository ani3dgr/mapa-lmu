# -*- coding: utf-8 -*-
"""
Modo comparacion: te mide contra la vuelta mas rapida de los rivales.

Como funciona:
  - Se parte el circuito en tramos iguales y se mide la velocidad media de cada
    coche en cada tramo.
  - Cuando un rival cruza la meta, su vuelta queda cerrada. Si es la mas rapida
    vista hasta ahora DE TU MISMA CATEGORIA, pasa a ser la REFERENCIA. Un LMP2
    no sirve de liston para un GT3: son coches distintos y la comparacion no
    dice nada. Si el juego no publica la clase se compara contra todos, como
    antes.
  - Tus tramos se comparan contra esa referencia y el color se decide en cada
    fotograma, nunca se guarda. Asi, si mas tarde alguien mejora la referencia,
    TODA tu vuelta se recolorea sola contra el nuevo liston.
  - Tus tramos no se borran al cruzar meta: cada uno guarda la ultima vez que
    pasaste por el y solo se actualiza cuando vuelves a pisarlo. De un vistazo
    ves donde estas perdiendo tiempo aunque no acabes de pasar por alli.

El registro corre SIEMPRE desde que se abre el programa, este o no visible el
modo: las posiciones ya se leen para pintar el mapa, asi que medir no cuesta
nada y al activar el modo suele haber ya una referencia lista.

Limitacion honesta: solo valen vueltas dadas con el PROGRAMA ABIERTO. El juego
publica el tiempo de la mejor vuelta de cada coche, pero no a que velocidad fue
en cada punto, asi que una vuelta anterior no se puede reconstruir.
"""
import idiomas
import lector_lmu as lmu
import re

TRAMOS = 100              # en cuantos trozos se parte la vuelta
TOLERANCIA_KMH = 2.0      # menos de esto de diferencia cuenta como ir igual
COBERTURA_MIN = 0.75      # fraccion de tramos medidos para dar una vuelta por buena
ESPERA_TIEMPO = 0.8       # s de margen hasta que el juego publica el tiempo de vuelta
VELOCIDAD_MAX = 400.0     # km/h; por encima es un dato corrupto
AVISO_SEGUNDOS = 6.0      # cuanto se muestra el aviso de nueva referencia
MARGEN_REFERENCIA = 1.03  # una vuelta no vale de referencia si se aleja mas de
                          # un 3% de la mejor vuelta que publica el juego
MARGEN_SALIDA = 0.8       # m por fuera del borde antes de dar la salida por buena.
                          # Es el valor por defecto: se puede cambiar en vivo
                          # desde las opciones, porque el punto justo depende
                          # del circuito y de como este puesto cada borde.
                          # Medido en pista: la mitad de las detecciones con
                          # margen 0,4 eran coches 20 cm fuera, o sea pisando el
                          # piano en la trazada normal. Con 1,5 m quedan solo las
                          # salidas de verdad (127 detecciones se quedaron en 17).
LECTURAS_DENTRO = 5             # lecturas seguidas dentro para dar la salida por terminada
VELOCIDAD_PARADO = 40.0         # km/h; por debajo de esto en pista es una anomalia:
                                # los coches medidos en carrera van a 120-180 y ni
                                # las horquillas mas lentas bajan de 45
LECTURAS_PARADO = 3             # lecturas seguidas, para no marcar un frenazo
LECTURAS_SALIDA = 2       # lecturas seguidas fuera, para no cazar bordillos


class PerfilRodante:
    """
    Velocidad media de cada tramo, con memoria entre vueltas.

    Cada tramo recuerda de que vuelta es su dato. Al volver a pisarlo en una
    vuelta nueva se descarta lo anterior y se mide de cero, asi que el perfil
    siempre tiene la ULTIMA vez que se paso por cada sitio. Eso es lo que hace
    que el mapa no se quede en blanco al cruzar meta.
    """

    def __init__(self):
        self.suma = [0.0] * TRAMOS
        self.veces = [0] * TRAMOS
        self.vuelta = [-1] * TRAMOS

    def anota(self, tramo, kmh, vuelta):
        if self.vuelta[tramo] != vuelta:
            self.suma[tramo] = 0.0
            self.veces[tramo] = 0
            self.vuelta[tramo] = vuelta
        self.suma[tramo] += kmh
        self.veces[tramo] += 1

    def perfil(self):
        return [self.suma[i] / self.veces[i] if self.veces[i] else None
                for i in range(TRAMOS)]

    def cobertura(self, vuelta):
        """Que parte de la vuelta indicada se llego a medir de verdad."""
        return sum(1 for i in range(TRAMOS)
                   if self.vuelta[i] == vuelta and self.veces[i]) / float(TRAMOS)


class Comparador:
    def __init__(self, largo_pista, sesion=None, circuito=""):
        # El nombre del circuito se guarda para poder saber que has cambiado
        # de sitio. Antes solo se miraba el largo y la sesion, y eso falla
        # entre dos variantes del mismo circuito: Silverstone WEC y
        # Silverstone ELMS se llevan veintidos metros y las dos pueden ser
        # "practica", asi que el programa creia que seguias donde estabas y
        # arrastraba las salidas de pista de la sesion anterior. Salian
        # triangulos de aviso nada mas entrar, sin haber rodado.
        self.circuito = circuito or ""
        self.largo = max(float(largo_pista), 1.0)
        self.sesion = sesion        # cambiar de sesion obliga a empezar de cero
        self.coches = {}            # nombre del piloto -> su seguimiento
        self.referencia = None      # {"nombre", "dorsal", "tiempo", "perfil"}
        self.mi_perfil = [None] * TRAMOS
        self.salidas = {}           # tramo -> {"x", "z", "vuelta"}
        self.usar_flag_juego = False  # False = tambien avisa por geometria
        self._fuera_seguidas = 0
        self._valida_antes = None
        self._penas_antes = None
        self.margen_salida = MARGEN_SALIDA   # ajustable desde las opciones
        self._en_salida = False      # ya se aviso de la salida que esta en curso
        self._dentro_seguidas = 0
        self.mejor_sesion = 0.0     # mejor vuelta de tu clase que publica el juego
        self.mi_clase = ""          # tu categoria; "" si el juego no la da
        self.aviso = ""
        self.aviso_hasta = 0.0

    # ---------- ciclo principal ----------
    def _misma_clase(self, c):
        """Si ese coche corre en tu categoria. Sin clase conocida, todos valen."""
        if not self.mi_clase:
            return True
        return lmu.familia(c.get("clase") or "") == self.mi_clase

    def actualiza(self, coches, ahora):
        # Tu categoria, antes de nada: de ella depende contra quien te mides.
        # Se guarda la ultima conocida y no se borra si en una lectura suelta no
        # apareces (paso por boxes), que si no la referencia se iria y volveria.
        for c in coches:
            if c.get("es_yo"):
                mia = lmu.familia(c.get("clase") or "")
                if mia and mia != self.mi_clase:
                    self.mi_clase = mia
                    # lo que hubiera de otra categoria ya no sirve de liston
                    if self.referencia and self.referencia.get("clase") != mia:
                        self.referencia = None
                break

        for c in coches:
            # La clave es el NOMBRE, no la posicion en la lista: el juego
            # reordena esa lista segun los puestos en carrera, y siguiendo el
            # indice se pierde el hilo de un coche en cuanto le adelantan
            # (y con el, todos sus tramos ya medidos).
            clave = c.get("nombre") or ""
            if not clave:
                continue

            st = self.coches.get(clave)
            if st is None:
                self.coches[clave] = {"dist": c["dist"], "t": ahora, "vuelta": 0,
                                      "perfil": PerfilRodante(), "pendiente": None,
                                      "kmh": None}
                continue

            self._resolver_pendiente(st, c, ahora)

            antes, ahora_d = st["dist"], c["dist"]

            # El mapa consulta 20 veces por segundo pero el juego solo publica
            # 5, asi que 3 de cada 4 lecturas repiten el dato anterior. Si se
            # avanzara el reloj en esas, al llegar el dato bueno se dividiria el
            # avance real entre un tiempo cuatro veces menor y la velocidad
            # saldria por las nubes. Aqui se espera a que el dato cambie.
            if ahora_d == antes:
                continue
            dt = ahora - st["t"]
            if dt <= 0:
                continue

            if ahora_d < antes - self.largo * 0.5:
                # ha cruzado la meta: la vuelta queda cerrada, pero el tiempo
                # tarda un instante en publicarse, asi que se deja en espera
                st["pendiente"] = {"vuelta": st["vuelta"], "t": ahora,
                                   "nombre": c["nombre"], "es_yo": c["es_yo"],
                                   "dorsal": dorsal(c.get("vehiculo", ""))}
                st["vuelta"] += 1
            elif ahora_d > antes:
                tramo = int(ahora_d / self.largo * TRAMOS) % TRAMOS
                kmh = (ahora_d - antes) / dt * 3.6
                if 0 <= kmh < VELOCIDAD_MAX:
                    st["kmh"] = kmh
                if 0 < kmh < VELOCIDAD_MAX:
                    st["perfil"].anota(tramo, kmh, st["vuelta"])
                if c["es_yo"]:
                    self._vigila_salida(c, tramo, st["vuelta"])

            st["dist"], st["t"] = ahora_d, ahora
            if c["es_yo"]:
                self.mi_perfil = st["perfil"].perfil()

        mejores = [c["mejor"] for c in coches
                   if c.get("mejor", 0) > 0 and self._misma_clase(c)]
        if mejores:
            self.mejor_sesion = min(mejores)

        if self.aviso and ahora > self.aviso_hasta:
            self.aviso = ""

    def _vigila_salida(self, c, tramo, vuelta):
        """
        Marca donde te saliste de la pista.

        Por defecto se usa el VEREDICTO DEL JUEGO (`mCountLapFlag`): vale 2
        mientras la vuelta cuenta y baja en cuanto el juego la invalida por
        pasarte de los limites. Se marca el instante del cambio, que es
        justo donde ocurrio. Asi el mapa dice exactamente lo mismo que el
        juego, ni un aviso de mas ni de menos.

        Alternativa (usar_flag_juego = False): detectarlo por geometria, con
        `mPathLateral` contra `mTrackEdge`. Es mas sensible -- caza cualquier
        rueda fuera aunque el juego no diga nada -- pero entonces el mapa y el
        juego pueden no coincidir.

        El aviso de un tramo se borra en cuanto vuelves a pasar por el: si te
        vuelves a salir se pone uno nuevo, y si no, desaparece.
        """
        vieja = self.salidas.get(tramo)
        if vieja and vieja["vuelta"] != vuelta:
            del self.salidas[tramo]

        motivo = None

        # 1) el juego anula la vuelta (practicas y clasificacion)
        valida = c.get("vuelta_valida")
        if valida is not None:
            antes, self._valida_antes = self._valida_antes, valida
            if antes is not None and antes >= 2 and valida < 2:
                motivo = "vuelta anulada"

        # 2) el juego sanciona. En CARRERA no anula la vuelta, penaliza, asi
        #    que sin esto las salidas en carrera no se marcaban nunca.
        penas = c.get("penalizaciones")
        if penas is not None:
            antes_p, self._penas_antes = self._penas_antes, penas
            if motivo is None and antes_p is not None and penas > antes_p:
                motivo = "sancion"

        # 3) red de seguridad por geometria: caza cualquier rueda fuera aunque
        #    el juego no diga nada. Se puede desactivar desde las opciones.
        lateral, borde = c.get("lateral"), c.get("borde")
        if lateral is not None and borde not in (None, 0.0):
            fuera = abs(lateral) > abs(borde) + self.margen_salida
            if fuera:
                self._fuera_seguidas += 1
                self._dentro_seguidas = 0
            else:
                self._dentro_seguidas += 1
                if self._dentro_seguidas >= LECTURAS_DENTRO:
                    # de vuelta en pista un rato: la salida se da por terminada
                    # y la siguiente contara como una nueva
                    self._fuera_seguidas = 0
                    self._en_salida = False
            if (motivo is None and not self.usar_flag_juego and fuera
                    and self._fuera_seguidas >= LECTURAS_SALIDA):
                motivo = "rueda fuera"

        # La bandera de "ya estoy en una salida" se aplica a los TRES
        # motivos, no solo al de la geometria. Una misma salida la cazan dos
        # caminos con menos de un segundo de diferencia: primero la
        # geometria ve la rueda fuera y despues el juego anula la vuelta.
        # Marcando los dos salian el doble de triangulos de los que uno se
        # habia salido, y en un circuito con los limites justos eso llena el
        # mapa. Medido en pista: 17 avisos para 8 salidas reales.
        if motivo and self._en_salida:
            motivo = None

        if motivo:
            self._en_salida = True
            # Una salida larga da muchas lecturas seguidas; el agrupado lo lleva
            # la bandera _en_salida, que solo se suelta al volver a pista un
            # rato. Antes se agrupaba por metros de pista y eso se comia
            # salidas distintas que ocurrian seguidas en el mismo tramo.
            # se guarda la posicion real del coche: asi el aviso cae solo del
            # lado por el que te saliste, sin tener que deducirlo
            self.salidas[tramo] = {"x": c["x"], "z": c["z"],
                                   "vuelta": vuelta, "motivo": motivo}

    def _resolver_pendiente(self, st, c, ahora):
        """Recoge el tiempo de una vuelta recien cerrada y decide si es la mejor."""
        pen = st["pendiente"]
        if not pen or ahora - pen["t"] < ESPERA_TIEMPO:
            return
        st["pendiente"] = None

        if pen["es_yo"]:
            return                                  # la referencia es de rivales
        if not self._misma_clase(c):
            return                                  # otra categoria: no compara
        tiempo = c["ultima"]
        if tiempo <= 0 or st["perfil"].cobertura(pen["vuelta"]) < COBERTURA_MIN:
            return                                  # vuelta incompleta o sin tiempo
        if self.referencia and tiempo >= self.referencia["tiempo"]:
            return

        # Sin este filtro, al arrancar el programa a mitad de carrera el primer
        # rezagado que cruzase meta se quedaba de referencia con su 2:10 hasta
        # que alguien decente cerrara vuelta. El juego publica la mejor vuelta
        # de cada coche aunque nosotros no la hayamos grabado, asi que se sabe
        # de sobra que ritmo se lleva de verdad.
        if self.mejor_sesion > 0 and tiempo > self.mejor_sesion * MARGEN_REFERENCIA:
            return

        mejora = self.referencia is not None
        self.referencia = {"nombre": pen["nombre"], "tiempo": tiempo,
                           "dorsal": pen["dorsal"],
                           "clase": lmu.familia(c.get("clase") or ""),
                           "perfil": st["perfil"].perfil()}
        self.aviso = idiomas.t("cmp.mejor_tiempo" if mejora
                               else "cmp.referencia") % (
            pen["dorsal"] or pen["nombre"], reloj(tiempo))
        self.aviso_hasta = ahora + AVISO_SEGUNDOS

    # ---------- lo que consulta el mapa ----------
    def texto_estado(self):
        if self.aviso:
            return self.aviso
        if not self.referencia:
            return idiomas.t("cmp.registrando")
        return "%s   %s" % (self.referencia["dorsal"] or self.referencia["nombre"],
                            reloj(self.referencia["tiempo"]))

    def colores(self):
        """
        Para cada tramo: 'lento', 'igual', 'rapido' o None si no hay con que
        compararlo. Se calcula al vuelo y nunca se guarda: por eso al cambiar la
        referencia se recolorea sola toda la vuelta contra el nuevo mejor coche.
        """
        if not self.referencia:
            return [None] * TRAMOS
        salida = []
        for mio, suyo in zip(self.mi_perfil, self.referencia["perfil"]):
            if mio is None or suyo is None:
                salida.append(None)
            elif mio > suyo + TOLERANCIA_KMH:
                salida.append("rapido")
            elif mio < suyo - TOLERANCIA_KMH:
                salida.append("lento")
            else:
                salida.append("igual")
        return salida


    def parados(self, coches):
        """
        Coches detenidos o casi, en plena pista.

        Nace como aviso de bandera amarilla, pero se comprobo en pista que
        **LMU no publica las banderas en la memoria compartida**: mGamePhase se
        queda en verde, mYellowFlagState en 0, mIndividualPhase nunca pasa a 10
        y el buffer de reglas esta vacio. Asi que no se espera al aviso del
        juego: se busca directamente el coche parado, que es el peligro real
        haya bandera o no.

        Se pide que este parado varias lecturas seguidas para no marcar a
        cualquiera que de un frenazo fuerte.
        """
        marcados = set()
        for c in coches:
            nombre = c.get("nombre") or ""
            st = self.coches.get(nombre)
            if st is None:
                continue
            if c.get("en_boxes"):
                st["quieto"] = 0
                continue
            kmh = st.get("kmh")
            if kmh is None:
                continue
            if kmh < VELOCIDAD_PARADO:
                st["quieto"] = st.get("quieto", 0) + 1
                if st["quieto"] >= LECTURAS_PARADO:
                    marcados.add(nombre)
            else:
                st["quieto"] = 0
        return marcados


def dorsal(nombre_vehiculo):
    """'Heart of Racing Team 2026 #23:WEC' -> '#23'"""
    hallado = re.search(r"#\s*(\d+)", nombre_vehiculo or "")
    return "#" + hallado.group(1) if hallado else ""


def reloj(segundos):
    """127.621 -> 2:07.621"""
    if segundos <= 0:
        return "--:--"
    m = int(segundos // 60)
    return "%d:%06.3f" % (m, segundos - m * 60)
