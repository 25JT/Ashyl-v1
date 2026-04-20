import json
import os
import time
import pyautogui
import cv2
import numpy as np
from mss import mss
from movermouse import MouseOperator
from teclado_pro import escribir_humanamente
from process_lifecycle import ProcessLifecycleManager
import pygetwindow as gw

class VisionManager:
    """
    Gestiona la memoria visual y operativa de Ashly.
    Permite aprender de acciones pasadas y analizar la pantalla.
    """
    def __init__(self, history_file=None):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        if history_file is None:
            self.history_file = os.path.join(self.base_dir, "ajustes_operativos.json")
        else:
            self.history_file = history_file
            
        self.mouse = MouseOperator()
        self.process_manager = ProcessLifecycleManager(self)
        self.history = self._load_history()
        self.screenshot_dir = os.path.join(self.base_dir, "capturas_aprendizaje")
        
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
            
        # Extensiones de imagen que buscaremos como iconos
        self.icon_extensions = ['.png', '.jpg', '.jpeg']
        self.known_icons = self._get_known_icons()

    def _get_known_icons(self):
        """Lista todos los archivos de imagen en el directorio raíz que pueden ser iconos."""
        return [f for f in os.listdir('.') if any(f.endswith(ext) for ext in self.icon_extensions)]

    def _load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_step(self, task, steps):
        """
        Guarda una secuencia de pasos exitosa para una tarea.
        Ejemplo de pasos: [{"action": "click", "image": "btn_next.png", "coord": [100, 200]}]
        """
        self.history[task] = {
            "steps": steps,
            "timestamp": time.time(),
            "usage_count": self.history.get(task, {}).get("usage_count", 0) + 1
        }
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=4, ensure_ascii=False)

    def capture_screen(self, name=None):
        if name is None:
            name = f"snap_{int(time.time())}"
        img_filename = f"{name}.png"
        path = os.path.join(self.screenshot_dir, img_filename)
        with mss() as sct:
            sct.shot(output=path)
        
        # Opcional: Dibujar rejilla (solo si se pide explícitamente en el nombre)
        # No cambiamos el color de la imagen original por defecto
        path_final = path
        base64_img = self.obtener_base64_imagen(path)
        
        if name and "grid" in name.lower():
            path_grid = os.path.join(self.screenshot_dir, f"{name}_grid.png")
            self.dibujar_rejilla(path, path_grid)
            path_final = path_grid
            base64_img = self.obtener_base64_imagen(path_grid)

        # Ya no mapeamos iconos automáticamente aquí para no depender de plantillas
        # mapa_iconos = self.mapear_iconos(path)
        
        return {
            "path": path_final, 
            "base64": base64_img,
            "contexto": "",
            "elementos_detectados": [], # Dejamos que la IA interprete
            "resolucion": list(pyautogui.size())
        }

    def dibujar_rejilla(self, input_path, output_path):
        """Dibuja una rejilla roja con coordenadas sobre la imagen."""
        img = cv2.imread(input_path)
        if img is None: return
        
        h, w = img.shape[:2]
        color = (0, 0, 255) # Rojo
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Dibujar líneas verticales cada 100px
        for x in range(0, w, 100):
            cv2.line(img, (x, 0), (x, h), color, 1)
            cv2.putText(img, str(x), (x + 5, 20), font, 0.5, color, 1)
            
        # Dibujar líneas horizontales cada 100px
        for y in range(0, h, 100):
            cv2.line(img, (0, y), (w, y), color, 1)
            cv2.putText(img, str(y), (5, y + 20), font, 0.5, color, 1)
            
        cv2.imwrite(output_path, img)

    def obtener_base64_imagen(self, image_path, max_dim=1024):
        """Convierte una imagen a base64 (JPEG comprimido y redimensionado) para enviarla a la IA, evitando crashear LM Studio."""
        import base64
        import cv2
        try:
            img = cv2.imread(image_path)
            if img is None: return None
            
            # Redimensionar si es muy grande
            h, w = img.shape[:2]
            if max(h, w) > max_dim:
                scale = max_dim / max(h, w)
                img = cv2.resize(img, (int(w * scale), int(h * scale)))
                
            # Codificar como JPEG en memoria con calidad 70 para reducir peso (de ~6MB a ~120KB)
            _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 70])
            return base64.b64encode(buffer).decode('utf-8')
        except:
            return None

    def mapear_iconos(self, screen_path, threshold=0.7, roi=None):
        """
        Busca todos los iconos conocidos en la captura y retorna sus coordenadas.
        roi: (left, top, width, height) para limitar la búsqueda.
        """
        screen = cv2.imread(screen_path)
        if screen is None: return []
        
        # Aplicar ROI si se especifica
        if roi:
            x, y, w, h = roi
            screen = screen[y:y+h, x:x+w]
        
        screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        elementos = []
        
        for icon_name in self.known_icons:
            template = cv2.imread(icon_name)
            if template is None: continue
            
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            th, tw = template_gray.shape[:2]
            
            # Busqueda multiescala acelerada (0.8x a 1.2x)
            found = None
            for scale in np.linspace(0.8, 1.2, 5):
                resized = cv2.resize(template_gray, (int(tw * scale), int(th * scale)))
                if resized.shape[0] > screen_gray.shape[0] or resized.shape[1] > screen_gray.shape[1]:
                    continue
                
                res = cv2.matchTemplate(screen_gray, resized, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
                
                if found is None or max_val > found[0]:
                    found = (max_val, max_loc, scale)

            if found and found[0] >= threshold:
                max_val, max_loc, scale = found
                rh, rw = int(th * scale), int(tw * scale)
                
                # Ajustar coordenadas si hubo ROI
                offset_x = roi[0] if roi else 0
                offset_y = roi[1] if roi else 0
                
                center = [
                    int(max_loc[0] + rw // 2) + offset_x,
                    int(max_loc[1] + rh // 2) + offset_y
                ]
                
                elementos.append({
                    "nombre": icon_name,
                    "coordenadas": center,
                    "confianza": round(float(max_val), 2)
                })
        return elementos

    def mapear_barra_tareas(self, altura_barra=80):
        """Toma una captura solo de la barra de tareas y detecta iconos allí."""
        with mss() as sct:
            monitor = sct.monitors[1]
            roi = {
                "top": monitor["height"] - altura_barra,
                "left": 0,
                "width": monitor["width"],
                "height": altura_barra
            }
            
            name = f"taskbar_{int(time.time())}"
            path = os.path.join(self.screenshot_dir, f"{name}.png")
            sct.shot(mon=1, output=path) # Capturamos todo pero analizaremos ROI
            
            roi_tuple = (roi["left"], roi["top"], roi["width"], roi["height"])
            mapa = self.mapear_iconos(path, roi=roi_tuple)
            
            return {
                "path": path,
                "elementos_detectados": mapa,
                "roi": roi
            }

    def guardar_observacion(self, tarea, observacion):
        """Guarda feedback o notas sobre una tarea específica."""
        if tarea not in self.history:
            self.history[tarea] = {"steps": [], "observaciones": []}
        
        if "observaciones" not in self.history[tarea]:
            self.history[tarea]["observaciones"] = []
            
        self.history[tarea]["observaciones"].append({
            "nota": observacion,
            "fecha": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=4, ensure_ascii=False)

    def analizar_entorno(self):
        """Retorna un mapa detallado de ventanas con posiciones y estados."""
        try:
            windows = gw.getWindowsWithTitle('')
            ventana_activa = gw.getActiveWindow()
            lista_ventanas = []
            
            for w in windows:
                if not w.title.strip(): continue
                
                estado = "normal"
                if w.isMinimized: estado = "minimizado"
                elif w.isMaximized: estado = "maximizado"
                
                # Coordenadas del centro para un clic rápido si es necesario
                centro = [w.left + w.width // 2, w.top + w.height // 2]
                
                lista_ventanas.append({
                    "titulo": w.title,
                    "box": {"x": w.left, "y": w.top, "w": w.width, "h": w.height},
                    "centro": centro,
                    "estado": estado,
                    "es_activa": (ventana_activa and w.title == ventana_activa.title)
                })
                
            return {
                "ventanas": lista_ventanas,
                "resolucion": list(pyautogui.size()),
                "fecha_hora": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            return {"error": f"Error al analizar ventanas: {str(e)}"}

    def find_and_click(self, template_path, threshold=0.7):
        """Busca una imagen en pantalla (multiescala) y hace click si la encuentra."""
        captura = self.capture_screen("temp_search")
        screen_path = captura["path"]
        
        screen = cv2.imread(screen_path)
        template = cv2.imread(template_path)
        if screen is None or template is None:
            return False, "Error cargando imágenes"

        screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        th, tw = template_gray.shape[:2]

        found = None
        for scale in np.linspace(0.8, 1.2, 5):
            resized = cv2.resize(template_gray, (int(tw * scale), int(th * scale)))
            if resized.shape[0] > screen_gray.shape[0] or resized.shape[1] > screen_gray.shape[1]:
                continue
            
            res = cv2.matchTemplate(screen_gray, resized, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            
            if found is None or max_val > found[0]:
                found = (max_val, max_loc, scale)

        if found and found[0] >= threshold:
            max_val, max_loc, scale = found
            center = (int(max_loc[0] + (tw * scale) // 2), int(max_loc[1] + (th * scale) // 2))
            self.mouse.smooth_move(center)
            pyautogui.click()
            return True, center
        
        return False, "No se encontró el elemento"

    def get_memory(self, task):
        return self.history.get(task)

    def buscar_y_clic_icono(self, icon_name, threshold=0.7):
        """Captura pantalla, busca un icono específico y hace clic si lo halla."""
        # 1. Capturar pantalla actual
        name = f"busqueda_{icon_name.split('.')[0]}"
        captura = self.capture_screen(name)
        screen_path = captura["path"]
        
        # 2. Buscar el icono en los detectados
        detectados = captura["elementos_detectados"]
        icono_encontrado = next((i for i in detectados if i["nombre"].lower() == icon_name.lower()), None)
        
        if icono_encontrado:
            coords = icono_encontrado["coordenadas"]
            self.mouse.smooth_move(coords)
            pyautogui.click()
            return {
                "status": "success",
                "mensaje": f"Icono '{icon_name}' encontrado en {coords} y clic realizado.",
                "coordenadas": coords
            }
        
        # 3. Si no se encontró en la lista general, intentar búsqueda específica (por si acaso)
        success, res = self.find_and_click(icon_name, threshold)
        if success:
            return {
                "status": "success",
                "mensaje": f"Icono '{icon_name}' encontrado mediante búsqueda directa en {res}.",
                "coordenadas": res
            }
            
        return {
            "status": "fail",
            "mensaje": f"No pude encontrar el icono '{icon_name}' en la pantalla actual.",
            "elementos_vistos": [i["nombre"] for i in detectados]
        }

    def ejecutar_comando_ia(self, accion, **kwargs):
        """
        Ejecuta un comando ordenado por la IA interactuando con el sistema local.
        Acciones soportadas: 'abrir_app', 'cerrar_app', 'abrir_carpeta', 'escribir', 'click_icono', 'click_coord'
        """
        if accion == "abrir_app":
            app_name = kwargs.get("app_name")
            if not app_name: return {"status": "error", "message": "Falta 'app_name'"}
            return self.process_manager.open_application(app_name, kwargs.get("icon_name"))
        elif accion == "cerrar_app":
            app_name = kwargs.get("app_name")
            if not app_name: return {"status": "error", "message": "Falta 'app_name'"}
            return self.process_manager.close_application(app_name)
        elif accion == "abrir_carpeta":
            folder_path = kwargs.get("folder_path")
            if not folder_path: return {"status": "error", "message": "Falta 'folder_path'"}
            return self.process_manager.open_folder(folder_path)
        elif accion == "escribir":
            texto = kwargs.get("texto", "")
            escribir_humanamente(texto, velocidad=kwargs.get("velocidad", 0.5))
            return {"status": "success", "message": f"Se ha escrito el texto de forma humana."}
        elif accion == "click_icono":
             icon_name = kwargs.get("icon_name")
             if not icon_name: return {"status": "error", "message": "Falta 'icon_name'"}
             return self.buscar_y_clic_icono(icon_name)
        elif accion == "click_coord":
            coords = kwargs.get("coordenadas")
            if coords and len(coords) == 2:
                self.mouse.smooth_move(coords)
                pyautogui.click()
                return {"status": "success", "message": f"Click realizado en {coords}"}
            return {"status": "error", "message": "Faltan las 'coordenadas' o están incompletas."}
        else:
            return {"status": "error", "message": f"Acción '{accion}' no reconocida."}

def operar_con_memoria(objetivo, instrucciones_ia=None):
    """
    Función principal para ser llamada por la IA.
    Si conoce el objetivo, lo ejecuta. Si no, pide instrucciones basadas en lo que ve.
    """
    manager = VisionManager()
    memoria = manager.get_memory(objetivo)
    
    if memoria:
        print(f"Ejecutando '{objetivo}' desde la memoria...")
        # Lógica de ejecución automática basada en pasos previos
        # Por simplicidad, retornamos que lo recordamos y los pasos
        return {"status": "success", "source": "memory", "steps": memoria["steps"]}
    
    # Si no hay memoria, tomamos foto y retornamos a la IA para que analice
    captura = manager.capture_screen(objetivo.replace(" ", "_"))
    img_path = captura["path"]
    
    return {
        "status": "new_task",
        "message": f"No recuerdo cómo hacer esto. He capturado la pantalla en {img_path}. Por favor, dime qué pasos debo seguir o qué buscar.",
        "image_path": img_path,
        "detalles_visuales": captura
    }
