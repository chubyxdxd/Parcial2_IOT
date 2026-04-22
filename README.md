# Parcial2_IOT
repo del particial 2 IOT

# Sistema Mecatrónico IoT: Telemetría y Edge AI en Cascada

Este repositorio contiene el código fuente de un Sistema Distribuido de Internet de las Cosas (IoT) diseñado para la adquisición de datos de sensores en tiempo real y la clasificación de imágenes mediante Inteligencia Artificial en el borde (Edge AI). 

El proyecto integra hardware embebido, visión artificial, bases de datos relacionales y una interfaz gráfica de usuario (GUI) interactiva.

---

## Arquitectura del Sistema

El sistema está dividido en tres nodos principales que se comunican de forma asíncrona a través de una red Wi-Fi local mediante peticiones HTTP (API REST).

### Nodo 0: Centro de Control (PC / Servidor)
Actúa como el cerebro administrativo y la interfaz principal del usuario.
* **Tecnología:** Python, `Tkinter`, `mysql.connector`.
* **Función:** * Despliega un Dashboard interactivo (GUI) para los operadores.
  * Gestiona el sistema de inicio de sesión de usuarios.
  * Realiza peticiones asíncronas a los nodos remotos para recolectar datos.
  * Decodifica imágenes en formato Base64 enviadas por el nodo de IA para mostrarlas en pantalla.
  * Opera como un sistema CRUD (Crear, Leer, Actualizar, Borrar) conectándose a una base de datos MySQL para mantener el histórico de telemetría y detecciones.

### Nodo 1: Adquisición de Telemetría (ESP32)
Nodo sensorial de bajo consumo para la captura de datos físicos.
* **Tecnología:** ESP32, MicroPython, `socket`.
* **Hardware:** * Sensor DHT22 (Temperatura y Humedad ambiente) vía protocolo One-Wire.
  * Sensor MPU6050 (Acelerómetro y Giroscopio para Pitch/Roll) vía bus I2C.
* **Función:** Levanta un micro-servidor web que, al recibir una petición, lee los sensores físicos y devuelve un objeto JSON empaquetado con las variables cinemáticas y climáticas al Centro de Control.

### Nodo 2: Inferencia Edge AI (Raspberry Pi 5)
Nodo de procesamiento intensivo dedicado a la visión artificial descentralizada.
* **Tecnología:** Raspberry Pi 5, PyTorch, OpenCV (`cv2`), Flask, Torchvision.
* **Arquitectura de IA:** Utiliza una Inferencia en Cascada basada en redes neuronales residuales (`ResNet18`):
  1. **Detector de Presencia (Modelo 1):** Clasificación binaria rápida para determinar si existe un objeto frente a la cámara, optimizando el uso de recursos.
  2. **Clasificador de Materiales (Modelo 2):** Si se detecta un objeto, se activa una segunda red para clasificarlo en 5 categorías (biological, paper, glass, plastics, metal).
* **Hardware:** Cámara USB (Configurada con `cv2.CAP_V4L2` y buffer minimizado para reducir la latencia).
* **Función:** Funciona como un servidor web Flask en modo Headless. Captura un frame de video, ejecuta la inferencia matricial en cascada, comprime la fotografía resultante en Base64 y responde con un JSON que incluye la clasificación final, la precisión (accuracy) y la evidencia visual.

---

## Flujo de Operación

1. El operador inicia sesión en el Nodo 0 mediante la interfaz gráfica.
2. Desde el menú principal, selecciona la operación deseada (Muestreo de sensores, Inferencia IA o Gestión de Base de Datos).
3. **Flujo de Telemetría:** El Nodo 0 realiza peticiones periódicas (*polling*) al Nodo 1 (ESP32) durante el intervalo especificado. Los datos recibidos se muestran en pantalla y se almacenan en la base de datos MySQL.
4. **Flujo de Inteligencia Artificial:** El operador solicita una inferencia remotamente. El Nodo 2 (Raspberry Pi 5) captura una imagen, la procesa mediante la arquitectura en cascada y devuelve el resultado junto con la fotografía codificada. El Nodo 0 renderiza la imagen en la interfaz y registra el evento en la base de datos.

