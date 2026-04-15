import platform
import psutil

def info_pc():

   return {
    "Sistema Operativo": platform.system(),
    "Versión": platform.version(),
    "Arquitectura": platform.machine(),
    "Procesador": platform.processor(),
   }


