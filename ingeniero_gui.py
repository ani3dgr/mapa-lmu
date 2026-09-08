# -*- coding: utf-8 -*-
"""
Las dos ventanas que salen de la biblioteca: comparar dos reglajes y el
ingeniero de pista.

El ingeniero es la parte que sustituye a preguntarle a alguien que sabe.
Se elige que hace el coche con tres desplegables, como se cuenta por radio
(donde pasa, que hace y cuando), y sale el diagnostico con lo que hay que
tocar y por que.

Dos normas que estan metidas a proposito y que no son un capricho:

  UN CAMBIO CADA VEZ. Si se tocan cinco cosas de golpe y el coche mejora,
  no se sabe cual de las cinco lo arreglo, y la siguiente vez se vuelve a
  empezar de cero. Se cambia una, se dan vueltas y se vuelve.

  NUNCA SE MACHACA EL ORIGINAL. Cada prueba es un archivo nuevo numerado.
  La mitad de los cambios no mejoran nada y hay que poder volver al de
  antes sin haberlo perdido.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox

import biblioteca as B
import idiomas
import ingenieria as I

T = idiomas.t

ROJO = "#b03a2e"
VERDE = "#1e7a44"


def _codigo():
    """El idioma que hay puesto, para los textos de reglas.json."""
    try:
        return idiomas.actual()
    except Exception:
        return "es"


class Comparar:
    """Las diferencias entre dos reglajes, en cristiano y por orden."""

    def __init__(self, padre, uno, otro):
        v = tk.Toplevel(padre)
        self.v = v
        v.title(T("cmp.titulo"))
        v.attributes("-topmost", True)
        v.geometry("860x520")

        cab = ttk.Frame(v, padding=(10, 8))
        cab.pack(fill="x")
        ttk.Label(cab, justify="left", font=("Segoe UI", 9),
                  text="%s\n%s" % (uno["nombre"], otro["nombre"])).pack(side="left")

        filas = I.comparar(uno, otro)
        ttk.Label(v, padding=(10, 0), foreground="#555",
                  text=T("cmp.resumen") % len(filas)).pack(fill="x")

        marco = ttk.Frame(v, padding=10)
        marco.pack(fill="both", expand=True)
        tabla = ttk.Treeview(marco, columns=("que", "uno", "otro"),
                             show="headings", selectmode="browse")
        for c, a in (("que", 330), ("uno", 200), ("otro", 200)):
            tabla.heading(c, text=T("cmp.col." + c))
            tabla.column(c, width=a)
        barra = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=barra.set)
        tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="left", fill="y")
        tabla.tag_configure("gordo", font=("Segoe UI", 9, "bold"))

        for f in filas:
            # Lo que de verdad cambia como va el coche sale en negrita, para
            # que no se pierda entre diez ajustes de detalle.
            tabla.insert("", "end", tags=("gordo",) if f["peso"] >= 7 else (),
                         values=(f["nombre"], f["de"], f["a"]))
        if not filas:
            tabla.insert("", "end", values=(T("cmp.iguales"), "", ""))

        ttk.Button(v, text=T("bib.cerrar"),
                   command=v.destroy).pack(side="right", padx=10, pady=(0, 10))


class Ingeniero:
    """Los tres desplegables, el diagnostico y los cambios."""

    def __init__(self, padre, ficha, calibracion, al_terminar=None):
        self.ficha = ficha
        self.cal = calibracion
        self.al_terminar = al_terminar
        self.propuestas = []
        self.codigo = _codigo()

        v = tk.Toplevel(padre)
        self.v = v
        v.title(T("ing.titulo"))
        v.attributes("-topmost", True)
        v.geometry("900x600")

        ttk.Label(v, padding=(10, 8), font=("Segoe UI", 10, "bold"),
                  text=ficha["nombre"]).pack(fill="x")

        self._preguntas(v)
        self._respuesta(v)
        self._pie(v)

    def _preguntas(self, v):
        m = ttk.LabelFrame(v, text=T("ing.pregunta"), padding=(10, 8))
        m.pack(fill="x", padx=10)

        self.combos = {}
        for col, (cual, etiqueta) in enumerate((("donde", "ing.donde"),
                                                ("que", "ing.que"),
                                                ("cuando", "ing.cuando"))):
            ttk.Label(m, text=T(etiqueta)).grid(row=0, column=col, sticky="w",
                                                padx=(0, 12), pady=(0, 2))
            opciones = I.opciones(cual, self.codigo)
            var = tk.StringVar(value=opciones[0][1] if opciones else "")
            combo = ttk.Combobox(m, textvariable=var, state="readonly", width=32,
                                 values=[t for _, t in opciones])
            combo.grid(row=1, column=col, sticky="w", padx=(0, 12))
            combo.bind("<<ComboboxSelected>>", lambda _: self.pensar())
            self.combos[cual] = (var, opciones)

    def _respuesta(self, v):
        m = ttk.Frame(v, padding=(10, 8))
        m.pack(fill="both", expand=True)

        self.diagnostico = tk.Text(m, height=4, wrap="word", relief="flat",
                                   background="#f4f4f4", font=("Segoe UI", 9))
        self.diagnostico.pack(fill="x", pady=(0, 8))
        self.diagnostico.configure(state="disabled")

        ttk.Label(m, text=T("ing.uno_cada_vez"), foreground=ROJO,
                  font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 4))

        # Por donde empezar, dicho con todas las letras. La lista ya venia
        # ordenada por prioridad y el primero salia marcado, pero eso no se
        # entiende mirando la pantalla: parece que este senalado por
        # casualidad. Si el programa sabe cual es el mejor sitio por donde
        # empezar, tiene que decirlo y no dejar que se adivine.
        self.consejo = ttk.Label(m, text="", foreground=VERDE,
                                 font=("Segoe UI", 9, "bold"))
        self.consejo.pack(anchor="w", pady=(0, 4))

        cuerpo = ttk.Frame(m)
        cuerpo.pack(fill="both", expand=True)
        self.tabla = ttk.Treeview(cuerpo,
                                  columns=("orden", "ajuste", "ahora", "nuevo"),
                                  show="headings", selectmode="browse", height=5)
        for c, a in (("orden", 55), ("ajuste", 290), ("ahora", 140),
                     ("nuevo", 140)):
            self.tabla.heading(c, text=T("ing.col." + c))
            self.tabla.column(c, width=a)
        self.tabla.column("orden", anchor="center", stretch=False)
        self.tabla.tag_configure("primero", background="#e6f4ea",
                                 font=("Segoe UI", 9, "bold"))
        self.tabla.pack(side="left", fill="both", expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self._porque)

        self.explica = tk.Text(cuerpo, width=42, wrap="word", relief="flat",
                               background="#f9f9f9", font=("Segoe UI", 9))
        self.explica.pack(side="left", fill="both", padx=(10, 0))
        self.explica.configure(state="disabled")

    def _pie(self, v):
        pie = ttk.Frame(v, padding=(10, 8))
        pie.pack(fill="x")
        ttk.Button(pie, text=T("ing.aplicar"),
                   command=self.aplicar).pack(side="left")
        self.estado = ttk.Label(pie, text="", foreground="#555")
        self.estado.pack(side="left", padx=(14, 0))
        ttk.Button(pie, text=T("bib.cerrar"),
                   command=v.destroy).pack(side="right")
        # Esta pantalla SIEMPRE contesta algo, y ahi esta su trampa: parece
        # que cualquier problema se arregle tocando el coche. El aviso va
        # detras de un boton y no en mitad de la pantalla a proposito: al
        # que no le hace falta no le da la brasa, y el que lleva veinte
        # cambios y sigue igual lo tiene a mano.
        ttk.Button(pie, text=T("ing.y_si_no"),
                   command=self._y_si_no).pack(side="right", padx=(0, 8))
        self.pensar()

    def _y_si_no(self):
        """Lo que nadie le dice a nadie: que a lo mejor no es el coche."""
        w = tk.Toplevel(self.v)
        w.title(T("ing.y_si_no_titulo"))
        w.attributes("-topmost", True)
        w.geometry("620x460")
        ttk.Label(w, padding=(14, 12), font=("Segoe UI", 11, "bold"),
                  text=T("ing.y_si_no_titulo")).pack(fill="x")
        marco = ttk.Frame(w, padding=(14, 0))
        marco.pack(fill="both", expand=True)
        caja = tk.Text(marco, wrap="word", relief="flat", padx=10, pady=10,
                       background="#f9f9f9", font=("Segoe UI", 9))
        barra = ttk.Scrollbar(marco, orient="vertical", command=caja.yview)
        caja.configure(yscrollcommand=barra.set)
        caja.pack(side="left", fill="both", expand=True)
        barra.pack(side="left", fill="y")
        caja.insert("1.0", T("ing.y_si_no_texto"))
        caja.configure(state="disabled")
        ttk.Button(w, text=T("bib.cerrar"),
                   command=w.destroy).pack(pady=10)

    # ------------------------------------------------------------ trabajo
    def _elegido(self, cual):
        var, opciones = self.combos[cual]
        for ident, texto in opciones:
            if texto == var.get():
                return ident
        return ""

    def _escribir(self, caja, texto):
        caja.configure(state="normal")
        caja.delete("1.0", "end")
        caja.insert("1.0", texto)
        caja.configure(state="disabled")

    def pensar(self):
        regla = I.diagnosticar(self._elegido("donde"), self._elegido("que"),
                               self._elegido("cuando"))
        self.tabla.delete(*self.tabla.get_children())
        self._escribir(self.explica, "")

        self.consejo.configure(text="")

        if not regla:
            self._escribir(self.diagnostico, T("ing.sin_regla"))
            self.propuestas = []
            return

        texto = I.en_idioma(regla, self.codigo)
        if not I.es_exacta(regla, self._elegido("cuando")):
            # La regla acierta el sintoma pero no habla de ese "cuando".
            # Se dice, en vez de darlo por bueno sin mas.
            texto = T("ing.parecido") + "\n\n" + texto
        self._escribir(self.diagnostico, texto)
        self.propuestas = I.proponer(self.ficha, regla, self.cal, self.codigo)
        for n, p in enumerate(self.propuestas, 1):
            # Se dice cuanto sube o baja, no el numero interno del juego: a
            # nadie le dice nada que la presion de freno "pase al 78".
            # Si el programa ha aprendido la escala de este coche, se dice
            # el valor de verdad. Si no, se dice cuanto sube o baja, que
            # sigue siendo mas util que el numero interno del juego.
            queda = p["queda"] or ("%s%d" % ("+" if p["sube"] else "-",
                                             p["saltos"]))
            # El numero de orden ES la recomendacion. La lista viene ordenada
            # de lo que mas arregla el sintoma a lo que menos, y los que
            # estan topados se han caido solos por el camino, asi que el 1
            # siempre es algo que se puede tocar de verdad en este coche.
            self.tabla.insert("", "end",
                              values=(n, p["nombre"], p["ahora"], queda),
                              tags=("primero",) if n == 1 else ())
        hijos = self.tabla.get_children()
        if not hijos:
            self._escribir(self.explica, T("ing.no_se_puede"))
        if hijos:
            self.consejo.configure(
                text=T("ing.empieza_por") % self.propuestas[0]["nombre"])
            self.tabla.selection_set(hijos[0])

    def _porque(self, _=None):
        sel = self.tabla.selection()
        if not sel:
            return
        i = self.tabla.index(sel[0])
        if 0 <= i < len(self.propuestas):
            porque = self.propuestas[i]["porque"]
            # Al de arriba se le pone delante por que es el de arriba. Los
            # demas siguen ahi por si el primero no convence o ya se probo.
            if i == 0:
                porque = T("ing.es_el_primero") + "\n\n" + porque
            self._escribir(self.explica, porque)

    def aplicar(self):
        sel = self.tabla.selection()
        if not sel or not self.propuestas:
            messagebox.showinfo(T("ing.titulo"), T("ing.elige_cambio"),
                                parent=self.v)
            return
        cambio = self.propuestas[self.tabla.index(sel[0])]
        destino = _siguiente_prueba(self.ficha["ruta"])
        if not I.aplicar(self.ficha, [cambio], destino):
            messagebox.showerror(T("ing.titulo"), T("ing.no_se_pudo"),
                                 parent=self.v)
            return
        self.estado.configure(
            text=T("ing.guardado") % os.path.basename(destino), foreground=VERDE)
        messagebox.showinfo(T("ing.titulo"),
                            T("ing.guardado_largo")
                            % (os.path.basename(destino), cambio["nombre"]),
                            parent=self.v)
        if self.al_terminar:
            self.al_terminar()


def _siguiente_prueba(ruta):
    """
    'Lexus_Dry_Race_Safe.svm' -> 'Lexus_Dry_Race_Safe_p2.svm', y luego p3.

    Se numeran las pruebas en vez de machacar porque asi queda el rastro de
    lo que se ha ido tocando y se puede volver a cualquiera de ellas.
    """
    carpeta = os.path.dirname(ruta)
    base = os.path.splitext(os.path.basename(ruta))[0]
    base = base.rsplit("_p", 1)[0] if base.rsplit("_p", 1)[-1].isdigit() else base
    n = 2
    while os.path.exists(os.path.join(carpeta, "%s_p%d.svm" % (base, n))):
        n += 1
    return os.path.join(carpeta, "%s_p%d.svm" % (base, n))
