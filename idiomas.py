# -*- coding: utf-8 -*-
"""
El idioma del programa.

Funciona igual que la carpeta de circuitos: cada idioma es UN archivo dentro
de la carpeta "idiomas". Para anadir un idioma nuevo se copia en.json, se
traduce y se deja ahi con el nombre del idioma; el programa lo ve solo. Y si
alguien traduce mejor una frase, cambia esa linea y ya esta, sin tocar codigo.

El espanol va escrito aqui dentro (BASE) porque es el idioma original: asi el
programa nunca se queda mudo aunque falte la carpeta entera.

Si a un idioma le falta una frase, se cae al ingles, y si tampoco esta, al
espanol. Nunca sale un hueco en blanco.

QUE ESTA TRADUCIDO: todo lo que se lee en pantalla. Las pestanas, los
botones, las ayudas largas de la (i), los rotulos que salen encima del mapa y
las indicaciones de las ventanas negras de escaneo. Son unos 450 textos por
idioma.

Lo unico que sigue en castellano son las herramientas de trabajo que no se
abren desde el programa (monitor_amarilla.py, diagnostico.py y los
construir_*.py), que se lanzan a mano y no las ve un usuario normal.
"""
import json
import os

import rutas

CARPETA = rutas.datos("idiomas")
MEMORIA = rutas.datos("idioma.txt")

# Los idiomas en los que se juega a LMU: son los que trae el propio juego
# traducidos, asi que es donde esta la gente.
IDIOMAS = [
    ("es", "Español"),
    ("en", "English"),
    ("fr", "Français"),
    ("it", "Italiano"),
    ("de", "Deutsch"),
    ("pt", "Português"),
    ("pl", "Polski"),
]

