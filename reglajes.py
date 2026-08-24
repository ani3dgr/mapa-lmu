# -*- coding: utf-8 -*-
"""
Fichas tecnicas de los coches y estructura de la pagina de reglajes.

De momento es solo una vista previa: se ve como quedara pero no hace nada
todavia, por eso la pestana sale en gris con el sello PROXIMAMENTE encima.

Dos cosas distintas viven aqui:

  FICHAS   lo que es cada coche (motor, cilindrada, potencia, donde lleva el
           motor, que ruedas mueve) y un resumen de como se comporta. Esto no
           lo publica el juego por ningun sitio, esta escrito a mano.

  PAGINAS  las mismas paginas de reglaje que tiene el juego en PIT GARAGE ->
           CONFIGURACION DEL COCHE, con los mismos nombres en espanol, para
           que al mirar aqui sepas exactamente donde tocar alli.

Los valores de ejemplo son de un BMW M4 LMGT3 con el reglaje de serie.
"""
import re

# ---------------------------------------------------------------- categorias
# A que categoria pertenece cada coche de los que trae el juego instalados.
# La clave es el nombre de la carpeta del juego, en minusculas y sin espacios.
CATEGORIAS = ["Hypercar", "LMP2", "LMP3", "GT3", "GTE", "Copa"]

CLASE_DE = {
    # Hypercar (LMH y LMDh)
    "alpinea424": "Hypercar", "astonmartinvalkyrie": "Hypercar",
    "bmwmhybridv8": "Hypercar", "cadillacv-lmdh": "Hypercar",
    "ferrari499p": "Hypercar", "genesisgmr001": "Hypercar",
    "isottatipo6": "Hypercar", "lamborghinisc63": "Hypercar",
    "peugeot9x8": "Hypercar", "porsche963": "Hypercar",
    "toyotagr10": "Hypercar", "vandervell680": "Hypercar",
    "sgc007": "Hypercar",
    # LMP2
    "oreca07elms": "LMP2", "oreca07lm": "LMP2",
    # LMP3
    "adessad25": "LMP3", "duqueined09lmp3": "LMP3",
    "ginettag61evo": "LMP3", "ligierjsp325": "LMP3",
    # GT3 / LMGT3
    "911gt3r": "GT3", "astonmartinvantageamr": "GT3",
    "vantageamrgt3evo": "GT3", "bmwm4lmgt3": "GT3",
    "corvettez06gt3r": "GT3", "ferrari296gt3": "GT3",
    "fordmustanggt3": "GT3", "lamborghinihuracangt3": "GT3",
    "lexusrcfgt3": "GT3", "mclaren720sgt3evo": "GT3",
    "mercedesamggt3evo": "GT3",
    # GTE
    "chevroletc8rlm": "GTE", "ferrari488gtelm": "GTE",
    "porsche911rsr-19": "GTE",
    # Coches de copa
    "992spc": "Copa", "mclaren720sgchallenge": "Copa",
}


# --------------------------------------------------------------- fichas
def _f(motor, cc, cv, sitio, traccion, resumen):
    return {"motor": motor, "cilindrada": cc, "potencia": cv,
            "posicion": sitio, "traccion": traccion, "resumen": resumen}


TRAS = "Trasera"
TRAS_H = "Trasera + hibrido trasero"
AWD_H = "Trasera + hibrido delantero (4x4 a alta velocidad)"
CENTRAL = "Central trasero"
COLGADO = "Trasero, detras del eje"
DELANTE = "Delantero"

