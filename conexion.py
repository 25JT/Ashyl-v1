import requests
import json
import infopc
import hora
import pokemon
import buscar
SERVER_URL = "http://localhost:1234/v1"

# Configuración inicial de la conversación
history = [
    {"role": "system", 
    "content": """Tu nombre es Ashly 
    eres un asistente inteligente. Siempre respondes en español y das respuestas correctas, útiles y bien razonadas. 
    si no savez algo no lo inventes simplemente di que no lo sabes.
     """},
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

 #   Envía el mensaje a la IA con streaming y maneja llamadas a funciones (tools).

    global history
    try:
        model = get_active_model()
        if not model:
            callback_chunk("❌ No hay modelo disponible en LM Studio.")
            return

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "info_pc",
                    "description": "Obtiene información del hardware y sistema operativo del computador del usuario",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "hora_actual",
                    "description": "obtiene la hroa actual del hardware",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "pokedex",
                    "description": "obtiene la pokedex de los pokemon",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                      
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "buscar",
                    "description": "obtiene informacion actual de internet de ser neseario puedes buscar cual quier cosa menos contenido sexual o de odio, no inventes informacion",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pregunta": {
                                "type": "string",
                                "description": "pregunta que se va a buscar en internet"
                            }
                        },
                        "required": ["pregunta"]
                      
                    }
                }
            },
        ]

        # Solo agregamos el mensaje del usuario si es una nueva interacción
        if mensaje:
            history.append({"role": "user", "content": mensaje})

        while True:
            response = requests.post(
                f"{SERVER_URL}/chat/completions",
                json={
                    "model": model,
                    "messages": history,
                    "tools": tools,
                    "temperature": 0.7,
                    "stream": True 
                },
                stream=True,
                timeout=60
            )

            if response.status_code != 200:
                callback_chunk(f"❌ Error del servidor: {response.status_code}")
                return

            full_response_content = ""
            tool_calls = []

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
                        
                        # Procesar contenido de texto
                        if "content" in delta and delta["content"]:
                            content = delta["content"]
                            full_response_content += content
                            callback_chunk(content)
                        
                        # Procesar llamadas a funciones (streaming)
                        if "tool_calls" in delta:
                            for tc_delta in delta["tool_calls"]:
                                index = tc_delta.get("index")
                                # Asegurar que el array tool_calls tenga espacio
                                while len(tool_calls) <= index:
                                    tool_calls.append({
                                        "id": None,
                                        "type": "function",
                                        "function": {"name": "", "arguments": ""}
                                    })
                                
                                if "id" in tc_delta:
                                    tool_calls[index]["id"] = tc_delta["id"]
                                if "function" in tc_delta:
                                    f = tc_delta["function"]
                                    if "name" in f:
                                        tool_calls[index]["function"]["name"] += f["name"]
                                    if "arguments" in f:
                                        tool_calls[index]["function"]["arguments"] += f["arguments"]
                    except Exception:
                        continue

            # Si no hubo llamadas a herramientas, guardamos y terminamos
            if not tool_calls:
                if full_response_content:
                    history.append({"role": "assistant", "content": full_response_content})
                break
            
            # Si hubo llamadas a herramientas, las procesamos
            assistant_msg = {"role": "assistant", "tool_calls": tool_calls}
            if full_response_content:
                assistant_msg["content"] = full_response_content
            history.append(assistant_msg)

            for tool_call in tool_calls:
                name = tool_call["function"]["name"]
                
                # Parsear argumentos de JSON string a dict
                try:
                    args = json.loads(tool_call["function"]["arguments"]) if tool_call["function"]["arguments"] else {}
                except json.JSONDecodeError:
                    args = {}

                if name == "info_pc":
                    resultado = infopc.info_pc()
                elif name == "hora_actual":
                    resultado = hora.hora_actual()
                elif name == "pokedex":
                    resultado = pokemon.pokedex()
                elif name == "buscar":
                    pregunta = args.get("pregunta", "")
                    resultado = buscar.buscar(pregunta)
                else:
                    resultado = {"error": "Función no encontrada"}

                # Añadir la respuesta de la herramienta al historial
                history.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "name": name,
                    "content": json.dumps(resultado)
                })
            
            # Limpiamos el mensaje para que en la siguiente iteración no se duplique
            mensaje = None
            # El bucle 'while' continuará y hará una nueva petición con los datos de la herramienta

    except requests.exceptions.ConnectionError:
        callback_chunk("❌ Error de conexión: ¿Está LM Studio abierto?")
    except Exception as e:
        callback_chunk(f"❌ Error: {str(e)}")


