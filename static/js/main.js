document.addEventListener('DOMContentLoaded', function() {
    // Éléments du DOM
    const uploadForm = document.getElementById('upload-form');
    const imageUpload = document.getElementById('image-upload');
    const previewImage = document.getElementById('preview-image');
    const predictedLetter = document.getElementById('predicted-letter');
    const confidence = document.getElementById('confidence');
    const predictionsList = document.getElementById('predictions-list');
    const loading = document.getElementById('loading');
    
    // Éléments webcam
    const video = document.getElementById('webcam-video');
    const canvas = document.getElementById('webcam-canvas');
    const captureBtn = document.getElementById('capture-btn');
    const startWebcamBtn = document.getElementById('start-webcam-btn');
    
    let stream = null;
    
    // Prévisualisation de l'image téléchargée
    imageUpload.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImage.src = e.target.result;
                previewImage.classList.remove('d-none');
            }
            reader.readAsDataURL(file);
        }
    });
    
    // Soumission du formulaire d'upload
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const file = imageUpload.files[0];
        if (!file) {
            alert('Veuillez sélectionner une image');
            return;
        }
        
        const formData = new FormData();
        formData.append('image', file);
        
        // Afficher le chargement
        loading.style.display = 'block';
        predictedLetter.textContent = '';
        confidence.textContent = '';
        predictionsList.innerHTML = '';
        
        // Envoyer l'image au serveur
        fetch('/predict', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            displayPrediction(data);
        })
        .catch(error => {
            console.error('Erreur:', error);
            alert('Une erreur est survenue lors de l\'analyse');
        })
        .finally(() => {
            loading.style.display = 'none';
        });
    });
    
    // Démarrer la webcam
    startWebcamBtn.addEventListener('click', function() {
        if (stream) {
            stopWebcam();
            startWebcamBtn.textContent = 'Démarrer la webcam';
        } else {
            navigator.mediaDevices.getUserMedia({ video: true })
                .then(function(s) {
                    stream = s;
                    video.srcObject = stream;
                    startWebcamBtn.textContent = 'Arrêter la webcam';
                })
                .catch(function(err) {
                    console.error('Erreur d\'accès à la webcam:', err);
                    alert('Impossible d\'accéder à la webcam');
                });
        }
    });
    
    // Arrêter la webcam
    function stopWebcam() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
            video.srcObject = null;
        }
    }
    
    // Capturer une image de la webcam
    captureBtn.addEventListener('click', function() {
        if (!stream) {
            alert('Veuillez d\'abord démarrer la webcam');
            return;
        }
        
        const context = canvas.getContext('2d');
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        const imageData = canvas.toDataURL('image/png');
        
        // Afficher le chargement
        loading.style.display = 'block';
        predictedLetter.textContent = '';
        confidence.textContent = '';
        predictionsList.innerHTML = '';
        
        // Envoyer l'image au serveur
        fetch('/webcam_predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ image: imageData })
        })
        .then(response => response.json())
        .then(data => {
            displayPrediction(data);
        })
        .catch(error => {
            console.error('Erreur:', error);
            alert('Une erreur est survenue lors de l\'analyse');
        })
        .finally(() => {
            loading.style.display = 'none';
        });
    });
    
    // Afficher les résultats de prédiction
    function displayPrediction(data) {
        if (data.error) {
            alert('Erreur: ' + data.error);
            return;
        }
        
        // Afficher la lettre prédite
        predictedLetter.textContent = data.predicted_class;
        
        // Afficher la confiance
        const confidencePercent = (data.confidence * 100).toFixed(2);
        confidence.textContent = `Confiance: ${confidencePercent}%`;
        
        // Afficher les meilleures prédictions
        predictionsList.innerHTML = '';
        data.top_predictions.forEach(pred => {
            const percent = (pred.confidence * 100).toFixed(2);
            const li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center';
            li.innerHTML = `
                ${pred.class}
                <span class="badge bg-primary rounded-pill">${percent}%</span>
            `;
            predictionsList.appendChild(li);
        });
    }
    
    // Nettoyer la webcam quand on quitte la page
    window.addEventListener('beforeunload', stopWebcam);
});