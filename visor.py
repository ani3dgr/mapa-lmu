# -*- coding: utf-8 -*-
"""
Ventana para comparar trazadas de las sesiones grabadas.

Arriba a la izquierda, las sesiones agrupadas por evento: si en el mismo
circuito y el mismo dia haces practica, clasificacion y carrera, las tres
cuelgan de la misma linea. Solo empieza una linea nueva al cambiar de circuito
o de dia.

Debajo, lo que se puede dibujar: la vuelta del rival mas rapido y todas tus
vueltas, cada una en su linea con su tiempo. Se marcan con el raton (varias con
Ctrl) y aparecen en el mapa.

COMO SE COLOREA TU TRAZADA -- esto es lo importante:

  * Con UNA sola vuelta tuya marcada se dibuja en tres colores comparandola con
    el rival: rojo donde ibas mas lento, amarillo igual y verde mas rapido.
  * Con VARIAS marcadas, cada una lleva su propio color liso. Con el tricolor
    no se sabria cual es cual al superponerse.

O sea: una vuelta para ver donde ganas y pierdes, varias para comparar por
donde pasa cada una.
"""
import math
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser

import idiomas
import grabador as grab
import lector_lmu as lmu

# colores para distinguir varias vueltas propias dibujadas a la vez
PALETA = ["#ffffff", "#ff9f0a", "#5ac8fa", "#ff2d92", "#a0e548", "#d0a0ff"]
TOLERANCIA_KMH = 2.0
SUAVIZADO = 15       # puntos promediados antes de decidir el color.
                     # Con 15 salen zonas de unos 220 m, que es el tamano
                     # de una curva con su frenada. Con menos sale confeti.

# aspecto del dibujo; se guarda en mapa_config.json como todo lo demas
ASPECTO = {
    "visor_color_borde": "#7a7a7a",
    "visor_grosor_borde": 2,
    "visor_color_trazado": "#3a3a3a",
    "visor_grosor_trazado": 1,
    "visor_grosor_referencia": 3,
    "visor_grosor_vuelta": 3,
}

# que se puede retocar y con que controles
def ajustes():
    """Se calcula al abrir la ventana, no al importar: asi sale en el
    idioma elegido aunque se cambie sin cerrar el programa."""
    T = idiomas.t
    return [
        (T("vis.aj_circuito"),
         [(T("vis.aj_bordes"), "color", "visor_color_borde"),
          (T("vis.aj_grosor"), "grosor", "visor_grosor_borde"),
          (T("vis.aj_guia"), "color", "visor_color_trazado"),
          (T("vis.aj_grosor"), "grosor", "visor_grosor_trazado")]),
        (T("vis.aj_rival"),
         [(T("vis.aj_color"), "color", "color_referencia"),
          (T("vis.aj_grosor"), "grosor", "visor_grosor_referencia")]),
        (T("vis.aj_mias"),
         [(T("vis.aj_lento"), "color", "color_lento"),
          (T("vis.aj_igual"), "color", "color_igual"),
          (T("vis.aj_rapido"), "color", "color_rapido"),
          (T("vis.aj_grosor"), "grosor", "visor_grosor_vuelta")]),
    ]


def ordenes():
    return [idiomas.t("vis.orden_nuevas"), idiomas.t("vis.orden_viejas"),
            idiomas.t("vis.orden_circuito")]


