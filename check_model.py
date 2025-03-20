from tensorflow.keras.models import load_model

try:
    # Charger le modèle
    print("Chargement du modèle...")
    model = load_model('sign_language_model.h5')
    
    # Afficher le résumé
    print("\nArchitecture du modèle:")
    model.summary()
    
    # Afficher la forme d'entrée
    print("\nForme d'entrée attendue:", model.input_shape)
    print("Forme de sortie:", model.output_shape)
    
except Exception as e:
    print(f"Erreur: {e}")

print("\nAppuyez sur Entrée pour quitter...")
input()