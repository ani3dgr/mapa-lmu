# -*- coding: utf-8 -*-
"""
El editor de reglajes: las mismas paginas del juego, pero que se tocan.

Se monta dentro de cualquier hueco (la sub-pestana Reglaje o una ventana
aparte), asi que el mismo editor sirve en los dos sitios y no hay dos
versiones que mantener.

COMO FUNCIONA GUARDAR
Se puede sobrescribir o guardar una copia, y lo elige la persona cada vez.
No hay una opcion mejor: sobrescribir va bien cuando estas afinando un
reglaje tuyo y quieres una sola cosa en la lista del juego; la copia va
bien cuando pruebas algo y no te fias. Lo que no cambia nunca es que ANTES
de escribir se apunta en el historial como estaba el reglaje entero, asi
que sobrescribir tampoco pierde nada: siempre se puede volver.

Y en el juego no hace falta salir: en la pantalla de cargar reglaje hay un
boton de actualizar que vuelve a leer la carpeta.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox

import biblioteca as B
import historial
import idiomas
import ingenieria as I
import paginas

T = idiomas.t

ROJO = "#b03a2e"
VERDE = "#1e7a44"
AZUL = "#1f5fa8"
GRIS = "#9a9a9a"
AMBAR = "#b8860b"       # una pieza desconectada: ni error ni cambio normal


def _visible(texto):
    """
    El valor tal y como hay que ensenarlo.

    El juego escribe "Detached" cuando una pieza va desconectada, y ademas
    lo escribe en el idioma de quien grabo el reglaje ("Desacoplada" en los
    de Manuel). Aqui se dice siempre igual y en el idioma del programa,
    porque no es un valor mas: es que esa pieza no esta puesta.
    """
    return T("ed.desconectado") if I.esta_desconectado(texto) else texto


class Editor:
    """
    Las paginas de reglaje, editables.

    `hueco` es el Frame donde se mete. `al_guardar` se llama cuando se ha
    escrito algo, por si quien lo abrio quiere refrescar su lista.
    """

    def __init__(self, hueco, al_guardar=None):
        self.hueco = hueco
        self.al_guardar = al_guardar
        self.ficha = None
        self.cal = I.leer_calibracion()
        self.pendientes = {}       # "SECCION/Clave" -> indice nuevo
        self.filas = {}            # clave de pagina -> widgets

        self.pagina = tk.IntVar(value=0)
        self._montar()

    # ------------------------------------------------------------ montaje
    def _montar(self):
        tira = ttk.Frame(self.hueco)
        tira.pack(fill="x", pady=(0, 4))
        for i, (titulo, _) in enumerate(paginas.PAGINAS):
            ttk.Radiobutton(tira, text=titulo.upper(), value=i,
                            variable=self.pagina, style="Toolbutton",
                            command=self.pintar).pack(side="left", padx=1)

        self.aviso = ttk.Label(self.hueco, text=T("ed.vacio"), foreground="#777")
        self.aviso.pack(fill="x", pady=(0, 2))

        # Un lienzo con barra porque hay paginas que no caben de alto.
        caja = ttk.Frame(self.hueco)
        caja.pack(fill="both", expand=True)
        self.lienzo = tk.Canvas(caja, highlightthickness=1, background="white",
                                highlightbackground="#d5d5d5")
        barra = ttk.Scrollbar(caja, orient="vertical", command=self.lienzo.yview)
        self.lienzo.configure(yscrollcommand=barra.set)
        self.lienzo.pack(side="left", fill="both", expand=True)
        barra.pack(side="left", fill="y")
        self.dentro = ttk.Frame(self.lienzo)
        self.ventana = self.lienzo.create_window((0, 0), window=self.dentro,
                                                 anchor="nw")
        self.dentro.bind("<Configure>", lambda _: self.lienzo.configure(
            scrollregion=self.lienzo.bbox("all")))
        self.lienzo.bind("<Configure>", lambda e: self.lienzo.itemconfigure(
            self.ventana, width=e.width))
        self.lienzo.bind_all("<MouseWheel>", self._rueda)

        pie = ttk.Frame(self.hueco)
        pie.pack(fill="x", pady=(6, 0))
        self.b_guardar = ttk.Button(pie, text=T("ed.guardar"),
                                    command=self.guardar, state="disabled")
        self.b_guardar.pack(side="left")
        ttk.Button(pie, text=T("ed.deshacer"),
                   command=self.deshacer).pack(side="left", padx=(6, 0))
        ttk.Button(pie, text=T("ed.historial"),
                   command=self.ver_historial).pack(side="left", padx=(6, 0))
        self.estado = ttk.Label(pie, text="", foreground="#555")
        self.estado.pack(side="left", padx=(12, 0))
        ttk.Label(pie, text=T("ed.pista_manual"), foreground="#777",
                  font=("Segoe UI", 8)).pack(side="right")

    def _rueda(self, evento):
        try:
            if self.lienzo.winfo_ismapped():
                self.lienzo.yview_scroll(-1 * (evento.delta // 120), "units")
        except tk.TclError:
            pass

    # -------------------------------------------------------------- cargar
    def cargar(self, ficha):
        """Pone un reglaje en el editor. Lo pendiente sin guardar se pierde."""
        self.ficha = ficha
        self.pendientes.clear()
        self.cal = I.leer_calibracion()
        self.pintar()

    def _valor(self, clave):
        """
        Lo que hay que ensenar en una linea: el pendiente o el guardado.

        MANDA EL NUMERO, NO EL TEXTO. En el .svm cada ajuste trae su indice
        y, detras de la barra, un texto con el valor en unidades. El indice
        es lo unico de fiar: el texto puede estar desfasado, porque cuando
        este programa toca un ajuste deja escrito de donde venia, y porque
        el juego lo guarda en el idioma de quien lo grabo.

        Paso justo esto el 08/09/2026: el aleron estaba puesto en 11 grados
        (indice 4) y el editor seguia ensenando "9.0 deg", que era la
        etiqueta anterior. Parecia que el juego hubiera deshecho el cambio,
        y lo que pasaba es que el mapa lo contaba mal.

        Asi que el indice se traduce con la calibracion, que sabe a que
        equivale cada numero en ESTE coche, y solo se cae al texto del
        archivo cuando ese numero no se ha visto nunca.
        """
        reales = paginas.reparte(clave)
        primera = next((r for r in reales if r in self.ficha["ajustes"]), None)
        if primera is None:
            return None, "", False
        a = self.ficha["ajustes"][primera]
        corto = B.coche_de(self.ficha)["corto"]
        crudo = I.sin_marcas(a["texto"])
        if primera in self.pendientes:
            nuevo = self.pendientes[primera]
            texto = I.como_queda(self.cal, corto, a["clave"], nuevo, crudo)
            return nuevo, _visible(texto or ("%d" % nuevo)), True
        if not I.tiene_marca(a["texto"]):
            # Sin tocar: el texto lo escribio el juego y es de fiar.
            return a["indice"], _visible(crudo or ("%g" % (a["indice"] or 0))), False
        # Tocado por este programa: el texto cuenta el valor viejo, asi que
        # se traduce el indice. Y si ese numero no se ha visto nunca, se
        # ensena el numero pelado antes que un texto que ya no es verdad.
        texto = I.como_queda(self.cal, corto, a["clave"], a["indice"], crudo)
        return a["indice"], _visible(texto or ("%g" % (a["indice"] or 0))), False

    def _desparejadas(self, clave):
        """True si las dos ruedas del eje llevan cosas distintas."""
        reales = [r for r in paginas.reparte(clave) if r in self.ficha["ajustes"]]
        if len(reales) < 2:
            return False
        return len(set(self.ficha["ajustes"][r]["indice"] for r in reales)) > 1

    # -------------------------------------------------------------- pintar
    def pintar(self):
        for hijo in self.dentro.winfo_children():
            hijo.destroy()
        self.filas.clear()

        if not self.ficha:
            self.aviso.configure(text=T("ed.vacio"), foreground="#777")
            return

        n = len(self.pendientes)
        self.aviso.configure(
            text=("%s   ·   %s" % (self.ficha["nombre"], self.ficha["circuito"]))
                 + ("   ·   " + T("ed.sin_guardar") % n if n else ""),
            foreground=ROJO if n else "#555")
        self.b_guardar.configure(state="normal" if n else "disabled")

        _, grupos = paginas.PAGINAS[self.pagina.get()]
        for titulo, filas in grupos:
            marco = ttk.LabelFrame(self.dentro, text=titulo, padding=(8, 4))
            marco.pack(fill="x", padx=6, pady=4)
            hay = False
            for fila, (nombre, clave) in enumerate(filas):
                if self._linea(marco, fila, nombre, clave):
                    hay = True
            if not hay:
                ttk.Label(marco, text=T("ed.no_tiene"),
                          foreground=GRIS).grid(row=0, column=0, sticky="w")

    def _linea(self, marco, fila, nombre, clave):
        indice, texto, tocado = self._valor(clave)
        if indice is None:
            return False

        se_toca = not I._NO_SE_TOCA.match(texto or "") and not self._desparejadas(clave)
        # Una pieza desconectada se canta en ambar y en negrita, aunque no
        # se acabe de tocar. No es un valor mas de la escala: es que esa
        # pieza no esta puesta, y quien mire el reglaje tiene que verlo de
        # un vistazo sin ir buscandolo.
        suelta = I.esta_desconectado(texto)
        color = (AMBAR if suelta else
                 (AZUL if tocado else ("#222" if se_toca else GRIS)))

        rotulo = ttk.Label(marco, text=nombre, foreground=color,
                           width=30, anchor="w")
        rotulo.grid(row=fila, column=0, sticky="w")
        self._enlazar_manual(rotulo, clave)
        valor = ttk.Label(marco, text=texto, foreground=color,
                          width=24, anchor="e",
                          font=("Segoe UI", 9,
                                "bold" if (tocado or suelta) else "normal"))
        valor.grid(row=fila, column=1, sticky="e", padx=(8, 6))

        if se_toca:
            for signo, simbolo in ((-1, "◀"), (1, "▶")):
                # La flecha se apaga cuando el ajuste ya esta en el tope.
                # Si no, se pulsa y no pasa nada, y uno se queda pensando
                # que el programa esta roto.
                tope = self._siguiente(clave, signo) is None
                tk.Button(marco, text=simbolo, width=2, relief="flat",
                          font=("Segoe UI", 7),
                          state="disabled" if tope else "normal",
                          disabledforeground="#dcdcdc",
                          command=lambda c=clave, s=signo: self.mover(c, s)
                          ).grid(row=fila, column=2 if signo < 0 else 3)
        elif self._desparejadas(clave):
            # Las dos ruedas van distintas. Se ensena pero no se toca por
            # eje: si el reglaje lleva un reparto puesto a mano, moverlo
            # desde aqui lo aplastaria sin que nadie se entere.
            ttk.Label(marco, text=T("ed.desparejado"), foreground=ROJO,
                      font=("Segoe UI", 8)).grid(row=fila, column=2,
                                                 columnspan=2, sticky="w")
        self.filas[clave] = valor
        return True

    def _enlazar_manual(self, rotulo, clave):
        """
        Pulsar en el nombre de un ajuste abre el manual por su explicacion.

        Va en el propio nombre y no en un boton aparte porque son cien
        lineas: cien botones de ayuda serian mas ruido que ayuda. Se subraya
        al pasar el raton para que se vea que se puede pulsar.
        """
        import manual
        if not manual.por_clave(clave):
            return
        normal = rotulo.cget("font") or "TkDefaultFont"
        rotulo.bind("<Button-1>", lambda _e, c=clave: self._ver_manual(c))
        rotulo.bind("<Enter>", lambda _e: rotulo.configure(
            cursor="hand2", font=("Segoe UI", 9, "underline")))
        rotulo.bind("<Leave>", lambda _e: rotulo.configure(
            cursor="", font=normal))

    def _ver_manual(self, clave):
        import manual_gui
        manual_gui.abrir(self.hueco.winfo_toplevel(), clave=clave)

    # -------------------------------------------------------------- tocar
    def _siguiente(self, clave, signo):
        """
        A que indice pasaria un ajuste al pulsar la flecha, o None si ya no
        se puede mover para ese lado: por arriba manda el maximo visto en
        reglajes de esa clase, y por abajo el cero. Ver `_recortar`.
        """
        reales = [r for r in paginas.reparte(clave) if r in self.ficha["ajustes"]]
        if not reales:
            return None
        a = self.ficha["ajustes"][reales[0]]
        if a["indice"] is None:
            return None
        ahora = self.pendientes.get(reales[0], a["indice"])
        categoria = B.coche_de(self.ficha)["categoria"] or "?"
        nuevo = int(ahora) + signo * I.paso_de(self.cal, categoria, a["clave"])
        nuevo = int(I._recortar(self.cal, categoria, a["clave"], nuevo))
        return None if nuevo == int(ahora) else nuevo

    def mover(self, clave, signo):
        """Sube o baja un ajuste un escalon."""
        nuevo = self._siguiente(clave, signo)
        if nuevo is None:
            return
        reales = [r for r in paginas.reparte(clave) if r in self.ficha["ajustes"]]
        original = self.ficha["ajustes"][reales[0]]["indice"]
        for r in reales:
            if nuevo == original:
                self.pendientes.pop(r, None)   # ha vuelto a donde estaba
            else:
                self.pendientes[r] = nuevo
        self.pintar()

    def deshacer(self):
        if not self.pendientes:
            return
        self.pendientes.clear()
        self.pintar()
        self.estado.configure(text=T("ed.deshecho"), foreground="#555")

    # ------------------------------------------------------------- guardar
    def guardar(self):
        if not self.ficha or not self.pendientes:
            return
        modo = _PreguntaGuardar(self.hueco.winfo_toplevel(),
                                self.ficha).respuesta
        if not modo:
            return

        if modo == "sobrescribir":
            destino = self.ficha["ruta"]
        else:
            destino = _siguiente(self.ficha["ruta"])

        cambios = self._lista_de_cambios()
        # El apunte se hace ANTES de escribir, con la foto de como estaba.
        # Asi sobrescribir tampoco pierde nada.
        historial.apuntar(self.ficha, cambios, destino, modo, "mano")

        if not I.aplicar(self.ficha, cambios, destino):
            messagebox.showerror(T("ed.titulo"), T("ing.no_se_pudo"),
                                 parent=self.hueco)
            return

        self.estado.configure(
            text=T("ed.guardado") % os.path.basename(destino), foreground=VERDE)
        nueva = B.leer(destino)
        if nueva:
            self.cargar(nueva)
        if self.al_guardar:
            self.al_guardar()

    def _lista_de_cambios(self):
        """Lo pendiente, en el formato que entienden aplicar() y el historial."""
        por_clave = {}
        for llave, nuevo in self.pendientes.items():
            a = self.ficha["ajustes"][llave]
            d = por_clave.setdefault(a["clave"], {
                "param": a["clave"], "clave": a["clave"], "claves": [],
                "nombre": I.nombre_ajuste(a["clave"], _codigo())
                          + _lado(a["seccion"]),
                "ahora": I.sin_marcas(a["texto"]) or "%g" % (a["indice"] or 0),
                "indice_ahora": int(a["indice"] or 0),
                "indice_nuevo": int(nuevo),
                "queda": I.como_queda(self.cal, B.coche_de(self.ficha)["corto"],
                                      a["clave"], nuevo, a["texto"])
                         or ("%d" % nuevo)})
            d["claves"].append(llave)
        return list(por_clave.values())

    # ----------------------------------------------------------- historial
    def ver_historial(self):
        if not self.ficha:
            return
        Historial(self.hueco.winfo_toplevel(), self.ficha, self._tras_restaurar)

    def _tras_restaurar(self, ruta):
        nueva = B.leer(ruta)
        if nueva:
            self.cargar(nueva)
        self.estado.configure(text=T("ed.restaurado"), foreground=VERDE)
        if self.al_guardar:
            self.al_guardar()


def _codigo():
    try:
        return idiomas.actual()
    except Exception:
        return "es"


def _lado(seccion):
    if seccion in ("FRONTLEFT", "FRONTRIGHT"):
        return " delantero" if _codigo() == "es" else " (front)"
    if seccion in ("REARLEFT", "REARRIGHT"):
        return " trasero" if _codigo() == "es" else " (rear)"
    return ""


def _siguiente(ruta):
    """El siguiente nombre libre: ..._p2.svm, _p3.svm."""
    carpeta = os.path.dirname(ruta)
    base = os.path.splitext(os.path.basename(ruta))[0]
    if base.rsplit("_p", 1)[-1].isdigit():
        base = base.rsplit("_p", 1)[0]
    n = 2
    while os.path.exists(os.path.join(carpeta, "%s_p%d.svm" % (base, n))):
        n += 1
    return os.path.join(carpeta, "%s_p%d.svm" % (base, n))


class _PreguntaGuardar:
    """
    Copia o encima. Se pregunta cada vez a proposito, sin recordar la
    respuesta: son dos maneras distintas de trabajar y se cambia de una a
    otra segun lo seguro que estes del cambio que acabas de hacer.
    """

    def __init__(self, padre, ficha):
        self.respuesta = None
        v = tk.Toplevel(padre)
        self.v = v
        v.title(T("ed.guardar"))
        v.attributes("-topmost", True)
        v.resizable(False, False)
        v.transient(padre)

        ttk.Label(v, padding=(14, 12), justify="left", wraplength=430,
                  text=T("ed.como_guardar")).pack()
        ttk.Label(v, padding=(14, 0), justify="left", foreground="#555",
                  font=("Consolas", 9),
                  text=T("ed.copia_sera") % os.path.basename(
                      _siguiente(ficha["ruta"]))).pack(anchor="w")

        botones = ttk.Frame(v, padding=(14, 12))
        botones.pack(fill="x")
        ttk.Button(botones, text=T("ed.hacer_copia"),
                   command=lambda: self._elegir("copia")).pack(side="left")
        ttk.Button(botones, text=T("ed.encima"),
                   command=lambda: self._elegir("sobrescribir")
                   ).pack(side="left", padx=8)
        ttk.Button(botones, text=T("ed.cancelar"),
                   command=v.destroy).pack(side="right")
        v.grab_set()
        padre.wait_window(v)

    def _elegir(self, cual):
        self.respuesta = cual
        self.v.destroy()


class Historial:
    """El cuaderno de a bordo de un reglaje, con el boton de volver atras."""

    def __init__(self, padre, ficha, al_restaurar):
        self.ficha = ficha
        self.al_restaurar = al_restaurar
        self.apuntes = historial.leer(ficha["circuito"], ficha["nombre"])

        v = tk.Toplevel(padre)
        self.v = v
        v.title(T("his.titulo"))
        v.attributes("-topmost", True)
        v.geometry("880x480")

        ttk.Label(v, padding=(10, 8), justify="left",
                  text=T("his.ayuda")).pack(fill="x")

        marco = ttk.Frame(v, padding=(10, 0))
        marco.pack(fill="both", expand=True)
        cols = ("cuando", "que", "modo", "archivo")
        self.tabla = ttk.Treeview(marco, columns=cols, show="headings",
                                  selectmode="browse")
        for c, a in zip(cols, (120, 360, 110, 220)):
            self.tabla.heading(c, text=T("his.col." + c))
            self.tabla.column(c, width=a)
        barra = ttk.Scrollbar(marco, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=barra.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="left", fill="y")

        for a in self.apuntes:
            que = "; ".join("%s: %s -> %s" % (c["nombre"], c["de"], c["a"])
                            for c in a["cambios"]) or "-"
            modo = (T("his.encima") if a["modo"] == "sobrescribir"
                    else T("his.copia"))
            if a.get("modo") == "restaurar":
                modo = T("his.vuelta")
            self.tabla.insert("", "end", values=(a["cuando"], que, modo,
                                                 a["archivo"]))
        if not self.apuntes:
            self.tabla.insert("", "end", values=(T("his.vacio"), "", "", ""))

        pie = ttk.Frame(v, padding=(10, 8))
        pie.pack(fill="x")
        ttk.Button(pie, text=T("his.restaurar"),
                   command=self.restaurar).pack(side="left")
        ttk.Button(pie, text=T("bib.cerrar"),
                   command=v.destroy).pack(side="right")

    def restaurar(self):
        sel = self.tabla.selection()
        if not sel or not self.apuntes:
            messagebox.showinfo(T("his.titulo"), T("his.elige"), parent=self.v)
            return
        apunte = self.apuntes[self.tabla.index(sel[0])]
        if not messagebox.askyesno(T("his.titulo"),
                                   T("his.confirmar") % apunte["cuando"],
                                   parent=self.v):
            return

        # Volver atras tambien se apunta. Si te equivocas al volver, puedes
        # volver de volver: el cuaderno no se rompe nunca.
        historial.apuntar(self.ficha, [], self.ficha["ruta"], "restaurar", "mano")
        if not historial.restaurar(apunte, self.ficha, self.ficha["ruta"]):
            messagebox.showerror(T("his.titulo"), T("ing.no_se_pudo"),
                                 parent=self.v)
            return
        self.v.destroy()
        self.al_restaurar(self.ficha["ruta"])
