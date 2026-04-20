import cv2
import numpy as np
import mss
import pyautogui
import time
import random
from movermouse import MouseOperator

pyautogui.FAILSAFE = True




def reproducir_musica(cancion):

    def find_template(screen, template, threshold=0.8):
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            h, w = template.shape[:2]
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            return (center_x, center_y), max_val

        return None, None

    import pyperclip

    # -------------------------
    # CONFIG / INIT
    # -------------------------
    THRESHOLD = 0.8
    image_files = ["sopty.png", "barra.png", "artista.png","repoducirv2.png"]
    templates = []

    for f in image_files:
        img = cv2.imread(f)
        if img is None:
            print(f"Advertencia: No se pudo cargar {f}")
        templates.append(img)

    mouse = MouseOperator()

    # Pedir texto al inicio
    texto_especifico = cancion
    print(texto_especifico)

    print("Iniciando secuencia en 3 segundos...")
    time.sleep(3)

    current_step = 0

    with mss.mss() as sct:
        monitor = sct.monitors[1]

        while current_step < len(templates):
            if templates[current_step] is None:
                print(f"Saltando paso {current_step} porque la imagen no existe.")
                current_step += 1
                continue

            screen = np.array(sct.grab(monitor))
            screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(templates[current_step], cv2.COLOR_BGR2GRAY)

            pos, confidence = find_template(screen_gray, template_gray, THRESHOLD)

            if pos:
                img_name = image_files[current_step]
                print(f"[{img_name}] detectado en {pos} (confianza: {confidence:.2f})")

                # Movimiento humano
                mouse.smooth_move(pos, duration=random.uniform(0.5, 0.8))
                time.sleep(random.uniform(0.1, 0.3))
                pyautogui.click()
                
                # ACCIÓN ESPECIAL: Si es img2.png y hay texto, escribirlo
                if img_name == "barra.png" and texto_especifico:
                    print(f"Escribiendo: {texto_especifico}")
                    time.sleep(0.5)
                    pyperclip.copy(texto_especifico)
                    pyautogui.hotkey('ctrl', 'v')
                    time.sleep(0.5)
                    pyautogui.press('enter')
                
                print(f"Paso {img_name} completado.")
                current_step += 1
                time.sleep(1) # Espera un poco antes de buscar la siguiente imagen
                
            # Debug visual
            cv2.imshow("Deteccion Secuencial", cv2.resize(screen, (800, 450)))
            if cv2.waitKey(1) == 27: # ESC para salir
                break

    print("Secuencia finalizada.")
    cv2.destroyAllWindows()

    return "musica reproducida"
