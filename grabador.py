# -*- coding: utf-8 -*-
"""
Graba las trazadas de cada sesion para poder revisarlas despues.

De cada vuelta que das se guarda el recorrido, el tiempo y los tres sectores.
De los rivales solo se guarda la vuelta mas rapida, que es la que sirve de
referencia para comparar.

Los archivos van a mapa/sesiones/ , uno por sesion, y se pueden borrar desde
las opciones del mapa: esto crece con el uso y no es plan de llenar el disco.

Ojo: el buffer del juego solo se refresca 5 veces por segundo, asi que a 200
km/h hay unos 11 m entre punto y punto. Vale para ver por donde va la trazada
(mas por dentro, mas por fuera) pero no para afinar al centimetro.
"""
import json
import math
import os
import time

import coches
import idiomas

import rutas

CARPETA = rutas.datos("sesiones")
PUNTOS_VUELTA = 300      # puntos guardados por vuelta tras remuestrear
GUARDAR_CADA = 20.0      # s entre volcados a disco
VUELTAS_MAX = 120        # tope por sesion, para que un archivo no crezca sin fin
VUELTAS_PROTEGIDAS = 30  # las ultimas nunca se tiran, aunque sean lentas
MIN_PUNTOS = 50          # una vuelta con menos que esto no se guarda
ESPERA_TIEMPO = 1.0      # s hasta que el juego publica el tiempo de la vuelta


def remuestrear(puntos, n):
    """
    Reparte n puntos a distancia constante a lo largo del recorrido.

    Cada punto es (x, z, kmh): la velocidad viaja con el punto porque sin ella
    no se puede colorear la trazada comparandola con la referencia.
    """
    if len(puntos) < 2:
        return puntos
    acum, total = [0.0], 0.0
    for a, b in zip(puntos, puntos[1:]):
        total += math.hypot(b[0] - a[0], b[1] - a[1])
        acum.append(total)
    if total <= 0:
        return puntos[:1]
    salida, j = [], 0
    for k in range(n):
        objetivo = total * k / n
        while j < len(acum) - 2 and acum[j + 1] < objetivo:
            j += 1
        tramo = acum[j + 1] - acum[j]
        t = 0.0 if tramo <= 0 else (objetivo - acum[j]) / tramo
        a, b = puntos[j], puntos[j + 1]
        salida.append((round(a[0] + (b[0] - a[0]) * t, 1),
                       round(a[1] + (b[1] - a[1]) * t, 1),
                       round(a[2] + (b[2] - a[2]) * t, 1)))
    return salida


