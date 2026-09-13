# -*- coding: utf-8 -*-
"""
Como esta puesta la pantalla del juego, y si el mapa va a poder verse encima.

POR QUE ESTO EXISTE. El mapa es una ventana por encima del juego, asi que
depende de dos cosas que no estan en el programa ni se ven a simple vista: el
modo de pantalla que tenga puesto LMU, y una casilla de Windows escondida en
las propiedades del ejecutable. Quien no sabe que existen se queda sin mapa y
sin saber por que, o pensando que el programa esta roto.

LAS DOS COSAS QUE SE MIRAN

1. EL MODO DE PANTALLA DEL JUEGO, en `UserData/Config_DX11.ini`:

       WindowedMode=1   ventana
       Borderless=1     ventana sin bordes a pantalla completa
       los dos a 0      pantalla completa exclusiva

2. LAS OPTIMIZACIONES DE PANTALLA COMPLETA DE WINDOWS. Desde Windows 10,
   cuando un juego pide la pantalla en exclusiva, Windows le dice que si pero
   en realidad lo ejecuta como ventana sin bordes con el camino rapido. Le da
   casi toda la velocidad de la exclusiva y a cambio deja el escritorio vivo:
   por eso el mapa se ve tambien en pantalla completa, y por eso el Alt+Tab es
   instantaneo.

   Eso se puede desactivar por juego, con la casilla "Deshabilitar las
   optimizaciones de pantalla completa" (boton derecho en el .exe ->
   Propiedades -> Compatibilidad). Es un consejo que circula mucho por foros
   de rendimiento, y quien la marco en su dia se queda **sin poder ver ningun
   overlay en pantalla completa**, incluido este mapa, sin relacionar una cosa
   con la otra.

DONDE LO GUARDA WINDOWS. En el registro, en la rama del usuario -asi que no
hacen falta permisos de administrador-:

    HKCU\\Software\\Microsoft\\Windows NT\\CurrentVersion\\AppCompatFlags\\Layers

El nombre del valor es la ruta entera del .exe y el contenido es una lista de
marcas separadas por espacios, empezando por "~". La que nos importa es
`DISABLEDXMAXIMIZEDWINDOWEDMODE`; las demas son de otras cosas (escalado,
ejecutar como administrador) y **no se tocan jamas**: una misma linea puede
llevar varias.

    ~ HIGHDPIAWARE DISABLEDXMAXIMIZEDWINDOWEDMODE

ESTE ES EL UNICO SITIO DEL PROGRAMA QUE ESCRIBE FUERA DE SU CARPETA, y se hace
solo cuando el usuario pulsa el boton, avisandole antes de que cambia y de que
hay que reiniciar el juego. El resto del programa no toca nada del sistema ni
del juego, que es parte de su gracia.
"""
import os

MARCA = "DISABLEDXMAXIMIZEDWINDOWEDMODE"
CLAVE = r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"
EXE_JUEGO = "Le Mans Ultimate.exe"


# ------------------------------------------------------ el modo del juego
def modo_del_juego(carpeta_juego):
    """
    "exclusiva", "sin_bordes", "ventana" o None si no se puede saber.

    Se lee del ini del propio juego, que es donde el juego lo guarda. Si el
    archivo no esta -otra version, otra ruta- se devuelve None y quien llame
    dira simplemente que no se sabe, que es mejor que inventarselo.
    """
    if not carpeta_juego:
        return None
    ini = os.path.join(carpeta_juego, "UserData", "Config_DX11.ini")
    try:
        with open(ini, encoding="utf-8-sig", errors="replace") as f:
            texto = f.read()
    except OSError:
        return None
    valores = {}
    for linea in texto.splitlines():
        if "=" in linea:
            k, v = linea.split("=", 1)
            valores[k.strip().lower()] = v.strip()
    try:
        ventana = int(valores.get("windowedmode", "0"))
        sin_bordes = int(valores.get("borderless", "0"))
    except ValueError:
        return None
    if sin_bordes:
        return "sin_bordes"
    if ventana:
        return "ventana"
    return "exclusiva"


def exe_del_juego(carpeta_juego):
    """La ruta del ejecutable, que es como Windows nombra sus ajustes."""
    if not carpeta_juego:
        return None
    ruta = os.path.join(carpeta_juego, EXE_JUEGO)
    return ruta if os.path.isfile(ruta) else None


# ------------------------------------- la casilla de Windows, en el registro
def _abrir(escritura=False):
    import winreg
    permiso = winreg.KEY_READ | (winreg.KEY_WRITE if escritura else 0)
    return winreg.OpenKey(winreg.HKEY_CURRENT_USER, CLAVE, 0, permiso)


def _marcas(exe):
    """Las marcas de compatibilidad de ese .exe, o None si no tiene ninguna."""
    import winreg
    try:
        with _abrir() as k:
            valor, _ = winreg.QueryValueEx(k, exe)
        return [t for t in str(valor).split() if t]
    except (OSError, FileNotFoundError):
        return None


def optimizaciones(exe):
    """
    Si Windows tiene ACTIVADAS las optimizaciones de pantalla completa.

    True  = activadas (lo normal, y lo que hace falta para ver el mapa)
    False = alguien marco la casilla y estan desactivadas
    None  = no se puede saber (no hay .exe, o no se puede leer el registro)
    """
    if not exe:
        return None
    marcas = _marcas(exe)
    if marcas is None:
        return True             # sin entrada en el registro = por defecto
    return MARCA not in [m.upper() for m in marcas]


def activar_optimizaciones(exe):
    """
    Quita la marca que las desactiva, dejando intacto todo lo demas.

    Devuelve (True, mensaje) o (False, motivo). Si en esa linea hay otras
    marcas -escalado, ejecutar como administrador- se conservan; si no queda
    ninguna, se borra la entrada entera, que es como la deja Windows cuando
    uno desmarca la casilla a mano.
    """
    import winreg
    if not exe:
        return False, "no se encuentra el ejecutable del juego"
    marcas = _marcas(exe)
    if marcas is None or MARCA not in [m.upper() for m in marcas]:
        return True, "ya estaban activadas"
    quedan = [m for m in marcas if m.upper() != MARCA and m != "~"]
    try:
        with _abrir(escritura=True) as k:
            if quedan:
                winreg.SetValueEx(k, exe, 0, winreg.REG_SZ,
                                  "~ " + " ".join(quedan))
            else:
                winreg.DeleteValue(k, exe)
    except OSError as e:
        return False, str(e)
    return True, "hecho"


# ------------------------------------------------------------- el resumen
def diagnostico(carpeta_juego):
    """
    Todo junto, para la ventana de opciones y para la revision de consola.

    {"modo": ..., "exe": ..., "optimizaciones": ..., "se_vera": ...}

    `se_vera` es la conclusion: si con lo que hay puesto el mapa se va a ver
    encima del juego. Es None cuando falta algun dato, porque decir "no se va
    a ver" sin estar seguro asusta para nada.
    """
    modo = modo_del_juego(carpeta_juego)
    exe = exe_del_juego(carpeta_juego)
    opt = optimizaciones(exe)
    if modo in ("ventana", "sin_bordes"):
        se_vera = True          # ahi se ve siempre, pase lo que pase
    elif modo == "exclusiva" and opt is not None:
        se_vera = opt           # en exclusiva depende de las optimizaciones
    else:
        se_vera = None
    return {"modo": modo, "exe": exe, "optimizaciones": opt,
            "se_vera": se_vera}
