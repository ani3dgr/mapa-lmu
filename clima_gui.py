# -*- coding: utf-8 -*-
"""
El panel del clima: lo que hace ahora y lo que va a hacer.

PARA QUE. En una carrera larga el tiempo decide la estrategia entera, y la
pantalla del juego que lo cuenta hay que ir a buscarla: sale de la vista al
salir a pista y obliga a apartar los ojos de la carretera para leer una tabla.
Esto es lo mismo pero de un vistazo, encima del juego, siempre a la vista y
donde uno lo ponga.

Y ademas ensena lo que la del juego no: **en los libres ya se ve el pronostico
DE LA CARRERA**. Eso sale de la API web del juego (ver clima.py), no de la
memoria compartida.

LOS DIBUJOS SON DIBUJOS, no imagenes. Sol, luna, nubes, gotas y rayo se pintan
con circulos y lineas en el lienzo. Asi el tamano se puede cambiar con una
barra sin que se vea pixelado, no hay archivos de imagen que empaquetar al
compilar, y si manana el juego anade un estado de cielo nuevo se pinta con una
linea de codigo.

Va en su propia ventana, como la bola de fuerzas G y el cartel de aviso: se
arrastra con el raton mientras las opciones estan abiertas.
"""
import tkinter as tk

import clima
import idiomas

T = idiomas.t

CHROMA = "#010203"          # el color que Windows vuelve transparente
GRADO = u"°"

# Medidas a tamano 100. Todo se multiplica por la escala que elija el usuario.
ANCHO_NODO = 54             # lo que ocupa cada punto del pronostico
MARGEN = 8

# De que color es cada nube segun lo tapado que este el cielo.
COLOR_NUBE = {
    1: ("#f4f6fa", "#a9b2bc"),
    2: ("#e9edf3", "#9aa3ad"),
    3: ("#cfd6de", "#828b95"),
    4: ("#9aa3ad", "#6b747e"),
}
PUNTO = u"\u00b7"           # el punto volado que separa rotulos

# Como se llama cada uno de los cinco puntos del pronostico cuando no se le
# puede poner una hora.
NOMBRE_NODO = {
    0.0: "clima.nodo.salida",
    0.25: "clima.nodo.25",
    0.5: "clima.nodo.mitad",
    0.75: "clima.nodo.75",
    1.0: "clima.nodo.final",
}
COLOR_SOL = "#ffd24a"
COLOR_LUNA = "#e8eef7"
COLOR_GOTA = "#4aa8ff"
COLOR_RAYO = "#ffd60a"


