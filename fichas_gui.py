# -*- coding: utf-8 -*-
"""
La ventanita para escribir la ficha de un coche.

Existe para que el programa no se muera el dia que dejemos de mantenerlo.
El juego saca coches nuevos cada temporada y sus datos no estan en ningun
archivo del juego: hay que escribirlos. Si solo pudieramos escribirlos
nosotros, los coches nuevos se quedarian en blanco para siempre.

Con esto, cualquiera rellena la ficha de un coche nuevo en un minuto, se
guarda en fichas_coches.json al lado del programa, y ese archivo se puede
pasar a quien quiera igual que un circuito escaneado.
"""
import tkinter as tk
from tkinter import ttk, messagebox

import fichas
import idiomas
import reglajes

T = idiomas.t


class Editar:
    """`modelo` es el nombre del coche tal y como sale en la lista."""

    def __init__(self, padre, modelo, al_guardar=None):
        self.modelo = modelo
        self.al_guardar = al_guardar
        actual = fichas.de(modelo) or {}

        v = tk.Toplevel(padre)
        self.v = v
        v.title(T("fic.titulo"))
        v.attributes("-topmost", True)
        v.resizable(False, False)
        v.transient(padre)

        ttk.Label(v, padding=(14, 10), font=("Segoe UI", 11, "bold"),
                  text=reglajes.bonito(modelo)).pack(anchor="w")
        ttk.Label(v, padding=(14, 0), justify="left", wraplength=460,
                  foreground="#555", text=T("fic.ayuda")).pack(anchor="w")

        m = ttk.Frame(v, padding=(14, 10))
        m.pack(fill="both", expand=True)

        self.campos = {}
        for fila, (campo, etiqueta, ejemplo) in enumerate((
                ("motor", "fic.motor", "V8 atmosferico"),
                ("cilindrada", "fic.cilindrada", "5.4 l"),
                ("potencia", "fic.potencia", "~500 CV (BoP)"))):
            ttk.Label(m, text=T(etiqueta)).grid(row=fila, column=0, sticky="e",
                                                pady=3, padx=(0, 8))
            var = tk.StringVar(value=actual.get(campo, ""))
            caja = ttk.Entry(m, textvariable=var, width=44)
            caja.grid(row=fila, column=1, sticky="w", pady=3)
            ttk.Label(m, foreground="#aaa", text=ejemplo).grid(
                row=fila, column=2, sticky="w", padx=(8, 0))
            self.campos[campo] = var

        # Estos dos van de lista para que todo el mundo escriba lo mismo.
        for fila, (campo, etiqueta, opciones) in enumerate((
                ("posicion", "fic.posicion", fichas.POSICIONES),
                ("traccion", "fic.traccion", fichas.TRACCIONES)), start=3):
            ttk.Label(m, text=T(etiqueta)).grid(row=fila, column=0, sticky="e",
                                                pady=3, padx=(0, 8))
            var = tk.StringVar(value=actual.get(campo, opciones[0]))
            ttk.Combobox(m, textvariable=var, values=opciones, width=42,
                         state="readonly").grid(row=fila, column=1,
                                                sticky="w", pady=3)
            self.campos[campo] = var

        ttk.Label(m, text=T("fic.resumen")).grid(row=5, column=0, sticky="ne",
                                                 pady=3, padx=(0, 8))
        self.resumen = tk.Text(m, width=46, height=5, wrap="word",
                               font=("Segoe UI", 9))
        self.resumen.grid(row=5, column=1, columnspan=2, sticky="w", pady=3)
        self.resumen.insert("1.0", actual.get("resumen", ""))
        ttk.Label(m, foreground="#aaa", justify="left", wraplength=460,
                  text=T("fic.resumen_ayuda")).grid(row=6, column=1,
                                                    sticky="w")

        pie = ttk.Frame(v, padding=(14, 10))
        pie.pack(fill="x")
        ttk.Button(pie, text=T("fic.guardar"),
                   command=self.guardar).pack(side="left")
        if fichas.es_mia(modelo):
            ttk.Button(pie, text=T("fic.quitar"),
                       command=self.quitar).pack(side="left", padx=8)
        ttk.Button(pie, text=T("ed.cancelar"),
                   command=v.destroy).pack(side="right")

    def guardar(self):
        datos = {c: v.get() for c, v in self.campos.items()}
        datos["resumen"] = self.resumen.get("1.0", "end").strip()
        if not datos["motor"].strip():
            messagebox.showinfo(T("fic.titulo"), T("fic.falta_motor"),
                                parent=self.v)
            return
        if not fichas.guardar(self.modelo, datos):
            messagebox.showerror(T("fic.titulo"), T("fic.no_se_pudo"),
                                 parent=self.v)
            return
        self.v.destroy()
        if self.al_guardar:
            self.al_guardar()

    def quitar(self):
        """
        Borra lo escrito a mano. Si el coche venia con ficha dentro del
        programa, vuelve a mandar esa; si no, se queda sin ficha.
        """
        if not messagebox.askyesno(T("fic.titulo"), T("fic.confirmar_quitar"),
                                   parent=self.v):
            return
        fichas.borrar(self.modelo)
        self.v.destroy()
        if self.al_guardar:
            self.al_guardar()
