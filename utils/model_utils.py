import numpy as np
import cv2
import base64
from PIL import Image
import io
from tensorflow.keras.preprocessing import image


def preprocess_image(file, from_webcam=False):
    """Prétraite l'image pour la prédiction"""
    if from_webcam:
        # Traiter l'image base64 de la webcam
        encoded_data = file.split(',')[1]
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convertir BGR en RGB
    else:
        # Traiter l'image téléchargée
        img = Image.open(file).convert('RGB')  # Assurer que c'est RGB
        img = np.array(img)
    
    # Redimensionner l'image à la taille attendue par le modèle (300x300)
    img = cv2.resize(img, (300, 300))
    
    # Normaliser l'image
    img = img / 255.0
    
    # Ajouter la dimension du batch
    img = np.expand_dims(img, axis=0)
    
    # Vérifier la forme
    print(f"Forme de l'image après prétraitement: {img.shape}")
    
    return img


def get_prediction(model, img, classes):
    """Obtient la prédiction du modèle"""
    # Vérifier et corriger la forme si nécessaire
    if len(img.shape) == 2 or (len(img.shape) == 3 and img.shape[0] == 1 and img.shape[1] == 270000):
        # L'image est aplatie, la remettre en forme
        print("L'image est aplatie, remise en forme...")
        img = img.reshape(1, 300, 300, 3)
    
    # Afficher la forme pour le débogage
    print(f"Forme de l'image envoyée au modèle: {img.shape}")
    
    # Faire la prédiction
    pred = model.predict(img)
    
    # Obtenir la classe prédite
    predicted_class_index = np.argmax(pred[0])
    predicted_class = classes[predicted_class_index]
    confidence = float(pred[0][predicted_class_index])
    
    # Obtenir les 3 meilleures prédictions
    top_indices = pred[0].argsort()[-3:][::-1]
    top_predictions = [
        {"class": classes[i], "confidence": float(pred[0][i])}
        for i in top_indices
    ]
    
    return {
        "predicted_class": predicted_class,
        "confidence": confidence,
        "top_predictions": top_predictions
    }







