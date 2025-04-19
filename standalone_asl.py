import cv2
from cvzone.HandTrackingModule import HandDetector
import numpy as np
import math
import tensorflow as tf
import os

# Paramètres
CONFIDENCE_THRESHOLD = 0.6  # Seuil de confiance (60%)
DETECTION_TIME = 2.0  # Temps de détection en secondes
LETTER_HOLD_FRAMES = int(DETECTION_TIME * 3)  # 30 FPS approximatif

# Charger le modèle
model = tf.keras.models.load_model('sign_language_model.h5')

# Charger les catégories
with open('categories.txt', 'r') as f:
    labels = [line.strip() for line in f]

# Initialisation de la vidéo et du détecteur de main
cap = cv2.VideoCapture(0)
detector = HandDetector(maxHands=1)
offset = 20
imgSize = 300

# Variables pour la concaténation et la détection
text = []  # Liste des lettres détectées
current_letter = None
last_letter = None
letter_count = 0  # Compteur pour la même lettre
last_added_letter = None  # Dernière lettre ajoutée au texte
auto_detection = True  # Mode de détection automatique activé par défaut

# Fonction pour dessiner le texte actuel
def draw_text_box(img, text_list):
    # Créer une boîte pour afficher le texte
    text_str = ''.join(text_list)
    box_height = 60
    cv2.rectangle(img, (0, 0), (img.shape[1], box_height), (50, 50, 50), cv2.FILLED)
    
    # Dessiner le texte
    font_scale = 1.0
    if len(text_str) > 15:  # Réduire la taille si le texte est long
        font_scale = 0.7
    
    cv2.putText(img, text_str, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 2)
    
    # Instructions
    instructions = "Espace: ajouter espace | Retour: effacer dernier | C: effacer tout | A: mode auto"
    cv2.putText(img, instructions, (10, img.shape[0]-10), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
    
    # Status Auto-détection
    auto_text = f"Auto-detection: {'ON' if auto_detection else 'OFF'}"
    cv2.putText(img, auto_text, (img.shape[1]-200, img.shape[0]-10), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0) if auto_detection else (0, 0, 255), 2)

# Fonction pour dessiner la barre de progression
def draw_progress_bar(img, progress):
    bar_width = 200
    bar_height = 15
    start_x = (img.shape[1] - bar_width) // 2
    start_y = img.shape[0] - 40
    
    # Fond de la barre
    cv2.rectangle(img, (start_x, start_y), (start_x + bar_width, start_y + bar_height), (100, 100, 100), cv2.FILLED)
    
    # Progression
    progress_width = int(bar_width * progress)
    if progress_width > 0:
        cv2.rectangle(img, (start_x, start_y), (start_x + progress_width, start_y + bar_height), (0, 255, 0), cv2.FILLED)
    
    # Cadre
    cv2.rectangle(img, (start_x, start_y), (start_x + bar_width, start_y + bar_height), (255, 255, 255), 1)

# Boucle principale
while True:
    success, img = cap.read()
    if not success:
        break
        
    imgOutput = img.copy()
    hands, img = detector.findHands(img)
    
    # Dessiner la boîte de texte
    draw_text_box(imgOutput, text)
    
    if hands:
        hand = hands[0]
        x, y, w, h = hand['bbox']
        imgWhite = np.ones((imgSize, imgSize, 3), np.uint8) * 255
        
        try:
            # Découper et traiter l'image de la main
            imgCrop = img[y - offset:y + h + offset, x - offset:x + w + offset]
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
            
            # Préparation pour la prédiction
            img_array = cv2.cvtColor(imgWhite, cv2.COLOR_BGR2RGB)
            img_array = img_array / 255.0
            img_array = np.expand_dims(img_array, axis=0)
            
            # Prédiction
            prediction = model.predict(img_array)
            index = np.argmax(prediction[0])
            confidence = prediction[0][index]
            
            # Mettre à jour la lettre actuelle si la confiance est suffisante
            if confidence >= CONFIDENCE_THRESHOLD:
                current_letter = labels[index]
                
                # Gérer la détection continue
                if current_letter == last_letter:
                    letter_count += 1
                    
                    # En mode auto, ajouter automatiquement la lettre si maintenue assez longtemps
                    if auto_detection and letter_count >= LETTER_HOLD_FRAMES:
                        text.append(current_letter)
                        last_added_letter = current_letter
                        letter_count = 0  # Réinitialiser le compteur après l'ajout
                else:
                    last_letter = current_letter
                    letter_count = 0
                
                # Calculer la progression pour la barre
                if auto_detection:
                    progress = min(1.0, letter_count / LETTER_HOLD_FRAMES)
                    draw_progress_bar(imgOutput, progress)
                
                # Texte à afficher
                display_text = f'{current_letter} ({confidence:.2f})'
            else:
                display_text = f'? ({confidence:.2f})'
                letter_count = 0
            
            # Dessiner les résultats sur l'image
            cv2.rectangle(imgOutput, (x - offset, y - offset-50),
                        (x - offset+150, y - offset-50+50), (255, 0, 255), cv2.FILLED)
            cv2.putText(imgOutput, display_text, 
                        (x, y -26), cv2.FONT_HERSHEY_COMPLEX, 1.0, (255, 255, 255), 2)
            cv2.rectangle(imgOutput, (x-offset, y-offset),
                        (x + w+offset, y + h+offset), (255, 0, 255), 4)
            
            # Afficher l'image prétraitée
            cv2.imshow("Image prétraitée", imgWhite)
            
        except Exception as e:
            print(f"Erreur lors du traitement: {e}")
    else:
        # Pas de main détectée
        current_letter = None
        letter_count = 0
    
    cv2.imshow("ASL Reconnaissance", imgOutput)
    key = cv2.waitKey(1)
    
    # Actions sur touches
    if key == ord('q'):  # Quitter
        break
    elif key == ord(' '):  # Espace
        text.append(' ')
        last_added_letter = None
    elif key == 8:  # Retour arrière (effacer dernier caractère)
        if text:
            text.pop()
            if text and text[-1] == ' ':
                last_added_letter = None
            elif text:
                last_added_letter = text[-1]
            else:
                last_added_letter = None
    elif key == ord('c'):  # Effacer tout
        text = []
        last_added_letter = None
    elif key == ord('a'):  # Activer/désactiver auto-détection
        auto_detection = not auto_detection
    elif key == 13:  # Entrée (ajouter manuellement la lettre actuelle)
        if current_letter:
            text.append(current_letter)
            last_added_letter = current_letter

cap.release()
cv2.destroyAllWindows() 