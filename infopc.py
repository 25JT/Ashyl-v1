import platform
import psutil

def info_pc():

   return {
    "Sistema Operativo": platform.system(),
    "Versión": platform.version(),
    "Arquitectura": platform.machine(),
    "Procesador": platform.processor(),
    "RAM": psutil.virtual_memory().total / (1024 * 1024 * 1024),
    "Disco Duro": psutil.disk_usage('/').total / (1024 * 1024 * 1024),
    "IP": platform.node(),
    "Nombre de usuario": platform.uname().node,
    "Nombre de la máquina": platform.uname().node,
    "Versión del sistema": platform.uname().release,
    "Información del sistema": platform.uname(),
    "Información de la CPU": psutil.cpu_count(),
    "pantalla": pyautogui.size(),
   }


