import random

def obtener_emocion():
    lista_emociones = [
        "feliz",
        "triste",
        "enojada",
        "sorprendida",
        "asustada",
        "asqueada",
        "normal"
    ]
    return {"emocion": random.choice(lista_emociones)}
    


