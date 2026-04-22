import tkinter as tk
import mysql.connector
import urllib.request
import json
import time
from datetime import datetime
import base64
import io
from PIL import Image, ImageTk

# Configuracion de red y base de datos
URL_ESP32  = "http://192.168.1.119"
URL_RASPI5 = "http://192.168.1.117:5000"

config = {
    'host': '192.168.1.112',
    'user': 'fabricio',
    'password': 'efenomas',
    'database': 'iot_telemetry'
}

# Estilos y colores
BG_DARK   = "#0D0F1A"; BG_CARD   = "#161929"; BG_INPUT  = "#1E2235"; BORDER    = "#2A2F4A"
TEXT_PRI  = "#E8EAFF"; TEXT_SEC  = "#7B82A8"; TEXT_HINT = "#454D70"
ACCENT_A  = "#6C63FF"; ACCENT_B  = "#00C2CB"; ACCENT_C  = "#00E899"; ACCENT_W  = "#FF6B6B"

FONT_TITLE  = ("Courier New", 22, "bold"); FONT_SUB    = ("Courier New", 11)
FONT_BTN    = ("Courier New", 12, "bold"); FONT_LABEL  = ("Courier New", 10)
FONT_INPUT  = ("Courier New", 13); FONT_SMALL  = ("Courier New", 9)

id_usuario_actual = ""
leyendo_datos = False 

# Inicializacion de ventana principal
root = tk.Tk()
root.title("INTERNET OF THINGS - Control Center")
root.geometry("620x720")
root.configure(bg=BG_DARK)
root.resizable(False, False)

root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
frame = tk.Frame(root, bg=BG_CARD)
frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
frame.grid_columnconfigure(0, weight=1)

# Helper widgets
def limpiar():
    for w in frame.winfo_children(): w.destroy()

def boton_moderno(texto, color, comando, parent, fill=True):
    outer = tk.Frame(parent, bg=color, padx=2, pady=0)
    if fill: outer.pack(fill="x", padx=30, pady=6)
    else: outer.pack(padx=10, pady=6)
    inner = tk.Frame(outer, bg=BG_INPUT, cursor="hand2"); inner.pack(fill="both")
    lbl = tk.Label(inner, text=texto, font=FONT_BTN, bg=BG_INPUT, fg=color, pady=13, anchor="center")
    lbl.pack(fill="both", expand=True)
    def on(e): inner.config(bg=color); lbl.config(bg=color, fg="white")
    def off(e): inner.config(bg=BG_INPUT); lbl.config(bg=BG_INPUT, fg=color)
    def click(e): comando()
    for w in (outer, inner, lbl):
        w.bind("<Enter>", on); w.bind("<Leave>", off); w.bind("<Button-1>", click)

def separador(parent, pady=10): tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=30, pady=pady)

def entry_widget(parent, placeholder="", show=None):
    wrap = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
    wrap.pack(fill="x", padx=30, pady=(0, 8))
    inner = tk.Frame(wrap, bg=BG_INPUT); inner.pack(fill="both")
    kw = dict(font=FONT_INPUT, bg=BG_INPUT, fg=TEXT_PRI, insertbackground=ACCENT_A, relief="flat", bd=8, highlightthickness=0)
    if show: kw["show"] = show
    e = tk.Entry(inner, **kw); e.pack(fill="x")
    def act(ev): wrap.config(bg=ACCENT_A)
    def des(ev): wrap.config(bg=BORDER)
    e.bind("<FocusIn>", lambda ev: (act(ev),)); e.bind("<FocusOut>", lambda ev: (des(ev),))
    return e

# Ventanas emergentes
def popup_error(titulo, mensaje): _popup(titulo, mensaje, ACCENT_W, "X " + titulo)
def popup_ok(titulo, mensaje): _popup(titulo, mensaje, ACCENT_C, "V " + titulo)
def popup_info(titulo, mensaje): _popup(titulo, mensaje, ACCENT_A, "O " + titulo)