# ------------------------------------------------------------------ textos
# Clave -> texto en espanol. Es la lista de todo lo que se puede traducir.
BASE = {
    # pestanas
    "tab.ver": "Que se ve",
    "tab.aspecto": "Tamanos y colores",
    "tab.tiempos": "Comparar tiempos",
    "tab.trazadas": "Comparar trazadas",
    "tab.escaneo": "Escanear pistas",
    "tab.coches": "Coches",
    "tab.reglajes": "Reglajes",
    "tab.acerca": "Acerca de",
    # avisos en pantalla
    'avi.sonar': 'Que suene un pitido al avisar',
    'avi.volumen': 'Volumen del pitido',
    'avi.suena_por': 'El pitido suena por el dispositivo predeterminado de Windows',
    'avi.activado': 'Avisar de coches parados por delante',
    'avi.antelacion': 'Segundos antes',
    'avi.antelacion_nota': 'Se mide en segundos y no en metros porque trescientos metros no son lo mismo en una recta que entrando a una horquilla. Y se cuenta por el trazado, no en linea recta: asi no avisa de un coche que esta cerca pero al otro lado de una curva.',
    'avi.colocar': 'Con esta ventana abierta veras el cartel en gris encima del juego: arrastralo con el raton al sitio donde quieras que salga.',
    'avi.color': 'Color del aviso',
    'avi.intro': 'Un cartel grande encima del juego cuando hay un coche parado por delante. No es un spotter de los que avisan cuando ya lo tienes al lado: como el programa sabe por donde va cada uno en el trazado, avisa mientras todavia se puede hacer algo.',
    'avi.muestra': 'COCHE PARADO  (muestra)',
    'avi.probar': 'Probar',
    'avi.sin_sonido': '-- sin sonido --',
    'avi.sonido': 'Que suene',
    'avi.sonido_nota': 'Es un pitido y no una voz a proposito: una voz hay que fabricarla y eso tarda medio segundo largo, que es justo el tiempo que el aviso queria ganarte. Para poner el tuyo, deja un .wav en la carpeta sonidos y aparecera en la lista.',
    'avi.tamano': 'Tamano de la letra',
    'avi.texto': 'COCHE PARADO',
    'avi.texto_etiqueta': 'Que ponga',
    'avi.texto_nota': 'Dejalo vacio para el texto de siempre. Si escribes %d en algun sitio, ahi saldran los segundos que faltan: por ejemplo  COCHE PARADO A %d s',
    'avi.tit_como': 'Como se ve',
    'avi.tit_cuando': 'Con cuanta antelacion',
    'avi.tit_sonido': 'Sonido',
    'ayuda.avisos': 'EL AVISO DE COCHE PARADO\n\nSale un cartel grande encima del juego cuando hay alguien parado en pista por delante de ti, con la antelacion que tu decidas.\n\nNO ES UN SPOTTER\nUn spotter avisa por cercania: te dice que tienes a alguien al lado cuando ya lo tienes al lado. Esto es distinto. El programa sabe por donde va cada coche EN EL TRAZADO, asi que puede avisarte cuando el coche parado todavia esta a diez segundos, que es cuando aun se puede levantar el pie o cambiar de linea.\n\nPOR QUE EN SEGUNDOS\nPorque trescientos metros no son lo mismo en la recta de Le Mans que entrando a una horquilla: alli son tres segundos y aqui quince. Al que conduce le importan los segundos.\n\nY se cuenta por el trazado, no en linea recta. Un coche al otro lado de una horquilla puede estar a treinta metros a vuelo de pajaro y a medio kilometro de pista: ese no es un peligro y avisar de el seria ruido.\n\nNO SE QUEDA PILLADO\nSe recalcula veinte veces por segundo. En cuanto el coche arranca, el aviso se va solo. Y para que no parpadee cuando esta justo en el limite, una vez encendido aguanta un momento en pantalla y no se apaga hasta que el peligro se aleja de verdad.\n\nCUANDO NO AVISA\nSi vas por debajo de unos 40 km/h no avisa: parado en boxes o rodando muy despacio, cualquier cosa queda a muchisimos segundos y el aviso no diria nada util.',
    'tab.avisos': 'Avisos',
    # pie de la ventana
    "pie.teclas": "F9 oculta o muestra el mapa   /   F10 cierra estas opciones\n"
                  "Con esta ventana abierta puedes arrastrar el mapa con el raton.",
    # acerca de
    "acerca.titulo": "Mapa de pista para Le Mans Ultimate",
    "acerca.descripcion": "Programa gratuito para la comunidad.\n"
                          "Se puede copiar, pasar a quien quieras y usar sin pagar nada.",
    "acerca.idioma": "Idioma",
    "acerca.reiniciar": "El idioma cambia del todo al volver a abrir el programa.",
    "acerca.donar.titulo": "Invitame a un cafe",
    "acerca.donar.texto": "Esto lo hago en mis ratos libres y seguira siendo gratis.\n"
                          "Si te ha servido y te apetece echar una mano, se agradece;\n"
                          "y si no, disfrutalo igual.",
    "acerca.donar.kofi": "Donar por Ko-fi",
    "acerca.donar.paypal": "Donar por PayPal",
    "acerca.proyecto": "Pagina del programa",
    "acerca.patrocinio": "Patrocinado por ciclotracker.com",
    "acerca.patrocinio.texto": "Si ademas de simracing le das al pedal de verdad,\n"
                               "ciclotracker.com lleva la cuenta de tus rutas.",
    "acerca.patrocinio.web": "Ir a ciclotracker.com",
    "acerca.patrocinio.android": "Bajarla para Android",
    "acerca.cerrar": "CERRAR EL MAPA",
    # reglajes
    "reg.aviso": "Lo de aqui abajo es solo una muestra: todavia no funciona.",
    "reg.sello": "PRÓXIMAMENTE",
    "reg.sub.caracteristicas": "  Caracteristicas  ",
    "reg.sub.reglaje": "  Reglaje  ",
    "reg.ejemplo": "valores de ejemplo",
    "reg.comportamiento": "COMO SE COMPORTA",
    "reg.motor": "Motor",
    "reg.cilindrada": "Cilindrada",
    "reg.potencia": "Potencia",
    "reg.posicion": "Posicion del motor",
    "reg.traccion": "Traccion",
    # calculadora de FOV
    "fov.abrir": "Calculadora de FOV...",
    "fov.alto": "Alto de la pantalla",
    "fov.alto_pista": "solo la imagen, sin marcos (cm)",
    "fov.ancho": "Ancho de la pantalla",
    "fov.ancho_pista": "solo la imagen, sin marcos (cm)",
    "fov.aspecto": "Relacion de aspecto",
    "fov.aviso_pulgadas": "Es aproximado: la diagonal que anuncian los fabricantes a veces incluye un poco de marco. Si puedes, mide con una cinta la parte que se ilumina.",
    "fov.como_usarlo": "Como usarlo",
    "fov.consejos": "CONSEJOS\nMide solo la imagen, de un borde a otro de la zona que se enciende. Los marcos negros no cuentan.\nLa distancia se mide desde tus ojos, sentado en tu postura de conducir, hasta el centro de la pantalla.\nEn Le Mans Ultimate el ajuste es el FOV VERTICAL: usa el numero grande.\nSe cambia dentro del coche, en las opciones de camara o de asiento.\nUn FOV correcto se siente raro los primeros dias: parece que vas mas rapido y que ves menos. Eso es justo lo que te estabas perdiendo. Dale tres o cuatro tandas antes de juzgarlo.",
    "fov.copiado": "Copiado: %s",
    "fov.copiar": "Copiar el numero",
    "fov.desde_pulgadas": "Si no sabes el ancho y el alto, sacalos de las pulgadas",
    "fov.diagonal": "FOV diagonal",
    "fov.dist": "Distancia a tus ojos",
    "fov.dist_pista": "de los ojos al centro de la pantalla (cm)",
    "fov.error": "Revisa los numeros: los tres tienen que ser mayores que cero.",
    "fov.f1610": "16:10",
    "fov.f169": "16:9 (monitor o television normal)",
    "fov.f219": "21:9 (panoramico)",
    "fov.f329": "32:9 (super panoramico)",
    "fov.f43": "4:3 (antiguo)",
    "fov.f4318": "43:18 (algunos 21:9)",
    "fov.formato": "Formato de imagen",
    "fov.formula": "LA CUENTA\nFOV vertical = 2 x arcotangente( alto / (2 x distancia) )\nFOV horizontal = 2 x arcotangente( ancho / (2 x distancia) )",
    "fov.horizontal": "FOV horizontal",
    "fov.medidas": "Tus medidas",
    "fov.pulgadas": "Diagonal (pulgadas)",
    "fov.rellenar": "Rellenar arriba",
    "fov.resultado": "Resultado",
    "fov.sub": "Mide tu pantalla y la distancia a la que tienes los ojos. El resultado se calcula solo.",
    "fov.titulo": "Calculadora de campo de vision (FOV)",
    "fov.tres_pantallas": "SI TIENES TRES PANTALLAS\nEl FOV vertical no cambia: es el que sale aqui usando el alto de UNA pantalla y tu distancia.\nLo que cambia es el angulo horizontal, y de eso se encarga el juego cuando activas el modo de tres pantallas y le dices el angulo de las laterales.",
    "fov.vertical": "FOV VERTICAL\nes el que pide Le Mans Ultimate",
    # manual
    "man.titulo": "Manual de reglajes y conduccion",
    "man.abrir": "Manual de reglajes y conduccion...",
    "man.buscar": "Buscar:",
    "man.limpiar": "Ver todo",
    "man.nada": "No hay nada con esas palabras.",
    "man.elige": "Elige un apartado en la lista de la izquierda.",
    "man.tomo.reglajes": "Reglajes",
    "man.tomo.conduccion": "Conduccion",
    "man.que_es": "QUE ES",
    "man.subir": "SI SUBES EL NUMERO",
    "man.bajar": "SI LO BAJAS",
    "man.donde": "DONDE SE NOTA",
    "man.combina": "SE TOCA JUNTO CON",
    "man.ojo": "OJO",
    "man.sintoma": "QUE NOTAS",
    "man.pasos": "QUE SE TOCA, POR ORDEN",
    "man.en_el_juego": "En el juego: %s",
    "man.claves": "En el archivo del reglaje: %s",
    "man.pie": "El manual es un archivo de texto (manual_reglajes.json): se puede corregir y ampliar sin tocar el programa.",
    "man.desde_editor": "Que hace este ajuste",
    "ed.pista_manual": "Pulsa en el nombre de un ajuste para ver que hace",
    # biblioteca de reglajes
    "reg.biblioteca": "Ordenar mis reglajes...",
    "bib.titulo": "Biblioteca de reglajes",
    "bib.importar": "Importar reglajes descargados...",
    "bib.tipos": "Reglajes y comprimidos",
    "bib.circuito": "Circuito:",
    "bib.todos": "Todos",
    "bib.solo_problemas": "Solo los que tienen algun problema",
    "bib.duplicados": "Buscar repetidos",
    "bib.detalle": "El reglaje elegido",
    "bib.nada": "Elige un reglaje de la lista para ver lo que sabemos de el.",
    "bib.varios": "%d reglajes elegidos. Los cambios de abajo son para uno solo.",
    "bib.sesion": "Para:",
    "bib.estilo": "Estilo:",
    "bib.lluvia": "De lluvia",
    "bib.por_el_nombre": "(la lluvia sale del nombre, no del neumatico)",
    "bib.cuadrar": "Cuadrar la gasolina",
    "bib.renombrar": "Renombrar los elegidos",
    "bib.cerrar": "Cerrar",
    "bib.elige": "Elige antes algun reglaje de la lista.",
    "bib.col.actual": "Como se llama ahora",
    "bib.col.nuevo": "Como se va a llamar",
    "bib.col.coche": "Coche",
    "bib.col.cat": "Clase",
    "bib.col.tipo": "Para que es",
    "bib.col.gasolina": "Gasolina",
    "bib.col.fuente": "De donde",
    "bib.col.archivo": "Archivo",
    "bib.col.circuito": "A que circuito va",
    "bib.sin_juego": "No encuentro el juego, asi que no se donde estan los reglajes.",
    "bib.sin_energia": "no gasta energia",
    "bib.gasolina_ok": "llega (%.1f vueltas)",
    "bib.faltan": "FALTAN %.1f vueltas",
    "bib.sobran": "sobran %.1f vueltas",
    "bib.resumen": "%d reglajes.   Con la gasolina corta: %d",
    "bib.dry": "Seco",
    "bib.wet": "Lluvia",
    "bib.confirmar_renombrar": "Se van a renombrar %d reglajes.\n\n"
                               "Ninguno se machaca: si el nombre ya esta cogido, "
                               "se le pone un numero detras.\n\n¿Sigo?",
    "bib.renombrados": "Renombrados: %d",
    "bib.nada_que_cuadrar": "A estos reglajes ya les llega la gasolina. "
                            "No hay nada que arreglar.",
    "bib.confirmar_cuadrar": "A %d reglajes no les llega la gasolina hasta donde "
                             "dice la barra de energia.\n\nSe les va a cargar la "
                             "que necesitan. Solo se toca esa linea, y antes se "
                             "guarda una copia del original en la carpeta "
                             "copias_reglajes.\n\n¿Los arreglo?",
    "bib.cuadrados": "Arreglados: %d",
    "bib.eliminar": "Eliminar los elegidos",
    "bib.ver_todos": "Ver todos otra vez",
    "bib.col.parecido": "En que se parecen",
    "bib.el_original": "el que yo me quedaria",
    "bib.no_sobra": "aqui no sobra ninguno",
    "bib.copia_exacta": "IGUAL que el de arriba",
    "bib.copia_casi": "mismo reglaje, distinta gasolina",
    "bib.resumen_repetidos": "%d grupos de repetidos.   Copias exactas "
                             "elegidas: %d",
    "bib.ya_no_hay_repetidos": "Ya no queda ningun repetido. Vuelvo a la lista "
                               "de siempre.",
    "bib.repetidos_ayuda": "La lista ensena ahora solo los repetidos, cada "
                           "copia justo debajo del reglaje del que es copia. "
                           "Cada grupo va sobre un fondo para que se vean "
                           "aparte.\n\nEn ROJO, las copias exactas: mismo "
                           "reglaje y misma gasolina. Esas son las que sobran "
                           "y ya te las he dejado elegidas.\n\nEn AMBAR, los "
                           "que llevan el coche igual pero cambian la gasolina "
                           "o las paradas: suele ser el de clasificacion y el "
                           "de carrera, y quieres los dos.\n\nPulsa Ver "
                           "todos otra vez para volver a la lista entera.",
    "bib.repetidos_ayuda_sin": "La lista ensena ahora solo los repetidos, cada "
                               "uno justo debajo del reglaje al que se "
                               "parece.\n\nNinguno es copia exacta de otro: "
                               "el coche va igual pero cambian la gasolina o "
                               "las paradas, que suele ser el de clasificacion "
                               "y el de carrera, y quieres los dos. Asi que no "
                               "te he elegido ninguno.\n\nPulsa Ver todos "
                               "otra vez para volver a la lista entera.",
    "bib.confirmar_eliminar": "Se van a quitar %d reglajes:\n\n%s\n\n"
                              "No se borran del todo: se guardan en la carpeta "
                              "copias_reglajes/_borrados del programa, por si "
                              "te arrepientes.\n\n¿Los quito?",
    "bib.eliminar_no_sobran": "OJO: %d de los que has elegido no dejan "
                              "ninguna copia detras. Si los quitas, ese "
                              "reglaje desaparece. Los que salen en AMBAR son "
                              "el mismo reglaje con distinta gasolina, que "
                              "suele ser el de clasificacion y el de carrera, "
                              "y seguramente quieres quedarte con los "
                              "dos.\n\n",
    "bib.eliminar_en_juego": "OJO: %d de ellos los tienes asignados en el "
                             "juego.\n\n",
    "bib.eliminados": "Eliminados: %d",
    "bib.no_pude_eliminar": "No he podido quitar %d. Puede que el juego los "
                            "tenga abiertos: cierralo y prueba otra vez.",
    "bib.y_mas": "... y %d mas.",

    "bib.sin_duplicados": "No hay dos reglajes iguales con nombres distintos.",
    "bib.hay_duplicados": "Hay %d reglajes repetidos con nombres distintos:",
    "bib.zip_vacio": "En ese archivo no hay ningun reglaje.",
    "bib.destino": "A que circuito va cada uno",
    "bib.destino_ayuda": "Un reglaje no lleva escrito dentro de que circuito es: "
                         "lo dice la carpeta donde se guarda.\n"
                         "Los que salen en rojo no los he sabido adivinar. Elige "
                         "esas filas, escoge el circuito abajo y pulsa Poner.",
    "bib.poner_en": "Circuito:",
    "bib.asignar": "Poner en las filas elegidas",
    "bib.copiar_aqui": "Importar",
    "bib.elige_circuito": "-- elige circuito --",
    "bib.falta_circuito": "Todavia no hay ningun reglaje con circuito asignado.",
    "bib.importados": "Importados: %d\nSin circuito, se han quedado fuera: %d",
    # que llevas puesto en el juego
    'bib.varios_asignados': 'Tienes %d reglajes asignados en el juego, uno por circuito y coche. Salen en gris verdoso. Con el juego abierto te digo cual es el de donde estas. Pulsa el interrogante.',
    'bib.asignado_ayuda': 'DE DONDE SALE ESTE DATO\n\nEl juego no apunta en ningun sitio el reglaje que CARGAS en el garaje. Se ha comprobado uno por uno: cargarlo no deja rastro, salir a pista tampoco, cambiar de sesion tampoco.\n\nLo unico que el juego escribe, y al instante, es el reglaje que ASIGNAS: en la pantalla de configuraciones, el boton ASIGNAR que hay al lado de CARGAR.\n\nPor eso aqui no se adivina nada. O lo has asignado y sale el nombre exacto, o no sale y se dice.\n\nOJO, QUE ASIGNAR HACE OTRA COSA\n\nAdemas de dejarlo escrito, asignar un reglaje hace que el juego te lo cargue solo la proxima vez que entres con ese coche a ese circuito. A unos les viene bien y a otros les estorba, asi que decidelo tu.\n\nEste programa solo LEE ese archivo. No asigna nada por su cuenta ni lo cambia nunca.\n\nLos reglajes que el juego tiene asignados salen en verde y con un asterisco delante.',
    'bib.en_juego': 'En el juego tienes asignado:  %s   (%s)',
    'bib.sin_asignar': 'No has asignado ningun reglaje en el juego, asi que no puedo saber cual llevas. Pulsa el interrogante.',
    # editor, historial y fichas de coche
    'bib.editar': 'Editar este reglaje',
    'ed.cancelar': 'Cancelar',
    'ed.como_guardar': '¿Como lo guardo?\n\nUNA COPIA deja el reglaje de antes como estaba y crea uno nuevo al lado. Va bien cuando pruebas algo y no te fias.\n\nENCIMA cambia el reglaje que ya tenias, sin crear otro. Va bien cuando estas afinando uno tuyo y no quieres la lista del juego llena de archivos.\n\nEn los dos casos queda apuntado en el historial como estaba antes, asi que siempre se puede volver.',
    'ed.copia_sera': 'La copia se llamaria:  %s',
    'ed.deshacer': 'Deshacer los cambios',
    'ed.deshecho': 'Cambios deshechos.',
    'ed.desparejado': 'las dos ruedas van distintas: se toca en el juego',
    'ed.encima': 'Guardar encima',
    'ed.guardado': 'Guardado en %s',
    'ed.guardar': 'Guardar',
    'ed.hacer_copia': 'Guardar una copia',
    'ed.historial': 'Historial de cambios',
    'ed.no_tiene': 'Este coche no tiene nada de esto.',
    'ed.restaurado': 'Reglaje restaurado.',
    'ed.sin_guardar': '%d cambios sin guardar',
    'ed.titulo': 'Editar el reglaje',
    'ed.vacio': 'Elige arriba el circuito y el reglaje que quieras tocar.',
    'fic.ayuda': 'Rellena lo que sepas. Lo que dejes en blanco simplemente no sale.',
    'fic.cilindrada': 'Cilindrada',
    'fic.confirmar_quitar': 'Se va a borrar lo que escribiste de este coche.\n\nSi el programa traia una ficha suya, vuelve a salir esa.\n\n¿Sigo?',
    'fic.corregir': 'Corregir esta ficha',
    'fic.escribir': 'Escribir la ficha de este coche',
    'fic.falta_motor': 'Pon al menos el motor.',
    'fic.guardar': 'Guardar la ficha',
    'fic.motor': 'Motor',
    'fic.no_hay': 'De este coche todavia no hay ficha escrita.\n\nLos datos de un coche (que motor lleva, cuanto cubica, cuanta potencia da) no estan en ningun archivo del juego: hay que escribirlos a mano. El programa trae escritos los coches que habia cuando se hizo, y el juego va sacando mas.\n\nPuedes escribirla tu con el boton de abajo. Se guarda en un archivo aparte, asi que no se pierde al actualizar el programa, y se lo puedes pasar a quien quieras.',
    'fic.no_se_pudo': 'No he podido guardar la ficha.',
    'fic.nota': 'Lo que escribas se guarda en fichas_coches.json y se puede pasar a quien quieras.',
    'fic.posicion': 'Donde va el motor',
    'fic.potencia': 'Potencia',
    'fic.quitar': 'Quitar lo que escribi',
    'fic.resumen': 'Como se comporta',
    'fic.resumen_ayuda': 'Dos o tres lineas: en que es bueno, en que hay que tenerle respeto.',
    'fic.titulo': 'Ficha del coche',
    'fic.traccion': 'Que ruedas mueve',
    'his.ayuda': 'Todo lo que se le ha tocado a este reglaje, lo mas nuevo arriba, y en que archivo acabo cada cambio.\nElige una linea y pulsa Restaurar para dejar el reglaje como estaba JUSTO ANTES de ese cambio.',
    'his.col.archivo': 'En que archivo',
    'his.col.cuando': 'Cuando',
    'his.col.modo': 'Como se guardo',
    'his.col.que': 'Que se toco',
    'his.confirmar': 'El reglaje va a quedar como estaba justo antes del cambio de %s.\n\nEsto tambien se apunta, asi que si te arrepientes puedes volver a donde estabas.\n\n¿Lo hago?',
    'his.copia': 'copia nueva',
    'his.elige': 'Elige la linea a la que quieras volver.',
    'his.encima': 'encima',
    'his.restaurar': 'Restaurar a como estaba',
    'his.titulo': 'Historial de cambios',
    'his.vacio': 'Todavia no se le ha tocado nada a este reglaje.',
    'his.vuelta': 'vuelta atras',
    # comparar, ingeniero y calibracion
    'ing.parecido': "OJO: no tengo nada escrito para ese 'cuando' en concreto, asi que te doy la respuesta general para ese sintoma. Suele valer, pero fiate un poco menos.",
    'ing.baja': 'baja %d puntos  (%d -> %d)',
    'ing.no_se_puede': 'Se de que va el problema, pero en este coche el juego no deja tocar lo que haria falta, o ya esta en el tope. Prueba con otro sintoma o compara este reglaje con otro del mismo coche a ver en que se diferencian.',
    'ing.sube': 'sube %d puntos  (%d -> %d)',
    'bib.calibrar': 'Aprender de mis reglajes',
    'bib.comparar': 'Comparar los dos elegidos',
    'bib.confianza': '(seguridad del programa: %d%%)',
    'bib.ingeniero': 'El coche hace algo raro...',
    'cal.hecho': 'Mirados %d reglajes.\n\nAprendido de cuanto en cuanto se mueven %d ajustes distintos. A partir de ahora el ingeniero propondra pasos que tienen sentido en tus coches.\n\nSe guardan numeros, no reglajes: ese archivo se puede repartir sin problema.',
    'cmp.col.otro': 'El segundo',
    'cmp.col.que': 'Que',
    'cmp.col.uno': 'El primero',
    'cmp.elige_dos': 'Para comparar hacen falta dos. Elige dos reglajes de la lista manteniendo pulsada la tecla Control.',
    'cmp.iguales': 'Son exactamente iguales.',
    'cmp.mejor_tiempo': 'MEJOR TIEMPO  %s  %s',
    'cmp.referencia': 'Referencia  %s  %s',
    'cmp.registrando': 'Registrando vueltas...',
    'cmp.resumen': '%d cosas cambian. En negrita, lo que de verdad cambia como va el coche.',
    'cmp.titulo': 'En que se diferencian',
    'ed.desconectado': 'DESCONECTADO',
    'ed.desconecta_aviso': 'OJO: en este coche ese es el ultimo escalon y no significa "mas blando": la pieza se queda DESCONECTADA del todo. El coche cambia bastante, asi que pruebalo sabiendolo.',
    'ing.aplicar': 'Probar este cambio',
    'ing.col.ahora': 'Como esta ahora',
    'ing.col.ajuste': 'Que tocar',
    'ing.col.nuevo': 'Como quedaria',
    'ing.col.orden': 'Orden',
    'ing.cuando': 'Cuando',
    'ing.donde': 'Donde pasa',
    'ing.elige_cambio': 'Elige de la lista el cambio que quieres probar.',
    'ing.empieza_por': 'Empieza por aqui: %s',
    'ing.es_el_primero': 'POR AQUI SE EMPIEZA. De todo lo que se puede tocar en este coche para lo que has contado, esto es lo que mas lo arregla y lo que menos estropea de paso. Los de debajo son el recambio, por si este no cuaja o ya lo probaste.',
    'ing.elige_uno': 'Elige un reglaje de la lista, el que estes usando en pista.',
    'ing.guardado': 'Guardado como %s',
    'ing.guardado_largo': 'Hecho. El reglaje nuevo se llama:\n\n%s\n\nEl de antes sigue donde estaba, sin tocar.\n\nCargalo en el juego, da unas vueltas y fijate solo en una cosa: %s.\nSi no mejora, vuelve al de antes y probamos otra cosa.',
    'ing.no_se_pudo': 'No he podido guardar el reglaje nuevo.',
    'ing.pasa_a': 'pasa al punto %d',
    'ing.pregunta': 'Cuentame que hace el coche',
    'ing.que': 'Que hace',
    'ing.sin_regla': "Para esa combinacion no hay ninguna regla escrita todavia. Prueba a poner el 'cuando' en Siempre: las respuestas generales suelen cubrirla.",
    'ing.titulo': 'Ingeniero de pista',
    'ing.uno_cada_vez': 'Cambia UNA cosa, da unas vueltas y vuelve. Si tocas cinco a la vez no sabras cual funciono.',
    'ing.y_si_no': '¿Y si no es el reglaje?',
    'ing.y_si_no_titulo': '¿Seguro que es el reglaje?',
    'ing.y_si_no_texto': (
        'Esta pantalla siempre te va a dar una respuesta, y ahi esta su trampa: parece que '
        'cualquier cosa que haga el coche se arregle tocando el reglaje. Muchas veces no.\n\n'
        'La cuenta que hacen los ingenieros de verdad es esta: un buen reglaje vale DECIMAS por '
        'vuelta. La conduccion vale SEGUNDOS. Asi que si llevas tiempo atascado en el mismo '
        'tiempo, lo mas probable es que esos segundos esten en como das la vuelta y no en la '
        'barra estabilizadora.\n\n'
        'Y esto no va de saber conducir o no saber. Le pasa a todo el mundo, y le pasa sobre todo '
        'al estrenar coche: cada uno frena en un sitio, entra de una manera y aguanta cosas '
        'distintas. Un reglaje que le va de maravilla a otro piloto te puede ir fatal a ti solo '
        'porque el entra a la curva de otra forma.\n\n\n'
        'LA PRUEBA PARA SALIR DE DUDAS\n\n'
        'Da cinco vueltas seguidas y mira los tiempos.\n\n'
        'Si se llevan mucho entre ellas, medio segundo o mas, el coche todavia no es el problema. '
        'Lo que falta es repetir: misma frenada, mismo punto de giro, mismo gas. Cuando las '
        'vueltas empiecen a parecerse, el reglaje se notara. Antes no, porque cada vuelta le '
        'estas pidiendo al coche una cosa distinta y no hay reglaje que valga para todas.\n\n'
        'Si salen muy parecidas y aun asi te falta ritmo, entonces si es el momento. El coche '
        'esta haciendo siempre lo mismo, ya puedes decir con seguridad que hace, y esta pantalla '
        'te va a servir de verdad.\n\n\n'
        'LA OTRA SENAL\n\n'
        'Si el coche hace una cosa distinta cada vuelta en la misma curva, eso no lo arregla '
        'ningun reglaje.\n\n'
        'Si hace siempre lo mismo, en el mismo sitio y en el mismo momento, entonces si es del '
        'coche. Y para eso esta esto.\n\n\n'
        'Y una ultima: estrenar coche es volver a empezar. Un GT3 y un Hypercar no se conducen '
        'igual ni de lejos, y las primeras horas con uno nuevo lo raro seria ir rapido. Dale un '
        'tiempo antes de darle la culpa al reglaje.'),
}

