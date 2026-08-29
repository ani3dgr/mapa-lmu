# -*- coding: utf-8 -*-
"""
El cartel de aviso que sale encima del juego, y su sonido.

Va en su propia ventanita, aparte del mapa, porque el mapa lo miras cuando
puedes y esto tiene que verte a ti aunque estes mirando el asfalto. Se
coloca donde uno quiera, arrastrandola con el raton mientras las opciones
estan abiertas, igual que el mapa.

POR QUE UN SONIDO Y NO UNA VOZ
Porque una voz hay que fabricarla: el programa tiene que sintetizar la
frase y luego reproducirla, y eso tarda entre medio segundo y un segundo.
Para un aviso de peligro esa demora se come justo el tiempo que el aviso
pretendia ganar. Un .wav ya grabado suena en el instante en que se pide,
sin fabricar nada. Por eso aqui hay pitidos y no palabras.
"""
import os
import tempfile
import time
import tkinter as tk

import idiomas
import rutas

T = idiomas.t

CHROMA = "#010203"          # el color que Windows vuelve transparente
CARPETA = rutas.datos("sonidos")

# Los que vienen con el programa. Quien quiera pone el suyo.
INCLUIDOS = ["bip.wav", "doble.wav", "alarma.wav"]


def sonidos_disponibles():
    """Los .wav que haya en la carpeta, vengan con el programa o no."""
    try:
        return sorted(f for f in os.listdir(CARPETA) if f.lower().endswith(".wav"))
    except OSError:
        return list(INCLUIDOS)


def _bajado(ruta, volumen):
    """
    Una copia del sonido mas floja, guardada para no rehacerla cada vez.

    Hace falta rebajar el propio archivo porque winsound no tiene mando de
    volumen: toca el .wav tal cual esta. Asi que se hace una copia con las
    muestras multiplicadas y se reproduce esa. Se guarda en la carpeta
    temporal de Windows, que se limpia sola, y se hace una sola vez por
    cada volumen que se elija.
    """
    import struct
    import wave
    destino = os.path.join(tempfile.gettempdir(),
                           "mapalmu_%d_%s" % (volumen, os.path.basename(ruta)))
    if os.path.isfile(destino):
        return destino
    try:
        with wave.open(ruta) as e:
            canales, ancho, hz = e.getnchannels(), e.getsampwidth(), e.getframerate()
            crudo = e.readframes(e.getnframes())
        if ancho != 2:
            return ruta               # solo se sabe rebajar el de 16 bits
        f = volumen / 100.0
        n = len(crudo) // 2
        muestras = struct.unpack("<%dh" % n, crudo)
        bajas = struct.pack("<%dh" % n,
                            *(int(max(-32768, min(32767, m * f))) for m in muestras))
        with wave.open(destino, "w") as s:
            s.setnchannels(canales)
            s.setsampwidth(ancho)
            s.setframerate(hz)
            s.writeframes(bajas)
        return destino
    except Exception:
        return ruta                   # si algo falla, mejor fuerte que mudo


def tocar(nombre, volumen=100, encendido=True):
    """
    Suena un aviso, sin bloquear.

    Se usa winsound porque va incluido en Windows y no necesita instalar
    nada. Con SND_ASYNC devuelve el control al instante: si esto esperase a
    que acabe el pitido, el mapa daria un tiron cada vez que avisa.
    """
    if not nombre or not encendido:
        return
    ruta = nombre if os.path.isabs(nombre) else os.path.join(CARPETA, nombre)
    if not os.path.isfile(ruta):
        return
    volumen = max(0, min(100, int(volumen)))
    if volumen == 0:
        return
    if volumen < 100:
        ruta = _bajado(ruta, volumen)
    try:
        import winsound
        winsound.PlaySound(ruta, winsound.SND_FILENAME | winsound.SND_ASYNC
                           | winsound.SND_NODEFAULT)
    except Exception:
        pass          # sin sonido se sigue viendo el cartel; no es motivo de error


