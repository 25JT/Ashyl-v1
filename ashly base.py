import requests
from dotenv import load_dotenv
load_dotenv()

SERVER_URL = "http://localhost:1234/v1"
mensajes = [
    {"role": "system", "content": "Eres Ashly, una asistente virtual amigable y servicial. hablas en español"}
]

def get_active_model():
    """Obtiene el primer modelo disponible en LM Studio."""
    try:
        response = requests.get(f"{SERVER_URL}/models", timeout=5)
        if response.status_code == 200:
            models_data = response.json().get("data", [])
            if models_data:
                return models_data[0]["id"]
            else:
                print("No hay modelos disponibles")
                return None
        else:
            print("Error al obtener los modelos 1")
            return None
    except Exception as e:
        print("Error al obtener los modelos 2", e)
        return None

def generate_response(prompt):
    """Genera una respuesta usando el modelo activo."""
    model = get_active_model()
    if not model:
        return "No se pudo obtener el modelo activo."
    
    try:
        response = requests.post(
            f"{SERVER_URL}/chat/completions",
            json={
                "model": model,
                "messages":  prompt,
                "temperature": 0.7,
                "max_tokens": 150
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            else:
                return "La respuesta del modelo está vacía."
        else:
            return f"Error en la generación: {response.status_code}"
    except Exception as e:
        return f"Error al generar respuesta: {e}"

# Ejemplo de uso
while True:
    if __name__ == "__main__":

        userEnvio = input("Usuario:").strip()
        if not userEnvio:
            continue
        elif userEnvio.lower() in ["salir", "adios", "bye", "chao"]:
            break
        else:
            mensajes.append({"role": "user", "content": userEnvio})
            resAshly = generate_response(mensajes)
            print("Ashly: ", resAshly)
            mensajes.append({"role": "assistant", "content": resAshly})


