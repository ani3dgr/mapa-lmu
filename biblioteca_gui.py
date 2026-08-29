# -*- coding: utf-8 -*-
"""
La ventana de la biblioteca de reglajes.

Va en ventana aparte y no como una pestana mas de opciones porque necesita
ancho: son ochenta reglajes con siete columnas, y la ventana de opciones ya
se quedo corta de alto una vez.

Aqui solo esta lo que se ve y lo que se pulsa. Todo lo que sabe de reglajes
esta en biblioteca.py, que no importa tkinter y se puede probar solo.
"""
import os
import shutil
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import biblioteca as B
import idiomas
import ingenieria
import editor_gui
import ingeniero_gui
import juego
import rutas

T = idiomas.t

# Donde se guarda el reglaje original antes de tocarlo. Se guarda SIEMPRE,
# aunque el cambio parezca inofensivo: son archivos que la gente ha pagado
# y el programa no puede ser el motivo de que pierda uno.
COPIAS = rutas.datos("copias_reglajes")

SESIONES = ["Qualy", "Race", "Endu"]
ESTILOS = ["Safe", "Fast"]

ROJO = "#b03a2e"
AMBAR = "#b9770e"
VERDE = "#1e7a44"


def settings():
    """La carpeta del juego donde viven los reglajes."""
    return juego.subcarpeta("UserData", "player", "Settings")


