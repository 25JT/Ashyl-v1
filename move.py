import pyautogui
import random
import time


# Mueve el mouse a la posición (968, 56) en 1 segundo
def reproducir_musica(cancion):
    img = pyautogui.locateCenterOnScreen('sopty.png', confidence=0.8)
    print(img)  
    pyautogui.moveTo(img.x, img.y, duration=1)
    pyautogui.click()
    time.sleep(1)
    img2 = pyautogui.locateCenterOnScreen('img2.png', confidence=0.2)
    print(img2)
    time.sleep(1)
    pyautogui.moveTo(img2.x, img2.y, duration=1)
    pyautogui.click()
    time.sleep(1)
    pyautogui.write('Espresso')
    time.sleep(3)
    img3 = pyautogui.locateCenterOnScreen('img3.png', confidence=0.8)
    print(img3)
    pyautogui.moveTo(img3.x, img3.y, duration=1)
    pyautogui.click()

    time.sleep(3)
    img4 = pyautogui.locateCenterOnScreen('img4.png', confidence=0.8)
    print(img4)
    pyautogui.moveTo(img4.x, img4.y, duration=1)
    pyautogui.doubleClick()
    return "Musica reproducida"
