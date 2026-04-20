import time
import pyautogui
from teclado_pro import escribir_humanamente, presionar_combinacion
from win32_api_wrapper import Win32APIWrapper
import psutil
import os

class ProcessLifecycleManager:
    """
    Se encarga de manejar el ciclo de vida de los procesos (abrir aplicaciones, 
    cerrar aplicaciones) utilizando la ruta más óptima disponible.
    """
    def __init__(self, vision_manager):
        self.vision = vision_manager

    def open_application(self, app_name, icon_name=None):
        """
        Abre una aplicación usando la lógica más corta:
        1. Si ya está abierta, la trae al frente.
        2. Si se ve en la barra de tareas, hace clic en ella usando Visión.
        3. Si no, busca en el menú de inicio para abrirla como humano.
        """
        app_name_lower = app_name.lower()
        
        # 1. Comprobar si ya está abierta usando win32 api
        window = Win32APIWrapper.find_window_by_title_or_process(app_name_lower)
        if window:
            Win32APIWrapper.focus_window(window["hwnd"])
            return {
                "status": "success", 
                "via": "ventana_abierta",
                "message": f"La aplicación {app_name} ya estaba abierta. Ha sido traída al frente."
            }

        # 2. Buscar en la barra de tareas mediante visión si existe un ícono definido
        if icon_name:
            # Puedes usar tu gestor de visión para detectar el click en barra
            resultado_vision = self.vision.buscar_y_clic_icono(icon_name)
            if resultado_vision["status"] == "success":
                time.sleep(2) # Dar tiempo a que la app restaure o abra
                return {
                    "status": "success", 
                    "via": "icono_tarea",
                    "message": f"{app_name} abierta clickeando el icono en la barra de tareas."
                }

        # 3. Fallback: Escribir en Inicio
        presionar_combinacion(['win'])
        time.sleep(1.0) # Tiempo para el menú
        escribir_humanamente(app_name, velocidad=0.8) # Velocidad moderada
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(3) # Esperar a que la app suba a memoria
        
        return {
            "status": "success", 
            "via": "menu_inicio",
            "message": f"{app_name} ejecutada desde el menú de inicio."
        }

    def close_application(self, app_name):
        """Cierra una aplicación buscándola y terminando su proceso."""
        window = Win32APIWrapper.find_window_by_title_or_process(app_name)
        if window:
            try:
                process = psutil.Process(window["pid"])
                process.terminate()
                return {"status": "success", "message": f"Aplicación {app_name} ha sido cerrada."}
            except Exception as e:
                return {"status": "error", "message": f"No pude cerrar {app_name}. Error: {str(e)}"}
        return {"status": "fail", "message": f"La aplicación {app_name} no se encuentra en ejecución."}

    def open_folder(self, folder_path):
        """Abre un directorio o carpeta en el explorador de archivos."""
        if os.path.exists(folder_path):
            os.startfile(folder_path)
            time.sleep(1)
            return {"status": "success", "message": f"Carpeta '{folder_path}' abierta."}
        else:
            return {"status": "error", "message": f"La carpeta '{folder_path}' no existe."}
