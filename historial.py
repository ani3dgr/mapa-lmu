# -*- coding: utf-8 -*-
"""
El cuaderno de a bordo: que se le ha tocado a cada reglaje, cuando, y como
quedo guardado.

Sirve para tres cosas, y la tercera es la importante:

  1. Ver que se ha ido cambiando, en cristiano y por orden.
  2. Ver DONDE acabo cada cambio: si se sobrescribio el mismo archivo o si
     se guardo con otro nombre, y con cual. Sin esto, despues de una tarde
     de pruebas nadie sabe cual de los seis archivos es el bueno.
  3. Volver atras. Cada apunte guarda el reglaje ENTERO tal y como estaba
     antes de tocarlo, asi que se puede restaurar cualquier momento. Es
     para cuando llevas cinco cambios, el coche va peor que al principio y
     no te acuerdas de por donde empezaste.

POR QUE SE GUARDA EL REGLAJE ENTERO Y NO SOLO LO QUE CAMBIO
Porque deshacer paso a paso falla en cuanto alguien toca un archivo por
fuera del programa, y la gente lo toca: lo edita en el juego, lo copia, lo
renombra. Guardar la foto completa son unos doscientos numeros por apunte,
que no es nada, y a cambio restaurar funciona siempre.
"""
import json
import os
import time

import rutas

RUTA = rutas.datos("historial_reglajes.json")

# Cuantos apuntes se guardan por reglaje. Cincuenta son muchas tardes de
# pruebas; a partir de ahi se van cayendo los mas viejos.
TOPE = 50


def _cargar():
    try:
        with open(RUTA, encoding="utf-8-sig") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _guardar(d):
    try:
        with open(RUTA, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        return True
    except OSError:
        return False


def _llave(circuito, nombre):
    """
    Un reglaje se identifica por circuito y nombre.

    Se apunta con el nombre ORIGINAL, el del reglaje del que se partio, no
    el del archivo que se acaba de escribir. Asi todas las pruebas de un
    mismo reglaje quedan juntas en la misma lista aunque cada una se haya
    guardado con un nombre distinto, que es justo lo que hace falta para
    poder volver a cualquiera de ellas.
    """
    return "%s|%s" % (circuito, nombre)


def foto(ficha):
    """Los numeros del reglaje tal y como esta ahora mismo."""
    return {k: a["indice"] for k, a in ficha["ajustes"].items()
            if a["indice"] is not None}


def apuntar(ficha, cambios, guardado_en, modo, quien="mano"):
    """
    Anota un cambio.

    `ficha` es el reglaje ANTES de tocarlo, `cambios` la lista de lo que se
    ha movido, `guardado_en` la ruta del archivo que ha quedado escrito y
    `modo` si fue "copia" o "sobrescribir". `quien` distingue lo que
    propuso el ingeniero de lo que se toco a mano.
    """
    d = _cargar()
    llave = _llave(ficha["circuito"], ficha["nombre"])
    lista = d.setdefault(llave, [])
    lista.append({
        "cuando": time.strftime("%Y-%m-%d %H:%M"),
        "quien": quien,
        "modo": modo,
        "archivo": os.path.basename(guardado_en),
        "ruta": guardado_en,
        "cambios": [{"nombre": c.get("nombre", c.get("clave", "")),
                     "de": c.get("ahora", ""), "a": c.get("queda", ""),
                     "clave": c.get("param") or c.get("clave", "")}
                    for c in cambios],
        "antes": foto(ficha),
    })
    d[llave] = lista[-TOPE:]
    _guardar(d)


def leer(circuito, nombre):
    """Los apuntes de un reglaje, del mas nuevo al mas viejo."""
    return list(reversed(_cargar().get(_llave(circuito, nombre), [])))


def todo():
    """Todos los apuntes de todos los reglajes."""
    return _cargar()


def restaurar(apunte, ficha_actual, destino):
    """
    Devuelve un reglaje a como estaba antes del cambio que dice el apunte.

    Se reescribe el archivo linea a linea igual que en el resto del
    programa: solo cambian los numeros que hay que cambiar y todo lo demas
    se copia tal cual. Lo que el programa no entienda sigue estando.
    """
    antes = apunte.get("antes") or {}
    if not antes:
        return None

    seccion = "GENERAL"
    salida = []
    for linea in ficha_actual["lineas"]:
        pelada = linea.strip()
        if pelada.startswith("[") and pelada.endswith("]"):
            seccion = pelada[1:-1].strip().upper()
            salida.append(linea)
            continue
        if pelada.startswith("//") or "=" not in pelada:
            salida.append(linea)
            continue
        clave = pelada.split("=", 1)[0].strip()
        llave = "%s/%s" % (seccion, clave)
        ahora = ficha_actual["ajustes"].get(llave, {}).get("indice")
        # Solo se reescribe lo que de verdad ha cambiado. Lo que sigue igual
        # se copia tal cual, letra por letra. Al reescribirlo todo, cuatro
        # lineas del apartado BASIC, que guardan medios (0.5), se quedaban
        # en 0 al pasarlas por un entero. Tocar solo lo justo evita esa
        # clase entera de problemas.
        if llave in antes and ahora is not None and ahora != antes[llave]:
            viejo = ficha_actual["ajustes"][llave]["texto"]
            salida.append("%s=%d//%s" % (clave, int(antes[llave]),
                                         ("<- %s" % viejo) if viejo else ""))
        else:
            salida.append(linea)

    try:
        with open(destino, "w", encoding="latin-1", newline="\r\n") as f:
            f.write("\n".join(salida) + "\n")
    except OSError:
        return None
    return destino


def olvidar(circuito, nombre):
    """Borra el historial de un reglaje."""
    d = _cargar()
    if d.pop(_llave(circuito, nombre), None) is not None:
        _guardar(d)