FICHAS = {
    # ---------------- Hypercar ----------------
    "alpinea424": _f("V6 turbo (Mecachrome)", "3.4 l", "~680 CV (BoP)", CENTRAL, TRAS_H,
                     "LMDh de motor pequeno y turbo largo. Empuja tarde pero muy\n"
                     "fuerte arriba. Agradecido de tren delantero, se apoya bien\n"
                     "en curva media."),
    "astonmartinvalkyrie": _f("V12 atmosferico (Cosworth)", "6.5 l", "~680 CV (BoP)",
                              CENTRAL, TRAS,
                              "El unico sin hibrido y sin turbo. Respuesta inmediata al\n"
                              "gas y freno motor de verdad, pero pierde en salida de\n"
                              "curva lenta contra los hibridos. Sensible al alabeo."),
    "bmwmhybridv8": _f("V8 turbo (P66/3)", "4.0 l", "~680 CV (BoP)", CENTRAL, TRAS_H,
                       "LMDh con mucho par abajo. Se le va de atras si abres pronto;\n"
                       "pide diferencial suave y algo de ala."),
    "cadillacv-lmdh": _f("V8 atmosferico", "5.5 l", "~680 CV (BoP)", CENTRAL, TRAS_H,
                         "Entrega muy lineal, facil de dosificar. De los mas nobles\n"
                         "de la clase, aguanta bien el rebufo por su carroceria."),
    "ferrari499p": _f("V6 turbo", "3.0 l", "~680 CV (BoP)", CENTRAL, AWD_H,
                      "LMH con motor electrico en el eje delantero: por encima de\n"
                      "190 km/h tracciona a las cuatro ruedas. Muy fuerte saliendo\n"
                      "de curva rapida, algo perezoso de morro en la lenta."),
    "genesisgmr001": _f("V8 turbo", "3.9 l", "~680 CV (BoP)", CENTRAL, TRAS_H,
                        "El mas nuevo de la parrilla. Comportamiento neutro, sin\n"
                        "manias, buena base para aprender la clase."),
    "isottatipo6": _f("V6 turbo (HWA)", "3.0 l", "~680 CV (BoP)", CENTRAL, TRAS_H,
                      "LMH pesado y con menos apoyo que el resto. Necesita reglaje\n"
                      "blando para no castigar el neumatico."),
    "lamborghinisc63": _f("V8 turbo", "3.8 l", "~680 CV (BoP)", CENTRAL, TRAS_H,
                          "Nervioso al entrar, sobrevira si sueltas freno de golpe.\n"
                          "Va mejor con la barra trasera floja."),
    "peugeot9x8": _f("V6 turbo", "2.6 l", "~680 CV (BoP)", CENTRAL, AWD_H,
                     "LMH con hibrido delantero. Aerodinamica muy particular: vive\n"
                     "de la altura del chasis, cualquier cambio se nota mucho mas\n"
                     "que en los demas."),
    "porsche963": _f("V8 turbo (derivado del 918)", "4.6 l", "~680 CV (BoP)",
                     CENTRAL, TRAS_H,
                     "De los mas equilibrados. Frena muy tarde y aguanta el\n"
                     "neumatico en tandas largas."),
    "toyotagr10": _f("V6 turbo", "3.5 l", "~680 CV (BoP)", CENTRAL, AWD_H,
                     "LMH con hibrido delantero. El mas afinado de la clase:\n"
                     "estable, previsible y muy bueno con lluvia por el 4x4."),
    "vandervell680": _f("V8 turbo (Gibson)", "4.5 l", "~680 CV (BoP)", CENTRAL, TRAS,
                        "LMH sin hibrido y sin ayudas. Duro de conducir, castiga el\n"
                        "neumatico trasero; recompensa al que es limpio con el gas."),
    "sgc007": _f("V8 turbo (Pipo)", "3.5 l", "~680 CV (BoP)", CENTRAL, TRAS,
                 "LMH sin hibrido, de concepcion antigua. Poca carga aerodinamica:\n"
                 "rapido en recta, sufre en curva enlazada."),
    # ---------------- LMP2 ----------------
    "oreca07elms": _f("V8 atmosferico Gibson GK428", "4.2 l", "~560 CV (BoP ELMS)",
                      CENTRAL, TRAS,
                      "Monomarca: todos llevan el mismo coche, la diferencia es solo\n"
                      "el reglaje y el piloto. Mucho apoyo aerodinamico para el peso\n"
                      "que tiene, frena de forma brutal."),
    "oreca07lm": _f("V8 atmosferico Gibson GK428", "4.2 l", "~600 CV (BoP WEC)",
                    CENTRAL, TRAS,
                    "Version WEC del Oreca 07, con algo mas de potencia. Mismo\n"
                    "comportamiento: enorme en curva rapida, delicado en la lenta\n"
                    "si abusas del piano."),
    # ---------------- LMP3 ----------------
    "adessad25": _f("V8 atmosferico Nissan VK56", "5.6 l", "~455 CV", CENTRAL, TRAS,
                    "Motor comun a toda la clase LMP3. Chasis con poco apoyo: se\n"
                    "conduce mas con el volante que con la aerodinamica."),
    "duqueined09lmp3": _f("V8 atmosferico Nissan VK56", "5.6 l", "~455 CV",
                          CENTRAL, TRAS,
                          "Igual de motor que el resto de LMP3. Algo mas estable de\n"
                          "atras que el Ligier, un poco mas perezoso de morro."),
    "ginettag61evo": _f("V8 atmosferico Nissan VK56", "5.6 l", "~455 CV", CENTRAL, TRAS,
                        "LMP3 de reacciones lentas, perdona mucho. Buena eleccion\n"
                        "para empezar en prototipos."),
    "ligierjsp325": _f("V8 atmosferico Nissan VK56", "5.6 l", "~455 CV", CENTRAL, TRAS,
                       "El mas vivo de los LMP3. Gira muy bien de entrada pero pide\n"
                       "mano derecha con el gas."),
    # ---------------- GT3 / LMGT3 ----------------
    "911gt3r": _f("Boxer 6 atmosferico", "4.2 l", "~500 CV (BoP)", COLGADO, TRAS,
                  "Motor colgado detras del eje trasero: enorme traccion saliendo\n"
                  "de curva lenta, pero si te pasas de frenada el peso empuja la\n"
                  "cola. Se frena recto y se gira despues."),
    "astonmartinvantageamr": _f("V8 turbo", "4.0 l", "~500 CV (BoP)", DELANTE, TRAS,
                                "Version anterior del Vantage GT3. Noble de atras,\n"
                                "tiende al subviraje si cargas mucho el morro."),
    "vantageamrgt3evo": _f("V8 turbo", "4.0 l", "~500 CV (BoP)", DELANTE, TRAS,
                           "Vantage actualizado. Mucho par abajo, hay que ser fino\n"
                           "con el gas al salir; muy estable frenando."),
    "bmwm4lmgt3": _f("6 en linea turbo (S58)", "3.0 l", "~500 CV (BoP)", DELANTE, TRAS,
                     "Motor delantero pero muy retrasado. Neutro y facil de leer,\n"
                     "aguanta bien el neumatico. Es el coche de las capturas que\n"
                     "sirven de ejemplo en esta pantalla."),
    "corvettez06gt3r": _f("V8 atmosferico", "5.5 l", "~500 CV (BoP)",
                          "Delantero centrado", TRAS,
                          "Atmosferico de respuesta directa. Frena muy fuerte y es\n"
                          "estable, pero pesa de morro en curva lenta."),
    "ferrari296gt3": _f("V6 turbo", "3.0 l", "~500 CV (BoP)", CENTRAL, TRAS,
                        "Motor central: gira de maravilla y cambia de direccion muy\n"
                        "rapido. A cambio, es facil pasarse de rotacion en curva\n"
                        "enlazada."),
    "fordmustanggt3": _f("V8 atmosferico Coyote", "5.4 l", "~500 CV (BoP)",
                         DELANTE, TRAS,
                         "Pesado de morro y muy noble. Perdona errores, pero castiga\n"
                         "el neumatico delantero en tandas largas."),
    "lamborghinihuracangt3": _f("V10 atmosferico", "5.2 l", "~500 CV (BoP)",
                                CENTRAL, TRAS,
                                "Uno de los mas rapidos en curva de la clase. Muy\n"
                                "directo, pide precision: cualquier correccion de\n"
                                "volante se paga en tiempo."),
    "lexusrcfgt3": _f("V8 atmosferico", "5.4 l", "~500 CV (BoP)", DELANTE, TRAS,
                      "Motor delantero atmosferico, entrega suavisima. Muy bueno\n"
                      "con neumatico gastado y con lluvia."),
    "mclaren720sgt3evo": _f("V8 turbo", "4.0 l", "~500 CV (BoP)", CENTRAL, TRAS,
                            "Central turbo con mucha carga aerodinamica. Vuela en\n"
                            "curva rapida; en la lenta hay que esperar al turbo\n"
                            "antes de abrir."),
    "mercedesamggt3evo": _f("V8 atmosferico", "6.3 l", "~500 CV (BoP)", DELANTE, TRAS,
                            "El clasico de la clase. Motor grande y suave,\n"
                            "comportamiento estable y previsible en todo momento."),
    # ---------------- GTE ----------------
    "chevroletc8rlm": _f("V8 atmosferico", "5.5 l", "~500 CV (BoP)", CENTRAL, TRAS,
                         "GTE de motor central. Mas apoyo y menos peso que un GT3:\n"
                         "todo pasa mas rapido, y el error se paga antes."),
    "ferrari488gtelm": _f("V8 turbo", "3.9 l", "~500 CV (BoP)", CENTRAL, TRAS,
                          "GTE muy afinado tras anos de desarrollo. Turbo de\n"
                          "respuesta rapida y una traccion excelente."),
    "porsche911rsr-19": _f("Boxer 6 atmosferico", "4.2 l", "~500 CV (BoP)",
                           CENTRAL, TRAS,
                           "Ojo: este 911 lleva el motor DELANTE del eje trasero, no\n"
                           "detras. Se comporta como un central, nada que ver con el\n"
                           "911 GT3 R de la clase GT3."),
    # ---------------- Copa ----------------
    "992spc": _f("Boxer 6 atmosferico", "4.0 l", "~510 CV", COLGADO, TRAS,
                 "Coche de copa monomarca, sin ABS ni control de traccion.\n"
                 "Escuela pura: si frenas torcido, se va."),
    "mclaren720sgchallenge": _f("V8 turbo", "4.0 l", "~720 CV", CENTRAL, TRAS,
                                "Version de circuito del coche de calle, con mas\n"
                                "potencia y menos carga que el GT3. Muy rapido en\n"
                                "recta, exige mucho al frenar."),
}

