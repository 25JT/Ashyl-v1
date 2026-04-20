import requests
import json
import infopc
import hora
import pokemon
#import buscar
import emociones
import reproducir_musica
import vision_manager
import teclado_pro
import os
import base64
SERVER_URL = "http://localhost:1234/v1"

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historial_chat.json")

def load_chat_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return [
        {"role": "system", 
        "content": """Tu nombre es Ashly, eres un asistente inteligente. 
        TU MEMORIA ES PERSISTENTE: Todo lo que aprendas hoy lo recordarás mañana.
        Siempre responde en español.
        
        REGLAS CRÍTICAS:
        1. CONSCIENCIA ESTRUCTURAL: Usa `verificar_estado_pc` para obtener la ubicación (box), centro y estado (minimizado/activo) de todas las ventanas. 
        2. INTERACCIÓN POR VENTANA: Si quieres actuar sobre una app abierta (ej: Spotify), usa sus coordenadas de `centro` obtenidas de la lista de ventanas en lugar de buscar iconos visuales.
        3. ATAJOS DE TECLADO: Prefiere usar `presionar_hotkey` para acciones rápidas: Windows + E (explorador), Alt + Tab (cambiar ventana).
        4. APPS CERRADAS: Si necesitas abrir algo como Spotify o Chrome, usa ÚNICA Y EXCLUSIVAMENTE la herramienta `abrir_aplicacion`. ¡No uses la rejilla, coordenadas ni atajos iterativos! Llama la herramienta y ábrelo instantáneamente.
        5. LIMITACIONES VISUALES: La función `analizar_visual_con_rejilla` te devuelve una imagen, pero debido a la compresión local NO puedes leer números pequeños. JAMÁS retornes coordenadas (0, 0).
        6. ICONOS: Si necesitas clickear algo muy visual como Spotify en el escritorio, debes usar `buscar_y_clic_icono` mandando el nombre (ej: 'spotify.png') en lugar de intentar adivinar coordenadas del mouse.
        """},
    ]

def save_chat_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

