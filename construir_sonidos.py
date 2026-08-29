# -*- coding: utf-8 -*-
"""
Genera los sonidos de aviso. Se ejecuta a mano, una vez:

    python construir_sonidos.py

Deja tres .wav en la carpeta "sonidos". Se generan aqui en vez de bajarlos
de ningun sitio por dos razones: asi no dependen de que una web siga viva, y
asi se pueden repartir con el programa sin lios de licencias.

COMO ESTAN PENSADOS
No son sonidos bonitos, son sonidos que se oyen. En marcha, con el motor y
el volante, un tono suave se pierde. Los tres van entre 700 y 1600 Hz, que
es donde mejor oye el oido humano y donde menos ruido hace un coche de
carreras. Duran poco a proposito: un aviso largo tapa lo que venga detras.

Se les pone una entrada y una salida suaves (unos milisegundos) porque un
tono que empieza de golpe suena a chasquido y molesta.
"""
import math
import os
import struct
import wave

AQUI = os.path.dirname(os.path.abspath(__file__))
CARPETA = os.path.join(AQUI, "sonidos")

HZ = 44100
VOLUMEN = 0.55


def tono(frecuencia, segundos, forma="seno"):
    """Un tono suelto, con los bordes suavizados."""
    n = int(HZ * segundos)
    subida = int(HZ * 0.004)
    muestras = []
    for i in range(n):
        t = i / HZ
        if forma == "cuadrada":
            v = 1.0 if math.sin(2 * math.pi * frecuencia * t) >= 0 else -1.0
            v *= 0.6                      # la cuadrada suena mas fuerte
        else:
            v = math.sin(2 * math.pi * frecuencia * t)
        # bordes suaves: sin esto suena un chasquido al empezar y al acabar
        if i < subida:
            v *= i / subida
        elif i > n - subida:
            v *= (n - i) / subida
        muestras.append(v)
    return muestras


def silencio(segundos):
    return [0.0] * int(HZ * segundos)


def guardar(nombre, muestras):
    os.makedirs(CARPETA, exist_ok=True)
    ruta = os.path.join(CARPETA, nombre)
    with wave.open(ruta, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(HZ)
        crudo = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, v))
                                               * VOLUMEN * 32767))
                         for v in muestras)
        w.writeframes(crudo)
    return ruta, len(muestras) / HZ


SONIDOS = {
    # Corto y seco. Para quien no quiere que le sobresalten.
    "bip.wav": tono(1200, 0.09),
    # Dos golpes. Se distingue de cualquier pitido del juego.
    "doble.wav": tono(1400, 0.07) + silencio(0.05) + tono(1400, 0.07),
    # Grave y aspero, de alarma. El que mas destaca con el motor sonando.
    "alarma.wav": (tono(760, 0.11, "cuadrada") + silencio(0.04)
                   + tono(640, 0.16, "cuadrada")),
}


def main():
    print("Generando los sonidos de aviso en:")
    print("   %s" % CARPETA)
    print()
    for nombre, muestras in SONIDOS.items():
        ruta, dura = guardar(nombre, muestras)
        print("   %-12s %.2f s   %d KB"
              % (nombre, dura, os.path.getsize(ruta) / 1024))
    print()
    print("Listo. En las opciones se elige cual, o se pone un .wav propio.")


main()