def reloj(segundos):
    if not segundos or segundos <= 0:
        return "--"
    m = int(segundos // 60)
    return "%d:%06.3f" % (m, segundos - m * 60)


def fecha_bonita(marca):
    """'20260824_1301' -> '24/08 13:01'"""
    if len(marca) >= 13 and "_" in marca:
        d, h = marca.split("_", 1)
        return "%s/%s %s:%s" % (d[6:8], d[4:6], h[:2], h[2:4])
    return marca


class Visor:
    def __init__(self, padre, cfg):
        self.cfg = cfg
        for clave, valor in ASPECTO.items():
            self.cfg.setdefault(clave, valor)
        self.sesiones = []
        self.filas = {}
        self.datos = None
        self.circuito = None
        self.zoom = 1.0
        self.centro = None
        self.arrastre = None
        self._vars = {}

        v = tk.Toplevel(padre)
        self.v = v
        v.title(idiomas.t("vis.titulo"))
        v.geometry("1180x720")
        v.attributes("-topmost", True)

        partido = ttk.PanedWindow(v, orient="horizontal")
        partido.pack(fill="both", expand=True)
        izq = ttk.Frame(partido, padding=8)
        der = ttk.Frame(partido)
        partido.add(izq, weight=0)
        partido.add(der, weight=1)

        self._panel_sesiones(izq)
        self._panel_vueltas(izq)
        self._barra(der)

        self.lienzo = tk.Canvas(der, bg="#141414", highlightthickness=0)
        self.lienzo.pack(fill="both", expand=True)
        self.lienzo.bind("<MouseWheel>", self._rueda)
        self.lienzo.bind("<Button-1>", lambda e: setattr(self, "arrastre", (e.x, e.y)))
        self.lienzo.bind("<B1-Motion>", self._arrastrar)
        self.lienzo.bind("<Configure>", lambda e: self._pintar())

        self._recargar()

    # ---------------- paneles ----------------
    def _panel_sesiones(self, padre):
        cab = ttk.Frame(padre)
        cab.pack(fill="x")
        ttk.Label(cab, text=idiomas.t("vis.sesiones"),
                  font=("Segoe UI", 10, "bold")).pack(side="left")
        ORDENES = ordenes()
        self.var_orden = tk.StringVar(value=ORDENES[0])
        combo = ttk.Combobox(cab, textvariable=self.var_orden, values=ORDENES,
                             state="readonly", width=20)
        combo.pack(side="right")
        combo.bind("<<ComboboxSelected>>", lambda e: self._recargar())

        marco = ttk.Frame(padre)
        marco.pack(fill="x", pady=(2, 4))
        self.arbol = ttk.Treeview(marco, columns=("coche", "vueltas"), height=8,
                                  selectmode="browse")
        self.arbol.heading("#0", text=idiomas.t("vis.col_sesion"))
        self.arbol.column("#0", width=260)
        self.arbol.heading("coche", text=idiomas.t("com.mi_coche"))
        self.arbol.column("coche", width=170, stretch=False)
        self.arbol.heading("vueltas", text=idiomas.t("vis.col_vueltas"))
        self.arbol.column("vueltas", width=58, anchor="center", stretch=False)
        barra = ttk.Scrollbar(marco, orient="vertical", command=self.arbol.yview)
        self.arbol.configure(yscrollcommand=barra.set)
        self.arbol.pack(side="left", fill="both", expand=True)
        barra.pack(side="left", fill="y")
        self.arbol.bind("<<TreeviewSelect>>", self._elegir_sesion)

        botones = ttk.Frame(padre)
        botones.pack(fill="x", pady=(0, 8))
        ttk.Button(botones, text=idiomas.t("com.actualizar"), command=self._recargar).pack(side="left")
        ttk.Button(botones, text=idiomas.t("vis.borrar_sesion"),
                   command=self._borrar).pack(side="right")

    def _panel_vueltas(self, padre):
        ttk.Label(padre, text=idiomas.t("vis.que_dibujar"),
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        marco = ttk.Frame(padre)
        marco.pack(fill="both", expand=True, pady=2)
        self.lista = ttk.Treeview(marco, columns=("tiempo", "s1", "s2", "s3"),
                                  height=15, selectmode="extended")
        self.lista.heading("#0", text=idiomas.t("vis.col_vuelta"))
        self.lista.column("#0", width=210)
        for col, titulo, ancho in (("tiempo", idiomas.t("vis.col_tiempo"), 80),
                                   ("s1", "S1", 50),
                                   ("s2", "S2", 50), ("s3", "S3", 50)):
            self.lista.heading(col, text=titulo)
            self.lista.column(col, width=ancho, anchor="e", stretch=False)
        barra = ttk.Scrollbar(marco, orient="vertical", command=self.lista.yview)
        self.lista.configure(yscrollcommand=barra.set)
        self.lista.pack(side="left", fill="both", expand=True)
        barra.pack(side="left", fill="y")
        self.lista.bind("<<TreeviewSelect>>", lambda e: self._pintar())
        self.lista.tag_configure("anulada", foreground="#b0524a")
        self.lista.tag_configure("mejor", foreground="#2f8f4f")

        self.info = ttk.Label(padre, foreground="#666", justify="left",
                              wraplength=430, text="")
        self.info.pack(anchor="w", pady=(6, 0))

    def _barra(self, padre):
        barra = ttk.Frame(padre, padding=(8, 6))
        barra.pack(fill="x")
        ttk.Label(barra, text=idiomas.t("vis.zoom")).pack(side="left")
        self.var_zoom = tk.DoubleVar(value=1.0)
        ttk.Scale(barra, from_=1.0, to=12.0, variable=self.var_zoom,
                  command=self._cambiar_zoom, length=150).pack(side="left", padx=6)
        ttk.Button(barra, text=idiomas.t("vis.ver_todo"), command=self._encajar).pack(side="left")
        ttk.Label(barra, foreground="#666", text=idiomas.t("vis.ajustar")).pack(side="left")

        # Un desplegable en vez de todos los controles a la vez: con tres
        # elementos y sus colores no cabria nada en la barra.
        AJUSTES = ajustes()
        self.var_ajuste = tk.StringVar(value=AJUSTES[0][0])
        combo = ttk.Combobox(barra, textvariable=self.var_ajuste,
                             values=[a[0] for a in AJUSTES],
                             state="readonly", width=19)
        combo.pack(side="left", padx=4)
        combo.bind("<<ComboboxSelected>>", lambda e: self._controles())
        self.zona = ttk.Frame(barra)
        self.zona.pack(side="left")
        self._controles()

    def _controles(self):
        for w in self.zona.winfo_children():
            w.destroy()
        for etiqueta, tipo, clave in dict(ajustes()).get(self.var_ajuste.get(), []):
            ttk.Label(self.zona, text=etiqueta).pack(side="left", padx=(8, 2))
            if tipo == "grosor":
                var = tk.IntVar(value=int(self.cfg.get(clave, 2)))
                self._vars[clave] = var
                ttk.Spinbox(self.zona, from_=1, to=10, width=3, textvariable=var,
                            command=lambda k=clave: self._cambiar_grosor(k)
                            ).pack(side="left")
            else:
                boton = tk.Button(self.zona, width=3, relief="groove",
                                  bg=self.cfg.get(clave, "#ffffff"))
                boton.config(command=lambda k=clave, b=boton: self._cambiar_color(k, b))
                boton.pack(side="left")

    def _cambiar_grosor(self, clave):
        try:
            self.cfg[clave] = int(self._vars[clave].get())
        except (ValueError, tk.TclError):
            return
        self._guardar()
        self._pintar()

    def _cambiar_color(self, clave, boton):
        nuevo = colorchooser.askcolor(color=boton["bg"], parent=self.v)[1]
        if nuevo:
            boton.config(bg=nuevo)
            self.cfg[clave] = nuevo
            self._guardar()
            self._pintar()

    def _guardar(self):
        import mapa_pista
        mapa_pista.guardar_config(self.cfg)

    # ---------------- sesiones ----------------
    def _recargar(self):
        self.sesiones = grab.listar_sesiones()
        modo = self.var_orden.get()
        lista_ordenes = ordenes()
        if modo == lista_ordenes[1]:
            self.sesiones.sort(key=lambda s: s["fecha"])
        elif modo == lista_ordenes[2]:
            self.sesiones.sort(key=lambda s: (s["circuito"], s["fecha"]))

        for i in self.arbol.get_children():
            self.arbol.delete(i)
        self.filas = {}
        grupos = {}
        for s in self.sesiones:
            # Un evento = mismo circuito y mismo dia. Asi practica,
            # clasificacion y carrera de una misma tarde cuelgan de una sola
            # linea, en vez de llenar la lista de entradas sueltas.
            clave = (s["circuito"], s["fecha"][:8])
            if clave not in grupos:
                grupos[clave] = self.arbol.insert(
                    "", "end", open=True, values=("", ""),
                    text="%s   %s" % (s["circuito"], fecha_bonita(s["fecha"])[:5]))
            self.filas[self.arbol.insert(
                grupos[clave], "end", values=(s.get("coche", ""), s["vueltas"]),
                text="      %s   %s" % (fecha_bonita(s["fecha"])[6:],
                                        grab.nombre_sesion(s["sesion"])))] = s

        for i in self.lista.get_children():
            self.lista.delete(i)
        self.datos = None
        if not self.sesiones:
            self.info.config(text=idiomas.t("vis.sin_sesiones"))
        self._pintar()

    def _sesion_elegida(self):
        sel = self.arbol.selection()
        return self.filas.get(sel[0]) if sel else None

    def _elegir_sesion(self, _=None):
        s = self._sesion_elegida()
        if not s:
            return
        try:
            self.datos = grab.cargar(s["ruta"])
        except (OSError, ValueError):
            messagebox.showerror(idiomas.t("vis.error"), idiomas.t("vis.no_se_lee"),
                                 parent=self.v)
            return
        self.circuito = lmu.cargar_circuitos().get(self.datos.get("clave"))
        self.centro = None
        self._llenar_lista()
        self._encajar()

    def _llenar_lista(self):
        for i in self.lista.get_children():
            self.lista.delete(i)

        ref = self.datos.get("referencia")
        if ref:
            self.lista.tag_configure(
                "ref", foreground=self.cfg.get("color_referencia", "#b06cff"))
            fila = self.lista.insert(
                "", "end", tags=("ref",),
                text=idiomas.t("vis.rival") % (ref.get("dorsal", ""),
                                                ref.get("nombre", ""),
                                                ref.get("equipo", "?")),
                values=(reloj(ref["tiempo"]), self._sec(ref, "s1"),
                        self._sec(ref, "s2"), self._sec(ref, "s3")))
            self.lista.selection_add(fila)

        vueltas = self.datos.get("mis_vueltas", [])
        mi_coche = self.datos.get("mi_coche", "")
        self.rama_mias = self.lista.insert(
            "", "end", open=True, values=("", "", "", ""),
            text=idiomas.t("vis.mis_vueltas")
                 + ("   (%s)" % mi_coche if mi_coche else ""))
        validas = [v for v in vueltas if v.get("valida", True)]
        mejor = min(validas, key=lambda x: x["tiempo"]) if validas else None
        for v in vueltas:
            etiquetas = []
            if not v.get("valida", True):
                etiquetas.append("anulada")
            elif v is mejor:
                etiquetas.append("mejor")
            fila = self.lista.insert(
                self.rama_mias, "end", tags=tuple(etiquetas),
                text=idiomas.t("vis.vuelta_n")
                     % (v["n"], "" if v.get("valida", True)
                        else idiomas.t("vis.anulada")),
                values=(reloj(v["tiempo"]), self._sec(v, "s1"),
                        self._sec(v, "s2"), self._sec(v, "s3")))
            if v is mejor:
                self.lista.selection_add(fila)

        self.info.config(text=self._explicacion(ref, vueltas))

    @staticmethod
    def _sec(v, clave):
        return "%.1f" % v[clave] if v.get(clave) else ""

    def _explicacion(self, ref, vueltas):
        texto = ""
        pilotos = self.datos.get("pilotos") or []
        if len(pilotos) > 1:
            texto += idiomas.t("vis.pilotos") + ", ".join(pilotos) + "\n"
        if not self.circuito:
            texto += idiomas.t("vis.sin_trazado")
        elif not self.circuito.get("bordes"):
            texto += idiomas.t("vis.sin_bordes")
        if not ref:
            texto += idiomas.t("vis.sin_rival")
        if not vueltas:
            texto += idiomas.t("vis.sin_mias")
        return texto + idiomas.t("vis.como_va")

    def _borrar(self):
        s = self._sesion_elegida()
        if not s:
            messagebox.showinfo(idiomas.t("com.borrar"),
                                idiomas.t("vis.elige_sesion_borrar"),
                                parent=self.v)
            return
        if messagebox.askyesno(
                idiomas.t("vis.tit_borrar"),
                idiomas.t("vis.confirmar_borrar")
                % (s["circuito"], fecha_bonita(s["fecha"]), s["vueltas"],
                   s["tamano"] / 1024.0) + idiomas.t("com.seguro"),
                parent=self.v):
            grab.borrar(s["ruta"])
            self._recargar()

    # ---------------- vista ----------------
    def _elegidos(self):
        """(referencia_marcada, [vueltas mias marcadas]) segun lo que haya en la lista."""
        ref = None
        mias = []
        vueltas = self.datos.get("mis_vueltas", []) if self.datos else []
        for fila in self.lista.selection():
            if self.lista.parent(fila):
                i = self.lista.index(fila)
                if i < len(vueltas):
                    mias.append(vueltas[i])
            elif self.lista.item(fila, "text").startswith("RIVAL"):
                ref = self.datos.get("referencia")
        return ref, mias

    def _limites(self):
        puntos = []
        if self.circuito:
            puntos += [tuple(p) for p in self.circuito["puntos"]]
            for lado in (self.circuito.get("bordes") or {}).values():
                puntos += [tuple(p) for p in lado]
        if self.datos:
            for v in self.datos.get("mis_vueltas", []):
                puntos += [(p[0], p[1]) for p in v["puntos"]]
            ref = self.datos.get("referencia")
            if ref:
                puntos += [(p[0], p[1]) for p in ref["puntos"]]
        if not puntos:
            return None
        xs = [p[0] for p in puntos]
        zs = [p[1] for p in puntos]
        return min(xs), min(zs), max(xs), max(zs)

    def _escala(self):
        lim = self._limites()
        if not lim:
            return None
        w = max(self.lienzo.winfo_width(), 50)
        h = max(self.lienzo.winfo_height(), 50)
        return min((w - 40) / max(lim[2] - lim[0], 1.0),
                   (h - 40) / max(lim[3] - lim[1], 1.0)) * self.zoom

    def _encajar(self):
        lim = self._limites()
        if lim:
            self.centro = ((lim[0] + lim[2]) / 2.0, (lim[1] + lim[3]) / 2.0)
        self.var_zoom.set(1.0)
        self.zoom = 1.0
        self._pintar()

    def _cambiar_zoom(self, _=None):
        self.zoom = self.var_zoom.get()
        self._pintar()

    def _rueda(self, e):
        self.var_zoom.set(max(1.0, min(12.0, self.zoom * (1.15 if e.delta > 0 else 0.87))))
        self._cambiar_zoom()

    def _arrastrar(self, e):
        if not self.arrastre or not self.centro:
            return
        esc = self._escala()
        if esc:
            self.centro = (self.centro[0] - (e.x - self.arrastre[0]) / esc,
                           self.centro[1] + (e.y - self.arrastre[1]) / esc)
        self.arrastre = (e.x, e.y)
        self._pintar()

    def _a_pantalla(self, x, z):
        esc = self._escala()
        return (self.lienzo.winfo_width() / 2.0 + (x - self.centro[0]) * esc,
                self.lienzo.winfo_height() / 2.0 - (z - self.centro[1]) * esc)

    # ---------------- dibujo ----------------
    def _pintar(self):
        c = self.lienzo
        c.delete("all")
        if not self.datos or not self.centro or not self._escala():
            c.create_text(self.lienzo.winfo_width() / 2,
                          self.lienzo.winfo_height() / 2,
                          text=idiomas.t("vis.elige_sesion"),
                          fill="#666", font=("Segoe UI", 12))
            return

        if self.circuito:
            self._pintar_circuito(c)

        ref, mias = self._elegidos()
        guardada = self.datos.get("referencia")
        leyenda = []

        if ref:
            self._linea(c, ref["puntos"], self.cfg.get("color_referencia", "#b06cff"),
                        self.cfg["visor_grosor_referencia"])
            leyenda.append((self.cfg.get("color_referencia", "#b06cff"),
                            idiomas.t("vis.ley_rival") % (ref.get("dorsal", ""),
                                               reloj(ref["tiempo"]))))

        # una sola vuelta -> tricolor contra el rival; varias -> un color cada una
        if len(mias) == 1 and guardada:
            self._linea_comparada(c, mias[0]["puntos"], guardada["puntos"])
            leyenda += [(self.cfg["color_lento"], idiomas.t("vis.ley_lento")),
                        (self.cfg["color_igual"], idiomas.t("vis.ley_igual")),
                        (self.cfg["color_rapido"], idiomas.t("vis.ley_rapido"))]
        else:
            for n, v in enumerate(mias):
                color = PALETA[n % len(PALETA)]
                self._linea(c, v["puntos"], color, self.cfg["visor_grosor_vuelta"])
                leyenda.append((color, idiomas.t("vis.ley_vuelta")
                               % (v["n"], reloj(v["tiempo"]))))
            if len(mias) > 1:
                leyenda.append(("#777", idiomas.t("vis.ley_una_sola")))
        self._leyenda(c, leyenda)

    def _pintar_circuito(self, c):
        bordes = self.circuito.get("bordes")
        if bordes:
            for lado in ("izquierda", "derecha"):
                self._linea(c, [(p[0], p[1]) for p in bordes[lado]],
                            self.cfg["visor_color_borde"],
                            self.cfg["visor_grosor_borde"])
        self._linea(c, [(p[0], p[1]) for p in self.circuito["puntos"]],
                    self.cfg["visor_color_trazado"],
                    self.cfg["visor_grosor_trazado"],
                    guiones=(4, 4) if bordes else None)
        if self.circuito.get("boxes"):
            self._linea(c, [(p[0], p[1]) for p in self.circuito["boxes"]],
                        self.cfg["visor_color_borde"],
                        self.cfg["visor_grosor_borde"], cerrada=False)
        for cur in self.circuito.get("curvas") or []:
            px, py = self._a_pantalla(cur["x"], cur["z"])
            etiqueta = str(cur["n"]) + ((" " + cur["nombre"]) if cur.get("nombre") else "")
            c.create_text(px, py, text=etiqueta, fill="#7a7a7a", font=("Segoe UI", 8))

    def _linea(self, c, puntos, color, grosor, guiones=None, cerrada=True):
        planos = []
        for p in puntos:
            px, py = self._a_pantalla(p[0], p[1])
            planos.extend((px, py))
        if len(planos) >= 4:
            if cerrada:
                planos.extend(planos[:2])
            kw = {"dash": guiones} if guiones else {}
            c.create_line(*planos, fill=color, width=grosor,
                          capstyle="round", joinstyle="round", **kw)

    @staticmethod
    def _suave(velocidades):
        """
        Media movil de las velocidades.

        Sin esto el color cambia cada pocos metros y la vuelta sale como
        confeti: cualquier variacion minima da la vuelta al veredicto. Lo que
        interesa ver son ZONAS donde se gana o se pierde, no el punto exacto.
        """
        n = len(velocidades)
        mitad = SUAVIZADO // 2
        salida = []
        for i in range(n):
            trozo = [velocidades[(i + k) % n] for k in range(-mitad, mitad + 1)]
            trozo = [v for v in trozo if v]
            salida.append(sum(trozo) / len(trozo) if trozo else 0.0)
        return salida

    def _linea_comparada(self, c, mios, suyos):
        """Tu trazada coloreada contra la referencia, por zonas."""
        colores = {"lento": self.cfg["color_lento"], "igual": self.cfg["color_igual"],
                   "rapido": self.cfg["color_rapido"]}
        n = min(len(mios), len(suyos))
        grosor = self.cfg["visor_grosor_vuelta"]
        mias = self._suave([p[2] if len(p) > 2 else 0.0 for p in mios[:n]])
        suyas = self._suave([p[2] if len(p) > 2 else 0.0 for p in suyos[:n]])

        for i in range(n):
            a, b = mios[i], mios[(i + 1) % n]
            mia, suya = mias[i], suyas[i]
            if not mia or not suya:
                cual = "igual"
            elif mia > suya + TOLERANCIA_KMH:
                cual = "rapido"
            elif mia < suya - TOLERANCIA_KMH:
                cual = "lento"
            else:
                cual = "igual"
            x1, y1 = self._a_pantalla(a[0], a[1])
            x2, y2 = self._a_pantalla(b[0], b[1])
            c.create_line(x1, y1, x2, y2, fill=colores[cual], width=grosor,
                          capstyle="round")

    def _leyenda(self, c, filas):
        if not filas:
            filas = [("#777", idiomas.t("vis.ley_marca_algo"))]
        y = 14
        for color, texto in filas:
            c.create_line(14, y, 40, y, fill=color, width=3)
            c.create_text(48, y, text=texto, fill="#bbb", anchor="w",
                          font=("Segoe UI", 8))
            y += 16


def abrir(padre, cfg):
    return Visor(padre, cfg).v


class VisorEscaneo:
    """
    Ventana simple para revisar como quedo el escaneo de un trazado: los dos
    bordes, la trazada de referencia y la calle de boxes, cada cosa de su color.
    Sirve para ver de un vistazo si un escaneo salio torcido.
    """

    COLORES = {"izquierda": "#4aa8ff", "derecha": "#ff9f0a",
               "trazada": "#ffffff", "boxes": "#3ddc84"}

    def __init__(self, padre, clave):
        circuitos = lmu.cargar_circuitos()
        self.d = circuitos.get(clave) or {}
        self.zoom = 1.0
        self.centro = None
        self.arrastre = None

        v = tk.Toplevel(padre)
        self.v = v
        v.title(idiomas.t("esv.titulo") % self.d.get("nombre", clave))
        v.geometry("900x640")
        v.attributes("-topmost", True)

        barra = ttk.Frame(v, padding=(8, 6))
        barra.pack(fill="x")
        partes = []
        bordes = self.d.get("bordes") or {}
        if bordes:
            partes.append(idiomas.t("esv.bordes"))
        if self.d.get("puntos"):
            partes.append(idiomas.t("esv.trazada") % len(self.d.get("curvas") or []))
        if self.d.get("boxes"):
            partes.append(idiomas.t("esv.boxes"))
        ttk.Label(barra, text=idiomas.t("esv.escaneado")
                  + (", ".join(partes) or idiomas.t("esv.nada"))
                  ).pack(side="left")
        ttk.Button(barra, text=idiomas.t("vis.ver_todo"), command=self._encajar).pack(side="right")
        ttk.Label(barra, foreground="#666",
                  text=idiomas.t("esv.raton")).pack(side="right")

        self.lienzo = tk.Canvas(v, bg="#141414", highlightthickness=0)
        self.lienzo.pack(fill="both", expand=True)
        self.lienzo.bind("<MouseWheel>", self._rueda)
        self.lienzo.bind("<Button-1>", lambda e: setattr(self, "arrastre", (e.x, e.y)))
        self.lienzo.bind("<B1-Motion>", self._arrastrar)
        self.lienzo.bind("<Configure>", lambda e: self._pintar())
        self._encajar()

    def _todos(self):
        puntos = [tuple(p) for p in self.d.get("puntos", [])]
        for lado in (self.d.get("bordes") or {}).values():
            puntos += [tuple(p) for p in lado]
        puntos += [tuple(p) for p in self.d.get("boxes", [])]
        return puntos

    def _limites(self):
        puntos = self._todos()
        if not puntos:
            return None
        xs = [p[0] for p in puntos]
        zs = [p[1] for p in puntos]
        return min(xs), min(zs), max(xs), max(zs)

    def _escala(self):
        lim = self._limites()
        if not lim:
            return None
        w = max(self.lienzo.winfo_width(), 50)
        h = max(self.lienzo.winfo_height(), 50)
        return min((w - 40) / max(lim[2] - lim[0], 1.0),
                   (h - 40) / max(lim[3] - lim[1], 1.0)) * self.zoom

    def _encajar(self):
        lim = self._limites()
        if lim:
            self.centro = ((lim[0] + lim[2]) / 2.0, (lim[1] + lim[3]) / 2.0)
        self.zoom = 1.0
        self._pintar()

    def _rueda(self, e):
        self.zoom = max(1.0, min(12.0, self.zoom * (1.15 if e.delta > 0 else 0.87)))
        self._pintar()

    def _arrastrar(self, e):
        if not self.arrastre or not self.centro:
            return
        esc = self._escala()
        if esc:
            self.centro = (self.centro[0] - (e.x - self.arrastre[0]) / esc,
                           self.centro[1] + (e.y - self.arrastre[1]) / esc)
        self.arrastre = (e.x, e.y)
        self._pintar()

    def _a_pantalla(self, x, z):
        esc = self._escala()
        return (self.lienzo.winfo_width() / 2.0 + (x - self.centro[0]) * esc,
                self.lienzo.winfo_height() / 2.0 - (z - self.centro[1]) * esc)

    def _linea(self, puntos, color, grosor, cerrada=True):
        planos = []
        for p in puntos:
            px, py = self._a_pantalla(p[0], p[1])
            planos.extend((px, py))
        if len(planos) >= 4:
            if cerrada:
                planos.extend(planos[:2])
            self.lienzo.create_line(*planos, fill=color, width=grosor,
                                    capstyle="round", joinstyle="round")

    def _pintar(self):
        c = self.lienzo
        c.delete("all")
        if not self.centro or not self._escala():
            c.create_text(self.lienzo.winfo_width() / 2, self.lienzo.winfo_height() / 2,
                          text=idiomas.t("esv.sin_nada"),
                          fill="#666", font=("Segoe UI", 12))
            return

        bordes = self.d.get("bordes") or {}
        for lado in ("izquierda", "derecha"):
            if bordes.get(lado):
                self._linea([(p[0], p[1]) for p in bordes[lado]],
                            self.COLORES[lado], 2)
        if self.d.get("puntos"):
            self._linea([(p[0], p[1]) for p in self.d["puntos"]],
                        self.COLORES["trazada"], 1)
        if self.d.get("boxes"):
            # boxes no es un bucle: no se cierra el final con el principio
            self._linea([(p[0], p[1]) for p in self.d["boxes"]],
                        self.COLORES["boxes"], 3, cerrada=False)
        for cur in self.d.get("curvas") or []:
            px, py = self._a_pantalla(cur["x"], cur["z"])
            etiqueta = str(cur["n"]) + ((" " + cur["nombre"]) if cur.get("nombre") else "")
            c.create_text(px, py, text=etiqueta, fill="#7a7a7a", font=("Segoe UI", 8))

        y = 14
        for clave, texto in (("izquierda", idiomas.t("esv.borde_izq")),
                             ("derecha", idiomas.t("esv.borde_der")),
                             ("trazada", idiomas.t("esv.trazada_ref")),
                             ("boxes", idiomas.t("esv.boxes"))):
            hay = bool(bordes.get(clave)) if clave in ("izquierda", "derecha") \
                else bool(self.d.get("puntos" if clave == "trazada" else "boxes"))
            c.create_line(14, y, 40, y,
                          fill=self.COLORES[clave] if hay else "#333", width=3)
            c.create_text(48, y, text=texto + ("" if hay else idiomas.t("esv.sin_escanear")),
                          fill="#bbb" if hay else "#555", anchor="w",
                          font=("Segoe UI", 8))
            y += 16


def abrir_escaneo(padre, clave):
    return VisorEscaneo(padre, clave).v
