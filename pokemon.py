import requests

def pokedex():
    ruta = "https://pokeapi.co/api/v2/pokemon?limit=100&offset=0"
    respuesta = requests.get(ruta).json()["results"]
    return {
        "pokemon": respuesta
    }
   