class Cartel:
    """
    La ventanita del aviso.

    Se crea escondida y solo aparece cuando hay algo que decir. Mientras no
    hay peligro no se ve ni ocupa: no es una ventana con el fondo vacio, es
    una ventana retirada de la pantalla.
    """

    def __init__(self, raiz, cfg, guardar):
        self.cfg = cfg
        self.guardar = guardar
        self.visible = False
        self.arrastre = None
        self.modo_mover = False

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
        self.cfg["aviso_x"] += e.x - self.arrastre[0]
        self.cfg["aviso_y"] += e.y - self.arrastre[1]
        self.v.geometry("+%d+%d" % (self.cfg["aviso_x"], self.cfg["aviso_y"]))
        self.guardar(self.cfg)

    def colocar(self, moviendo):
        """
        Con las opciones abiertas se ensena una muestra para poder colocarlo.

        Si no, no habria manera de ponerlo en su sitio: el cartel de verdad
        solo sale cuando hay un coche parado delante, y eso no pasa cuando
        a uno le apetece.
        """
        self.modo_mover = moviendo
        if moviendo:
            self._pintar(T("avi.muestra"), muestra=True)
        elif not self.visible:
            self.esconder()

    # -------------------------------------------------------------- pintar
    def mostrar(self, peligro):
        """Ensena el aviso de un coche parado."""
        texto = (self.cfg.get("aviso_texto") or "").strip() or T("avi.texto")
        if "%" in texto:
            try:
                texto = texto % int(round(peligro["segundos"]))
            except (TypeError, ValueError):
                pass
        self._pintar(texto)
        self.visible = True

    def esconder(self):
        if self.modo_mover:
            return
        self.visible = False
        self.v.withdraw()

    def _pintar(self, texto, muestra=False):
        tam = int(self.cfg.get("aviso_tam", 26))
        color = self.cfg.get("aviso_color", "#ff2d2d")
        fuente = ("Segoe UI", tam, "bold")

        c = self.lienzo
        c.delete("all")
        # Se mide el texto con un dibujo de prueba para que la ventana quede
        # justo del tamano que hace falta. Si sobrara fondo, ese trozo seria
        # un rectangulo transparente que se come los clics del juego.
        temporal = c.create_text(0, 0, text=texto, font=fuente, anchor="nw")
        x1, y1, x2, y2 = c.bbox(temporal)
        c.delete(temporal)
        ancho, alto = x2 - x1 + 24, y2 - y1 + 14

        c.configure(width=ancho, height=alto)
        # Un borde oscuro detras de la letra: sobre un cielo claro o sobre
        # asfalto, un texto de un solo color se pierde en uno de los dos.
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2)):
            c.create_text(ancho / 2 + dx, alto / 2 + dy, text=texto,
                          font=fuente, fill="#000000")
        c.create_text(ancho / 2, alto / 2, text=texto, font=fuente,
                      fill="#8a8a8a" if muestra else color)

        self.v.geometry("%dx%d+%d+%d" % (ancho, alto,
                                         self.cfg["aviso_x"], self.cfg["aviso_y"]))
        self.v.deiconify()
        self.v.lift()


class Motor:
    """
    Junta el vigia, el cartel y el sonido.

    Quien lo usa solo tiene que llamar a `latido` en cada lectura y olvidarse.
    """

    def __init__(self, raiz, cfg, guardar):
        import avisos
        self.cfg = cfg
        self.vigia = avisos.Vigia()
        self.cartel = Cartel(raiz, cfg, guardar)
        self.sonando = False

    def latido(self, coches, parados, largo, mi_kmh):
        """Se llama en cada lectura del juego."""
        if not self.cfg.get("aviso_parados", True):
            self.cartel.esconder()
            return

        ahora = time.time()
        antes = self.vigia.encendido
        peligro = self.vigia.mirar(ahora, coches, parados, largo, mi_kmh,
                                   float(self.cfg.get("aviso_segundos", 8)))
        if peligro:
            self.cartel.mostrar(peligro)
            # El sonido solo al encenderse, no en cada lectura: si no, serian
            # veinte pitidos por segundo.
            if not antes:
                tocar(self.cfg.get("aviso_sonido", "doble.wav"),
                      self.cfg.get("aviso_volumen", 60),
                      self.cfg.get("aviso_sonar", True))
        else:
            self.cartel.esconder()

    def colocar(self, moviendo):
        self.cartel.colocar(moviendo)
