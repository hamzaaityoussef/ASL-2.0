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

# Variables globales pour stocker les lettres détectées
detected_letters = []
current_prediction = None  # Pour stocker la prédiction actuelle

@app.route('/')
def index():
    return render_template('index.html')

def generate_frames():
    global current_prediction
    cap = cv2.VideoCapture(0)
    while True:
        success, img = cap.read()
        if not success:
            break
        
        imgOutput = img.copy()
        hands, img = detector.findHands(img)
        
        if hands:
            hand = hands[0]
            x, y, w, h = hand['bbox']
            imgWhite = np.ones((imgSize, imgSize, 3), np.uint8) * 255
            
            try:
                imgCrop = img[y - offset:y + h + offset, x - offset:x + w + offset]
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
                
                # Prepare image for prediction
                img_array = cv2.cvtColor(imgWhite, cv2.COLOR_BGR2RGB)
                img_array = img_array / 255.0
                img_array = np.expand_dims(img_array, axis=0)
                
                # Make prediction
                prediction = model.predict(img_array)
                index = np.argmax(prediction[0])
                confidence = prediction[0][index]
                predicted_letter = CLASSES[index]
                
                # Store current prediction
                current_prediction = predicted_letter
                
                # Draw prediction results
                cv2.rectangle(imgOutput, (x - offset, y - offset-50),
                            (x - offset+90, y - offset-50+50), (255, 0, 255), cv2.FILLED)
                cv2.putText(imgOutput, f'{predicted_letter} ({confidence:.2f})', 
                            (x, y -26), cv2.FONT_HERSHEY_COMPLEX, 1.0, (255, 255, 255), 2)
                cv2.rectangle(imgOutput, (x-offset, y-offset),
                            (x + w+offset, y + h+offset), (255, 0, 255), 4)
                
            except Exception as e:
                print(f"Error processing frame: {e}")
        else:
            # No hand detected
            current_prediction = None
        
        # Encode the frame in JPEG format
        ret, buffer = cv2.imencode('.jpg', imgOutput)
        frame = buffer.tobytes()
        
        # Yield the frame in the byte format
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/add_letter', methods=['POST'])
def add_letter():
    global current_prediction, detected_letters
    data = request.json
    letter = data.get('letter')
    
    if letter == 'current' and current_prediction:
        detected_letters.append(current_prediction)
    elif letter != 'current':  # Pour les espaces ou autres caractères manuels
        detected_letters.append(letter)
    else:
        return jsonify({'success': False, 'error': 'Aucune lettre détectée'})
        
    return jsonify({'success': True, 'text': ''.join(detected_letters)})

@app.route('/clear_text', methods=['POST'])
def clear_text():
    global detected_letters
    detected_letters = []
    return jsonify({'success': True})

@app.route('/get_current_prediction', methods=['GET'])
def get_current_prediction():
    global current_prediction
    return jsonify({'letter': current_prediction if current_prediction else ''})

if __name__ == '__main__':
    app.run(debug=True)