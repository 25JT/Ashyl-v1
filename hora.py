from datetime import datetime

def hora_actual():
    ahora = datetime.now()
    fecha = datetime.now().strftime("%d/%m/%Y")
    dia = datetime.now().strftime("%A")
    return {
        "hora": ahora.hour,
        "minuto": ahora.minute,
        "fecha": fecha,
        "dia": dia

    }