def _popup(titulo, mensaje, color, header):
    win = tk.Toplevel(root); win.configure(bg=BG_CARD); win.resizable(False, False); win.transient(root)
    root.update_idletasks()
    x = root.winfo_x() + root.winfo_width()//2 - 220; y = root.winfo_y() + root.winfo_height()//2 - 100
    win.geometry(f"440x220+{x}+{y}")
    tk.Frame(win, bg=color, height=4).pack(fill="x")
    tk.Label(win, text=header, font=("Courier New", 13, "bold"), bg=BG_CARD, fg=color).pack(anchor="w", padx=24, pady=(16,4))
    tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=24)
    tk.Label(win, text=mensaje, font=FONT_LABEL, bg=BG_CARD, fg=TEXT_PRI, wraplength=390, justify="left").pack(anchor="w", padx=24, pady=12)
    btn = tk.Frame(win, bg=color, cursor="hand2"); btn.pack(pady=(0,18))
    lbl = tk.Label(btn, text="  OK  ", font=FONT_BTN, bg=color, fg="white", padx=20, pady=6); lbl.pack()
    def cerrar(e=None): win.destroy()
    btn.bind("<Button-1>", cerrar); lbl.bind("<Button-1>", cerrar)
    win.update_idletasks(); win.grab_set(); win.wait_window()

def popup_yesno(titulo, mensaje, color=ACCENT_A):
    result = [False]
    win = tk.Toplevel(root); win.configure(bg=BG_CARD); win.resizable(False, False); win.transient(root)
    root.update_idletasks()
    x = root.winfo_x() + root.winfo_width()//2 - 230; y = root.winfo_y() + root.winfo_height()//2 - 110
    win.geometry(f"460x210+{x}+{y}")
    tk.Frame(win, bg=color, height=4).pack(fill="x")
    tk.Label(win, text="? " + titulo, font=("Courier New", 13, "bold"), bg=BG_CARD, fg=color).pack(anchor="w", padx=24, pady=(16,4))
    tk.Label(win, text=mensaje, font=FONT_LABEL, bg=BG_CARD, fg=TEXT_PRI, wraplength=400, justify="left").pack(anchor="w", padx=24, pady=12)
    row = tk.Frame(win, bg=BG_CARD); row.pack(pady=(0,18))
    def _btn(parent, texto, accion, bg):
        f = tk.Frame(parent, bg=bg, cursor="hand2"); f.pack(side="left", padx=8)
        l = tk.Label(f, text=texto, font=FONT_BTN, bg=bg, fg="white", padx=18, pady=6); l.pack()
        def do(e=None): result[0] = accion; win.destroy()
        f.bind("<Button-1>", do); l.bind("<Button-1>", do)
    _btn(row, " Si ", True, ACCENT_C); _btn(row, " No ", False, ACCENT_W)
    win.update_idletasks(); win.grab_set(); win.wait_window()
    return result[0]