## Requisitos de Instalación

### Hardware
* Nodo 0: PC con sistema operativo Windows, Linux o macOS.
* Nodo 1: ESP32 con sensores DHT22 y MPU6050.
* Nodo 2: Raspberry Pi 5 con cámara USB.
* Red: Conectividad WLAN (Wi-Fi) para comunicación entre nodos.

### Dependencias de Software

**PC (Interfaz Gráfica):**
Requiere Python 3.10 o superior.
```bash
pip install mysql-connector-python pillow
```
Raspberry Pi 5 (Edge AI):

Requiere PyTorch y OpenCV. Se recomienda usar un entorno virtual.

```bash
pip install torch torchvision opencv-python pillow flask
```
## Estructura de la Base de Datos

El sistema utiliza un servidor MySQL con un esquema denominado `iot_telemetry`. A continuación se detallan las tablas y sus campos principales:

* **usuarios**: Almacena las credenciales para el control de acceso.
    * `id`: Identificador único (Primary Key, Auto-increment).
    * `nombre_usuario`: Nombre de cuenta del operador.
    * `password`: Contraseña cifrada o plana para validación.

* **dht22_data**: Registro histórico de variables climáticas.
    * `id`: Identificador de registro (Auto-increment).
    * `idu`: ID del usuario que realizó la captura (Foreign Key).
    * `temp_amb`: Temperatura ambiente capturada por el sensor.
    * `hum_amb`: Humedad relativa del entorno.
    * `timed`: Timestamp del momento de la inserción.

* **mpu_data**: Registro de telemetría cinemática y movimiento.
    * `id`: Identificador de registro (Auto-increment).
    * `idu`: ID del usuario vinculado.
    * `ax`, `ay`, `az`: Datos del acelerómetro en los tres ejes.
    * `gx`, `gy`, `gz`: Datos del giroscopio.
    * `pitch`, `roll`: Cálculo de inclinación y balanceo.
    * `temp_mpu`: Temperatura interna del sensor.
    * `timed`: Timestamp de la captura.

* **ai_inference**: Histórico de resultados del sistema de visión artificial.
    * `id`: Identificador de registro.
    * `idu`: ID del usuario que disparó la inferencia.
    * `clase_detectada`: Categoría identificada (Ej: metal, plástico, papel).
    * `accuracy`: Nivel de confianza del modelo (0.0 a 1.0).
    * `timed`: Fecha y hora de la detección.
    
## Instrucciones de Ejecución

Para poner en marcha el sistema distribuido, siga estos pasos en orden:

1. **Base de Datos y servidor** Active su servidor MySQL (XAMPP, LAMP o servicio independiente) y asegúrese de haber creado las tablas mencionadas en la sección de estructura. Verifique que las credenciales en `cliente.py` coincidan con su configuración local.
```bash
   streamlit run servidor.py
```

2. **Nodo ESP32** Cargue el script de MicroPython en el dispositivo esp.py. Al iniciar, el ESP32 se conectará a la red local; verifique en la consola serial la **dirección IP** asignada para configurarla posteriormente.

3. **Nodo Raspberry Pi** Asegúrese de que los archivos del modelo (`basura.pth`) estén en la misma carpeta que el script del servidor. Ejecute el siguiente comando para iniciar el servicio de IA:
```bash
   python3 raspi.py
```
4. **Nodo PC (Centro de Control)** Configure las direcciones IP correspondientes a los nodos anteriores (`URL_ESP32` y `URL_RASPI5`) dentro del archivo `cliente.py`. Una vez verificada la conexión a la base de datos, inicie la interfaz gráfica ejecutando:
```bash
   python3 cliente.py
   ```
