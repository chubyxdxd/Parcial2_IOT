from flask import Flask, jsonify
import cv2
import torch
import torch.nn.functional as F
import torchvision.transforms as transforms
from PIL import Image
import torchvision.models as models
import base64

app = Flask(__name__)

# Cargar modelo y configurar arquitectura
print("Cargando modelo...")
state_dict = torch.load('basura.pth', map_location='cpu')
modelo = models.resnet18(weights=None)

if any("fc.1.weight" in k for k in state_dict.keys()):
    modelo.fc = torch.nn.Sequential(
        torch.nn.Dropout(p=0.5),
        torch.nn.Linear(modelo.fc.in_features, 5)
    )
else:
    modelo.fc = torch.nn.Linear(modelo.fc.in_features, 5)

modelo.load_state_dict(state_dict)
modelo.eval()

CLASES = ['biological', 'paper', 'glass', 'plastics', 'metal']

# Transformaciones de imagen
transformacion = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

# Endpoint de inferencia
@app.route('/', methods=['GET'])
def realizar_inferencia():
    # Captura de imagen
    cap = cv2.VideoCapture(2, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        return jsonify({"error": "No se pudo abrir la cámara"}), 500

    for _ in range(5):
        ret, frame = cap.read()
    cap.release()

    if not ret:
        return jsonify({"error": "Fallo al capturar imagen"}), 500

    # Preprocesamiento
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)
    tensor_entrada = transformacion(img_pil).unsqueeze(0)

    # Inferencia de IA
    with torch.no_grad():
        salida = modelo(tensor_entrada)
        probs = F.softmax(salida[0], dim=0)
        prob_max, indice = torch.max(probs, 0)
        clase = CLASES[indice.item()]
        confianza = float(prob_max.item())

    # Codificación de imagen a base64
    _, buffer = cv2.imencode('.jpg', frame)
    imagen_b64 = base64.b64encode(buffer).decode('utf-8')

    return jsonify({
        "clase": clase,
        "accuracy": confianza,
        "imagen_b64": imagen_b64
    })

# Ejecución del servidor
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
