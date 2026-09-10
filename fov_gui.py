# -*- coding: utf-8 -*-
"""
La calculadora de campo de vision (FOV), dentro del programa.

POR QUE ESTA AQUI
El manual de conduccion empieza diciendo que el campo de vision es lo primero
que hay que ajustar y lo que casi nadie toca. Decirlo y luego mandar a la
gente a buscar una calculadora por internet es dejar el trabajo a medias: el
que abre el manual mientras juega no va a salirse a buscar una pagina web.

QUE CALCULA
El angulo que abarca tu pantalla vista desde donde tienes los ojos. Con eso,
lo que ves en el monitor tiene el mismo tamano angular que tendria en la vida
real, y por eso puedes juzgar bien a que velocidad vas y cuanto falta para la
curva.

  FOV vertical = 2 x arcotangente( alto / (2 x distancia) )

EL VERTICAL ES EL QUE PIDE EL JUEGO. Le Mans Ultimate, como rFactor 2,
configura el campo de vision por el angulo VERTICAL. Por eso el numero gordo
de esta ventana es ese, y los otros dos (horizontal y diagonal) salen abajo y
mas pequenos, que son los que piden otros juegos.

VIENE DE UNA PAGINA WEB que se hizo antes en HTML. Esto es la misma cuenta y
los mismos consejos, en una ventana del programa y traducido.
"""
import math
import tkinter as tk
from tkinter import ttk

import idiomas

T = idiomas.t

NARANJA = "#c0620a"
AZUL = "#1a5fb4"
GRIS = "#555555"

# (relacion ancho/alto, clave del texto). El orden es el de la lista.
FORMATOS = [
    (16 / 9.0, "fov.f169"),
    (16 / 10.0, "fov.f1610"),
    (21 / 9.0, "fov.f219"),
    (43 / 18.0, "fov.f4318"),
    (32 / 9.0, "fov.f329"),
    (4 / 3.0, "fov.f43"),
]

# Los formatos con nombre, para poder decir "16:9" en vez de "1.78:1".
CONOCIDOS = [(1.3333, "4:3"), (1.6, "16:10"), (1.7778, "16:9"),
             (2.3333, "21:9"), (2.3889, "43:18"), (3.5556, "32:9")]

_abierta = None


def abrir(padre):
    """Abre la calculadora, o trae al frente la que ya estuviera abierta."""
    global _abierta
    if _abierta is not None and _abierta.viva():
        _abierta.delante()
        return _abierta
    _abierta = Calculadora(padre)
    return _abierta


def angulo(medida, distancia):
    """El angulo que abarca una medida vista desde una distancia, en grados."""
    return math.degrees(2 * math.atan(medida / (2.0 * distancia)))