class Panel:
    def __init__(self, raiz, cfg, guardar):
        self.cfg = cfg
        self.guardar = guardar
        self.arrastre = None
        self.modo_mover = False
        self._mi_sesion = True

        v = tk.Toplevel(raiz)
        self.v = v
        v.overrideredirect(True)
        v.attributes("-topmost", True)
        v.attributes("-transparentcolor", CHROMA)
        v.attributes("-alpha", float(cfg.get("clima_opacidad", 0.95)))
        v.configure(bg=CHROMA)
        v.withdraw()

        self.lienzo = tk.Canvas(v, bg=CHROMA, highlightthickness=0)
        self.lienzo.pack()
        self.lienzo.bind("<Button-1>", self._empezar_arrastre)
        self.lienzo.bind("<B1-Motion>", self._arrastrar)

    # ------------------------------------------------------------ arrastre
    def _empezar_arrastre(self, e):
        self.arrastre = (e.x, e.y)

    def _arrastrar(self, e):
        if not self.arrastre:
            return
        self.cfg["clima_x"] += e.x - self.arrastre[0]
        self.cfg["clima_y"] += e.y - self.arrastre[1]
        self.v.geometry("+%d+%d" % (self.cfg["clima_x"], self.cfg["clima_y"]))
        self.guardar(self.cfg)

    def colocar(self, moviendo):
        """
        Con las opciones abiertas se ensena aunque el juego no diga nada, con
        un tiempo de muestra, para poder ponerlo en su sitio y elegir tamano
        sin tener que estar en pista.
        """
        self.modo_mover = moviendo
        if moviendo:
            self.pintar(_MUESTRA, _MUESTRA_NODOS, "RACE", False)
        elif not self.cfg.get("clima_ver", False):
            self.esconder()

    def esconder(self):
        if self.modo_mover:
            return
        self.v.withdraw()

    # -------------------------------------------------------------- pintar
    def pintar(self, ahora, nodos, cual_sesion, mi_sesion=True):
        """
        `ahora` es lo que devuelve Scoring.clima() (o None).
        `nodos` es la lista del pronostico que da clima.Pronostico.sesion().
        `cual_sesion` es "PRACTICE", "QUALIFY" o "RACE", para el rotulo.

        `mi_sesion` dice si ese pronostico es el de la sesion que se esta
        corriendo. Importa mucho: solo entonces se pueden poner horas y
        cuentas atras. Ensenando el pronostico de la CARRERA desde los libres
        no se sabe ni cuando empieza ni cuanto dura, asi que ahi los cinco
        puntos se rotulan por lo que son -salida, mitad, final- en vez de
        inventarse una hora que saldria del reloj de la sesion equivocada.
        """
        self._mi_sesion = bool(mi_sesion)
        if not self.cfg.get("clima_ver", False) and not self.modo_mover:
            self.esconder()
            return

        esc = max(0.5, float(self.cfg.get("clima_tam", 100)) / 100.0)
        c = self.lienzo
        c.delete("all")

        ver_ahora = self.cfg.get("clima_ahora", True) and ahora is not None
        ver_pron = self.cfg.get("clima_pronostico", True) and bool(nodos)
        # Con las dos horas, el bloque del pronostico crece lo que mide el
        # segundo renglon. No se aprieta en el hueco que ya habia: apretado,
        # el numero de abajo se pegaba al dibujo del cielo y las dos cosas se
        # leian peor, que es justo lo contrario de para lo que esta.
        self._doble_reloj = (self.cfg.get("clima_reloj", "circuito") == "ambas"
                             and self._mi_sesion)
        crece = 11 if self._doble_reloj else 0

        ancho = int((ANCHO_NODO * 5 + MARGEN * 2) * esc)
        if not ver_pron:
            ancho = int(210 * esc)
        alto = int(MARGEN * esc)

        if ver_ahora:
            alto += int(54 * esc)
        if ver_pron:
            if ver_ahora:
                alto += int(6 * esc)
            alto += int((78 + crece) * esc)
        renglon = self._renglon(ahora, nodos) if ver_pron else None
        if renglon:
            alto += int(22 * esc)
        if not ver_ahora and not ver_pron:
            # Encendido pero sin nada que ensenar (el juego cerrado, o todo
            # apagado en las opciones): un rotulo, para que no parezca que el
            # programa se ha roto.
            alto += int(26 * esc)
        alto += int(MARGEN * esc)

        c.configure(width=ancho, height=alto)
        fondo = self.cfg.get("clima_color_fondo", "#0d1116")
        if self.cfg.get("clima_fondo", True):
            self._caja(c, 0, 0, ancho, alto, fondo, esc)
        else:
            fondo = CHROMA

        y = int(MARGEN * esc)
        if ver_ahora:
            self._pintar_ahora(c, ahora, y, ancho, esc, fondo)
            y += int(54 * esc)
            if ver_pron:
                gris = "#3a424c" if self.cfg.get("clima_fondo", True) else "#6b747e"
                c.create_line(int(MARGEN * esc), y + int(3 * esc),
                              ancho - int(MARGEN * esc), y + int(3 * esc),
                              fill=gris)
                y += int(6 * esc)
        if ver_pron:
            self._pintar_pronostico(c, ahora, nodos, cual_sesion, y, ancho,
                                    esc, fondo)
            y += int((78 + crece) * esc)
        if renglon:
            self._pintar_renglon(c, renglon, y, ancho, esc, fondo)
            y += int(22 * esc)
        if not ver_ahora and not ver_pron:
            self._texto(c, ancho / 2, y + int(12 * esc), T("clima.sin_datos"),
                        "#9aa3ad", int(10 * esc))

        self.v.attributes("-alpha", float(self.cfg.get("clima_opacidad", 0.95)))
        self.v.geometry("%dx%d+%d+%d" % (ancho, alto,
                                         self.cfg.get("clima_x", 60),
                                         self.cfg.get("clima_y", 260)))
        self.v.deiconify()
        self.v.lift()

    # ------------------------------------------------------------- bloques
    def _pintar_ahora(self, c, a, y, ancho, esc, fondo):
        """
        Lo que hace en este momento: el icono grande, los grados y como esta
        la pista.

        Los rotulos van ENCIMA de cada numero y no al lado. Asi el numero se
        lee de un vistazo sin tener que separarlo de su etiqueta, que es de lo
        que se trata: esto se mira de reojo a doscientos por hora.
        """
        self._hora_dia = a.get("hora_dia")
        noche = clima.es_de_noche(a.get("hora_dia"))
        r = 16 * esc
        cx = MARGEN * esc + r
        self._icono(c, cx, y + 22 * esc, r,
                    clima.dibujo_cielo(a.get("cielo"), noche), fondo)

        col = self.cfg.get("clima_color_texto", "#ffffff")
        x = cx + r + 8 * esc
        gris = "#8b949e"

        if self.cfg.get("clima_temps", True):
            # Las dos columnas no van a un hueco fijo: se mide la primera y la
            # segunda se pone detras. En espanol "AIRE" cabia de sobra en los
            # 46 pixeles de siempre, pero en polaco "POWIETRZE" se metia
            # encima de "TOR" y se leia "POWIETRZTOR". Midiendo, cualquier
            # idioma cuadra, tambien los que traduzca alguien manana.
            pequena, grande = int(8 * esc), int(15 * esc)
            columnas = (("clima.aire", a.get("aire")),
                        ("clima.asfalto", a.get("asfalto")))
            salto = 0.0
            for clave, valor in columnas:
                rotulo, numero = T(clave), "%d%s" % (round(valor or 0), GRADO)
                self._texto(c, x + salto, y + 8 * esc, rotulo, gris, pequena,
                            anclaje="w")
                self._texto(c, x + salto, y + 25 * esc, numero, col, grande,
                            "bold", anclaje="w")
                salto += max(46 * esc,
                             self._ancho(rotulo, pequena) + 8 * esc,
                             self._ancho(numero, grande, "bold") + 8 * esc)

        if self.cfg.get("clima_hora", True):
            self._texto(c, ancho - MARGEN * esc, y + 10 * esc,
                        clima.reloj(a.get("hora_dia")), "#c9d1d9",
                        int(12 * esc), "bold", anclaje="e")
            # Y debajo la hora de verdad, si se han pedido las dos.
            #
            # No es un adorno ni una repeticion de lo de abajo: **dentro del
            # juego no hay ningun sitio donde ver la hora real**. Todos los
            # relojes que ensena LMU son del circuito. Quien esta rodando y
            # quiere saber que hora es de verdad -para un relevo, para cenar,
            # para saber si le da tiempo- tiene que mirar el reloj de la
            # muneca, y mirarse la muneca a doscientos por hora es como se
            # sale uno de la pista. Idea de Manuel, 12/09/2026.
            if self.cfg.get("clima_reloj", "circuito") == "ambas":
                self._texto(c, ancho - MARGEN * esc, y + 24 * esc,
                            clima.reloj_real(), "#6f7883", int(9 * esc),
                            anclaje="e")

        # La segunda fila lleva tres cosas y no siempre caben las tres, asi
        # que se reparten por orden de importancia: como esta la pista (lo que
        # decide las gomas), si llueve ahora mismo, y el agarre, que es el que
        # sobra si no hay sitio.
        #
        # Antes iban a sitios fijos y con lluvia se pisaban entre ellas:
        # "BASTANTE MOJADO" es largo, empujaba el agarre a la derecha y este
        # se metia encima del "LLUEVE 60%". Ahora se pinta primero lo de la
        # derecha, se apunta donde acaba el sitio libre, y el agarre solo sale
        # si cabe entero.
        # La segunda fila empieza en el MARGEN, no detras del dibujo: va por
        # debajo de el y ahi no estorba, y asi dispone del ancho entero.
        #
        # Hacia falta: con la pista empapada y lloviendo fuerte, "MOJADO
        # EXTREMO" (122 px) y "LLUVIA MODERADA" (124 px) suman mas de lo que
        # quedaba a la derecha del dibujo, y lo que se caia era justo lo mas
        # importante: como esta la pista. Visto en Interlagos el 13/09/2026.
        fila2 = y + 46 * esc
        xi = MARGEN * esc
        tope = ancho - MARGEN * esc

        # Llueve: se pone COMO LO LLAMA EL JUEGO ("Chispeando", "Lluvia
        # moderada", "Tormenta") y no un porcentaje. El numero no decia nada
        # -¿un 30 % de lluvia es mucho?- y la palabra se entiende sola. Son
        # ademas las mismas que uno lee en la pantalla del juego.
        nombre_lluvia = clima.nombre_lluvia(a.get("lluvia"))
        if nombre_lluvia:
            derecha = nombre_lluvia.upper()
            tam, peso, color_d = int(10 * esc), "bold", COLOR_GOTA
        elif self.cfg.get("clima_viento", False):
            derecha = "%d km/h" % round(a.get("viento") or 0)
            tam, peso, color_d = int(9 * esc), "normal", gris
        else:
            derecha = None
        if derecha:
            self._texto(c, tope, fila2, derecha, color_d, tam, peso,
                        anclaje="e")
            tope -= self._ancho(derecha, tam, peso) + 8 * esc

        if self.cfg.get("clima_pista", True):
            # Tres piezas por orden de importancia, y se pintan mientras
            # quepan: el NOMBRE de como esta la pista, su NUMERO y el AGARRE.
            #
            # El nombre se lee de un vistazo, pero el nombre es cosa nuestra:
            # el juego NO lo ensena en carrera, en su pantalla pone "Mojado
            # 34%", un porcentaje. Esos seis nombres (Seco, Humedo, Poco
            # mojado...) salen de su pantalla de CONFIGURACION, donde se elige
            # como empieza la pista. Por eso va tambien el numero: ese si es
            # comparable con el suyo. Se usa la media del trazado.
            #
            # Y por eso se van cayendo de derecha a izquierda si no caben:
            # mojada, "BASTANTE MOJADO 60%" mas el agarre no entran, y antes
            # se metian encima del "LLUEVE 60%" de la derecha.
            mojado = a.get("mojado") or 0.0
            color = COLOR_GOTA if mojado >= 0.005 else "#8fd694"
            piezas = [
                (clima.nombre_mojado(mojado).upper(), 10, "bold", color),
                ("%d%%" % round(mojado * 100), 10, "bold", color),
                (clima.nombre_agarre(a.get("agarre")), 9, "normal", gris),
            ]
            xx = xi
            for i, (texto, tam, peso, col) in enumerate(piezas):
                if not texto:
                    continue
                letra = int(tam * esc)
                ancho_pieza = self._ancho(texto, letra, peso)
                if xx + ancho_pieza > tope:
                    break
                self._texto(c, xx, fila2, texto, col, letra, peso, anclaje="w")
                xx += ancho_pieza + (5 if i == 0 else 8) * esc

    def _pintar_pronostico(self, c, a, nodos, cual, y, ancho, esc, fondo):
        rotulo = "%s %s %s" % (T("clima.pronostico"), PUNTO,
                               T("clima.sesion." + cual.lower()))
        # Cuando lo que se ensena NO es la sesion que se esta corriendo, el
        # rotulo lo dice. Y no es un adorno: el pronostico que da el juego es
        # **el del servidor al que estas conectado**, asi que un servidor de
        # practicas suelto tambien tiene su carrera configurada por dentro,
        # aunque nadie la corra nunca, y esa carrera no es la tuya. Paso el
        # 12/09/2026: en un servidor de practicas su carrera traia un 90 % de
        # lluvia a mitad, y al entrar en el evento de verdad el pronostico era
        # otro completamente distinto y sin una gota.
        if not self._mi_sesion:
            rotulo += " %s %s" % (PUNTO, T("clima.este_evento"))
        self._texto(c, MARGEN * esc, y + 6 * esc, rotulo.upper(), "#7d8794",
                    int(8 * esc), anclaje="w")

        crece = 11 if getattr(self, "_doble_reloj", False) else 0
        parte, factor = self._donde_vamos(a)
        if not self._mi_sesion:
            parte = None                # no somos esa sesion: no hay "aqui"
        paso = (ancho - 2 * MARGEN * esc) / max(1, len(nodos))
        base = MARGEN * esc
        for i, n in enumerate(nodos):
            cx = base + paso * (i + 0.5)
            aqui = parte is not None and abs(n["parte"] - parte) < 0.125

            if aqui:
                # Un recuadro detras de la columna por la que vamos. Antes era
                # una flechita debajo y no se veia: con el coche en marcha hay
                # que encontrar la columna de un golpe de vista.
                self._caja(c, cx - paso / 2 + 2 * esc, y + 12 * esc,
                           paso - 4 * esc, (66 + crece) * esc,
                           self._realzado(fondo), esc)

            arriba, abajo = self._etiqueta_nodo(a, n, parte, factor)
            self._texto(c, cx, y + 20 * esc, arriba,
                        "#ffffff" if aqui else "#aeb6bf", int(9 * esc),
                        "bold" if aqui else "normal")
            if abajo:
                # La hora de verdad, debajo y en pequeno: quien quiera
                # comparar el pronostico con su reloj lo tiene ahi mismo.
                self._texto(c, cx, y + 31 * esc, abajo, "#6f7883",
                            int(8 * esc))

            # El icono junta las dos cosas que dice el juego de ese momento:
            # como esta el cielo y la probabilidad de lluvia. Con mucha
            # probabilidad se le ponen gotas aunque el cielo venga flojo,
            # porque un 90 % de lluvia dibujado con un sol entre nubes es
            # justo lo contrario de lo que hay que entender de un vistazo.
            pct = n.get("lluvia") or 0
            noche = self._noche_en(a, n, parte, factor)
            nubes, gotas, rayo, _ = clima.dibujo_cielo(n["cielo"], noche)
            if pct >= 50 and not gotas:
                nubes, gotas = max(nubes, 3), 3
            self._icono(c, cx, y + (42 + crece) * esc, 13 * esc,
                        (nubes, gotas, rayo, noche), fondo)

            color = (self.cfg.get("clima_color_aviso", "#ff9f0a")
                     if pct >= 50 else ("#c9d1d9" if pct else "#7d8794"))
            self._texto(c, cx, y + (62 + crece) * esc, "%d%%" % pct, color,
                        int(10 * esc), "bold" if pct >= 50 else "normal")

            if self.cfg.get("clima_temps", True) and n.get("temp") is not None:
                extra = "%d%s" % (n["temp"], GRADO)
                if self.cfg.get("clima_humedad", False) \
                        and n.get("humedad") is not None:
                    extra += "  %d%%" % n["humedad"]
                self._texto(c, cx, y + (74 + crece) * esc, extra, "#7d8794",
                            int(8 * esc))

    def _realzado(self, fondo):
        """Un gris un poco mas claro que el fondo, para el recuadro de 'aqui'."""
        if not self.cfg.get("clima_fondo", True):
            return "#2a3138"
        try:
            r, g, b = (int(fondo[i:i + 2], 16) for i in (1, 3, 5))
        except (ValueError, IndexError):
            return "#242b33"
        return "#%02x%02x%02x" % (min(255, r + 22), min(255, g + 24),
                                  min(255, b + 26))

    # ------------------------------------------------------------- cuentas
    def _donde_vamos(self, a):
        """
        Por que parte de la sesion vamos (0 a 1) y a que velocidad corre el
        reloj del juego.

        El factor es cuantos segundos de reloj del dia pasan por cada segundo
        de sesion. En las 24 h de Le Mans jugadas en 6 h vale 4, y ahi sin
        tenerlo en cuenta el pronostico diria que amanece cuando ya es de dia.
        No se le pregunta al juego: se MIDE, comparando el reloj del dia con
        el de la sesion entre dos lecturas, que es la unica forma que no se
        equivoca en una sala online (la configuracion que publica la API es la
        de tu ordenador, no la del servidor).
        """
        if not a:
            return None, 1.0
        fin = a.get("fin_sesion") or 0.0
        et = a.get("reloj_sesion") or 0.0
        parte = None
        if fin > 0 and 0 <= et <= fin * 1.02:
            parte = max(0.0, min(1.0, et / fin))

        hora, sello = a.get("hora_dia"), et
        antes = getattr(self, "_antes", None)
        factor = getattr(self, "_factor", 1.0)
        if antes and sello - antes[1] > 20.0:
            paso_dia = (hora - antes[0]) % 86400.0
            paso_ses = sello - antes[1]
            if paso_ses > 0:
                medido = paso_dia / paso_ses
                if 0.5 <= medido <= 40.0:
                    factor = medido
                    self._factor = factor
            self._antes = (hora, sello)
        elif not antes:
            self._antes = (hora, sello)
        return parte, factor

    def _etiqueta_nodo(self, a, n, parte, factor):
        """
        Los dos renglones que van encima de un punto del pronostico.

        Devuelve (arriba, abajo), y `abajo` puede ser None.

        Arriba, LA HORA DEL CIRCUITO, que es la del sol que se ve por el
        parabrisas y la misma que ensenan las pantallas del juego. No es la
        hora real: el juego mete la carrera en la franja de tarde del
        circuito (una de 6 h empezada a las 17:23 reales salio a las 14:00 del
        circuito) y encima el reloj del circuito puede ir a escala.

        Abajo, y solo si se pide, LA HORA DE VERDAD, para poder comparar el
        pronostico con el reloj de pared sin hacer cuentas.

        Si no se puede saber cuando le toca a ese punto -el pronostico es de
        otra sesion, o el juego no dice cuanto dura esta- se rotula por lo que
        es el punto: salida, mitad, final.
        """
        seg = self._segundos_hasta(a, n, parte)
        if seg is None:
            return self._nombre_nodo(n), None
        modo = self.cfg.get("clima_reloj", "circuito")
        if modo == "falta":
            # Lo que falta en tiempo REAL de carrera, que es lo que se cuenta
            # para los relevos y las paradas. Lo ya pasado va en negativo.
            return (("+" if seg >= 0 else "-")
                    + clima.cuanto_falta(abs(seg), corto=True)), None
        circuito = clima.reloj((a.get("hora_dia") or 0) + seg * factor)
        if modo == "ambas":
            return circuito, clima.reloj_real(seg)
        return circuito, None

    def _nombre_nodo(self, n):
        clave = NOMBRE_NODO.get(n["parte"])
        return T(clave) if clave else "%d%%" % round(n["parte"] * 100)

    def _segundos_hasta(self, a, n, parte):
        """Segundos de sesion que faltan para ese punto, o None si no se sabe."""
        if parte is None or not a:
            return None
        fin = a.get("fin_sesion") or 0.0
        if fin <= 0:
            return None
        return n["parte"] * fin - (a.get("reloj_sesion") or 0.0)

    def _noche_en(self, a, n, parte, factor):
        seg = self._segundos_hasta(a, n, parte)
        if seg is None or not a:
            return clima.es_de_noche(a.get("hora_dia") if a else None)
        return clima.es_de_noche((a.get("hora_dia") or 0) + seg * factor)

    def _renglon(self, a, nodos):
        """
        El renglon de abajo, que contesta a "vale, ¿y ahora que viene?".

        Devuelve (texto, color, cielo) o None. `cielo` es para dibujar al lado
        el tiempo del que se habla.

        Mirando el panel se sabe que tiempo hace y por que punto del
        pronostico vamos, pero para saber que viene despues hay que buscar la
        columna siguiente y hacer la cuenta de cuanto falta. Eso conduciendo
        no lo hace nadie. Este renglon lo da mascado, y tiene dos formas:

        1. **Si viene agua y todavia no ha llegado**, manda el agua, aunque no
           sea en el punto siguiente sino tres mas alla. Es lo unico del panel
           por lo que merece la pena apartar los ojos de la pista, y por eso
           va en su color.
        2. **Si no**, el punto siguiente del pronostico: que cielo trae y
           cuanto queda para el.

        Pedido por Manuel el 13/09/2026: *"lo que echo en falta es que en
        algun sitio ponga cual es el siguiente clima y cuanto queda para esa
        prediccion"*.
        """
        if not nodos:
            return None
        parte, factor = self._donde_vamos(a)
        if not self._mi_sesion:
            parte = None

        # 1) el agua que viene
        lloviendo = bool(a and (a.get("lluvia") or 0.0) > 0.02)
        if self.cfg.get("clima_aviso_lluvia", True) and not lloviendo:
            for n in nodos:
                if (n.get("lluvia") or 0) < 50:
                    continue
                seg = self._segundos_hasta(a, n, parte)
                color = self.cfg.get("clima_color_aviso", "#ff9f0a")
                if seg is None:
                    # Sin saber CUANDO, se dice DONDE: "LLUVIA 90% - MITAD".
                    return ("%s %d%%  %s  %s" % (T("clima.lluvia"), n["lluvia"],
                                                 PUNTO, self._nombre_nodo(n)),
                            color, n["cielo"])
                if seg > 0:
                    return ("%s %d%%  %s %s" % (T("clima.lluvia"), n["lluvia"],
                                                T("clima.en"),
                                                clima.cuanto_falta(seg)),
                            color, n["cielo"])

        # 2) el punto siguiente, sea el que sea
        if parte is None:
            return None                 # no sabemos por donde vamos
        for n in nodos:
            seg = self._segundos_hasta(a, n, parte)
            if seg is None or seg <= 0:
                continue
            # Si lo que viene trae agua se pinta en azul, que llame la
            # atencion sin llegar a ser el aviso naranja.
            color = COLOR_GOTA if n["cielo"] >= 5 else "#c9d1d9"
            return ("%s  %s %s" % (clima.nombre_cielo(n["cielo"]), PUNTO,
                                   clima.cuanto_falta(seg)), color, n["cielo"])
        return None

    def _pintar_renglon(self, c, renglon, y, ancho, esc, fondo):
        """
        'LUEGO  [dibujo]  Cubierto - 1h 12m', centrado.

        Se mide todo antes de pintar para poder centrar el grupo entero. Con
        el dibujo al lado se entiende de un golpe sin leer: el icono dice que
        va de tiempo, el texto dice cual y cuando.
        """
        texto, color, cielo = renglon
        etiqueta = T("clima.luego")
        peq, normal = int(9 * esc), int(11 * esc)
        r = 8 * esc
        hueco = 6 * esc
        total = (self._ancho(etiqueta, peq) + hueco + 2 * r + hueco
                 + self._ancho(texto, normal, "bold"))
        x = (ancho - total) / 2.0
        medio = y + 11 * esc
        self._texto(c, x, medio, etiqueta, "#7d8794", peq, anclaje="w")
        x += self._ancho(etiqueta, peq) + hueco + r
        noche = clima.es_de_noche(getattr(self, "_hora_dia", None))
        self._icono(c, x, medio, r, clima.dibujo_cielo(cielo, noche), fondo)
        x += r + hueco
        self._texto(c, x, medio, texto, color, normal, "bold", anclaje="w")

    # -------------------------------------------------------------- pintar
    def _caja(self, c, x, y, ancho, alto, color, esc):
        """El fondo, con las esquinas redondeadas a mano."""
        r = int(7 * esc)
        c.create_rectangle(x + r, y, x + ancho - r, y + alto, fill=color,
                           outline=color)
        c.create_rectangle(x, y + r, x + ancho, y + alto - r, fill=color,
                           outline=color)
        for ex, ey in ((x, y), (x + ancho - 2 * r, y),
                       (x, y + alto - 2 * r), (x + ancho - 2 * r, y + alto - 2 * r)):
            c.create_oval(ex, ey, ex + 2 * r, ey + 2 * r, fill=color,
                          outline=color)

    def _icono(self, c, cx, cy, r, dibujo, fondo):
        """
        El dibujo del tiempo. `r` es medio icono.

        Se pinta de atras adelante: primero el sol o la luna, que asoma por
        detras, y encima las nubes y el agua.
        """
        nubes, gotas, rayo, noche = dibujo
        if nubes == 0:
            self._astro(c, cx, cy, r * 0.95, noche, fondo)
        elif nubes <= 3 and not gotas:
            # El sol asomando por arriba a la izquierda. Solo si NO llueve:
            # un dibujo de sol con gotas cayendo no lo lee nadie como lluvia,
            # y "Nublado y llovizna" es nublado, sin sol.
            self._astro(c, cx - r * 0.34, cy - r * 0.38,
                        r * (0.62 if nubes < 3 else 0.5), noche, fondo)
        if nubes >= 1:
            relleno, borde = COLOR_NUBE[nubes]
            escala = 0.72 if nubes == 1 else (0.86 if nubes == 2 else 1.0)
            self._nube(c, cx + r * 0.1, cy + r * 0.22, r * escala,
                       relleno, borde)
        if gotas:
            self._gotas(c, cx + r * 0.1, cy + r * 0.5, r, gotas)
        if rayo:
            self._rayo(c, cx + r * 0.1, cy + r * 0.55, r)

    def _astro(self, c, cx, cy, r, noche, fondo):
        if noche:
            # La luna se hace con dos circulos: uno claro y otro del color del
            # fondo por encima, desplazado. Si el fondo es el transparente, el
            # recorte deja ver el juego y el creciente sale igual de limpio.
            rr = r * 0.56
            c.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, fill=COLOR_LUNA,
                          outline="")
            c.create_oval(cx - rr * 0.45, cy - rr * 1.25,
                          cx + rr * 1.55, cy + rr * 0.75, fill=fondo,
                          outline="")
            return
        rr = r * 0.5
        for i in range(8):
            ang = i * 3.14159 / 4.0
            dx, dy = _sincos(ang)
            c.create_line(cx + dx * rr * 1.35, cy + dy * rr * 1.35,
                          cx + dx * rr * 1.85, cy + dy * rr * 1.85,
                          fill=COLOR_SOL, width=max(1, int(r * 0.11)))
        c.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, fill=COLOR_SOL,
                      outline="")

    def _nube(self, c, cx, cy, r, relleno, borde):
        grosor = max(1, int(r * 0.09))
        bolas = ((-0.42, 0.06, 0.34), (-0.04, -0.16, 0.44), (0.38, 0.04, 0.30))
        for ox, oy, rad in bolas:
            c.create_oval(cx + (ox - rad) * r, cy + (oy - rad) * r,
                          cx + (ox + rad) * r, cy + (oy + rad) * r,
                          fill=relleno, outline=borde, width=grosor)
        # la base, para que no se vean los huecos entre las bolas
        c.create_rectangle(cx - 0.7 * r, cy + 0.02 * r, cx + 0.66 * r,
                           cy + 0.36 * r, fill=relleno, outline=relleno)
        c.create_line(cx - 0.7 * r, cy + 0.36 * r, cx + 0.66 * r,
                      cy + 0.36 * r, fill=borde, width=grosor)

    def _gotas(self, c, cx, cy, r, cuantas):
        # No solo cuantas gotas: tambien mas largas y mas gordas cuanto mas
        # arrecia. Con solo contarlas, un chubasco y un diluvio se parecian
        # demasiado en un icono de trece pixeles de radio.
        if cuantas <= 3:
            grosor, largo = max(1, int(r * 0.11)), r * 0.30
        elif cuantas <= 5:
            grosor, largo = max(1, int(r * 0.13)), r * 0.42
        else:
            grosor, largo = max(2, int(r * 0.16)), r * 0.52
        sitios = [-0.44, 0.0, 0.44, -0.22, 0.22, -0.62, 0.62][:cuantas]
        for i, ox in enumerate(sorted(sitios)):
            desfase = 0.0 if i % 2 == 0 else r * 0.12
            x = cx + ox * r
            c.create_line(x + largo * 0.25, cy + desfase,
                          x - largo * 0.25, cy + largo + desfase,
                          fill=COLOR_GOTA, width=grosor)

    def _rayo(self, c, cx, cy, r):
        p = [cx + 0.10 * r, cy - 0.05 * r,
             cx - 0.18 * r, cy + 0.42 * r,
             cx + 0.02 * r, cy + 0.42 * r,
             cx - 0.10 * r, cy + 0.80 * r,
             cx + 0.26 * r, cy + 0.30 * r,
             cx + 0.06 * r, cy + 0.30 * r,
             cx + 0.22 * r, cy - 0.05 * r]
        c.create_polygon(p, fill=COLOR_RAYO, outline="#8a6d00",
                         width=max(1, int(r * 0.06)))

    def _texto(self, c, x, y, texto, color, tam, peso="normal", anclaje="center"):
        letra = ("Segoe UI", max(6, int(tam)), peso)
        if not self.cfg.get("clima_fondo", True):
            # sin fondo, el texto va sobre el juego y hace falta sombra para
            # que se lea igual encima de un cielo claro o de un muro blanco
            for ox, oy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                c.create_text(x + ox, y + oy, text=texto, font=letra,
                              fill="#000000", anchor=anclaje)
        c.create_text(x, y, text=texto, font=letra, fill=color, anchor=anclaje)

    def _ancho(self, texto, tam, peso="normal"):
        """Lo que mide un texto, para poder poner otro justo detras."""
        clave = (texto, tam, peso)
        cache = getattr(self, "_anchos", None)
        if cache is None:
            cache = self._anchos = {}
        if clave not in cache:
            import tkinter.font as tkfont
            try:
                cache[clave] = tkfont.Font(
                    family="Segoe UI", size=max(6, int(tam)),
                    weight=peso).measure(texto)
            except tk.TclError:
                cache[clave] = int(len(texto) * tam * 0.6)
        return cache[clave]


