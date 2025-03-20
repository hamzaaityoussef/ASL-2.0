from flask import Flask, render_template, request, jsonify
import os
import numpy as np
from tensorflow.keras.models import load_model
from utils.model_utils import preprocess_image, get_prediction

app = Flask(__name__)

# Charger le modèle au démarrage
MODEL_PATH = 'sign_language_model.h5'
model = load_model(MODEL_PATH)

# Définir les classes ASL (à adapter selon votre modèle)
# Définir les classes ASL (26 lettres, mais J et Z impliquent du mouvement)
CLASSES = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L', 
           'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'Aucune image trouvée'})
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Aucun fichier sélectionné'})
    
    try:
        # Prétraiter l'image
        img = preprocess_image(file)
        
        # Vérifier la forme avant de passer au modèle
        print(f"Forme de l'image avant prédiction: {img.shape}")
        
        # Faire la prédiction
        prediction = get_prediction(model, img, CLASSES)
        
        return jsonify(prediction)
    
    except Exception as e:
        print(f"Erreur lors de la prédiction: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)})


@app.route('/webcam_predict', methods=['POST'])
def webcam_predict():
    try:
        # Récupérer les données d'image de la webcam (format base64)
        image_data = request.json.get('image')
        
        # Prétraiter l'image
        img = preprocess_image(image_data, from_webcam=True)
        
        # Faire la prédiction
        prediction = get_prediction(model, img, CLASSES)
        
        return jsonify(prediction)
    
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)