# -*- coding: utf-8 -*-
"""
La ventana de "cual de estos coches eres tu" (F11).

POR QUE EXISTE. El mapa saca tu coche del propio juego, y cuando el juego lo
dice no hay nada que elegir. El problema son las salas donde NO lo dice:
entras de espectador a una carrera por equipos, o coges el coche en un relevo,
y ahi el juego no marca a nadie. Antes el mapa lo adivinaba en silencio, y el
29/08/2026, en las 6 h de Silverstone, se engancho a un BMW M4 de otro equipo
durante las seis horas enteras -grabando sus vueltas como si fueran tuyas- sin
avisar de nada.

Ahora, cuando no lo sabe, lo dice en el mapa y se elige aqui a mano. La
eleccion se guarda pegada al COCHE (su mID), no al piloto, asi que aguanta los
relevos: entra tu companero y el mapa sigue con vuestro coche.
"""
import tkinter as tk
from tkinter import ttk

import coches as cat
import idiomas


FILAS = 12


def abrir(mapa):
    return Ventana(mapa)


class Ventana(tk.Toplevel):
    def __init__(self, mapa):
        tk.Toplevel.__init__(self, mapa.root)
        self.mapa = mapa
        self.title(idiomas.t("sel.titulo"))
        self.attributes("-topmost", True)
        self.configure(bg="#202020")
        self.protocol("WM_DELETE_WINDOW", mapa.cerrar_eleccion)
        self._ids = []                 # mID de cada fila, en el mismo orden
        self._tarea = None

        marco = tk.Frame(self, bg="#202020", padx=12, pady=12)
        marco.pack(fill="both", expand=True)

        tk.Label(marco, text=idiomas.t("sel.ayuda"), bg="#202020", fg="#cfcfcf",
                 justify="left", wraplength=430,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 8))

        self.rotulo = tk.Label(marco, text="", bg="#202020", fg="#ffd24a",
                               justify="left", font=("Segoe UI", 10, "bold"))
        self.rotulo.pack(anchor="w", pady=(0, 6))

        caja = tk.Frame(marco, bg="#202020")
        caja.pack(fill="both", expand=True)
        barra = tk.Scrollbar(caja)
        barra.pack(side="right", fill="y")
        self.lista = tk.Listbox(caja, height=FILAS, activestyle="none",
                                bg="#101010", fg="#e8e8e8",
                                selectbackground="#3a6ea5", selectforeground="#ffffff",
                                highlightthickness=0, font=("Consolas", 10),
                                yscrollcommand=barra.set)
        self.lista.pack(side="left", fill="both", expand=True)
        barra.config(command=self.lista.yview)
        self.lista.bind("<Double-Button-1>", lambda e: self._fijar())

        botones = tk.Frame(marco, bg="#202020")
        botones.pack(fill="x", pady=(10, 0))
        ttk.Button(botones, text=idiomas.t("sel.fijar"),
                   command=self._fijar).pack(side="left")
        ttk.Button(botones, text=idiomas.t("sel.auto"),
                   command=self._auto).pack(side="left", padx=6)
        ttk.Button(botones, text=idiomas.t("sel.cerrar"),
                   command=mapa.cerrar_eleccion).pack(side="right")

        self.geometry("+%d+%d" % (mapa.cfg["x"] + 40, mapa.cfg["y"] + 40))
        self.refrescar()

    # ---------- contenido ----------
    def _coches(self):
        return getattr(self.mapa.fuente, "_ultimos", []) or []

    def refrescar(self):
        """
        Repinta la lista con los coches que hay ahora mismo en la sala.

        Se refresca sola porque en una carrera la gente entra y sale, y una
        lista congelada de hace cinco minutos haria elegir un coche que ya no
        existe. Se conserva lo que hubiera seleccionado el usuario, buscandolo
        por su mID y no por el numero de fila: las filas bailan.
        """
        antes = self.seleccionado()
        # Agrupados por categoria y por puesto dentro de ella, que es como se
        # ven en la pantalla de tiempos del juego: asi se encuentra el coche
        # sin tener que leerse los sesenta.
        lista = sorted(self._coches(), key=lambda c: (c.get("clase") or "~",
                                                      c.get("puesto") or 99,
                                                      c.get("nombre") or ""))
        self.lista.delete(0, "end")
        self._ids = []
        for c in lista:
            if c.get("id") is None:
                continue
            # El equipo es lo que de verdad distingue un coche de otro en la
            # pantalla del juego; el modelo ayuda a encontrarlo de un vistazo.
            equipo = cat.equipo_de(c.get("vehiculo", ""))
            modelo = cat.texto(c.get("vehiculo", ""), c.get("clase", ""),
                               c.get("codigo", ""))
            self.lista.insert("end", "%s%2s  %-20.20s  %-22.22s  %-20.20s %s"
                              % ("> " if c.get("es_yo") else "  ",
                                 c.get("puesto") or "", c.get("nombre") or "?",
                                 equipo, modelo, c.get("clase") or ""))
            self._ids.append(c["id"])
        if antes in self._ids:
            fila = self._ids.index(antes)
            self.lista.selection_set(fila)
            self.lista.see(fila)

        yo = next((c for c in self._coches() if c.get("es_yo")), None)
        quien = ("%s  (%s)" % (yo.get("nombre") or "?", yo.get("vehiculo") or "")
                 if yo else idiomas.t("sel.nadie"))
        self.rotulo.config(text=idiomas.t("sel.actual") % quien,
                           fg="#3ddc84" if (yo and yo.get("yo_fiable"))
                           else "#ff9f0a")
        self._tarea = self.after(1000, self.refrescar)

    def seleccionado(self):
        sel = self.lista.curselection()
        if not sel or sel[0] >= len(self._ids):
            return None
        return self._ids[sel[0]]

    # ---------- acciones ----------
    def _fijar(self):
        mid = self.seleccionado()
        if mid is None:
            return
        self.mapa.fijar_mi_coche(mid)

    def _auto(self):
        self.mapa.fijar_mi_coche(None)

    def destroy(self):
        if self._tarea is not None:
            try:
                self.after_cancel(self._tarea)
            except Exception:
                pass
            self._tarea = None
        tk.Toplevel.destroy(self)