# ------------------------------------------------------- paginas de reglaje
# Copia de las paginas del juego: PIT GARAGE -> CONFIGURACION DEL COCHE.
# Cada campo es (nombre, valor de ejemplo, se puede tocar).
NO = False
SI = True

PAGINAS = [
    ("Transmision", [
        ("MOTOR", [
            ("Energia virtual", "100%", SI),
            ("Capacidad de combustible", "0.93  (93.0 l)", SI),
            ("Limitador de revoluciones", "7.500", NO),
            ("Mezcla del motor", "Race", SI),
            ("Tapa del radiador de agua", "Open", SI),
            ("Tapa del radiador de aceite", "Open", SI),
        ]),
        ("ELECTRONICA", [
            ("Control de traccion de a bordo", "6", SI),
            ("Menor potencia del CT de a bordo", "6", SI),
            ("Angulo de deslizamiento del CT", "6", SI),
            ("Nivel de regeneracion", "0%", NO),
            ("Mapa motor electrico", "0", NO),
        ]),
        ("DIFERENCIAL", [
            ("Potencia", "Non-adjustable", NO),
            ("Inercia", "Non-adjustable", NO),
            ("Precarga", "120 Nm", SI),
            ("Potencia delantera", "0%", NO),
            ("Inercia delantera", "0%", NO),
            ("Precarga delantera", "1", NO),
        ]),
        ("MARCHAS", [
            ("Relacion de cambio", "Standard", NO),
        ]),
    ]),
    ("Ruedas y frenos", [
        ("RUEDAS DELANTERAS", [
            ("Compuesto", "Nueva  (M)", SI),
            ("Presion de los neumaticos", "136 kPa", SI),
            ("Caida del tren", "-2.20 grados", SI),
            ("Disco de freno", "3.60 cm", NO),
        ]),
        ("RUEDAS TRASERAS", [
            ("Compuesto", "Nueva  (M)", SI),
            ("Presion de los neumaticos", "136 kPa", SI),
            ("Caida del tren", "-1.20 grados", SI),
            ("Disco de freno", "3.20 cm", NO),
        ]),
        ("FRENOS", [
            ("Distribucion de frenada", "50.5 : 49.5", SI),
            ("Migracion de frenos", "0.0", NO),
            ("Max Pedal Force", "108 kgf  (90%)", SI),
            ("Obturacion conducto delantero", "Open", SI),
            ("Obturacion conducto trasero", "Open", SI),
            ("Frenos antibloqueo instalados", "6 (Balanced)", SI),
        ]),
    ]),
    ("Suspension", [
        ("SUSPENSION DELANTERA", [
            ("Indice de muelles", "2", SI),
            ("Indice de muelles tender", "Standard", NO),
            ("Muelle central (3rd spring)", "Desacoplada", NO),
            ("Topes", "0.5 cm", SI),
            ("Altura del chasis", "5.2 cm", SI),
            ("Muelle de goma", "N/D", NO),
        ]),
        ("SUSPENSION TRASERA", [
            ("Indice de muelles", "2", SI),
            ("Indice de muelles tender", "Standard", NO),
            ("Muelle central (3rd spring)", "Desacoplada", NO),
            ("Topes", "0.0 cm", SI),
            ("Altura del chasis", "6.5 cm", SI),
            ("Muelle de goma", "N/D", NO),
        ]),
    ]),
    ("Amortiguadores", [
        ("SUSPENSION DELANTERA", [
            ("Compresion lenta", "4", SI),
            ("Rebote lento", "5", SI),
            ("Compresion rapida", "4", SI),
            ("Rebote rapido", "5", SI),
        ]),
        ("SUSPENSION TRASERA", [
            ("Compresion lenta", "5", SI),
            ("Rebote lento", "3", SI),
            ("Compresion rapida", "5", SI),
            ("Rebote rapido", "3", SI),
        ]),
    ]),
    ("Chasis y aerodinamica", [
        ("CHASIS DELANTERO", [
            ("Caster", "Non-adjustable", NO),
            ("Convergencia", "-0.117 grados", SI),
            ("Barra antivuelco", "P5", SI),
            ("Ancho de via delantero", "Non-adjustable", NO),
            ("Radio de giro (bloqueo)", "516 deg (19.7)", SI),
            ("Difusor delantero", "Estandar", NO),
        ]),
        ("CHASIS TRASERO", [
            ("Convergencia", "0.234 grados", SI),
            ("Barra antivuelco", "P3", SI),
            ("Ancho de via trasero", "Non-adjustable", NO),
            ("Aleron trasero", "2.1 grados", SI),
        ]),
        ("PESO", [
            ("Vertical", "Non-adjustable", NO),
            ("Lateral", "Non-adjustable", NO),
            ("Distribucion del peso", "Non-adjustable", NO),
        ]),
        ("CHASIS AVANZADO", [
            ("Ajuste del chasis 0", "N/A", NO),
            ("Ajuste del chasis 1", "N/A", NO),
            ("Ajuste del chasis 2", "N/A", NO),
            ("Ajuste del chasis 3", "N/A", NO),
        ]),
    ]),
]


