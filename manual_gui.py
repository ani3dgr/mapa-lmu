# -*- coding: utf-8 -*-
"""
La ventana del manual: indice a la izquierda, texto a la derecha.

COMO SE USA DESDE EL RESTO DEL PROGRAMA
    manual_gui.abrir(padre)                       -> el manual por el principio
    manual_gui.abrir(padre, clave="EJE_del/...")  -> directo a ese ajuste

Lo segundo es lo que engancha el manual con el editor de reglajes: estas
mirando una linea del reglaje, no sabes que hace, y con un boton te plantas
en la explicacion de esa linea.

SOLO SE ABRE UNA. Si ya esta abierta, se trae al frente y se va al sitio que
le pidas, en vez de llenar la pantalla de ventanas iguales.

LOS ENLACES AZULES del apartado "se toca junto con" llevan a la ficha del
otro ajuste. Es la parte que mas se usa: casi ningun cambio de reglaje se
hace solo, y asi se ve la pareja sin buscarla.
"""
import tkinter as tk
from tkinter import ttk

import idiomas
import manual as M

T = idiomas.t

AZUL = "#1a5fb4"
GRIS = "#555555"
ROJO = "#b03a2e"

_abierta = None


def abrir(padre, clave=None, tomo=None):
    """Abre el manual, o trae al frente el que ya estuviera abierto."""
    global _abierta
    if _abierta is not None and _abierta.viva():
        _abierta.delante()
        if clave:
            _abierta.ir_a_clave(clave)
        return _abierta
    _abierta = Manual(padre, clave=clave, tomo=tomo)
    return _abierta