def nombre_formato(ancho, alto):
    """'16:9' a partir de las medidas, o la proporcion si no es conocida."""
    if alto <= 0:
        return "-"
    r = ancho / float(alto)
    for valor, nombre in CONOCIDOS:
        if abs(r - valor) < 0.03:
            return nombre
    a, b = int(round(ancho * 10)), int(round(alto * 10))
    d = math.gcd(a, b) or 1
    if a // d <= 40 and b // d <= 40:
        return "%d:%d" % (a // d, b // d)
    return "%.2f:1" % r


class Calculadora:

    def __init__(self, padre):
        v = tk.Toplevel(padre)
        self.v = v
        v.title(T("fov.titulo"))
        # Encima de todo, como las demas ventanas del programa: si no, se
        # abre detras del manual y parece que el boton no ha hecho nada.
        v.attributes("-topmost", True)
        v.resizable(False, False)

        cuerpo = ttk.Frame(v, padding=14)
        cuerpo.pack(fill="both", expand=True)

        ttk.Label(cuerpo, text=T("fov.titulo"),
                  font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(cuerpo, text=T("fov.sub"), foreground=GRIS,
                  wraplength=560, justify="left").pack(anchor="w", pady=(2, 12))

        self._medidas(cuerpo)
        self._resultado(cuerpo)
        self._pulgadas(cuerpo)
        self._consejos(cuerpo)

        pie = ttk.Frame(cuerpo)
        pie.pack(fill="x", pady=(12, 0))
        self.rotulo_copiado = ttk.Label(pie, text="", foreground=AZUL)
        self.rotulo_copiado.pack(side="left")
        ttk.Button(pie, text=T("bib.cerrar"),
                   command=v.destroy).pack(side="right")
        ttk.Button(pie, text=T("fov.copiar"),
                   command=self.copiar).pack(side="right", padx=(0, 6))

        self.calcular()

    def viva(self):
        try:
            return bool(self.v.winfo_exists())
        except tk.TclError:
            return False

    def delante(self):
        try:
            self.v.deiconify()
            self.v.attributes("-topmost", True)
            self.v.lift()
            self.v.focus_force()
        except tk.TclError:
            pass

    # ------------------------------------------------------------- montaje
    def _campo(self, padre, fila, etiqueta, pista, valor):
        """Una casilla de numero con su explicacion debajo."""
        caja = ttk.Frame(padre)
        caja.grid(row=0, column=fila, sticky="nw", padx=(0, 14))
        ttk.Label(caja, text=etiqueta, foreground=GRIS).pack(anchor="w")
        var = tk.StringVar(value=valor)
        entrada = ttk.Entry(caja, textvariable=var, width=12,
                            font=("Segoe UI", 12))
        entrada.pack(anchor="w", pady=(2, 0))
        ttk.Label(caja, text=pista, foreground=GRIS,
                  font=("Segoe UI", 8)).pack(anchor="w")
        # Se recalcula segun escribes, sin botones: es lo que hacia la
        # version web y es lo que espera cualquiera.
        var.trace_add("write", lambda *_: self.calcular())
        return var

    def _medidas(self, padre):
        marco = ttk.LabelFrame(padre, text=T("fov.medidas"), padding=(10, 8))
        marco.pack(fill="x")
        fila = ttk.Frame(marco)
        fila.pack(fill="x")
        self.ancho = self._campo(fila, 0, T("fov.ancho"), T("fov.ancho_pista"),
                                 "60")
        self.alto = self._campo(fila, 1, T("fov.alto"), T("fov.alto_pista"),
                                "33.7")
        self.dist = self._campo(fila, 2, T("fov.dist"), T("fov.dist_pista"),
                                "70")
        self.aviso = ttk.Label(marco, text="", foreground="#b03a2e",
                               wraplength=540, justify="left")
        self.aviso.pack(anchor="w", pady=(6, 0))

    def _resultado(self, padre):
        marco = ttk.LabelFrame(padre, text=T("fov.resultado"), padding=(10, 8))
        marco.pack(fill="x", pady=(10, 0))

        arriba = ttk.Frame(marco)
        arriba.pack(fill="x")
        self.vertical = ttk.Label(arriba, text="-", foreground=NARANJA,
                                  font=("Segoe UI", 40, "bold"))
        self.vertical.pack(side="left")
        ttk.Label(arriba, text="°", foreground=GRIS,
                  font=("Segoe UI", 18)).pack(side="left", anchor="s",
                                              pady=(0, 8))
        ttk.Label(arriba, text=T("fov.vertical"), foreground=GRIS,
                  justify="right", wraplength=300).pack(side="right", anchor="s")

        abajo = ttk.Frame(marco)
        abajo.pack(fill="x", pady=(8, 0))
        self.horizontal = self._mini(abajo, T("fov.horizontal"))
        self.diagonal = self._mini(abajo, T("fov.diagonal"))
        self.aspecto = self._mini(abajo, T("fov.aspecto"))

    def _mini(self, padre, titulo):
        caja = ttk.Frame(padre)
        caja.pack(side="left", padx=(0, 24))
        ttk.Label(caja, text=titulo, foreground=GRIS,
                  font=("Segoe UI", 8)).pack(anchor="w")
        valor = ttk.Label(caja, text="-", font=("Segoe UI", 13, "bold"))
        valor.pack(anchor="w")
        return valor

    def _pulgadas(self, padre):
        marco = ttk.LabelFrame(padre, text=T("fov.desde_pulgadas"),
                               padding=(10, 8))
        marco.pack(fill="x", pady=(10, 0))
        fila = ttk.Frame(marco)
        fila.pack(fill="x")

        izq = ttk.Frame(fila)
        izq.pack(side="left", padx=(0, 14))
        ttk.Label(izq, text=T("fov.pulgadas"), foreground=GRIS).pack(anchor="w")
        self.pulgadas = tk.StringVar(value="27")
        ttk.Entry(izq, textvariable=self.pulgadas, width=12,
                  font=("Segoe UI", 12)).pack(anchor="w", pady=(2, 0))

        med = ttk.Frame(fila)
        med.pack(side="left", padx=(0, 14))
        ttk.Label(med, text=T("fov.formato"), foreground=GRIS).pack(anchor="w")
        self.formato = ttk.Combobox(med, state="readonly", width=30,
                                    values=[T(c) for _, c in FORMATOS])
        self.formato.current(0)
        self.formato.pack(anchor="w", pady=(2, 0))

        der = ttk.Frame(fila)
        der.pack(side="left")
        ttk.Label(der, text=" ").pack()
        ttk.Button(der, text=T("fov.rellenar"),
                   command=self.desde_pulgadas).pack(pady=(2, 0))

        ttk.Label(marco, text=T("fov.aviso_pulgadas"), foreground=GRIS,
                  font=("Segoe UI", 8), wraplength=540,
                  justify="left").pack(anchor="w", pady=(8, 0))

    def _consejos(self, padre):
        marco = ttk.LabelFrame(padre, text=T("fov.como_usarlo"),
                               padding=(10, 8))
        marco.pack(fill="x", pady=(10, 0))
        texto = tk.Text(marco, wrap="word", height=11, relief="flat",
                        background=padre.winfo_toplevel().cget("background"),
                        font=("Segoe UI", 9), cursor="arrow")
        texto.pack(fill="x")
        texto.tag_configure("t", font=("Segoe UI", 9, "bold"),
                            foreground=AZUL, spacing1=6)
        for clave in ("fov.consejos", "fov.tres_pantallas", "fov.formula"):
            bloque = T(clave).split("\n")
            texto.insert("end", bloque[0] + "\n", ("t",))
            for linea in bloque[1:]:
                texto.insert("end", linea + "\n")
        texto.configure(state="disabled")

    # ------------------------------------------------------------- cuentas
    def _numero(self, var):
        try:
            valor = float(str(var.get()).replace(",", "."))
        except ValueError:
            return None
        return valor if valor > 0 else None

    def calcular(self, *_):
        ancho = self._numero(self.ancho)
        alto = self._numero(self.alto)
        dist = self._numero(self.dist)

        if None in (ancho, alto, dist):
            self.aviso.configure(text=T("fov.error"))
            for etiqueta in (self.vertical, self.horizontal, self.diagonal,
                             self.aspecto):
                etiqueta.configure(text="-")
            return

        self.aviso.configure(text="")
        diagonal = math.sqrt(ancho * ancho + alto * alto)
        self.vertical.configure(text="%.1f" % angulo(alto, dist))
        self.horizontal.configure(text="%.1f°" % angulo(ancho, dist))
        self.diagonal.configure(text="%.1f°" % angulo(diagonal, dist))
        self.aspecto.configure(text=nombre_formato(ancho, alto))

    def desde_pulgadas(self):
        """Saca ancho y alto de la diagonal en pulgadas y el formato."""
        try:
            pulgadas = float(str(self.pulgadas.get()).replace(",", "."))
        except ValueError:
            return
        if pulgadas <= 0:
            return
        relacion = FORMATOS[self.formato.current()][0]
        diagonal = pulgadas * 2.54
        alto = diagonal / math.sqrt(relacion * relacion + 1)
        self.ancho.set("%.1f" % (alto * relacion))
        self.alto.set("%.1f" % alto)
        self.calcular()

    def copiar(self):
        """El numero al portapapeles, que es a donde va a ir de todas formas."""
        valor = self.vertical.cget("text")
        if valor == "-":
            return
        self.v.clipboard_clear()
        self.v.clipboard_append(valor)
        self.rotulo_copiado.configure(text=T("fov.copiado") % valor)
        self.v.after(2500, lambda: self.rotulo_copiado.configure(text=""))