# El juego nombra algunas carpetas de forma abreviada o sin la marca. Aqui se
# les pone el nombre real para que la lista se lea bien.
NOMBRES = {
    "911gt3r": "Porsche 911 GT3 R (992)",
    "992spc": "Porsche 911 GT3 Cup (992)",
    "cadillacv-lmdh": "Cadillac V-Series.R",
    "chevroletc8rlm": "Chevrolet Corvette C8.R",
    "corvettez06gt3r": "Chevrolet Corvette Z06 GT3.R",
    "duqueined09lmp3": "Duqueine D09",
    "ferrari488gtelm": "Ferrari 488 GTE Evo",
    "ginettag61evo": "Ginetta G61-LT-P3 Evo",
    "isottatipo6": "Isotta Fraschini Tipo6 LMH-C",
    "lexusrcfgt3": "Lexus RC F GT3",
    "ligierjsp325": "Ligier JS P325",
    "mclaren720sgchallenge": "McLaren 720S GT3 Challenge",
    "mclaren720sgt3evo": "McLaren 720S GT3 Evo",
    "mercedesamggt3evo": "Mercedes-AMG GT3 Evo",
    "porsche911rsr-19": "Porsche 911 RSR-19",
    "sgc007": "Glickenhaus SCG 007 LMH",
    "toyotagr10": "Toyota GR010 Hybrid",
    "vandervell680": "Vanwall Vandervell 680",
    "vantageamrgt3evo": "Aston Martin Vantage AMR GT3 Evo",
    "astonmartinvantageamr": "Aston Martin Vantage AMR GT3",
    "peugeot9x8": "Peugeot 9X8",
    "lamborghinihuracangt3": "Lamborghini Huracan GT3 Evo2",
    "genesisgmr001": "Genesis GMR-001",
    "adessad25": "ADESS AD25 LMP3",
}