class Biblioteca:
    """La ventana. `padre` es la ventana de opciones que la abre."""

    def __init__(self, padre):
        self.padre = padre
        self.fichas = {}          # id de fila -> ficha leida
        self.datos = {}           # id de fila -> lo que sabemos, ya corregido
        self.asignados = {}       # ruta -> lo que el juego tiene asignado
        self.ultimo_asignado = None
        self.primera_vez = True

        v = tk.Toplevel(padre)
        self.v = v
        v.title(T("bib.titulo"))
        v.attributes("-topmost", True)
        # Se mide la pantalla antes de decidir el tamano: en un portatil con
        # el escalado de Windows al 150%, una ventana "de 1400" se sale por
        # el borde y no hay manera de llegar a los botones de abajo.
        ancho = min(1330, v.winfo_screenwidth() - 80)
        alto = min(700, v.winfo_screenheight() - 120)
        v.geometry("%dx%d" % (ancho, alto))
        v.minsize(900, 460)

        self._barra(v)
        self._mirar_el_juego()
        self._tabla(v)
        self._detalle(v)
        self._pie(v)
        self.recargar()
        self._primera_calibracion()

    def _primera_calibracion(self):
        """
        La primera vez que se abre la biblioteca, se calibra sola.

        Asi el ingeniero funciona bien desde el minuto uno sin que nadie
        tenga que saber que existe un boton llamado "aprender". Despues ya
        solo se recalibra cuando se pulsa, que es cuando hay reglajes
        nuevos que aprender.
        """
        if os.path.exists(ingenieria.RUTA_CALIBRACION):
            return
        base = settings()
        if not base:
            return
        try:
            ingenieria.calibrar(base)
        except OSError:
            pass

    # ------------------------------------------------------------ montaje
    def _barra(self, v):
        barra = ttk.Frame(v, padding=(10, 8))
        barra.pack(fill="x")

        ttk.Button(barra, text=T("bib.importar"),
                   command=self.importar).pack(side="left")

        ttk.Label(barra, text=T("bib.circuito")).pack(side="left", padx=(16, 4))
        self.circuito = tk.StringVar(value=T("bib.todos"))
        self.combo_circuito = ttk.Combobox(barra, textvariable=self.circuito,
                                           state="readonly", width=24)
        self.combo_circuito.pack(side="left")
        self.combo_circuito.bind("<<ComboboxSelected>>", lambda _: self.recargar())

        self.solo_malos = tk.BooleanVar(value=False)
        ttk.Checkbutton(barra, text=T("bib.solo_problemas"),
                        variable=self.solo_malos,
                        command=self.recargar).pack(side="left", padx=(16, 0))

        ttk.Button(barra, text=T("bib.duplicados"),
                   command=self.ver_duplicados).pack(side="right")
        ttk.Button(barra, text=T("bib.calibrar"),
                   command=self.calibrar).pack(side="right", padx=(0, 8))

        # La franja de "que llevas puesto en el juego". Va debajo de la
        # barra y no en la tabla porque es lo primero que hay que mirar
        # cuando vienes de dar vueltas y quieres retocar algo.
        franja = ttk.Frame(v, padding=(10, 0))
        franja.pack(fill="x")
        self.en_juego = ttk.Label(franja, text="", justify="left")
        self.en_juego.pack(side="left")
        tk.Button(franja, text=" ? ", font=("Segoe UI", 7, "bold"),
                  fg="white", bg="#3a7bd5", relief="groove",
                  command=self._explicar_asignado).pack(side="left", padx=(8, 0))

    def _explicar_asignado(self):
        messagebox.showinfo(T("bib.titulo"), T("bib.asignado_ayuda"),
                            parent=self.v)

    def _mirar_el_juego(self):
        """
        Lee del propio juego que reglaje tiene asignado para el coche y el
        circuito de la ultima vez.

        No se adivina nada: o el juego lo tiene escrito o no se dice.
        """
        try:
            lista = [a for a in B.asignados(juego.subcarpeta("UserData", "player"))
                     if a["existe"]]
        except Exception:
            lista = []
        self.asignados = {os.path.abspath(a["ruta"]).lower(): a for a in lista}
        self.ultimo_asignado = None
        if not lista:
            self.en_juego.configure(text=T("bib.sin_asignar"), foreground="#777")
            return

        # El juego guarda un reglaje asignado por cada circuito y coche.
        # Solo uno es el de donde estas ahora, y para saber cual hay que
        # preguntarle al juego. Si esta cerrado, no se sabe y se dice.
        suyo = B.el_que_llevas(juego.subcarpeta("UserData", "player"))
        if suyo:
            self.ultimo_asignado = os.path.abspath(suyo["ruta"]).lower()
            self.en_juego.configure(
                text=T("bib.en_juego") % (suyo["nombre"], suyo["circuito"]),
                foreground=VERDE)
        else:
            self.en_juego.configure(
                text=T("bib.varios_asignados") % len(self.asignados),
                foreground="#555")

    def _tabla(self, v):
        marco = ttk.Frame(v, padding=(10, 0))
        marco.pack(fill="both", expand=True)

        # Los anchos salen de medir los nombres de verdad, no a ojo: el
        # nombre mas largo que puede salir ocupa unos sesenta caracteres, y
        # con la columna estrecha se cortaba justo lo unico que hay que
        # leer. Mejor sobrar de ancho que cortar un nombre.
        cols = ("actual", "nuevo", "coche", "cat", "tipo", "gasolina", "fuente")
        anchos = (400, 330, 140, 62, 128, 132, 66)
        self.tabla = ttk.Treeview(marco, columns=cols, show="headings",
                                  selectmode="extended")
        for c, a in zip(cols, anchos):
            self.tabla.heading(c, text=T("bib.col." + c))
            self.tabla.column(c, width=a, minwidth=60,
                              stretch=(c in ("actual", "nuevo")))

        barra = ttk.Scrollbar(marco, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=barra.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="left", fill="y")

        self.tabla.tag_configure("malo", foreground=ROJO)
        self.tabla.tag_configure("sobra", foreground=AMBAR)
        self.tabla.tag_configure("dudoso", foreground="#666")
        # Dos marcas distintas a proposito: el reglaje de donde estas AHORA
        # en verde y en negrita, y los demas que tengas asignados en un
        # tono apagado. Marcandolos todos igual, diez reglajes en verde no
        # decian nada y encima parecia que llevabas diez puestos.
        self.tabla.tag_configure("enjuego", foreground=VERDE,
                                 font=("Segoe UI", 9, "bold"))
        self.tabla.tag_configure("asignado", foreground="#7a8b7f")
        self.tabla.bind("<<TreeviewSelect>>", self._elegido)

    def _detalle(self, v):
        m = ttk.LabelFrame(v, text=T("bib.detalle"), padding=(10, 6))
        m.pack(fill="x", padx=10, pady=(8, 0))

        self.rotulo = ttk.Label(m, text=T("bib.nada"), foreground="#555")
        self.rotulo.grid(row=0, column=0, columnspan=8, sticky="w", pady=(0, 6))

        self.v_sesion = tk.StringVar()
        self.v_estilo = tk.StringVar()
        self.v_mojado = tk.BooleanVar()

        ttk.Label(m, text=T("bib.sesion")).grid(row=1, column=0, sticky="e")
        self.c_sesion = ttk.Combobox(m, textvariable=self.v_sesion, width=10,
                                     state="readonly", values=SESIONES)
        self.c_sesion.grid(row=1, column=1, padx=(4, 14))
        self.c_sesion.bind("<<ComboboxSelected>>", lambda _: self._corregir())

        ttk.Label(m, text=T("bib.estilo")).grid(row=1, column=2, sticky="e")
        self.c_estilo = ttk.Combobox(m, textvariable=self.v_estilo, width=10,
                                     state="readonly", values=ESTILOS)
        self.c_estilo.grid(row=1, column=3, padx=(4, 14))
        self.c_estilo.bind("<<ComboboxSelected>>", lambda _: self._corregir())

        ttk.Checkbutton(m, text=T("bib.lluvia"), variable=self.v_mojado,
                        command=self._corregir).grid(row=1, column=4, padx=(0, 14))

        self.nombre_final = ttk.Label(m, text="", font=("Consolas", 10, "bold"))
        self.nombre_final.grid(row=1, column=5, sticky="w")

    def _pie(self, v):
        pie = ttk.Frame(v, padding=(10, 8))
        pie.pack(fill="x")
        ttk.Button(pie, text=T("bib.cuadrar"),
                   command=self.cuadrar).pack(side="left")
        ttk.Button(pie, text=T("bib.renombrar"),
                   command=self.renombrar).pack(side="left", padx=(8, 0))
        ttk.Button(pie, text=T("bib.comparar"),
                   command=self.comparar).pack(side="left", padx=(8, 0))
        ttk.Button(pie, text=T("bib.ingeniero"),
                   command=self.ingeniero).pack(side="left", padx=(8, 0))
        ttk.Button(pie, text=T("bib.editar"),
                   command=self.editar).pack(side="left", padx=(8, 0))
        self.estado = ttk.Label(pie, text="", foreground="#555")
        self.estado.pack(side="left", padx=(16, 0))
        ttk.Button(pie, text=T("bib.cerrar"),
                   command=self.v.destroy).pack(side="right")

    # ------------------------------------------------------------- llenar
    def recargar(self):
        base = settings()
        if not base or not os.path.isdir(base):
            self.estado.configure(text=T("bib.sin_juego"), foreground=ROJO)
            return

        circuitos = B.circuitos_del_juego(base)
        self.combo_circuito.configure(values=[T("bib.todos")] + circuitos)
        elegido = self.circuito.get()
        if elegido != T("bib.todos") and elegido not in circuitos:
            self.circuito.set(T("bib.todos"))
            elegido = T("bib.todos")

        self._mirar_el_juego()
        self.tabla.delete(*self.tabla.get_children())
        self.fichas.clear()
        self.datos.clear()

        mirar = circuitos if elegido == T("bib.todos") else [elegido]
        malos = 0
        for circuito in mirar:
            carpeta = os.path.join(base, circuito)
            for archivo in sorted(os.listdir(carpeta)):
                if not archivo.lower().endswith(".svm"):
                    continue
                ficha = B.leer(os.path.join(carpeta, archivo))
                if not ficha:
                    continue
                d = B.describir(ficha)
                c = d["combustible"]
                if c and c["estado"] == "malo":
                    malos += 1
                if self.solo_malos.get() and not (c and c["estado"] == "malo"):
                    continue
                self._fila(circuito, ficha, d)

        self.estado.configure(
            text=T("bib.resumen") % (len(self.fichas), malos),
            foreground=ROJO if malos else "#555")
        self._marcar_los_del_juego(ir_a_el=self.primera_vez)
        self.primera_vez = False

    def _marcar_los_del_juego(self, ir_a_el=False):
        """
        Pone una marca en las filas que el juego tiene asignadas y, la
        primera vez, baja hasta el que llevas puesto.

        Lo de bajar hasta el no es un adorno. La lista va por orden
        alfabetico y el que llevas puesto puede caer en la fila sesenta de
        noventa: se ponia en verde pero quedaba fuera de la pantalla, asi
        que el programa te decia arriba que llevabas un reglaje y luego te
        tocaba buscarlo a mano. Si te lo dice, te lo ensena.
        """
        suyo = None
        for fid, ficha in self.fichas.items():
            if os.path.abspath(ficha["ruta"]).lower() in self.asignados:

                es_el_de_ahora = (self.ultimo_asignado and
                                  os.path.abspath(ficha["ruta"]).lower()
                                  == self.ultimo_asignado)
                if es_el_de_ahora:
                    actual = self.tabla.set(fid, "actual")
                    if not actual.startswith("► "):
                        self.tabla.set(fid, "actual", "► " + actual)
                self.tabla.item(fid, tags=("enjuego" if es_el_de_ahora
                                           else "asignado",))
                if es_el_de_ahora and suyo is None:
                    suyo = fid
        if ir_a_el and suyo:
            self.tabla.selection_set(suyo)
            self.tabla.focus(suyo)
            self.tabla.see(suyo)
            self._elegido()

    def _fila(self, circuito, ficha, d):
        c = d["combustible"]
        if not c:
            gasolina, tag = T("bib.sin_energia"), ""
        elif c["estado"] == "malo":
            gasolina = T("bib.faltan") % c["faltan"]
            tag = "malo"
        elif c["estado"] == "sobra":
            gasolina = T("bib.sobran") % (c["gasolina"] - c["energia"])
            tag = "sobra"
        else:
            gasolina, tag = T("bib.gasolina_ok") % c["gasolina"], ""

        tipo = "%s / %s / %s" % (T("bib.wet") if d["mojado"] else T("bib.dry"),
                                 d["sesion"], d["estilo"])
        fid = self.tabla.insert(
            "", "end", tags=(tag,) if tag else (),
            values=(("%s  ·  %s" % (circuito, ficha["nombre"]))[:60],
                    B.nombre_propuesto(d),
                    d["coche"]["corto"], d["coche"]["categoria"],
                    tipo, gasolina, d["fuente"]))
        self.fichas[fid] = ficha
        self.datos[fid] = d

    # ------------------------------------------------------------ detalle
    def _uno(self):
        sel = self.tabla.selection()
        return sel[0] if len(sel) == 1 else None

    def _elegido(self, _=None):
        fid = self._uno()
        if not fid:
            self.rotulo.configure(text=T("bib.varios") % len(self.tabla.selection())
                                  if self.tabla.selection() else T("bib.nada"))
            self.nombre_final.configure(text="")
            return
        ficha, d = self.fichas[fid], self.datos[fid]
        self.v_sesion.set(d["sesion"])
        self.v_estilo.set(d["estilo"])
        self.v_mojado.set(d["mojado"])

        pista = "" if d.get("mojado_seguro", True) else "   " + T("bib.por_el_nombre")
        # El detector compara contra los demas reglajes del MISMO coche y
        # circuito: comparar un Lexus con un Porsche no dice nada.
        hermanos = [f for f in self.fichas.values()
                    if f["circuito"] == ficha["circuito"]
                    and B.coche_de(f)["corto"] == d["coche"]["corto"]]
        det = ingenieria.detectar(ficha, hermanos)
        if det["confianza"]:
            pista += "   " + T("bib.confianza") % det["confianza"]
        self.rotulo.configure(text="%s   ·   %s%s" % (ficha["nombre"],
                                                      ficha["clase"], pista))
        self.nombre_final.configure(text=B.nombre_propuesto(d))

    def _corregir(self):
        """Lo que toca la persona manda sobre lo que adivino el programa."""
        fid = self._uno()
        if not fid:
            return
        d = self.datos[fid]
        d["sesion"] = self.v_sesion.get()
        d["estilo"] = self.v_estilo.get()
        d["mojado"] = self.v_mojado.get()
        d["mojado_seguro"] = True
        nuevo = B.nombre_propuesto(d)
        self.nombre_final.configure(text=nuevo)
        self.tabla.set(fid, "nuevo", nuevo)
        self.tabla.set(fid, "tipo", "%s / %s / %s" % (
            T("bib.wet") if d["mojado"] else T("bib.dry"),
            d["sesion"], d["estilo"]))

    # ------------------------------------------------------------ acciones
    def _copia(self, ruta):
        """Guarda el original antes de tocarlo. Devuelve si pudo."""
        try:
            destino = os.path.join(COPIAS,
                                   os.path.basename(os.path.dirname(ruta)))
            os.makedirs(destino, exist_ok=True)
            shutil.copy2(ruta, B.sin_pisar(os.path.join(
                destino, os.path.basename(ruta))))
            return True
        except OSError:
            return False

    def renombrar(self):
        """
        Pone a los reglajes elegidos el nombre nuevo.

        No se machaca nunca un archivo que ya exista: si el nombre esta
        cogido se numera. Un reglaje que se pierde puede ser una carrera
        perdida, y el programa no va a ser el culpable.
        """
        sel = self.tabla.selection()
        if not sel:
            messagebox.showinfo(T("bib.titulo"), T("bib.elige"), parent=self.v)
            return
        if not messagebox.askyesno(T("bib.titulo"),
                                   T("bib.confirmar_renombrar") % len(sel),
                                   parent=self.v):
            return

        hechos = 0
        for fid in sel:
            ficha, d = self.fichas[fid], self.datos[fid]
            nuevo = B.nombre_propuesto(d) + ".svm"
            destino = os.path.join(os.path.dirname(ficha["ruta"]), nuevo)
            if os.path.abspath(destino) == os.path.abspath(ficha["ruta"]):
                continue
            try:
                os.rename(ficha["ruta"], B.sin_pisar(destino))
                hechos += 1
            except OSError:
                pass
        self.recargar()
        self.estado.configure(text=T("bib.renombrados") % hechos,
                              foreground=VERDE)

    def cuadrar(self):
        """
        Arregla los reglajes a los que no les llega la gasolina.

        Es el boton que le habria ahorrado a alguien quedarse tirado en la
        primera vuelta de una clasificacion. Solo toca la linea del
        combustible; el resto del reglaje se queda exactamente igual.
        """
        sel = self.tabla.selection() or self.tabla.get_children()
        pendientes = [f for f in sel if B.cuadrar(self.fichas[f])]
        if not pendientes:
            messagebox.showinfo(T("bib.titulo"), T("bib.nada_que_cuadrar"),
                                parent=self.v)
            return
        if not messagebox.askyesno(T("bib.titulo"),
                                   T("bib.confirmar_cuadrar") % len(pendientes),
                                   parent=self.v):
            return

        hechos = 0
        for fid in pendientes:
            ficha = self.fichas[fid]
            self._copia(ficha["ruta"])
            if B.guardar_cuadrado(ficha):
                hechos += 1
        self.recargar()
        self.estado.configure(text=T("bib.cuadrados") % hechos, foreground=VERDE)

    def comparar(self):
        """Las diferencias entre dos reglajes, que hay que elegir a pares."""
        sel = self.tabla.selection()
        if len(sel) != 2:
            messagebox.showinfo(T("bib.titulo"), T("cmp.elige_dos"),
                                parent=self.v)
            return
        ingeniero_gui.Comparar(self.v, self.fichas[sel[0]], self.fichas[sel[1]])

    def ingeniero(self):
        """El de los sintomas, sobre el reglaje que este elegido."""
        fid = self._uno()
        if not fid:
            messagebox.showinfo(T("bib.titulo"), T("ing.elige_uno"),
                                parent=self.v)
            return
        ingeniero_gui.Ingeniero(self.v, self.fichas[fid],
                                ingenieria.leer_calibracion(), self.recargar)

    def editar(self):
        """
        Abre el reglaje elegido en el editor, en ventana aparte.

        Es el mismo editor que hay en la pestana Reglajes: se monta dentro
        de un hueco cualquiera, asi que sirve en los dos sitios sin tener
        dos versiones que mantener.
        """
        fid = self._uno()
        if not fid:
            messagebox.showinfo(T("bib.titulo"), T("ing.elige_uno"),
                                parent=self.v)
            return
        VentanaEditor(self.v, self.fichas[fid], self.recargar)

    def calibrar(self):
        """
        Vuelve a aprender de todos los reglajes que haya en el ordenador.

        Cuanto mas reglaje bueno tengas, mejor sabe el programa de cuanto en
        cuanto conviene mover cada cosa. Se guardan numeros, no reglajes.
        """
        base = settings()
        if not base:
            messagebox.showerror(T("bib.titulo"), T("bib.sin_juego"),
                                 parent=self.v)
            return
        self.v.configure(cursor="watch")
        self.v.update()
        try:
            c = ingenieria.calibrar(base)
        finally:
            self.v.configure(cursor="")
        messagebox.showinfo(T("bib.titulo"),
                            T("cal.hecho") % (c["reglajes_mirados"],
                                              sum(len(v) for v in c["pasos"].values())),
                            parent=self.v)

    def ver_duplicados(self):
        grupos = B.buscar_duplicados(list(self.fichas.values()))
        if not grupos:
            messagebox.showinfo(T("bib.titulo"), T("bib.sin_duplicados"),
                                parent=self.v)
            return
        lineas = []
        for g in grupos:
            lineas.append("· " + "\n  ".join(
                "%s  (%s)" % (f["nombre"], f["circuito"]) for f in g))
        messagebox.showinfo(T("bib.titulo"),
                            T("bib.hay_duplicados") % len(grupos)
                            + "\n\n" + "\n\n".join(lineas[:12]),
                            parent=self.v)

    # ----------------------------------------------------------- importar
    def importar(self):
        base = settings()
        if not base:
            messagebox.showerror(T("bib.titulo"), T("bib.sin_juego"),
                                 parent=self.v)
            return
        elegidos = filedialog.askopenfilenames(
            parent=self.v, title=T("bib.importar"),
            filetypes=[(T("bib.tipos"), "*.svm *.zip"),
                       ("Reglajes", "*.svm"), ("Comprimidos", "*.zip")])
        if not elegidos:
            return

        # De un comprimido salen muchos de golpe. Se sacan a un sitio
        # temporal de Windows, que se limpia solo, y de ahi se reparten por
        # circuitos. En la carpeta del programa no, que se iria llenando de
        # restos de cada importacion.
        temporal = tempfile.mkdtemp(prefix="reglajes_")
        sueltos = []
        for ruta in elegidos:
            if ruta.lower().endswith(".zip"):
                sueltos += B.desempaquetar(ruta, temporal)
            else:
                sueltos.append((ruta, ""))
        if not sueltos:
            messagebox.showwarning(T("bib.titulo"), T("bib.zip_vacio"),
                                   parent=self.v)
            return
        Destino(self.v, sueltos, base, self.recargar)