def popup_input(titulo, prompt, tipo="str", color=ACCENT_A):
    result = [None]
    win = tk.Toplevel(root); win.configure(bg=BG_CARD); win.resizable(False, False); win.transient(root)
    root.update_idletasks()
    x = root.winfo_x() + root.winfo_width()//2 - 220; y = root.winfo_y() + root.winfo_height()//2 - 120
    win.geometry(f"440x240+{x}+{y}")
    tk.Frame(win, bg=color, height=4).pack(fill="x")
    tk.Label(win, text="> " + titulo, font=("Courier New", 13, "bold"), bg=BG_CARD, fg=color).pack(anchor="w", padx=24, pady=(14,4))
    tk.Label(win, text=prompt, font=FONT_LABEL, bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", padx=24, pady=(10,4))
    e_frame = tk.Frame(win, bg=color, padx=2, pady=2); e_frame.pack(padx=24, fill="x")
    e = tk.Entry(e_frame, font=FONT_INPUT, bg=BG_INPUT, fg=TEXT_PRI, insertbackground=color, relief="flat", bd=6); e.pack(fill="x"); e.focus()
    row = tk.Frame(win, bg=BG_CARD); row.pack(pady=14)
    def confirmar(e_ev=None):
        val = e.get().strip()
        try:
            if tipo == "int": result[0] = int(val)
            elif tipo == "float": result[0] = float(val)
            else: result[0] = val
            win.destroy()
        except ValueError:
            e.config(bg="#3A1A1A"); e.after(300, lambda: e.config(bg=BG_INPUT))
    def cancelar(e_ev=None): win.destroy()
    e.bind("<Return>", confirmar)
    def _btn(parent, texto, accion, bg):
        f = tk.Frame(parent, bg=bg, cursor="hand2"); f.pack(side="left", padx=6)
        l = tk.Label(f, text=texto, font=FONT_BTN, bg=bg, fg="white", padx=16, pady=5); l.pack()
        f.bind("<Button-1>", lambda ev: accion()); l.bind("<Button-1>", lambda ev: accion())
    _btn(row, " Confirmar ", confirmar, color); _btn(row, " Cancelar  ", cancelar, ACCENT_W)
    win.update_idletasks(); win.grab_set(); win.wait_window()
    return result[0]

# Operaciones de base de datos
def guardar_en_db(tabla, columnas, valores):
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        placeholder = ", ".join(["%s"] * len(valores))
        sql = f"INSERT INTO {tabla} ({columnas}) VALUES ({placeholder})"
        cursor.execute(sql, valores)
        conn.commit()
        cursor.close(); conn.close()
        return True
    except Exception as e:
        print(f"Error DB: {e}"); return False

# Modulo de autenticacion
def login_screen():
    global entry_id, entry_pass
    limpiar()
    banner = tk.Frame(frame, bg=ACCENT_A); banner.pack(fill="x")
    tk.Label(banner, text=" INTERNET OF THINGS", font=("Courier New", 16, "bold"), bg=ACCENT_A, fg="white").pack(side="left", padx=16, pady=12)
    
    tk.Label(frame, text="", bg=BG_CARD).pack(pady=8)
    tk.Label(frame, text="ACCESO AL SISTEMA", font=("Courier New", 20, "bold"), bg=BG_CARD, fg=TEXT_PRI).pack()
    tk.Label(frame, text="Ingrese sus credenciales", font=FONT_SUB, bg=BG_CARD, fg=TEXT_SEC).pack(pady=(4,20))
    separador(frame)

    tk.Label(frame, text="ID DE OPERADOR", font=FONT_LABEL, bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", padx=30, pady=(10,2))
    entry_id = entry_widget(frame)
    tk.Label(frame, text="CONTRASEÑA", font=FONT_LABEL, bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", padx=30, pady=(8,2))
    entry_pass = entry_widget(frame, show="*")
    
    boton_moderno("Conectar al servidor", ACCENT_A, guardar_usuario, frame)

def guardar_usuario():
    global id_usuario_actual
    entrada_id   = entry_id.get().strip()
    entrada_pass = entry_pass.get().strip()
    if not entrada_id.isdigit():
        popup_error("ID invalido", "El ID debe ser numerico.")
        return
    try:
        conexion = mysql.connector.connect(**config)
        cursor   = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (entrada_id,))
        usuario  = cursor.fetchone()
        if usuario:
            if usuario["password"] == entrada_pass:
                id_usuario_actual = int(entrada_id)
                menu_principal()
            else: popup_error("Acceso denegado", "Contrasena incorrecta.")
        else:
            if popup_yesno("Nuevo operador", f"El ID {entrada_id} no existe.\nCrear cuenta nueva?", ACCENT_A):
                cursor.execute("INSERT INTO usuarios (id, password, nombre_usuario) VALUES (%s, %s, %s)", (entrada_id, entrada_pass, f"Operador_{entrada_id}"))
                conexion.commit()
                id_usuario_actual = int(entrada_id)
                menu_principal()
        cursor.close(); conexion.close()
    except mysql.connector.Error as err:
        popup_error("Error DB", f"{err}")

# Menu principal
def menu_principal():
    global leyendo_datos
    leyendo_datos = False
    limpiar()

    status = tk.Frame(frame, bg=BG_DARK); status.pack(fill="x", padx=0, pady=0)
    tk.Label(status, text=f"CONECTADO | OP-{id_usuario_actual}", font=FONT_SMALL, bg=BG_DARK, fg=ACCENT_C).pack(side="left", padx=16, pady=6)

    tk.Label(frame, text="SISTEMA MECATRONICO IOT", font=("Courier New", 22, "bold"), bg=BG_CARD, fg=TEXT_PRI).pack(pady=(28, 4))
    separador(frame)

    boton_moderno("1. Configurar Adquisicion (ESP32)", ACCENT_A, menu_config_telemetria, frame)
    boton_moderno("2. Inferencia IA (Raspi 5)", ACCENT_B, pantalla_ia, frame)
    boton_moderno("3. Base de Datos / CRUD", ACCENT_C, menu_base_datos, frame)
    boton_moderno("Cerrar Sesion", ACCENT_W, login_screen, frame)

# Configuracion de sensores
def menu_config_telemetria():
    limpiar()
    hdr = tk.Frame(frame, bg=ACCENT_A); hdr.pack(fill="x")
    tk.Label(hdr, text="  CONFIGURAR ADQUISICION DE DATOS", font=("Courier New", 14, "bold"), bg=ACCENT_A, fg="white").pack(pady=10)

    tk.Label(frame, text="Sensor a muestrear:", font=FONT_LABEL, bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", padx=30, pady=(15,2))
    
    var_sensor = tk.StringVar(value="1")
    opciones_frame = tk.Frame(frame, bg=BG_CARD)
    opciones_frame.pack(fill="x", padx=30, pady=5)
    
    tk.Radiobutton(opciones_frame, text="Solo Clima (DHT22)", variable=var_sensor, value="1", bg=BG_CARD, fg=TEXT_PRI, selectcolor=BG_INPUT, font=FONT_LABEL).pack(anchor="w")
    tk.Radiobutton(opciones_frame, text="Solo Movimiento (MPU6050)", variable=var_sensor, value="2", bg=BG_CARD, fg=TEXT_PRI, selectcolor=BG_INPUT, font=FONT_LABEL).pack(anchor="w")
    tk.Radiobutton(opciones_frame, text="Ambos Sensores", variable=var_sensor, value="3", bg=BG_CARD, fg=TEXT_PRI, selectcolor=BG_INPUT, font=FONT_LABEL).pack(anchor="w")

    tk.Label(frame, text="Duracion (segundos):", font=FONT_LABEL, bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", padx=30, pady=(15,2))
    entry_duracion = entry_widget(frame, placeholder="Ej: 5")

    tk.Label(frame, text="Intervalo (milisegundos):", font=FONT_LABEL, bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", padx=30, pady=(15,2))
    entry_intervalo = entry_widget(frame, placeholder="Ej: 100")

    def validar_e_iniciar():
        try:
            dur = int(entry_duracion.get().strip())
            inter = int(entry_intervalo.get().strip())
            if dur <= 0 or inter < 50:
                popup_error("Valores invalidos", "Duracion > 0 e intervalo > 50ms.")
                return
            pantalla_telemetria(var_sensor.get(), dur, inter)
        except ValueError:
            popup_error("Error", "Ingrese numeros validos.")

    separador(frame)
    boton_moderno("Iniciar Muestreo", ACCENT_A, validar_e_iniciar, frame)
    boton_moderno("Volver", TEXT_HINT, menu_principal, frame)

# Modulo de telemetria en tiempo real
def pantalla_telemetria(tipo_sensor, duracion_seg, intervalo_ms):
    global leyendo_datos
    limpiar()
    leyendo_datos = True
    tiempo_inicio = time.time()

    hdr = tk.Frame(frame, bg=ACCENT_A); hdr.pack(fill="x")
    tk.Label(hdr, text=f"  MUESTREO EN CURSO ({duracion_seg}s)", font=("Courier New", 14, "bold"), bg=ACCENT_A, fg="white").pack(pady=10)

    panel = tk.Frame(frame, bg=BG_INPUT, bd=2, relief="groove"); panel.pack(fill="both", expand=True, padx=30, pady=10)
    lbl_tiempo = tk.Label(panel, text="Tiempo Restante: -- s", font=("Courier New", 16, "bold"), bg=BG_INPUT, fg=ACCENT_W)
    lbl_tiempo.pack(pady=10)

    lbl_pitch = tk.Label(panel, text="", font=("Courier New", 20, "bold"), bg=BG_INPUT, fg=ACCENT_B)
    lbl_roll = tk.Label(panel, text="", font=("Courier New", 20, "bold"), bg=BG_INPUT, fg=ACCENT_B)
    lbl_clima = tk.Label(panel, text="", font=("Courier New", 14, "bold"), bg=BG_INPUT, fg=ACCENT_C)
    
    if tipo_sensor in ["2", "3"]:
        lbl_pitch.pack(pady=5); lbl_roll.pack(pady=5)
    if tipo_sensor in ["1", "3"]:
        lbl_clima.pack(pady=15)
    
    lbl_estado = tk.Label(frame, text="Conectando...", font=FONT_SMALL, bg=BG_CARD, fg=TEXT_SEC)
    lbl_estado.pack(pady=10)

    def pedir_datos():
        global leyendo_datos
        if not leyendo_datos: return
        
        tiempo_actual = time.time()
        tiempo_transcurrido = tiempo_actual - tiempo_inicio
        tiempo_restante = max(0, duracion_seg - tiempo_transcurrido)
        lbl_tiempo.config(text=f"Tiempo Restante: {tiempo_restante:.1f} s")

        if tiempo_transcurrido >= duracion_seg:
            leyendo_datos = False
            lbl_estado.config(text="Muestreo Finalizado.", fg=ACCENT_C)
            lbl_tiempo.config(text="MUESTREO COMPLETADO", fg=ACCENT_C)
            return

        try:
            req = urllib.request.urlopen(URL_ESP32, timeout=2)
            datos = json.loads(req.read())
            ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if tipo_sensor in ["1", "3"]:
                lbl_clima.config(text=f"AMB: {datos['temp_amb']:.1f}C | HUM: {datos['hum_amb']:.1f}%")
                guardar_en_db("dht22_data", "idu, temp_amb, hum_amb, timed", 
                              (id_usuario_actual, datos['temp_amb'], datos['hum_amb'], ahora))
                
            if tipo_sensor in ["2", "3"]:
                lbl_pitch.config(text=f"PITCH: {datos['pitch']:>6.1f}")
                lbl_roll.config(text=f"ROLL:  {datos['roll']:>6.1f}")
                guardar_en_db("mpu_data", "idu, ax, ay, az, gx, gy, gz, pitch, roll, temp_mpu, timed", 
                              (id_usuario_actual, datos['ax'], datos['ay'], datos['az'], datos['gx'], datos['gy'], datos['gz'], datos['pitch'], datos['roll'], datos['temp_mpu'], ahora))
            
            lbl_estado.config(text=f"Guardando a {intervalo_ms}ms...", fg=TEXT_PRI)
        except Exception as e:
            lbl_estado.config(text=f"Error: {str(e)[:40]}", fg=ACCENT_W)

        if leyendo_datos: root.after(intervalo_ms, pedir_datos)

    pedir_datos()
    boton_moderno("Detener y Volver", TEXT_HINT, menu_principal, frame)

# Modulo de Inteligencia Artificial
def pantalla_ia():
    limpiar()
    hdr = tk.Frame(frame, bg=ACCENT_B); hdr.pack(fill="x")
    tk.Label(hdr, text="  INFERENCIA IA (NODO 2)", font=("Courier New", 14, "bold"), bg=ACCENT_B, fg="white").pack(pady=10)
    
    lbl_status = tk.Label(frame, text="Esperando ejecucion...", font=("Courier New", 12), bg=BG_CARD, fg=TEXT_SEC)
    lbl_status.pack(pady=5)
    
    lbl_imagen = tk.Label(frame, bg=BG_DARK, text="[ CAMARA APAGADA ]", fg=TEXT_SEC, font=("Courier New", 12))
    lbl_imagen.pack(pady=5)
    
    panel = tk.Frame(frame, bg=BG_DARK, padx=20, pady=10); panel.pack(fill="x", padx=30)
    lbl_clase = tk.Label(panel, text="CLASE: ---", font=("Courier New", 20, "bold"), bg=BG_DARK, fg=ACCENT_C); lbl_clase.pack(pady=5)
    lbl_acc = tk.Label(panel, text="ACCURACY: 0.0%", font=("Courier New", 16), bg=BG_DARK, fg=ACCENT_B); lbl_acc.pack(pady=5)

    def solicitar_inferencia():
        try:
            lbl_status.config(text="Procesando en Raspi...", fg=TEXT_PRI); root.update()
            req = urllib.request.urlopen(URL_RASPI5, timeout=8)
            res = json.loads(req.read())
            
            lbl_clase.config(text=f"CLASE: {res['clase']}")
            lbl_acc.config(text=f"ACCURACY: {res['accuracy']*100:.2f}%")
            
            if "imagen_b64" in res:
                img_data = base64.b64decode(res["imagen_b64"])
                img = Image.open(io.BytesIO(img_data))
                img = img.resize((320, 240), Image.Resampling.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)
                lbl_imagen.config(image=img_tk, text="")
                lbl_imagen.image = img_tk 
            
            ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            guardar_en_db("ai_inference", "idu, clase_detectada, accuracy, timed", (id_usuario_actual, res['clase'], res['accuracy'], ahora))
            lbl_status.config(text="Inferencia y foto guardadas", fg=ACCENT_C)
        except Exception as e:
            lbl_status.config(text=f"Error Raspi: {str(e)[:40]}", fg=ACCENT_W)

    boton_moderno("Ejecutar Deteccion", ACCENT_B, solicitar_inferencia, frame)
    boton_moderno("Volver", TEXT_SEC, menu_principal, frame)

# Modulo CRUD
def menu_base_datos():
    global leyendo_datos; leyendo_datos = False; limpiar()
    hdr = tk.Frame(frame, bg=ACCENT_C); hdr.pack(fill="x")
    tk.Label(hdr, text="  GESTION CRUD DE HISTORICOS", font=("Courier New", 14, "bold"), bg=ACCENT_C, fg="white").pack(pady=10)
    
    ops = [
        ("Leer Registro", ACCENT_B, leer_registro),
        ("Editar Clima o MPU", ACCENT_A, editar_registro),
        ("Borrar un Registro", ACCENT_W, borrar_registro_id),
        ("VACIAR HISTORICO", "#FF3333", vaciar_historico)
    ]
    
    for texto, col, cmd in ops: boton_moderno(texto, col, cmd, frame)
    separador(frame, pady=5)
    boton_moderno("Volver al menu", TEXT_HINT, menu_principal, frame)

# Logica CRUD
def leer_registro():
    tabla = popup_input("Leer", "Tabla (dht22_data, mpu_data o ai_inference):", "str", ACCENT_B)
    if not tabla or tabla not in ["dht22_data", "mpu_data", "ai_inference"]: return
    id_reg = popup_input("Leer", f"ID en {tabla}:", "int", ACCENT_B)
    if not id_reg: return
    try:
        conexion = mysql.connector.connect(**config)
        cursor   = conexion.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {tabla} WHERE id = %s", (id_reg,))
        reg = cursor.fetchone()
        if not reg: popup_error("No encontrado", "ID inexistente."); return
        if tabla == "dht22_data": 
            info = f"ID: {reg['id']} | OP-{reg['idu']}\nFecha: {reg['timed']}\nAmb: {reg['temp_amb']}C\nHum: {reg['hum_amb']}%"
        elif tabla == "mpu_data":
            info = f"ID: {reg['id']} | OP-{reg['idu']}\nFecha: {reg['timed']}\nPitch: {reg['pitch']:.2f}\nRoll: {reg['roll']:.2f}"
        else:
            info = f"ID: {reg['id']} | OP-{reg['idu']}\nFecha: {reg['timed']}\nClase: {reg['clase_detectada']}\nAcc: {reg['accuracy']*100:.1f}%"
        popup_info(f"Detalle {tabla}", info)
        cursor.close(); conexion.close()
    except Exception as e: popup_error("Error DB", str(e))

def editar_registro():
    tabla = popup_input("Editar", "Tabla (dht22_data o mpu_data):", "str", ACCENT_A)
    if not tabla or tabla not in ["dht22_data", "mpu_data"]: return
    id_reg = popup_input("Editar", f"ID en {tabla}:", "int", ACCENT_A)
    if not id_reg: return
    try:
        conexion = mysql.connector.connect(**config)
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {tabla} WHERE id = %s", (id_reg,))
        if not cursor.fetchone():
            popup_error("Error", "ID no existe."); cursor.close(); conexion.close(); return
        if tabla == "dht22_data":
            t = popup_input("Editar", "Temp (C):", "float", ACCENT_A)
            h = popup_input("Editar", "Hum (%):", "float", ACCENT_A)
            if t is not None and h is not None:
                cursor.execute("UPDATE dht22_data SET temp_amb=%s, hum_amb=%s WHERE id=%s", (t, h, id_reg))
        elif tabla == "mpu_data":
            p = popup_input("Editar", "Pitch:", "float", ACCENT_A)
            r = popup_input("Editar", "Roll:", "float", ACCENT_A)
            if p is not None and r is not None:
                cursor.execute("UPDATE mpu_data SET pitch=%s, roll=%s WHERE id=%s", (p, r, id_reg))
        conexion.commit()
        popup_ok("Exito", "Registro actualizado.")
        cursor.close(); conexion.close()
    except Exception as e: popup_error("Error DB", str(e))

def borrar_registro_id():
    tabla = popup_input("Borrar", "Tabla:", "str", ACCENT_W)
    if not tabla or tabla not in ["dht22_data", "mpu_data", "ai_inference"]: return
    id_reg = popup_input("Borrar", "ID:", "int", ACCENT_W)
    if not id_reg: return
    if popup_yesno("Confirmar", f"Borrar ID {id_reg} de {tabla}?", ACCENT_W):
        try:
            conexion = mysql.connector.connect(**config)
            cursor = conexion.cursor()
            cursor.execute(f"DELETE FROM {tabla} WHERE id = %s", (id_reg,))
            conexion.commit()
            if cursor.rowcount > 0: popup_ok("Borrado", "Registro eliminado.")
            else: popup_error("Error", "ID no existe.")
            cursor.close(); conexion.close()
        except Exception as e: popup_error("Error DB", str(e))

def vaciar_historico():
    if popup_yesno("PELIGRO", "Borrar TODO el historico?", "#FF3333"):
        try:
            conexion = mysql.connector.connect(**config)
            cursor = conexion.cursor()
            for t in ["dht22_data", "mpu_data", "ai_inference"]: cursor.execute(f"DELETE FROM {t}")
            conexion.commit()
            popup_ok("Limpio", "Tablas vaciadas.")
            cursor.close(); conexion.close()
        except Exception as e: popup_error("Error DB", str(e))

# Inicio
login_screen()
root.mainloop()
