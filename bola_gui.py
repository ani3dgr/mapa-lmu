# -*- coding: utf-8 -*-
"""
La bola de reparto de carga: una circunferencia con un punto que se mueve.

QUE ENSENA. El punto se va hacia donde se esta apoyando el peso del coche en
ese instante: hacia arriba al frenar, hacia abajo al acelerar, y hacia el lado
de fuera en las curvas. En el centro, el coche esta repartido como cuando esta
parado.

NO es el centro de gravedad, aunque de ahi salio la idea. El centro de gravedad
de un coche apenas se mueve -solo despacio, segun se vacia el deposito-. Lo que
si se mueve en cada instante, y mucho, es DONDE SE APOYA ese peso, y eso es lo
que dice si el coche se va a ir de morro o de atras. Es lo que se dibuja aqui.

DE DONDE SALE. De la fuerza que mide el juego en cada una de las cuatro
suspensiones (`mSuspForce`). No es un calculo con suposiciones: es el peso que
lleva cada esquina, medido. Se dibuja el DESPLAZAMIENTO respecto al coche
parado, porque en reposo un LMP2 ya lleva mas peso detras que delante (48/52) y
sin restar ese reposo la bola nunca estaria centrada.

OJO: la carga del neumatico (`mTireLoad`) seria lo suyo, pero LMU la publica
siempre a cero -medido en marcha el 30/08/2026-, asi que se usa la de la
suspension.

Va en su propia ventana, como el cartel de aviso, para poder ponerla donde uno
quiera: se arrastra con el raton mientras las opciones estan abiertas.
"""
import tkinter as tk

import idiomas

T = idiomas.t

CHROMA = "#010203"          # el color que Windows vuelve transparente


class Bola:
    def __init__(self, raiz, cfg, guardar):
        self.cfg = cfg
        self.guardar = guardar
        self.arrastre = None
        self.modo_mover = False
        self.cero = None            # el reparto del coche parado

        v = tk.Toplevel(raiz)
        self.v = v
        v.overrideredirect(True)
        v.attributes("-topmost", True)
        v.attributes("-transparentcolor", CHROMA)
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
        self.cfg["bola_x"] += e.x - self.arrastre[0]
        self.cfg["bola_y"] += e.y - self.arrastre[1]
        self.v.geometry("+%d+%d" % (self.cfg["bola_x"], self.cfg["bola_y"]))
        self.guardar(self.cfg)

    def colocar(self, moviendo):
        """Con las opciones abiertas se ensena aunque no se este rodando, para
        poder ponerla en su sitio sin tener que salir a pista."""
        self.modo_mover = moviendo
        if moviendo:
            self.pintar(0.0, 0.0, None)
        elif not self.cfg.get("bola_ver", True):
            self.esconder()

    def esconder(self):
        if self.modo_mover:
            return
        self.v.withdraw()

    # -------------------------------------------------------------- pintar
    def pintar(self, dx, dy, reparto):
        """
        `dx` y `dy` van de -1 a 1: cuanto se ha ido el peso a un lado y hacia
        delante. `reparto` es (delante%, izquierda%) para los numeros, o None.
        """
        if not self.cfg.get("bola_ver", True) and not self.modo_mover:
            self.esconder()
            return

        tam = int(self.cfg.get("bola_tam", 120))
        c = self.lienzo
        c.delete("all")
        c.configure(width=tam, height=tam)
        centro = tam / 2.0
        radio = centro - 6

        if self.cfg.get("bola_circulo", True):
            color = self.cfg.get("bola_color_circulo", "#b0b0b0")
            c.create_oval(centro - radio, centro - radio, centro + radio,
                          centro + radio, outline="#000000", width=3)
            c.create_oval(centro - radio, centro - radio, centro + radio,
                          centro + radio, outline=color, width=1)
            # media escala, para tener una referencia de cuanto es mucho
            m = radio / 2.0
            c.create_oval(centro - m, centro - m, centro + m, centro + m,
                          outline=color, width=1, dash=(2, 4))
            for a, b in ((centro - radio, centro), (centro + radio, centro),
                         (centro, centro - radio), (centro, centro + radio)):
                c.create_line(centro, centro, a, b, fill=color, dash=(2, 6))

        # el punto: se recorta al borde para que no se salga del dibujo
        d = (dx * dx + dy * dy) ** 0.5
        if d > 1.0:
            dx, dy = dx / d, dy / d
        px, py = centro + dx * radio, centro - dy * radio
        r = max(4, int(self.cfg.get("bola_tam", 120) * 0.055))
        c.create_oval(px - r - 2, py - r - 2, px + r + 2, py + r + 2,
                      outline="#000000", width=3)
        c.create_oval(px - r, py - r, px + r, py + r,
                      fill=self.cfg.get("bola_color_punto", "#00ff00"),
                      outline="#000000", width=1)

        if self.cfg.get("bola_numeros", False) and reparto:
            delante, izquierda = reparto
            self._texto(c, centro, 10, "%d%%" % round(delante), tam)
            self._texto(c, centro, tam - 10, "%d%%" % round(100 - delante), tam)
            self._texto(c, 14, centro, "%d%%" % round(izquierda), tam)
            self._texto(c, tam - 14, centro, "%d%%" % round(100 - izquierda), tam)

        self.v.geometry("%dx%d+%d+%d" % (tam, tam, self.cfg.get("bola_x", 40),
                                         self.cfg.get("bola_y", 40)))
        self.v.deiconify()
        self.v.lift()

    def _texto(self, c, x, y, texto, tam):
        letra = ("Segoe UI", max(7, int(tam * 0.09)), "bold")
        for ox, oy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            c.create_text(x + ox, y + oy, text=texto, font=letra, fill="#000000")
        c.create_text(x, y, text=texto, font=letra,
                      fill=self.cfg.get("bola_color_numeros", "#ffffff"))