class Grabador:
    """Una instancia por sesion. Al cambiar de sesion o circuito se crea otra."""

    def __init__(self, clave, nombre_circuito, sesion, largo, marca_tiempo):
        self.clave = clave
        self.nombre_circuito = nombre_circuito
        self.sesion = sesion
        self.largo = max(float(largo), 1.0)
        self.marca = marca_tiempo          # texto con fecha y hora, para el nombre
        self.mis_vueltas = []
        self.contador = 0                  # numero de vuelta, sigue subiendo
        self.referencia = None             # la vuelta rival mas rapida
        self.coches = {}                   # nombre -> seguimiento
        self._ultimo_guardado = 0.0
        self._sucio = False

    @property
    def archivo(self):
        return os.path.join(CARPETA, "%s_%s.json" % (self.clave, self.marca))

    # ---------- captura ----------
    def actualiza(self, coches, ahora):
        for c in coches:
            nombre = c.get("nombre") or ""
            if not nombre:
                continue
            st = self.coches.get(nombre)
            if st is None:
                # 'entera' solo se pone a True tras ver cruzar la meta: hasta
                # entonces lo que se lleva grabado es un trozo de vuelta
                self.coches[nombre] = {"dist": c["dist"], "t": ahora, "puntos": [],
                                       "entera": False, "pendiente": None,
                                       "desde": c["dist"], "meta": ahora}
                continue

            self._resolver_pendiente(st, c, ahora)

            antes, ahora_d = st["dist"], c["dist"]
            if ahora_d == antes:
                continue                    # el juego aun no ha publicado dato nuevo

            if ahora_d < antes - self.largo * 0.5:
                # El tiempo de la vuelta tarda unas decimas en publicarse: si se
                # leyera aqui saldria cero o el de la vuelta anterior. Se deja
                # en espera y se recoge un segundo despues.
                # Vale si se vio empezar la vuelta, o si se empezo a mirar tan
                # cerca de la meta que da igual. Se mide con la DISTANCIA DE
                # VUELTA del juego, no con lo largo que sea la trazada: un
                # coche recorta las curvas y su trazada es mas corta que el
                # circuito, asi que medir por longitud rechazaria vueltas buenas.
                if st["entera"] or st["desde"] <= self.largo * 0.03:
                    st["pendiente"] = {"puntos": st["puntos"], "t": ahora,
                                       "duracion": ahora - st["meta"]}
                st["meta"] = ahora
                st["puntos"] = []
                st["desde"] = 0.0
                st["entera"] = True         # la siguiente empieza en la meta
            elif ahora_d > antes:
                dt = ahora - st["t"]
                kmh = (ahora_d - antes) / dt * 3.6 if dt > 0 else 0.0
                if not 0 <= kmh < 400:
                    kmh = 0.0
                st["puntos"].append((c["x"], c["z"], kmh))
            st["dist"], st["t"] = ahora_d, ahora

        if self._sucio and ahora - self._ultimo_guardado > GUARDAR_CADA:
            self.guardar()

    def _resolver_pendiente(self, st, c, ahora):
        """Recoge el tiempo de la vuelta que acaba de cerrarse y la guarda."""
        pen = st.get("pendiente")
        if not pen or ahora - pen["t"] < ESPERA_TIEMPO:
            return
        st["pendiente"] = None
        self._cerrar_vuelta(c, pen["puntos"], pen["duracion"])

    def _cerrar_vuelta(self, c, puntos, duracion=0.0):
        """Guarda la vuelta si el recorrido es bueno."""
        # Una vuelta ANULADA (te has salido) se publica con tiempo -1. Antes se
        # descartaba, y como casi todas las vueltas de aprendizaje son anuladas
        # no se guardaba ninguna. Ahora se cronometra por nuestra cuenta entre
        # cruces de meta y se marca como no valida, que para comparar trazadas
        # sirve igual, y ademas es donde mas interesa mirar.
        publicado = c.get("ultima", 0.0)
        valida = publicado > 0
        tiempo = publicado if valida else duracion
        quien = ("TU" if c.get("es_yo") else c.get("nombre", "?"))
        if len(puntos) < MIN_PUNTOS or tiempo <= 0:
            print("[grabador] %s: vuelta descartada (%d puntos, %.1f s)"
                  % (quien, len(puntos), tiempo))
            return

        # comprobacion de respaldo: lo recorrido tiene que parecerse al largo
        # del circuito, por si se perdieron lecturas por el camino
        # respaldo por si se perdieron lecturas por el camino; el umbral es
        # holgado porque la trazada real es algo mas corta que el circuito
        recorrido = sum(math.hypot(b[0] - a[0], b[1] - a[1])
                        for a, b in zip(puntos, puntos[1:]))
        if recorrido < self.largo * 0.85:
            print("[grabador] %s: vuelta descartada (recorrido %.0f m de %.0f)"
                  % (quien, recorrido, self.largo))
            return

        trazada = remuestrear(puntos, PUNTOS_VUELTA)
        sec1 = c.get("sec1", 0.0)
        sec2 = c.get("sec2", 0.0)
        vuelta = {
            "tiempo": round(tiempo, 3),
            "s1": round(sec1, 3) if sec1 > 0 else None,
            "s2": round(sec2 - sec1, 3) if sec1 > 0 and sec2 > sec1 else None,
            "s3": round(tiempo - sec2, 3) if sec2 > 0 and tiempo > sec2 else None,
            "puntos": trazada,
            "valida": valida,
            # En vivo el juego solo da el equipo con su dorsal y un codigo
            # interno tipo "10_26_GARA63384034". El modelo sale de ese codigo,
            # buscandolo en el catalogo que se monta con los resultados de las
            # sesiones terminadas (resultados.py).
            "equipo": equipo_de(c.get("vehiculo", "")),
            "dorsal": dorsal_de(c.get("vehiculo", "")),
            "clase": c.get("clase", ""),
            "coche": coches.texto(c.get("vehiculo", ""), c.get("clase", ""),
                                  c.get("codigo", "")),
        }

        # Solo cae aqui un coche que no haya terminado ninguna sesion todavia:
        # en cuanto acabe una, el juego escribe su archivo y se identifica solo.
        coches.anotar_desconocido(c.get("vehiculo", ""), c.get("clase", ""),
                                  self.nombre_circuito, self.marca,
                                  c.get("codigo", ""))

        if c.get("es_yo"):
            self.contador += 1
            vuelta["n"] = self.contador
            print("[grabador] TU: vuelta %d guardada  %.3f s%s"
                  % (self.contador, tiempo, "" if valida else "  (anulada)"))
            # Quien iba al volante. En resistencia el coche cambia de piloto en
            # las paradas, y sin esto se mezclarian las vueltas de los dos.
            vuelta["piloto"] = c.get("nombre", "")
            self.mis_vueltas.append(vuelta)
            if len(self.mis_vueltas) > VUELTAS_MAX:
                # Se tira la mas lenta, PERO nunca una de las ultimas: en una
                # carrera de 6 h las mejores suelen ser del principio con poco
                # combustible, y sin esta proteccion se perderia todo el final.
                recientes = set(id(v) for v in self.mis_vueltas[-VUELTAS_PROTEGIDAS:])
                candidatas = [v for v in self.mis_vueltas if id(v) not in recientes]
                if candidatas:
                    self.mis_vueltas.remove(max(candidatas, key=lambda v: v["tiempo"]))
            self._sucio = True
        elif self.referencia is None or tiempo < self.referencia["tiempo"]:
            vuelta["nombre"] = c["nombre"]
            self.referencia = vuelta
            self._sucio = True

    def _mi_coche(self):
        """Con que coche se rodo, para poder comparar entre sesiones."""
        for v in reversed(self.mis_vueltas):
            if v.get("equipo"):
                partes = [v.get("coche") or v["equipo"], v.get("dorsal", "")]
                if v.get("coche") and v["equipo"]:
                    partes.insert(1, "(%s)" % v["equipo"])
                return " ".join(x for x in partes if x)
        return ""

    # ---------- disco ----------
    def guardar(self):
        if not self.mis_vueltas and not self.referencia:
            return
        try:
            os.makedirs(CARPETA, exist_ok=True)
            with open(self.archivo, "w", encoding="utf-8") as f:
                json.dump({
                    "circuito": self.nombre_circuito,
                    "clave": self.clave,
                    "sesion": self.sesion,
                    "fecha": self.marca,
                    "largo": round(self.largo, 1),
                    "pilotos": sorted({v.get("piloto", "") for v in self.mis_vueltas} - {""}),
                    "mi_coche": self._mi_coche(),
                    "mis_vueltas": self.mis_vueltas,
                    "referencia": self.referencia,
                }, f, ensure_ascii=False, separators=(",", ":"))
            # OJO: monotonic, no time.time(). Quien llama pasa un monotonic
            # (segundos desde que arranco el ordenador) y aqui se guardaba un
            # time.time() (segundos desde 1970). Al restarlos salia un numero
            # enorme y negativo, la condicion de volcar no se cumplia NUNCA
            # mas, y la sesion se quedaba con la primera vuelta y nada mas.
            self._ultimo_guardado = time.monotonic()
            self._sucio = False
        except OSError:
            pass


