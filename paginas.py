# -*- coding: utf-8 -*-
"""
Las paginas de reglaje del juego, con cada linea atada a su ajuste real.

Son las mismas paginas que hay en PIT GARAGE -> CONFIGURACION DEL COCHE, en
el mismo orden y con los mismos nombres, para que quien mire aqui sepa
exactamente donde tocar alli. La diferencia con la version de antes es que
ahora cada linea sabe de que ajuste del .svm habla, asi que ya no son
valores de ejemplo: son los del reglaje que tengas abierto, y se pueden
cambiar.

QUE ES EJE_del Y EJE_tras
El archivo guarda las cuatro ruedas por separado, pero un reglaje normal
lleva las dos de un eje iguales, y en el juego se tocan juntas. Cuando una
linea dice EJE_del, se aplica a la rueda delantera izquierda y a la derecha
a la vez. Si el reglaje trae las dos ruedas distintas, el editor lo avisa y
no deja tocarlas por eje, para no aplastar un reparto puesto a proposito.
"""

# (titulo de la pagina, [(titulo del grupo, [(nombre, clave o None), ...])])
# Una clave a None es una linea que se ensena pero no se toca: o el juego no
# la deja, o es informativa.
PAGINAS = [
    ("Transmision", [
        ("MOTOR", [
            ("Energia virtual", "GENERAL/VirtualEnergySetting"),
            ("Capacidad de combustible", "GENERAL/FuelSetting"),
            ("Combustible cargado", "GENERAL/FuelCapacitySetting"),
            ("Limitador de revoluciones", "ENGINE/RevLimitSetting"),
            ("Mezcla del motor", "ENGINE/EngineMixtureSetting"),
            ("Freno motor", "ENGINE/EngineBrakingMapSetting"),
            ("Tapa del radiador de agua", "BODYAERO/WaterRadiatorSetting"),
            ("Tapa del radiador de aceite", "BODYAERO/OilRadiatorSetting"),
        ]),
        ("ELECTRONICA", [
            ("Control de traccion", "CONTROLS/TractionControlMapSetting"),
            ("Menor potencia del CT", "CONTROLS/TCPowerCutMapSetting"),
            ("Angulo de deslizamiento del CT", "CONTROLS/TCSlipAngleMapSetting"),
            ("Nivel de regeneracion", "ENGINE/RegenerationMapSetting"),
            ("Mapa del motor electrico", "ENGINE/ElectricMotorMapSetting"),
            ("Control de traccion instalado", "CONTROLS/TCSetting"),
        ]),
        ("DIFERENCIAL", [
            ("Potencia", "DRIVELINE/DiffPowerSetting"),
            ("Inercia", "DRIVELINE/DiffCoastSetting"),
            ("Precarga", "DRIVELINE/DiffPreloadSetting"),
            ("Potencia delantera", "DRIVELINE/FrontDiffPowerSetting"),
            ("Inercia delantera", "DRIVELINE/FrontDiffCoastSetting"),
            ("Precarga delantera", "DRIVELINE/FrontDiffPreloadSetting"),
            ("Bomba", "DRIVELINE/DiffPumpSetting"),
            ("Bomba delantera", "DRIVELINE/FrontDiffPumpSetting"),
            ("Reparto de par", "DRIVELINE/RearSplitSetting"),
        ]),
        ("MARCHAS", [
            ("Relacion de cambio", "DRIVELINE/RatioSetSetting"),
            ("Grupo final", "DRIVELINE/FinalDriveSetting"),
            ("Marcha 1", "DRIVELINE/Gear1Setting"),
            ("Marcha 2", "DRIVELINE/Gear2Setting"),
            ("Marcha 3", "DRIVELINE/Gear3Setting"),
            ("Marcha 4", "DRIVELINE/Gear4Setting"),
            ("Marcha 5", "DRIVELINE/Gear5Setting"),
            ("Marcha 6", "DRIVELINE/Gear6Setting"),
            ("Marcha 7", "DRIVELINE/Gear7Setting"),
        ]),
    ]),
    ("Ruedas y frenos", [
        ("RUEDAS DELANTERAS", [
            ("Compuesto", "EJE_del/CompoundSetting"),
            ("Presion de los neumaticos", "EJE_del/PressureSetting"),
            ("Caida del tren", "EJE_del/CamberSetting"),
            ("Disco de freno", "EJE_del/BrakeDiscSetting"),
            ("Pastillas de freno", "EJE_del/BrakePadSetting"),
        ]),
        ("RUEDAS TRASERAS", [
            ("Compuesto", "EJE_tras/CompoundSetting"),
            ("Presion de los neumaticos", "EJE_tras/PressureSetting"),
            ("Caida del tren", "EJE_tras/CamberSetting"),
            ("Disco de freno", "EJE_tras/BrakeDiscSetting"),
            ("Pastillas de freno", "EJE_tras/BrakePadSetting"),
        ]),
        ("FRENOS", [
            ("Distribucion de frenada", "CONTROLS/RearBrakeSetting"),
            ("Migracion de frenos", "CONTROLS/BrakeMigrationSetting"),
            ("Fuerza maxima del pedal", "CONTROLS/BrakePressureSetting"),
            ("Obturacion conducto delantero", "BODYAERO/BrakeDuctSetting"),
            ("Obturacion conducto trasero", "BODYAERO/BrakeDuctRearSetting"),
            ("Frenos antibloqueo", "CONTROLS/AntilockBrakeSystemMapSetting"),
            ("ABS instalado", "CONTROLS/ABSSetting"),
        ]),
    ]),
    ("Suspension", [
        ("SUSPENSION DELANTERA", [
            ("Indice de muelles", "EJE_del/SpringSetting"),
            ("Indice de muelles tender", "EJE_del/TenderSpringSetting"),
            ("Recorrido tender", "EJE_del/TenderTravelSetting"),
            ("Muelle central (3rd spring)", "SUSPENSION/Front3rdSpringSetting"),
            ("Tope del muelle central", "SUSPENSION/Front3rdPackerSetting"),
            ("Muelle tender central", "SUSPENSION/Front3rdTenderSpringSetting"),
            ("Recorrido tender central", "SUSPENSION/Front3rdTenderTravelSetting"),
            ("Topes", "EJE_del/PackerSetting"),
            ("Altura del chasis", "EJE_del/RideHeightSetting"),
            ("Muelle de goma", "EJE_del/SpringRubberSetting"),
        ]),
        ("SUSPENSION TRASERA", [
            ("Indice de muelles", "EJE_tras/SpringSetting"),
            ("Indice de muelles tender", "EJE_tras/TenderSpringSetting"),
            ("Recorrido tender", "EJE_tras/TenderTravelSetting"),
            ("Muelle central (3rd spring)", "SUSPENSION/Rear3rdSpringSetting"),
            ("Tope del muelle central", "SUSPENSION/Rear3rdPackerSetting"),
            ("Muelle tender central", "SUSPENSION/Rear3rdTenderSpringSetting"),
            ("Recorrido tender central", "SUSPENSION/Rear3rdTenderTravelSetting"),
            ("Topes", "EJE_tras/PackerSetting"),
            ("Altura del chasis", "EJE_tras/RideHeightSetting"),
            ("Muelle de goma", "EJE_tras/SpringRubberSetting"),
        ]),
    ]),
    ("Amortiguadores", [
        ("SUSPENSION DELANTERA", [
            ("Compresion lenta", "EJE_del/SlowBumpSetting"),
            ("Rebote lento", "EJE_del/SlowReboundSetting"),
            ("Compresion rapida", "EJE_del/FastBumpSetting"),
            ("Rebote rapido", "EJE_del/FastReboundSetting"),
        ]),
        ("SUSPENSION TRASERA", [
            ("Compresion lenta", "EJE_tras/SlowBumpSetting"),
            ("Rebote lento", "EJE_tras/SlowReboundSetting"),
            ("Compresion rapida", "EJE_tras/FastBumpSetting"),
            ("Rebote rapido", "EJE_tras/FastReboundSetting"),
        ]),
        ("MUELLE CENTRAL DELANTERO", [
            ("Compresion lenta", "SUSPENSION/Front3rdSlowBumpSetting"),
            ("Rebote lento", "SUSPENSION/Front3rdSlowReboundSetting"),
            ("Compresion rapida", "SUSPENSION/Front3rdFastBumpSetting"),
            ("Rebote rapido", "SUSPENSION/Front3rdFastReboundSetting"),
        ]),
        ("MUELLE CENTRAL TRASERO", [
            ("Compresion lenta", "SUSPENSION/Rear3rdSlowBumpSetting"),
            ("Rebote lento", "SUSPENSION/Rear3rdSlowReboundSetting"),
            ("Compresion rapida", "SUSPENSION/Rear3rdFastBumpSetting"),
            ("Rebote rapido", "SUSPENSION/Rear3rdFastReboundSetting"),
        ]),
    ]),
    ("Chasis y aerodinamica", [
        ("CHASIS DELANTERO", [
            ("Caster", "SUSPENSION/LeftCasterSetting"),
            ("Convergencia", "SUSPENSION/FrontToeInSetting"),
            ("Barra antivuelco", "SUSPENSION/FrontAntiSwaySetting"),
            ("Ancho de via", "SUSPENSION/FrontWheelTrackSetting"),
            ("Radio de giro (bloqueo)", "CONTROLS/SteerLockSetting"),
            ("Difusor delantero", "FRONTWING/FWSetting"),
        ]),
        ("CHASIS TRASERO", [
            ("Convergencia", "SUSPENSION/RearToeInSetting"),
            ("Barra antivuelco", "SUSPENSION/RearAntiSwaySetting"),
            ("Ancho de via", "SUSPENSION/RearWheelTrackSetting"),
            ("Aleron trasero", "REARWING/RWSetting"),
        ]),
        ("PESO", [
            ("Vertical", "GENERAL/CGHeightSetting"),
            ("Lateral", "GENERAL/CGRightSetting"),
            ("Distribucion del peso", "GENERAL/CGRearSetting"),
        ]),
        ("PARADAS EN BOXES", [
            ("Paradas previstas", "GENERAL/NumPitstopsSetting"),
        ]),
    ]),
]


def claves():
    """Todas las claves que salen en las paginas, sin repetir."""
    vistas = []
    for _, grupos in PAGINAS:
        for _, filas in grupos:
            for _, clave in filas:
                if clave and clave not in vistas:
                    vistas.append(clave)
    return vistas


def reparte(clave):
    """
    'EJE_del/SpringSetting' -> ['FRONTLEFT/SpringSetting',
                                'FRONTRIGHT/SpringSetting']
    Cualquier otra clave se devuelve tal cual, en una lista de uno.
    """
    if clave.startswith("EJE_del/"):
        resto = clave.split("/", 1)[1]
        return ["FRONTLEFT/" + resto, "FRONTRIGHT/" + resto]
    if clave.startswith("EJE_tras/"):
        resto = clave.split("/", 1)[1]
        return ["REARLEFT/" + resto, "REARRIGHT/" + resto]
    return [clave]
