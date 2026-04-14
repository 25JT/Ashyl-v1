import customtkinter as ctk
import conexion
import threading

# Configuración de la interfaz
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("800x600")
app.title("Ashly AI - Streaming")

# Título
title = ctk.CTkLabel(app, text="Ashly V1", font=("Arial", 28, "bold"))
title1 = ctk.CTkLabel(app, text="Asistente", font=("Arial",18, "bold", "italic"))
title.pack(pady=15)
title1.pack(pady=15)

# Área de chat
chat_display = ctk.CTkTextbox(app, width=740, height=400, font=("Arial", 14))
chat_display.pack(pady=10, padx=20)
chat_display.configure(state="disabled")

# Frame para input y botón
input_frame = ctk.CTkFrame(app, fg_color="transparent")
input_frame.pack(pady=10, fill="x", padx=20)

entry = ctk.CTkEntry(input_frame, placeholder_text="Escribe un mensaje aquí...", height=50, font=("Arial", 14))
entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

def append_to_chat(text):
    """Inserta texto al final del chat de forma segura."""
    chat_display.configure(state="normal")
    chat_display.insert("end", text)
    chat_display.configure(state="disabled")
    chat_display.see("end")

def recibir_chunk(chunk):
    """Callback que recibe cada pedacito de texto de la IA."""
    app.after(0, lambda: append_to_chat(chunk))

def procesar_respuesta(mensaje_usuario):
    """Hilo secundario para manejar la conexión y el streaming."""
    boton_enviar.configure(state="disabled", text="Escribiendo...")
    
    # Preparamos el inicio del mensaje de Ashly
    app.after(0, lambda: append_to_chat("Ashly: "))
    
    # Llamamos a la lógica de conexión pasando el callback
    conexion.conexion_ia(mensaje_usuario, recibir_chunk)
    
    # Al finalizar el stream, añadimos espacio y reactivamos botón
    app.after(0, lambda: append_to_chat("\n\n"))
    app.after(0, lambda: boton_enviar.configure(state="normal", text="Enviar"))

def enviarMsg(event=None):
    mensaje = entry.get().strip()
    if not mensaje:
        return
    
    # Mostrar mensaje usuario
    append_to_chat(f"Tú: {mensaje}\n\n")
    entry.delete(0, "end")
    
    # Iniciar streaming en hilo separado
    hilo = threading.Thread(target=procesar_respuesta, args=(mensaje,), daemon=True)
    hilo.start()

# Botón y binds
entry.bind("<Return>", enviarMsg)
boton_enviar = ctk.CTkButton(input_frame, text="Enviar", width=100, height=50, command=enviarMsg, font=("Arial", 14, "bold"))
boton_enviar.pack(side="right")

app.mainloop()