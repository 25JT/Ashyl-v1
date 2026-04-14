import requests
import json

SERVER_URL = "http://localhost:1234/v1"

# Configuración inicial de la conversación
history = [
    {"role": "system", "content": "Tu nombre es Ashly habla como mujer y eres un asistente inteligente. Siempre respondes en español y das respuestas correctas, útiles y bien razonadas. si no savez algo no lo inventes simplemente di que no lo sabes."},
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
                return None
        else:
            return None
    except Exception:
        return None

def conexion_ia(mensaje, callback_chunk):
    """
    Envía el mensaje a la IA con streaming.
    Llama a callback_chunk(texto_parcial) por cada fragmento recibido.
    """
    global history
    try:
        model = get_active_model()
        if not model:
            callback_chunk("❌ No hay modelo disponible en LM Studio.")
            return

        # Añadimos el mensaje del usuario al historial
        history.append({"role": "user", "content": mensaje})

        response = requests.post(
            f"{SERVER_URL}/chat/completions",
            json={
                "model": model,
                "messages": history,
                "temperature": 0.7,
                "stream": True # Streaming activo
            },
            stream=True,
            timeout=60
        )

        if response.status_code == 200:
            full_response_content = ""
            
            for line in response.iter_lines():
                if not line:
                    continue
                
                line_str = line.decode("utf-8")
                if line_str.startswith("data: "):
                    data_content = line_str[6:].strip()
                    
                    if data_content == "[DONE]":
                        break
                    
                    try:
                        chunk_json = json.loads(data_content)
                        delta = chunk_json["choices"][0].get("delta", {})
                        if "content" in delta:
                            content = delta["content"]
                            full_response_content += content
                            # Enviamos el pedacito a la interfaz
                            callback_chunk(content)
                    except Exception:
                        continue
            
            # Al terminar, guardamos la respuesta completa en el historial
            if full_response_content:
                history.append({"role": "assistant", "content": full_response_content})
        else:
            callback_chunk(f"❌ Error del servidor: {response.status_code}")

    except requests.exceptions.ConnectionError:
        callback_chunk("❌ Error de conexión: ¿Está LM Studio abierto?")
    except Exception as e:
        callback_chunk(f"❌ Error: {str(e)}")