class Manual:

    def __init__(self, padre, clave=None, tomo=None):
        self.tomo = tomo or (M.tomos() or ["reglajes"])[0]
        self.nodos = {}          # id de la linea del arbol -> nodo
        self.enlaces = {}        # nombre del tag -> clave del .svm

        v = tk.Toplevel(padre)
        self.v = v
        v.title(T("man.titulo"))
        # Encima de todo, igual que la biblioteca y el editor. Si no, como
        # esas ventanas si son topmost, el manual se abre DETRAS de ellas y
        # parece que el boton no ha hecho nada.
        v.attributes("-topmost", True)
        v.geometry("1020x660")
        v.minsize(760, 480)

        self._cabecera(v)
        cuerpo = ttk.Frame(v, padding=(10, 0, 10, 10))
        cuerpo.pack(fill="both", expand=True)
        self._arbol(cuerpo)
        self._texto(cuerpo)
        self._pie(v)

        self.recargar()
        if clave:
            self.ir_a_clave(clave)
        else:
            self._primero()

    def delante(self):
        """La saca del fondo: desminimiza, sube y se queda con el foco."""
        try:
            self.v.deiconify()
            self.v.attributes("-topmost", True)
            self.v.lift()
            self.v.focus_force()
        except tk.TclError:
            pass

    def viva(self):
        try:
            return bool(self.v.winfo_exists())
        except tk.TclError:
            return False

    # ---------------------------------------------------------- construccion
    def _cabecera(self, v):
        cab = ttk.Frame(v, padding=(10, 8))
        cab.pack(fill="x")

        # Los tomos solo se ensenan si hay mas de uno puesto: mientras solo
        # exista el de reglajes, un selector de uno solo seria ruido.
        disponibles = M.tomos()
        if len(disponibles) > 1:
            self.var_tomo = tk.StringVar(value=self.tomo)
            for t in disponibles:
                ttk.Radiobutton(cab, text=T("man.tomo." + t), value=t,
                                variable=self.var_tomo,
                                command=self._cambiar_tomo).pack(side="left",
                                                                 padx=(0, 10))

        ttk.Label(cab, text=T("man.buscar")).pack(side="left", padx=(0, 6))
        self.var_buscar = tk.StringVar()
        caja = ttk.Entry(cab, textvariable=self.var_buscar, width=32)
        caja.pack(side="left")
        caja.bind("<KeyRelease>", lambda _e: self.recargar())
        ttk.Button(cab, text=T("man.limpiar"),
                   command=self._limpiar).pack(side="left", padx=6)

    def _arbol(self, cuerpo):
        izq = ttk.Frame(cuerpo)
        izq.pack(side="left", fill="y")
        self.arbol = ttk.Treeview(izq, show="tree", selectmode="browse",
                                  height=28)
        self.arbol.column("#0", width=300, stretch=False)
        barra = ttk.Scrollbar(izq, orient="vertical", command=self.arbol.yview)
        self.arbol.configure(yscrollcommand=barra.set)
        self.arbol.pack(side="left", fill="y")
        barra.pack(side="left", fill="y")
        self.arbol.bind("<<TreeviewSelect>>", self._elegido)
        self.arbol.tag_configure("cap", font=("Segoe UI", 9, "bold"))

    def _texto(self, cuerpo):
        der = ttk.Frame(cuerpo)
        der.pack(side="left", fill="both", expand=True, padx=(10, 0))
        self.txt = tk.Text(der, wrap="word", relief="flat", padx=14, pady=10,
                           font=("Segoe UI", 10), background="#ffffff",
                           cursor="arrow")
        barra = ttk.Scrollbar(der, orient="vertical", command=self.txt.yview)
        self.txt.configure(yscrollcommand=barra.set)
        self.txt.pack(side="left", fill="both", expand=True)
        barra.pack(side="left", fill="y")

        self.txt.tag_configure("h1", font=("Segoe UI", 14, "bold"),
                               spacing3=8)
        self.txt.tag_configure("h2", font=("Segoe UI", 10, "bold"),
                               foreground=AZUL, spacing1=10, spacing3=3)
        self.txt.tag_configure("cuerpo", spacing1=2, spacing3=7, lmargin1=0,
                               lmargin2=0)
        self.txt.tag_configure("lista", spacing1=2, spacing3=6, lmargin1=12,
                               lmargin2=24)
        self.txt.tag_configure("donde", foreground=GRIS, spacing3=7)
        self.txt.tag_configure("ojo", foreground=ROJO, spacing1=4, spacing3=7)
        self.txt.tag_configure("pie", foreground=GRIS,
                               font=("Segoe UI", 8), spacing1=10)
        self.txt.configure(state="disabled")

    def _pie(self, v):
        pie = ttk.Frame(v, padding=(10, 0, 10, 8))
        pie.pack(fill="x")
        ttk.Label(pie, foreground=GRIS, font=("Segoe UI", 8),
                  text=T("man.pie")).pack(side="left")
        ttk.Button(pie, text=T("bib.cerrar"),
                   command=self.v.destroy).pack(side="right")

    # ------------------------------------------------------------- contenido
    def _cambiar_tomo(self):
        self.tomo = self.var_tomo.get()
        self.recargar()
        self._primero()

    def _limpiar(self):
        self.var_buscar.set("")
        self.recargar()

    def recargar(self):
        """Rehace el arbol, filtrado por lo que haya en el buscador."""
        self.arbol.delete(*self.arbol.get_children())
        self.nodos = {}
        texto = self.var_buscar.get()
        encontrados = M.buscar(self.tomo, texto)

        if encontrados is not None:
            # BUSCA EN LOS DOS TOMOS, no solo en el que tengas abierto.
            #
            # Antes solo miraba el tomo activo, y eso enganaba de verdad:
            # buscando "fov" desde el tomo de reglajes no salia nada, y
            # parecia que el manual no hablaba del campo de vision cuando
            # tiene un apartado entero en el de conduccion.
            otros = [t for t in M.tomos() if t != self.tomo]
            resultados = [(self.tomo, n) for n in encontrados]
            for tomo in otros:
                resultados += [(tomo, n) for n in (M.buscar(tomo, texto) or [])]

            if not resultados:
                self.arbol.insert("", "end", text=T("man.nada"))
                return

            # Si solo hay de un tomo, lista plana. Si hay de los dos, se
            # separan por tomo para que se vea de donde sale cada cosa.
            mezclados = len(set(t for t, _ in resultados)) > 1
            ramas = {}
            for tomo, n in resultados:
                padre = ""
                if mezclados:
                    if tomo not in ramas:
                        ramas[tomo] = self.arbol.insert(
                            "", "end", open=True, tags=("cap",),
                            text=T("man.tomo." + tomo))
                    padre = ramas[tomo]
                linea = self.arbol.insert(padre, "end", text="  " + n["titulo"])
                self.nodos[linea] = n
            return

        for cap, ramas in M.indice(self.tomo):
            padre = self.arbol.insert("", "end", tags=("cap",), open=True,
                                      text=M.texto(cap["titulo"]))
            self.nodos[padre] = {"tipo": "capitulo", "dato": cap}
            for grupo, nodos in ramas:
                destino = padre
                if grupo is not None:
                    destino = self.arbol.insert(
                        padre, "end", open=False,
                        text="  " + M.texto(grupo["titulo"]))
                    self.nodos[destino] = {"tipo": "grupo", "dato": grupo}
                for n in nodos:
                    linea = self.arbol.insert(destino, "end",
                                              text="  " + n["titulo"])
                    self.nodos[linea] = n

    def _primero(self):
        hijos = self.arbol.get_children()
        if hijos:
            self.arbol.selection_set(hijos[0])
            self.arbol.focus(hijos[0])

    def _elegido(self, _e=None):
        sel = self.arbol.selection()
        if not sel:
            return
        nodo = self.nodos.get(sel[0])
        if not nodo:
            return
        # Un resultado del otro tomo cambia el tomo abierto, para que al
        # borrar la busqueda el indice sea el del apartado que estas leyendo
        # y no el de donde venias.
        if nodo.get("tomo") and nodo["tomo"] != self.tomo:
            self.tomo = nodo["tomo"]
            if hasattr(self, "var_tomo"):
                self.var_tomo.set(self.tomo)
        self.pintar(nodo)

    def ir_a_clave(self, clave):
        """Se planta en la ficha del ajuste que le digan, abriendo el arbol."""
        nodo = M.por_clave(clave)
        if not nodo:
            return False
        if nodo["tomo"] != self.tomo:
            self.tomo = nodo["tomo"]
            if hasattr(self, "var_tomo"):
                self.var_tomo.set(self.tomo)
        self.var_buscar.set("")
        self.recargar()
        for linea, n in self.nodos.items():
            if n.get("tipo") == "ficha" and n["id"] == nodo["id"]:
                padre = self.arbol.parent(linea)
                while padre:
                    self.arbol.item(padre, open=True)
                    padre = self.arbol.parent(padre)
                self.arbol.selection_set(linea)
                self.arbol.focus(linea)
                self.arbol.see(linea)
                return True
        return False

    # ---------------------------------------------------------------- pintar
    def _escribir(self, texto, *tags):
        self.txt.insert("end", texto + "\n", tags)

    def pintar(self, nodo):
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.enlaces = {}

        tipo = nodo.get("tipo")
        if tipo == "capitulo":
            self._pintar_capitulo(nodo["dato"])
        elif tipo == "grupo":
            self._pintar_grupo(nodo["dato"])
        elif tipo == "ficha":
            self._pintar_ficha(nodo["dato"])
        elif tipo == "receta":
            self._pintar_receta(nodo["dato"])
        else:
            self._pintar_tema(nodo["dato"])

        self.txt.configure(state="disabled")
        self.txt.yview_moveto(0)

    def _pintar_capitulo(self, cap):
        self._escribir(M.texto(cap["titulo"]), "h1")
        for parrafo in M.parrafos(cap.get("entrada")):
            self._escribir(parrafo, "cuerpo")
        if not cap.get("entrada"):
            self._escribir(T("man.elige"), "donde")

    def _pintar_grupo(self, grupo):
        self._escribir(M.texto(grupo["titulo"]), "h1")
        self._escribir(T("man.elige"), "donde")

    def _pintar_tema(self, tema):
        self._escribir(M.texto(tema.get("titulo")), "h1")
        for parrafo in M.parrafos(tema.get("texto")):
            self._escribir(parrafo, "cuerpo")
        if tema.get("boton"):
            self._boton(tema["boton"])

    # Las herramientas que el manual puede abrir desde un apartado. El
    # manual solo dice el nombre de la accion; que abre cada una se decide
    # aqui, para que el archivo de texto no sepa nada de codigo.
    HERRAMIENTAS = {"fov": ("fov_gui", "fov.abrir")}

    def _boton(self, ficha):
        """
        Un boton dentro del texto, para la herramienta que trate ese
        apartado. De momento solo la calculadora de campo de vision: el
        manual dice que es lo primero que hay que ajustar, y mandar a la
        gente a buscarla fuera seria dejar el trabajo a medias.
        """
        que = self.HERRAMIENTAS.get(ficha.get("accion"))
        if not que:
            return
        modulo, clave = que
        self.txt.insert("end", "\n")
        boton = ttk.Button(self.txt, text=T(clave),
                           command=lambda m=modulo: self._abrir_herramienta(m))
        self.txt.window_create("end", window=boton, padx=14, pady=6)
        self.txt.insert("end", "\n")

    def _abrir_herramienta(self, modulo):
        import importlib
        try:
            importlib.import_module(modulo).abrir(self.v)
        except Exception:
            pass

    def _pintar_receta(self, r):
        self._escribir(M.texto(r["titulo"]), "h1")
        self._escribir(T("man.sintoma"), "h2")
        self._escribir(M.texto(r["sintoma"]), "cuerpo")
        # El tomo de conduccion usa su propio encabezado ("QUE HACER"), que
        # aqui casi nada se toca en el garaje.
        cabecera = M.texto(r.get("pasos_titulo")) or T("man.pasos")
        self._escribir(cabecera, "h2")
        for paso in M.parrafos(r["pasos"]):
            self._escribir(paso, "lista")
        if r.get("ojo"):
            self._escribir(T("man.ojo"), "h2")
            self._escribir(M.texto(r["ojo"]), "ojo")

    def _pintar_ficha(self, f):
        self._escribir(M.texto(f["nombre"]), "h1")
        pagina = M.texto(f.get("pagina"))
        if pagina:
            self._escribir(T("man.en_el_juego") % pagina, "donde")

        for clave_txt, campo, tag in (
                ("man.que_es", "que_es", "cuerpo"),
                ("man.subir", "subir", "cuerpo"),
                ("man.bajar", "bajar", "cuerpo"),
                ("man.donde", "donde", "cuerpo")):
            if f.get(campo):
                self._escribir(T(clave_txt), "h2")
                self._escribir(M.texto(f[campo]), tag)

        if f.get("combina"):
            self._escribir(T("man.combina"), "h2")
            for c in f["combina"]:
                self._enlace(c["clave"])
                self._escribir(M.texto(c), "lista")

        if f.get("ojo"):
            self._escribir(T("man.ojo"), "h2")
            self._escribir(M.texto(f["ojo"]), "ojo")

        self._escribir(T("man.claves") % ", ".join(f["claves"]), "pie")

    def _enlace(self, clave):
        """
        El nombre del ajuste con el que se combina, como enlace azul.

        Se pinta el nombre bonito sacado de la propia ficha destino, no la
        clave tecnica: quien lee el manual no tiene por que saber que
        'SUSPENSION/RearAntiSwaySetting' es la barra de atras.
        """
        destino = M.por_clave(clave)
        if not destino:
            return
        tag = "enlace%d" % len(self.enlaces)
        self.enlaces[tag] = clave
        self.txt.tag_configure(tag, foreground=AZUL, underline=True,
                               font=("Segoe UI", 10, "bold"), lmargin1=12,
                               lmargin2=24, spacing1=6)
        self.txt.tag_bind(tag, "<Button-1>",
                          lambda _e, c=clave: self.ir_a_clave(c))
        self.txt.tag_bind(tag, "<Enter>",
                          lambda _e: self.txt.configure(cursor="hand2"))
        self.txt.tag_bind(tag, "<Leave>",
                          lambda _e: self.txt.configure(cursor="arrow"))
        self.txt.insert("end", destino["titulo"] + "\n", (tag,))