_actual = None
_textos = {}

def _leer(codigo):
    try:
        with open(os.path.join(CARPETA, "%s.json" % codigo), encoding="utf-8-sig") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}

def actual():
    """El idioma elegido. Por defecto, espanol."""
    global _actual
    if _actual is None:
        try:
            with open(MEMORIA, encoding="utf-8-sig") as f:
                codigo = f.read().strip().lower()
        except OSError:
            codigo = ""
        _actual = codigo if codigo in dict(disponibles()) else "es"
        _cargar()
    return _actual

def _cargar():
    """
    Monta el idioma elegido por capas, de abajo arriba.

    Abajo del todo el espanol, que es el original y esta completo; encima el
    ingles, que tambien lo esta; y encima el idioma elegido. Asi, a una
    traduccion a medias le salen las frases que le faltan en ingles, y si el
    ingles tampoco las tiene, en espanol. Nunca queda un hueco en blanco.
    """
    global _textos
    _textos = dict(_leer("es"))
    if _actual != "es":
        _textos.update(_leer("en"))
        if _actual != "en":
            _textos.update(_leer(_actual))

def elegir(codigo):
    """Guarda el idioma. Lo que ya esta dibujado no cambia hasta reabrir."""
    global _actual
    if codigo not in dict(disponibles()):
        return False
    try:
        with open(MEMORIA, "w", encoding="utf-8") as f:
            f.write(codigo)
    except OSError:
        return False
    _actual = codigo
    _cargar()
    return True