class Destino:
    """
    La ventana que decide a que circuito va cada reglaje importado.

    Hace falta porque el circuito NO esta escrito dentro del archivo: lo
    dice la carpeta donde vive. El programa lo adivina por el nombre (los
    packs abrevian, SIL es Silverstone) pero cuando no lo tiene claro
    prefiere preguntar antes que colar un reglaje en el circuito
    equivocado, que es de las cosas que mas se tarda en descubrir.
    """

    def __init__(self, padre, sueltos, base, al_terminar):
        self.base = base
        self.al_terminar = al_terminar
        self.circuitos = B.circuitos_del_juego(base)

        v = tk.Toplevel(padre)
        self.v = v
        v.title(T("bib.destino"))
        v.attributes("-topmost", True)
        v.geometry("760x460")

        ttk.Label(v, padding=(10, 8), justify="left",
                  text=T("bib.destino_ayuda")).pack(fill="x")

        marco = ttk.Frame(v, padding=(10, 0))
        marco.pack(fill="both", expand=True)
        self.tabla = ttk.Treeview(marco, columns=("archivo", "coche", "circuito"),
                                  show="headings", selectmode="extended")
        for c, a in (("archivo", 300), ("coche", 140), ("circuito", 200)):
            self.tabla.heading(c, text=T("bib.col." + c))
            self.tabla.column(c, width=a)
        self.tabla.tag_configure("falta", foreground=ROJO)
        self.tabla.pack(side="left", fill="both", expand=True)
        barra = ttk.Scrollbar(marco, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=barra.set)
        barra.pack(side="left", fill="y")

        elegir = ttk.Frame(v, padding=(10, 8))
        elegir.pack(fill="x")
        ttk.Label(elegir, text=T("bib.poner_en")).pack(side="left")
        self.cual = tk.StringVar()
        ttk.Combobox(elegir, textvariable=self.cual, values=self.circuitos,
                     state="readonly", width=28).pack(side="left", padx=6)
        ttk.Button(elegir, text=T("bib.asignar"),
                   command=self.asignar).pack(side="left")
        ttk.Button(elegir, text=T("bib.copiar_aqui"),
                   command=self.copiar).pack(side="right")

        self.rutas = {}
        for ruta, carpeta in sueltos:
            ficha = B.leer(ruta)
            if not ficha:
                continue
            coche = B.coche_de(ficha)["corto"]
            adivinado = B.adivinar_circuito(
                [os.path.basename(ruta), carpeta, coche], self.circuitos)
            fid = self.tabla.insert("", "end",
                                    tags=() if adivinado else ("falta",),
                                    values=(os.path.basename(ruta), coche,
                                            adivinado or T("bib.elige_circuito")))
            self.rutas[fid] = ruta

    def asignar(self):
        cual = self.cual.get()
        if not cual:
            return
        for fid in self.tabla.selection():
            self.tabla.set(fid, "circuito", cual)
            self.tabla.item(fid, tags=())

    def copiar(self):
        """Copia cada reglaje a la carpeta de su circuito."""
        listos = [(f, self.tabla.set(f, "circuito")) for f in self.rutas
                  if self.tabla.set(f, "circuito") in self.circuitos]
        if not listos:
            messagebox.showinfo(T("bib.destino"), T("bib.falta_circuito"),
                                parent=self.v)
            return
        faltan = len(self.rutas) - len(listos)
        hechos = 0
        for fid, circuito in listos:
            try:
                destino = B.sin_pisar(os.path.join(
                    self.base, circuito, os.path.basename(self.rutas[fid])))
                shutil.copy2(self.rutas[fid], destino)
                hechos += 1
            except OSError:
                pass
        messagebox.showinfo(T("bib.destino"),
                            T("bib.importados") % (hechos, faltan),
                            parent=self.v)
        self.v.destroy()
        self.al_terminar()


def abrir(padre):
    Biblioteca(padre)


class VentanaEditor:
    """El editor en ventana propia, para abrirlo desde la biblioteca."""

    def __init__(self, padre, ficha, al_guardar=None):
        v = tk.Toplevel(padre)
        self.v = v
        v.title(T("ed.titulo"))
        v.attributes("-topmost", True)
        v.geometry("760x640")

        marco = ttk.Frame(v, padding=10)
        marco.pack(fill="both", expand=True)
        self.editor = editor_gui.Editor(marco, al_guardar=al_guardar)
        self.editor.cargar(ficha)
        ttk.Button(v, text=T("bib.cerrar"),
                   command=v.destroy).pack(side="right", padx=10, pady=(0, 10))
