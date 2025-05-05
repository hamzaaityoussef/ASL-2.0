from flask import Flask, render_template, request, jsonify, Response
import os
import numpy as np
from tensorflow.keras.models import load_model
import cv2
import math
from cvzone.HandTrackingModule import HandDetector

app = Flask(__name__)

# Charger le modèle au démarrage
MODEL_PATH = 'sign_language_model.h5'
model = load_model(MODEL_PATH)

# Charger les catégories
with open('categories.txt', 'r') as f:
    CLASSES = [line.strip() for line in f]

# Initialiser le détecteur de main
detector = HandDetector(maxHands=1)
offset = 20
imgSize = 300

# Variables globales pour le quiz
current_prediction = None
current_confidence = 0.0
CONFIDENCE_THRESHOLD = 0.6  # Seuil de confiance minimum (60%)
current_target_letter = None  # Lettre cible actuelle

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route('/songs')
def songs():
    return render_template('songs.html')

@app.route('/learn')
def learn():
    return render_template('learn.html')

# Route pour définir la lettre cible
@app.route('/set_target_letter', methods=['POST'])
def set_target_letter():
    global current_target_letter
    data = request.json
    current_target_letter = data.get('letter')
    return jsonify({'status': 'success', 'letter': current_target_letter})

# Route pour vérifier le signe
@app.route('/check_sign', methods=['GET'])
def check_sign():
    global current_prediction, current_confidence, current_target_letter
    
    if current_target_letter is None:
        return jsonify({
            'status': 'error',
            'message': 'No target letter set'
        })
    
    if current_prediction is None:
        return jsonify({
            'status': 'error',
            'message': 'No prediction available'
        })
    
    # Vérifier si la prédiction correspond à la lettre cible
    is_correct = (current_prediction == current_target_letter 
                 and current_confidence >= CONFIDENCE_THRESHOLD)
    
    return jsonify({
        'status': 'success',
        'is_correct': is_correct,
        'detected_letter': current_prediction,
        'confidence': current_confidence,
        'target_letter': current_target_letter
    })

def generate_frames():
    cap = cv2.VideoCapture(0)
    while True:
        success, img = cap.read()
        if not success:
            break
        else:
            hands, img = detector.findHands(img)
            if hands:
                hand = hands[0]
                x, y, w, h = hand['bbox']
                imgWhite = np.ones((imgSize, imgSize, 3), np.uint8) * 255
                imgCrop = img[y - offset:y + h + offset, x - offset:x + w + offset]
                
                try:
                    imgCropShape = imgCrop.shape
                    aspectRatio = h / w
                    if aspectRatio > 1:
                        k = imgSize / h
                        wCal = math.ceil(k * w)
                        imgResize = cv2.resize(imgCrop, (wCal, imgSize))
                        wGap = math.ceil((imgSize - wCal) / 2)
                        imgWhite[:, wGap:wCal + wGap] = imgResize
                    else:
                        k = imgSize / w
                        hCal = math.ceil(k * h)
                        imgResize = cv2.resize(imgCrop, (imgSize, hCal))
                        hGap = math.ceil((imgSize - hCal) / 2)
                        imgWhite[hGap:hCal + hGap, :] = imgResize
                    
                    # Préparer l'image pour la prédiction
                    img_array = cv2.cvtColor(imgWhite, cv2.COLOR_BGR2RGB)
                    img_array = img_array / 255.0
                    img_array = np.expand_dims(img_array, axis=0)
                    
                    # Faire la prédiction
                    prediction = model.predict(img_array)
                    index = np.argmax(prediction[0])
                    confidence = prediction[0][index]
                    
                    # Mettre à jour les variables globales
                    global current_prediction, current_confidence
                    current_prediction = CLASSES[index]
                    current_confidence = float(confidence)
                    
                    # Dessiner la prédiction sur l'image
                    cv2.rectangle(img, (x - offset, y - offset-50),
                                (x - offset+90, y - offset-50+50), (255, 0, 255), cv2.FILLED)
                    cv2.putText(img, f'{CLASSES[index]}', 
                                (x, y -26), cv2.FONT_HERSHEY_COMPLEX, 1.0, (255, 255, 255), 2)
                    cv2.rectangle(img, (x-offset, y-offset),
                                (x + w+offset, y + h+offset), (255, 0, 255), 4)
                    
                except Exception as e:
                    print(f"Error processing frame: {e}")
            
            ret, buffer = cv2.imencode('.jpg', img)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_current_prediction')
def get_current_prediction():
    return jsonify({
        'letter': current_prediction,
        'confidence': current_confidence
    })

if __name__ == '__main__':
    app.run(debug=True)