def nombre(codigo):
    return dict(IDIOMAS).get(codigo, codigo)

def disponibles():
    """
    [(codigo, nombre), ...] con los idiomas que hay.

    A los que trae el programa se les suma cualquier archivo suelto que
    alguien haya dejado en la carpeta: asi un idioma nuevo aparece en la lista
    sin tocar nada, igual que pasa con los circuitos.
    """
    lista = list(IDIOMAS)
    conocidos = dict(IDIOMAS)
    try:
        for archivo in sorted(os.listdir(CARPETA)):
            codigo = os.path.splitext(archivo)[0].lower()
            if archivo.lower().endswith(".json") and codigo not in conocidos:
                lista.append((codigo, codigo.upper()))
                conocidos[codigo] = codigo.upper()
    except OSError:
        pass
    return lista

def t(clave):
    """El texto en el idioma elegido, con el ingles y el espanol por debajo."""
    actual()
    texto = _textos.get(clave)
    if texto:
        return texto
    return BASE.get(clave, clave)

def textos_es():
    """
    Todo el espanol: lo que hay en los archivos mas lo que trae el codigo.

    Es la lista completa de lo traducible, y de aqui salen las plantillas.
    """
    completo = dict(BASE)
    completo.update(_leer("es"))
    return completo

def guardar(codigo, textos):
    """Escribe un archivo de idioma. Solo lo usan las herramientas."""
    os.makedirs(CARPETA, exist_ok=True)
    with open(os.path.join(CARPETA, "%s.json" % codigo), "w", encoding="utf-8") as f:
        json.dump(textos, f, ensure_ascii=False, indent=2, sort_keys=True)
    return len(textos)

def que_falta(codigo):
    """Las frases que ese idioma todavia no tiene traducidas."""
    return sorted(set(textos_es()) - set(_leer(codigo)))