def _sincos(ang):
    import math
    return math.cos(ang), math.sin(ang)


# Un tiempo de muestra para poder colocar el panel con el juego cerrado.
_MUESTRA = {
    "aire": 21.0, "asfalto": 34.0, "lluvia": 0.0, "nubes": 0.3,
    "cielo": 2, "agarre": 2, "mojado": 0.0, "mojado_min": 0.0,
    "mojado_max": 0.0, "viento": 12.0, "hora_dia": 14 * 3600.0,
    "reloj_sesion": 0.0, "fin_sesion": 0.0,
}

# Y un pronostico de muestra, para que al colocarlo se vea el panel entero
# con su tamano de verdad en vez de media caja.
_MUESTRA_NODOS = [
    {"parte": 0.0, "cielo": 1, "lluvia": 0, "temp": 18, "humedad": 60,
     "viento": "", "viento_dir": ""},
    {"parte": 0.25, "cielo": 2, "lluvia": 10, "temp": 19, "humedad": 62,
     "viento": "", "viento_dir": ""},
    {"parte": 0.50, "cielo": 8, "lluvia": 90, "temp": 17, "humedad": 80,
     "viento": "", "viento_dir": ""},
    {"parte": 0.75, "cielo": 5, "lluvia": 40, "temp": 17, "humedad": 75,
     "viento": "", "viento_dir": ""},
    {"parte": 1.0, "cielo": 3, "lluvia": 0, "temp": 16, "humedad": 70,
     "viento": "", "viento_dir": ""},
]
