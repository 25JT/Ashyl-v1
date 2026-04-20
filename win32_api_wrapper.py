import win32gui
import win32process
import win32con
import psutil

class Win32APIWrapper:
    """
    Controla y obtiene información sobre las ventanas y procesos activos de Windows,
    permitiendo a la IA saber qué está abierto exactamente.
    """
    @staticmethod
    def get_open_windows():
        windows = []
        def enum_windows_proc(hwnd, lParam):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    process = psutil.Process(pid)
                    process_name = process.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    process_name = "Unknown"
                
                windows.append({
                    "hwnd": hwnd,
                    "title": win32gui.GetWindowText(hwnd).strip(),
                    "process_name": process_name,
                    "pid": pid,
                    "rect": win32gui.GetWindowRect(hwnd) # (left, top, right, bottom)
                })
            return True

        win32gui.EnumWindows(enum_windows_proc, None)
        return windows

    @staticmethod
    def find_window_by_title_or_process(name):
        name = name.lower()
        windows = Win32APIWrapper.get_open_windows()
        for w in windows:
            if name in w["title"].lower() or name in w["process_name"].lower():
                return w
        return None

    @staticmethod
    def focus_window(hwnd):
        """Trae una ventana específica al frente para que el usuario o la IA interactúe."""
        try:
            # Si la ventana está minimizada, la restaura
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            # La trae al frente
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception as e:
            print(f"Error al traer la ventana al frente: {e}")
            return False
