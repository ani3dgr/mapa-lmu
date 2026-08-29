# Mapa de pista para Le Mans Ultimate

Un mapa que se pone encima del juego y te enseña dónde está cada coche, con
**tu coche bien visible**, los rivales por colores de categoría, los números y
nombres de las curvas, y un modo para compararte con el más rápido de tu categoría.

Es gratuito. Úsalo y pásalo a quien quieras.

*(English below — [jump to English](#track-map-for-le-mans-ultimate))*

---

## Qué hace

- **Mapa transparente** encima del juego, en cualquier esquina y del tamaño que
  quieras. F9 lo oculta o lo muestra, F10 abre las opciones.
- **Tu coche destacado** con un anillo, para que no se pierda cuando los puntos
  se amontonan.
- **Comparar tiempos en vivo** contra la vuelta más rápida **de tu categoría**,
  que a un GT3 no se le mide contra un LMP2: el trazado se pinta del color de la
  referencia y encima se superponen tus tramos en rojo, amarillo o verde. Si un
  rival de tu clase mejora, tu vuelta se recolorea sola.
- **Aviso de salidas de pista**, marcando con un triángulo dónde te saliste la
  última vez que pasaste por ahí.
- **Aviso de coches parados** en plena pista, que parpadean en el mapa y
  suenan. No avisa por cercanía como un spotter, sino **por segundos**: sabe por
  dónde va cada coche en el trazado y te avisa mientras todavía queda tiempo de
  hacer algo. El sonido se elige de una lista y puedes dejar el tuyo en la
  carpeta `sonidos`.
- **Comparador de trazadas**: guarda tus vueltas con sus sectores y las dibuja
  sobre el circuito a su anchura real, coloreadas contra la del rival.
- **Reglajes** *(nuevo en la 1.4)*: una biblioteca con todos los `.svm` que
  tienes en el ordenador, ordenados por coche y circuito, con las fichas de los
  coches y un editor con **las mismas páginas que el juego**, pero que se tocan.
  Guarda encima o guarda una copia, y en cualquier caso apunta en el historial
  cómo estaba el reglaje entero antes, así que **siempre se puede volver atrás**.
  Incluye un ingeniero al que le cuentas el síntoma ("se me va de atrás al
  frenar") y te dice qué tocar y cuánto: el qué sale de una tabla de reglas que
  puedes leer y corregir (`reglas.json`), y el cuánto lo aprende de los reglajes
  que ya tienes. **No hay ninguna IA aquí dentro**, y es a propósito.
- **Escáner de circuitos**, para medir una pista nueva desde dentro del juego.
- **Siete idiomas**: español, inglés, francés, italiano, alemán, portugués y
  polaco.

## Cómo se instala

**Lo normal: bájate el programa ya montado.** Ve a
[Releases](../../releases), descarga el `.zip`, descomprímelo **donde quieras**
y abre `MapaLMU.exe`. No hace falta instalar nada, ni siquiera Python.

**No lo pongas dentro de `Archivos de programa`**: Windows no deja escribir ahí
y el programa necesita guardar su configuración, tus vueltas y los circuitos
que escanees.

La primera vez Windows dirá *"Windows protegió tu PC"*, porque el programa no
está firmado (firmarlo cuesta dinero). Pulsa **Más información** → **Ejecutar
de todas formas**.

Y en el juego, antes de nada: ponlo en modo **borderless** y quita el mapa que
LMU trae de serie. Lo del borderless es obligatorio; en pantalla completa
exclusiva Windows no deja poner nada encima y no verías el mapa.

Si algo no va, doble clic en `COMPROBAR SI ALGO NO VA.bat`: dice de un vistazo
qué encuentra y qué no.

## Si prefieres ejecutarlo desde el código

Hace falta **Python 3.12** o superior, y nada más: el programa solo usa lo que
Python trae de serie. Descarga el repositorio y abre `MAPA.bat`.

Para generar el `.exe` y el `.zip` tú mismo: `python compilar.py`.

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
- **La marca y el modelo del coche, en vivo.** Mientras ruedas el juego solo da
  el equipo con su dorsal y un código interno del coche. Pero al *terminar* cada
  sesión sí escribe la marca y el modelo de todos, en
  `UserData/Log/Results`, con ese mismo código. El programa lee esos archivos y
  monta su tabla solo. Es la pestaña *Coches*, y no hay que teclear nada: cuando
  saquen coches nuevos, basta con correr una sesión con ellos delante.
- **La velocidad de cada coche en cada punto.** Solo publica el tiempo de la
  mejor vuelta, así que una vuelta anterior no se puede reconstruir: solo cuentan
  las vueltas dadas con el programa abierto.

---

# Track map for Le Mans Ultimate

An overlay map that shows you where every car is, with **your own car clearly
visible**, rivals coloured by class, corner numbers and names, and a mode that
measures you against the fastest car in your own class.

It is free. Use it and pass it on to anyone.

## What it does

- **Transparent overlay map**, in any corner and at any size. F9 hides or shows
  it, F10 opens the options.
- **Your car highlighted** with a ring, so it is never covered when the dots
  pile up.
- **Live time comparison** against the fastest lap **in your own class**, so a
  GT3 is not judged against an LMP2: the track is painted in the reference
  colour and your own segments are laid over it in red, yellow or green. If a
  rival in your class improves, your lap recolours itself.
- **Off-track warnings**, marking with a triangle where you last went off.
- **Stopped-car warnings** out on track, flashing on the map and sounding an
  alert. It does not warn by proximity like a spotter, but **by seconds**: it
  knows where every car is along the track and warns you while there is still
  time to do something. The sound is picked from a list, and you can drop your
  own into the `sonidos` folder.
- **Line comparator**: saves your laps with their sectors and draws them over
  the track at its real width, coloured against the rival's.
- **Car setups** *(new in 1.4)*: a library of every `.svm` on your computer,
  sorted by car and track, with car spec sheets and an editor laid out in **the
  same pages as the game**, only editable. Overwrite or save a copy — either way
  the whole setup is written to the history first, so **you can always go back**.
  It includes an engineer you tell the symptom to ("it steps out at the rear
  under braking") and it tells you what to change and by how much: the *what*
  comes from a rules table you can read and correct (`reglas.json`), and the
  *how much* is learnt from the setups you already own. **There is no AI in
  here**, and that is on purpose.
- **Track scanner**, to measure a new track from inside the game.
- **Seven languages**: Spanish, English, French, Italian, German, Portuguese and
  Polish.

## How to install it

**The normal way: grab the ready-built program.** Go to
[Releases](../../releases), download the `.zip`, extract it **wherever you
like** and open `MapaLMU.exe`. Nothing to install, not even Python.

**Do not put it inside `Program Files`**: Windows will not allow writing there,
and the program needs to save its settings, your laps and any tracks you scan.

The first time, Windows will say *"Windows protected your PC"*, because the
program is not signed (signing costs money). Press **More info** → **Run
anyway**.

And in the game, first of all: set it to **borderless** and turn off the map
LMU ships with. Borderless is mandatory; in exclusive fullscreen Windows will
not let anything sit on top and you would not see the map.

If something is wrong, double click `COMPROBAR SI ALGO NO VA.bat`: it says at a
glance what it finds and what it does not.

## If you would rather run it from source

You need **Python 3.12** or newer, and nothing else: the program only uses what
Python ships with. Download the repository and open `MAPA.bat`.

To build the `.exe` and the `.zip` yourself: `python compilar.py`.

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
- **Car make and model, live.** While you drive, the game only gives the team
  with its number and an internal code for the car. But when a session *ends* it
  does write everyone's make and model, in `UserData/Log/Results`, keyed by that
  same code. The program reads those files and builds its table on its own. That
  is the *Cars* tab, and there is nothing to type in: when new cars come out,
  just run a session with them on track.
- **Each car's speed at each point.** It only publishes the best lap time, so an
  earlier lap cannot be reconstructed: only laps driven with the program open
  count.
