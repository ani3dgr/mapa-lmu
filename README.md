# Mapa de pista para Le Mans Ultimate

Un mapa que se pone encima del juego y te enseña dónde está cada coche, con
**tu coche bien visible**, los rivales por colores de categoría, los números y
nombres de las curvas, y un modo para compararte con el más rápido de la sesión.

Es gratuito. Úsalo y pásalo a quien quieras.

*(English below — [jump to English](#track-map-for-le-mans-ultimate))*

---

## Qué hace

- **Mapa transparente** encima del juego, en cualquier esquina y del tamaño que
  quieras. F9 lo oculta o lo muestra, F10 abre las opciones.
- **Tu coche destacado** con un anillo, para que no se pierda cuando los puntos
  se amontonan.
- **Comparar tiempos en vivo** contra la vuelta más rápida de los rivales: el
  trazado se pinta del color de la referencia y encima se superponen tus tramos
  en rojo, amarillo o verde. Si un rival mejora, tu vuelta se recolorea sola.
- **Aviso de salidas de pista**, marcando con un triángulo dónde te saliste la
  última vez que pasaste por ahí.
- **Aviso de coches parados** en plena pista, que parpadean en el mapa. Sirve
  sobre todo para las curvas ciegas.
- **Comparador de trazadas**: guarda tus vueltas con sus sectores y las dibuja
  sobre el circuito a su anchura real, coloreadas contra la del rival.
- **Escáner de circuitos**, para medir una pista nueva desde dentro del juego.
- **Siete idiomas**: español, inglés, francés, italiano, alemán, portugués y
  polaco.

## Qué hace falta

- **Le Mans Ultimate** (Steam o Epic; el programa encuentra la carpeta solo).
- El juego en modo **borderless**. En pantalla completa exclusiva, Windows no
  deja poner nada encima y el mapa no se vería.
- **Python 3.12** o superior. No hace falta instalar nada más: usa solo lo que
  Python trae de serie.

## Cómo se usa

1. Descarga la carpeta y déjala donde quieras (el escritorio vale). **No la
   pongas dentro de `Archivos de programa`**: Windows no deja escribir ahí y el
   programa necesita guardar su configuración.
2. En el juego, desactiva el mapa que trae de serie y ponlo en borderless.
3. Abre `MAPA.bat`.

Todo lo demás está explicado dentro del programa: cada pestaña de las opciones
tiene un botón **(i)** con su explicación. Y en `INSTRUCCIONES.txt` está el
manual completo.

## Compartir circuitos

Cada circuito medido es **un archivo suelto** dentro de `circuitos/`. Para
pasarle una pista a alguien basta con mandarle su `.json` y que lo copie en esa
misma carpeta: el programa lo detecta al arrancar, sin instalar nada.

## Traducir a otro idioma

Cada idioma es un archivo de `idiomas/`. Se copia `en.json`, se le pone el
código del idioma nuevo y se traduce el texto de la derecha de cada línea.
Aparece solo en la lista. Lo que falte sale en inglés, así que se puede
traducir poco a poco. Hay más detalles en `idiomas/LEEME.txt`.

## Lo que el juego NO publica

Merece la pena decirlo, porque explica por qué faltan cosas:

- **Las banderas.** Se comprobó grabando una sesión entera con incidentes
  provocados a propósito: LMU no publica ninguna señal de bandera para
  programas externos. Por eso no hay aviso de amarilla, y en su lugar se detecta
  directamente el coche parado, que es el peligro de verdad.
- **La marca y el modelo del coche.** El juego solo da el nombre del equipo con
  su dorsal. Por eso hay una tabla en la pestaña *Coches* que se rellena una vez
  por equipo, y que el programa va completando solo con los que no conoce.
- **La velocidad de cada coche en cada punto.** Solo publica el tiempo de la
  mejor vuelta, así que una vuelta anterior no se puede reconstruir: solo cuentan
  las vueltas dadas con el programa abierto.

---

# Track map for Le Mans Ultimate

An overlay map that shows you where every car is, with **your own car clearly
visible**, rivals coloured by class, corner numbers and names, and a mode that
measures you against the fastest car in the session.

It is free. Use it and pass it on to anyone.

## What it does

- **Transparent overlay map**, in any corner and at any size. F9 hides or shows
  it, F10 opens the options.
- **Your car highlighted** with a ring, so it is never covered when the dots
  pile up.
- **Live time comparison** against the rivals' fastest lap: the track is painted
  in the reference colour and your own segments are laid over it in red, yellow
  or green. If a rival improves, your lap recolours itself.
- **Off-track warnings**, marking with a triangle where you last went off.
- **Stopped-car warnings** out on track, flashing on the map. Mainly for blind
  corners.
- **Line comparator**: saves your laps with their sectors and draws them over
  the track at its real width, coloured against the rival's.
- **Track scanner**, to measure a new track from inside the game.
- **Seven languages**: Spanish, English, French, Italian, German, Portuguese and
  Polish.

## What you need

- **Le Mans Ultimate** (Steam or Epic; the program finds the folder by itself).
- The game in **borderless** mode. In exclusive fullscreen, Windows will not let
  anything sit on top and the map would not show.
- **Python 3.12** or newer. Nothing else to install: it only uses what Python
  ships with.

## How to use it

1. Download the folder and put it wherever you like (the desktop is fine).
   **Do not put it inside `Program Files`**: Windows will not allow writing
   there and the program needs to save its settings.
2. In the game, turn off the built-in map and set borderless.
3. Open `MAPA.bat`.

Everything else is explained inside the program: every options tab has an
**(i)** button with its own explanation.

## Sharing tracks

Each measured track is **a single file** inside `circuitos/`. To pass a track to
someone, send them its `.json` and have them copy it into that same folder: the
program picks it up on startup, with nothing to install.

## Translating

Each language is one file in `idiomas/`. Copy `en.json`, rename it to your
language code and translate the right-hand side of each line. It shows up in the
list on its own. Anything missing falls back to English, so it can be done bit
by bit.

## What the game does NOT publish

Worth stating, because it explains what is missing:

- **Flags.** Checked by recording a full session with deliberate incidents: LMU
  publishes no flag signal at all to external programs. That is why there is no
  yellow-flag warning, and why stopped cars are detected directly instead.
- **Car make and model.** The game only gives the team name with its number.
  Hence the table in the *Cars* tab, filled in once per team, which the program
  keeps topping up on its own.
- **Each car's speed at each point.** It only publishes the best lap time, so an
  earlier lap cannot be reconstructed: only laps driven with the program open
  count.