# Cargar historial al inicio
history = load_chat_history()

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
                    "description": "obtiene la hora actual del hardware",
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
                    "description": "obtiene la pokedex de los pokemones que actualmente tenemos",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                      
                    }
                }
            },
            # {
            #     "type": "function",
            #     "function": {
            #         "name": "buscar",
            #         "description": "obtiene informacion actual de internet de ser neseario puedes buscar cual quier cosa menos contenido sexual o de odio, no inventes informacion",
            #         "parameters": {
            #             "type": "object",
            #             "properties": {
            #                 "pregunta": {
            #                     "type": "string",
            #                     "description": "pregunta que se va a buscar en internet"
            #                 }
            #             },
            #             "required": ["pregunta"]
                      
            #         }
            #     }
            # },
            {
                "type": "function",
                "function": {
                    "name": "obtener_emocion",
                    "description": "obtiene la emocion actual de ashly ",
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
                    "name": "reproducir_musica",
                    "description": "reproduce un artista de musica en spotify",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "artista": {
                                "type": "string",
                                "description": "nombre del artista que se va a reproducir"
                            }
                        },
                        "required": ["artista"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "abrir_aplicacion",
                    "description": "HERRAMIENTA OBLIGATORIA VELOZ para abrir aplicaciones o procesos (Spotify, Word, Chrome). Si necesitas abrir algo, llama a esta en vez de intentar usar la visión o atajos manuales.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "app_name": {
                                "type": "string",
                                "description": "Nombre de la app (ej: 'spotify', 'chrome', 'calculadora')"
                            }
                        },
                        "required": ["app_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "controlar_mouse",
                    "description": "Realiza acciones con el mouse (movimiento, click, arrastrar).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "accion": {"type": "string", "enum": ["click", "mover", "doble_click", "click_derecho"]},
                            "x": {"type": "integer"},
                            "y": {"type": "integer"}
                        },
                        "required": ["accion", "x", "y"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "presionar_hotkey",
                    "description": "Presiona una combinación de teclas (ej: ['win', 'e'], ['ctrl', 'c'], ['alt', 'tab']).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "teclas": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Lista de teclas a presionar simultáneamente"
                            }
                        },
                        "required": ["teclas"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "escribir_humanamente",
                    "description": "Escribe texto o presiona teclas especiales.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "texto": {"type": "string", "description": "Texto a escribir"},
                            "tecla": {"type": "string", "description": "Tecla especial (enter, tab, esc, etc)"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "buscar_y_clic_icono",
                    "description": "Busca un icono específico en la pantalla, lo localiza y hace clic automáticamente. Ideal para Spotify, botones de reproducción, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "icono": {
                                "type": "string",
                                "description": "Nombre del archivo de imagen del icono (ej: 'sopty.png', 'barra.png')"
                            }
                        },
                        "required": ["icono"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analizar_visual_con_rejilla",
                    "description": "Toma una captura de pantalla con una cuadrícula roja numerada cada 100px. Úsala para identificar coordenadas exactas de botones o texto.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nombre": {"type": "string", "description": "Tarea que se está analizando"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mapear_barra_tareas",
                    "description": "Busca iconos rápidos específicamente en la barra de tareas (fondo de la pantalla). Es más veloz y preciso para abrir apps.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "altura": {"type": "integer", "description": "Altura en píxeles de la barra (default 80)"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "capturar_pantalla",
                    "description": "Toma una captura de la pantalla y obtiene la lista de ventanas abiertas para verificar el estado real de la PC.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nombre": {
                                "type": "string",
                                "description": "Nombre descriptivo para la captura"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "verificar_estado_pc",
                    "description": "Obtiene la lista de ventanas abiertas y la ventana activa actual sin tomar captura.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ejecutar_tarea_memorizada",
                    "description": "Busca en el historial operativo si ya se sabe cómo realizar una tarea específica.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tarea": {
                                "type": "string",
                                "description": "La tarea a realizar (ej: 'cambiar cancion')"
                            }
                        },
                        "required": ["tarea"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "guardar_aprendizaje",
                    "description": "Guarda una secuencia de pasos exitosa en el historial para recordarla en el futuro.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tarea": {
                                "type": "string",
                                "description": "Nombre de la tarea aprendida"
                            },
                            "pasos": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "accion": {"type": "string", "description": "click, escribir, esperar, etc"},
                                        "detalle": {"type": "string", "description": "qué se hizo o qué se buscó"}
                                    }
                                },
                                "description": "Lista de pasos realizados"
                            }
                        },
                        "required": ["tarea", "pasos"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "guardar_observacion",
                    "description": "Guarda una nota, observación o retroalimentación sobre una tarea para no olvidarla.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tarea": {
                                "type": "string",
                                "description": "Nombre de la tarea a la que se refiere la nota"
                            },
                            "nota": {
                                "type": "string",
                                "description": "La observación o el consejo del usuario"
                            }
                        },
                        "required": ["tarea", "nota"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "recordar_preferencia",
                    "description": "Guarda información importante sobre el usuario o sus gustos para siempre.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "categoria": {"type": "string", "description": "Ej: 'musica', 'horario', 'usuario'"},
                            "informacion": {"type": "string", "description": "Lo que se debe recordar"}
                        },
                        "required": ["categoria", "informacion"]
                    }
                }
            }
        ]

        # Solo agregamos el mensaje del usuario si es una nueva interacción
        if mensaje:
            history.append({"role": "user", "content": mensaje})

        while True:
            # SANITIZACIÓN DE HISTORIAL PARA EVITAR OOM DE LM STUDIO
            # Mantenemos solo la última imagen subida en toda la sesión
            history_para_enviar = []
            imagenes_encontradas = 0
            
            for msg in reversed(history):
                msg_copy = dict(msg)
                if isinstance(msg.get("content"), list):
                    nuevo_content = []
                    for item in reversed(msg["content"]):
                        if isinstance(item, dict) and item.get("type") == "image_url":
                            if imagenes_encontradas == 0:
                                nuevo_content.insert(0, item)
                                imagenes_encontradas += 1
                            else:
                                nuevo_content.insert(0, {"type": "text", "text": "[Imagen anterior eliminada de contexto para ahorrar memoria RAM/VRAM]"})
                        else:
                            nuevo_content.insert(0, item)
                    msg_copy["content"] = nuevo_content
                history_para_enviar.insert(0, msg_copy)

            response = requests.post(
                f"{SERVER_URL}/chat/completions",
                json={
                    "model": model,
                    "messages": history_para_enviar,
                    "tools": tools,
                    "temperature": 0.7,
                    "stream": True 
                },
                stream=True,
                timeout=120
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
                # elif name == "buscar":
                #     pregunta = args.get("pregunta", "")
                #     resultado = buscar.buscar(pregunta)
                elif name == "obtener_emocion":
                    resultado = emociones.obtener_emocion()
                elif name == "capturar_pantalla":
                    manager = vision_manager.VisionManager()
                    resultado = manager.capture_screen(args.get("nombre", "captura_ia"))
                elif name == "mapear_barra_tareas":
                    manager = vision_manager.VisionManager()
                    try:
                        altura = int(args.get("altura", 80))
                    except (ValueError, TypeError):
                        altura = 80
                    resultado = manager.mapear_barra_tareas(altura)
                elif name == "analizar_visual_con_rejilla":
                    manager = vision_manager.VisionManager()
                    resultado = manager.capture_screen(args.get("nombre", "vision_grid"))
                elif name == "buscar_y_clic_icono":
                    manager = vision_manager.VisionManager()
                    resultado = manager.buscar_y_clic_icono(args.get("icono", ""))
                elif name == "verificar_estado_pc":
                    manager = vision_manager.VisionManager()
                    resultado = manager.analizar_entorno()
                elif name == "ejecutar_tarea_memorizada":
                    resultado = vision_manager.operar_con_memoria(args.get("tarea", ""))
                elif name == "abrir_aplicacion":
                    manager = vision_manager.VisionManager()
                    app_name = args.get("app_name", "")
                    if app_name:
                        resultado = manager.process_manager.open_application(app_name)
                    else:
                        resultado = {"error": "Falta enviar el nombre de la app ('app_name')"}
                elif name == "guardar_aprendizaje":
                    manager = vision_manager.VisionManager()
                    manager.save_step(args.get("tarea", ""), args.get("pasos", []))
                    resultado = {"mensaje": f"Tarea '{args.get('tarea')}' guardada exitosamente en el historial operativo."}
                elif name == "guardar_observacion":
                    manager = vision_manager.VisionManager()
                    manager.guardar_observacion(args.get("tarea", ""), args.get("nota", ""))
                    resultado = {"mensaje": f"Observación sobre '{args.get('tarea')}' guardada correctamente."}
                elif name == "recordar_preferencia":
                    manager = vision_manager.VisionManager()
                    manager.guardar_observacion("PREFERENCIAS_GENERALES", f"{args.get('categoria')}: {args.get('informacion')}")
                    resultado = {"mensaje": "Preferencia guardada en mi memoria a largo plazo."}
                elif name == "controlar_mouse":
                    mouse = vision_manager.MouseOperator()
                    accion = args.get("accion")
                    
                    try:
                        x_coord = int(args.get("x", 0))
                    except (ValueError, TypeError):
                        x_coord = 0
                        
                    try:
                        y_coord = int(args.get("y", 0))
                    except (ValueError, TypeError):
                        y_coord = 0
                    
                    # Evitar el failsafe (0, 0)
                    if x_coord <= 2: x_coord = 5
                    if y_coord <= 2: y_coord = 5
                    
                    pos = (x_coord, y_coord)
                    
                    if accion == "mover":
                        mouse.smooth_move(pos)
                    elif accion == "click":
                        mouse.smooth_move(pos)
                        vision_manager.pyautogui.click()
                    elif accion == "doble_click":
                        mouse.smooth_move(pos)
                        vision_manager.pyautogui.doubleClick()
                    elif accion == "click_derecho":
                        mouse.smooth_move(pos)
                        vision_manager.pyautogui.rightClick()
                    resultado = {"status": "ok", "accion": accion, "pos": pos, "nota": "Failsafe evitado." if x_coord <= 5 and y_coord <= 5 else ""}
                elif name == "escribir_humanamente":
                    texto = args.get("texto")
                    tecla = args.get("tecla")
                    if texto:
                        teclado_pro.escribir_humanamente(texto, velocidad=0.5)
                    if tecla:
                        vision_manager.pyautogui.press(tecla)
                    resultado = {"status": "ok", "escribio": texto, "presiono": tecla}
                elif name == "presionar_hotkey":
                    teclas = args.get("teclas", [])
                    if teclas:
                        teclado_pro.presionar_combinacion(teclas)
                        resultado = {"status": "ok", "hotkey": teclas}
                    else:
                        resultado = {"error": "No se enviaron teclas"}
                else:
                    resultado = {"error": "Función no encontrada"}

                # Añadir la respuesta de la herramienta al historial
                content_to_save = json.dumps(resultado)
                history.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "name": name,
                    "content": content_to_save
                })
                
                # SI LA HERRAMIENTA DEVOLVIÓ BASE64, PREPARAMOS LA PRÓXIMA PETICIÓN COMO MULTIMODAL
                if "base64" in resultado and resultado["base64"]:
                    last_b64 = resultado["base64"]
                    # Insertamos un mensaje visual ficticio en el historial para que lo vea el modelo
                    # Nota: Algunos APIs de LM Studio requieren que el último mensaje sea del usuario con la imagen
                    history.append({
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Aquí tienes la captura de pantalla para analizar:"},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{last_b64}"}}
                        ]
                    })
            
            # Guardar historial después de procesar herramientas
            save_chat_history(history)
            
            # Limpiamos el mensaje para que en la siguiente iteración no se duplique
            mensaje = None
            # El bucle 'while' continuará y hará una nueva petición con los datos de la herramienta

    except requests.exceptions.ConnectionError:
        callback_chunk("❌ Error de conexión: ¿Está LM Studio abierto?")
    except Exception as e:
        import traceback
        callback_chunk(f"❌ Error: {traceback.format_exc()}")
    finally:
        # Siempre intentamos guardar el historial al final del turno
        save_chat_history(history)