def equipo_de(nombre_vehiculo):
    return coches.equipo_de(nombre_vehiculo)


def dorsal_de(nombre_vehiculo):
    return coches.dorsal_de(nombre_vehiculo)


# ---------- consulta desde las opciones ----------
def listar_sesiones():
    """Sesiones guardadas, de la mas reciente a la mas antigua."""
    salida = []
    if not os.path.isdir(CARPETA):
        return salida
    for archivo in os.listdir(CARPETA):
        if not archivo.endswith(".json"):
            continue
        ruta = os.path.join(CARPETA, archivo)
        try:
            with open(ruta, encoding="utf-8") as f:
                d = json.load(f)
            salida.append({
                "ruta": ruta,
                "circuito": d.get("circuito", "?"),
                "fecha": d.get("fecha", ""),
                "sesion": d.get("sesion"),
                "vueltas": len(d.get("mis_vueltas", [])),
                "pilotos": d.get("pilotos", []),
                "coche": d.get("mi_coche", ""),
                "tamano": os.path.getsize(ruta),
            })
        except (OSError, ValueError):
            continue
    salida.sort(key=lambda s: s["fecha"], reverse=True)
    return salida


def cargar(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def borrar(ruta):
    try:
        os.remove(ruta)
        return True
    except OSError:
        return False


def nombre_sesion(codigo):
    """
    5 = clasificacion, 10-13 = carrera... para mostrarlo legible.

    Lo que se guarda en el archivo de la sesion es el NUMERO, no este texto,
    asi que las sesiones grabadas hace meses tambien salen en el idioma que
    tengas puesto ahora.
    """
    if codigo is None:
        return ""
    if codigo == 0:
        return idiomas.t("ses.sin_empezar")
    if 1 <= codigo <= 4:
        return idiomas.t("ses.practica")
    if 5 <= codigo <= 8:
        return idiomas.t("ses.clasificacion")
    if codigo == 9:
        return idiomas.t("ses.warmup")
    return idiomas.t("ses.carrera")
