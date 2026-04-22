### CÓDIGO MICROPYTHON
import machine
from machine import Pin
import dht
import time
import math
import struct
import network
import socket
import json

# --- Configuración Hardware ---
i2c = machine.I2C(0, sda=Pin(21), scl=Pin(22), freq=400_000)
sensor_dht = dht.DHT22(Pin(4))
MPU_ADDR = 0x68

def iniciar_mpu():
    try:
        i2c.writeto_mem(MPU_ADDR, 0x6B, b'\x00') # Despertar
        print("MPU6050 listo.")
    except:
        print("Error: MPU6050 no detectado.")

def obtener_lectura():
    # Lectura MPU6050
    raw = i2c.readfrom_mem(MPU_ADDR, 0x3B, 14)
    v = struct.unpack(">7h", raw)
    ax, ay, az = v[0]/16384.0, v[1]/16384.0, v[2]/16384.0
    temp_mpu = (v[3]/340.0) + 36.53
    gx, gy, gz = v[4]/131.0, v[5]/131.0, v[6]/131.0
    
    pitch = math.atan2(ay, math.sqrt(ax*ax + az*az)) * 180 / math.pi
    roll = math.atan2(-ax, az) * 180 / math.pi
    
    # Lectura DHT22
    t_amb, h_amb = 0.0, 0.0
    try:
        sensor_dht.measure()
        t_amb, h_amb = sensor_dht.temperature(), sensor_dht.humidity()
    except: pass

    return {
        "ax": ax, "ay": ay, "az": az, "gx": gx, "gy": gy, "gz": gz,
        "pitch": pitch, "roll": roll, "temp_mpu": temp_mpu,
        "temp_amb": t_amb, "hum_amb": h_amb
    }

def conectar_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False); time.sleep(0.5); wlan.active(True)
    wlan.connect(ssid, password)
    intentos = 0
    while not wlan.isconnected() and intentos < 20:
        time.sleep(0.5); intentos += 1
    if wlan.isconnected():
        print("Conectado. IP:", wlan.ifconfig()[0])
        return wlan.ifconfig()[0]
    machine.reset()

# --- Main ---

iniciar_mpu()
ip = conectar_wifi("Familia Cabrera G", "Moiquito980207")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80)); s.listen(5)

while True:
    try:
        conn, addr = s.accept()
        request = conn.recv(1024)
        respuesta = json.dumps(obtener_lectura())
        conn.send('HTTP/1.1 200 OK\nContent-Type: application/json\nConnection: close\n\n' + respuesta)
        conn.close()
    except Exception as e:
        print("Error:", e)