def clave(modelo):
    """Nombre comparable: 'BMW M4 LMGT3' -> 'bmwm4lmgt3'"""
    return "".join(c for c in (modelo or "").lower() if c.isalnum() or c == "-")


def bonito(modelo):
    """El nombre que se ensena en pantalla."""
    return NOMBRES.get(clave(modelo), modelo)


def ficha(modelo):
    return FICHAS.get(clave(modelo))


def por_categoria():
    """
    {'GT3': ['BMW M4 LMGT3', ...], ...} con los coches que trae instalados el
    juego. Si el juego no aparece, se usa la lista que trae el programa.
    """
    import coches
    modelos = coches.modelos_instalados()
    if not modelos:
        modelos = sorted(FICHAS.keys())
    salida = {}
    for c in CATEGORIAS:
        salida[c] = []
    for m in modelos:
        salida.setdefault(CLASE_DE.get(clave(m), "GT3"), []).append(m)
    for lista in salida.values():
        lista.sort(key=bonito)
    return salida


# ----------------------------------------------------------- traduccion
# Los datos de arriba estan en castellano porque es donde se escribieron. Lo
# que se ensena en pantalla sale de la carpeta idiomas, con estas funciones.

def _slug(texto):
    """El mismo apano que usa la herramienta que genero las claves."""
    s = texto.lower()
    s = (s.replace("\u00e1", "a").replace("\u00e9", "e").replace("\u00ed", "i")
          .replace("\u00f3", "o").replace("\u00fa", "u").replace("\u00f1", "n"))
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s[:44]


def _tr(prefijo, texto):
    import idiomas
    return idiomas.t(prefijo + _slug(texto))


def ficha_traducida(modelo):
    """La ficha del coche en el idioma elegido, o None si no hay ficha."""
    import idiomas
    f = ficha(modelo)
    if not f:
        return None
    hueco = clave(modelo).replace("-", "_")
    return {
        "motor": _tr("reg.v.", f["motor"]),
        "cilindrada": f["cilindrada"],          # "3.4 l" se dice igual en todas
        "potencia": _tr("reg.v.", f["potencia"]),
        "posicion": _tr("reg.v.", f["posicion"]),
        "traccion": _tr("reg.v.", f["traccion"]),
        "resumen": idiomas.t("reg.res." + hueco),
    }


def paginas_traducidas():
    """Las paginas de reglaje con todo el texto en el idioma elegido."""
    salida = []
    for pagina, secciones in PAGINAS:
        nuevas = []
        for seccion, campos in secciones:
            nuevas.append((_tr("reg.sec.", seccion),
                           [(_tr("reg.campo.", e), _tr("reg.val.", v), a)
                            for e, v, a in campos]))
        salida.append((_tr("reg.pag.", pagina), nuevas))
    return salida
