document.addEventListener('DOMContentLoaded', function() {
    // Configuration
    const YOUTUBE_API_KEY = 'AIzaSyAlA3c894fEz5ABvQnrir1h1lQ9q0_1OPs'; // Remplacez par votre clé
    const PLAYLIST_ID = 'PLQK2XiUY9C2jQg-OhyWUKJfL9D5Ze2o1W'; // ID de la playlist
    const VIDEOS_PER_PAGE = 12;
    
    // Éléments DOM
    const videosGrid = document.getElementById('videosGrid');
    const videoPlayer = document.getElementById('youtubePlayer');
    const searchInput = document.getElementById('searchInput');
    const loadMoreBtn = document.getElementById('loadMoreButton');
    const loadingIndicator = document.getElementById('loadingIndicator');
    
    // Variables d'état
    let nextPageToken = '';
    let isLoading = false;

    // Initialisation
    loadPlaylistVideos();

    // Charger les vidéos de la playlist
    async function loadPlaylistVideos(pageToken = '') {
        if (isLoading) return;
        
        isLoading = true;
        loadingIndicator.style.display = 'block';
        loadMoreBtn.style.display = 'none';
        
        try {
            let url = `https://www.googleapis.com/youtube/v3/playlistItems?` +
                     `part=snippet&` +
                     `playlistId=${PLAYLIST_ID}&` +
                     `maxResults=${VIDEOS_PER_PAGE}&` +
                     `key=${YOUTUBE_API_KEY}`;
            
            if (pageToken) url += `&pageToken=${pageToken}`;
            
            const response = await fetch(url);
            const data = await response.json();
            
            nextPageToken = data.nextPageToken || '';
            
            if (data.items?.length > 0) {
                const videoIds = data.items.map(item => item.snippet.resourceId.videoId).filter(Boolean);
                
                if (videoIds.length > 0) {
                    const detailsUrl = `https://www.googleapis.com/youtube/v3/videos?` +
                                     `part=snippet,contentDetails&` +
                                     `id=${videoIds.join(',')}&` +
                                     `key=${YOUTUBE_API_KEY}`;
                    
                    const detailsResponse = await fetch(detailsUrl);
                    const detailsData = await detailsResponse.json();
                    
                    displayVideos(detailsData.items);
                }
            } else {
                videosGrid.innerHTML = '<p class="no-results">Aucune vidéo trouvée dans la playlist.</p>';
            }
            
            if (nextPageToken) {
                loadMoreBtn.style.display = 'block';
            }
        } catch (error) {
            console.error("Erreur API YouTube:", error);
            videosGrid.innerHTML = `
                <div class="error">
                    <p>Erreur de chargement de la playlist</p>
                    <button onclick="window.location.reload()">Réessayer</button>
                </div>
            `;
        } finally {
            isLoading = false;
            loadingIndicator.style.display = 'none';
        }
    }

    // Afficher les vidéos (même fonction que précédemment)
    function displayVideos(videos) {
        videos.forEach(video => {
            const card = document.createElement('div');
            card.className = 'video-card';
            
            const title = video.snippet?.title || "Titre inconnu";
            const thumbnail = video.snippet?.thumbnails?.medium?.url || "";
            const date = video.snippet?.publishedAt ? 
                new Date(video.snippet.publishedAt).toLocaleDateString() : 
                "Date inconnue";
            const duration = formatDuration(video.contentDetails?.duration);
            
            card.innerHTML = `
                <div class="thumbnail" onclick="playVideo('${video.id}')">
                    <img src="${thumbnail}" alt="${title}" onerror="this.src='https://i.imgur.com/6M9fYu3.png'">
                    <div class="play-icon"></div>
                    <div class="duration">${duration}</div>
                </div>
                <div class="video-info">
                    <h3>${title}</h3>
                    <p>${date}</p>
                </div>
            `;
            
            videosGrid.appendChild(card);
        });
    }

    // Formatage de la durée (identique)
    function formatDuration(duration) {
        if (!duration) return '00:00';
        
        const match = duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
        const hours = (match[1] ? parseInt(match[1]) : 0);
        const minutes = (match[2] ? parseInt(match[2]) : 0);
        const seconds = (match[3] ? parseInt(match[3]) : 0);
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
    }

    // Lecture vidéo (identique)
    window.playVideo = function(videoId) {
        document.getElementById('videoPlayerContainer').style.display = 'flex';
        videoPlayer.src = `https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0`;
    };

    // Fermer le lecteur (identique)
    document.getElementById('closePlayer').addEventListener('click', function() {
        document.getElementById('videoPlayerContainer').style.display = 'none';
        videoPlayer.src = '';
    });

    // Charger plus de vidéos
    loadMoreBtn.addEventListener('click', function() {
        loadPlaylistVideos(nextPageToken);
    });

    // Recherche dans la playlist
    document.getElementById('searchButton').addEventListener('click', function() {
        const query = searchInput.value.trim();
        if (query) {
            searchInPlaylist(query);
        }
    });

    async function searchInPlaylist(query) {
        try {
            // On recharge toute la playlist et on filtre côté client
            // (L'API YouTube ne permet pas de rechercher directement dans une playlist)
            loadingIndicator.style.display = 'block';
            videosGrid.innerHTML = '';
            
            let allVideos = [];
            let token = '';
            
            // Récupérer toutes les vidéos de la playlist
            do {
                const url = `https://www.googleapis.com/youtube/v3/playlistItems?` +
                            `part=snippet&` +
                            `playlistId=${PLAYLIST_ID}&` +
                            `maxResults=50&` +
                            `key=${YOUTUBE_API_KEY}` +
                            (token ? `&pageToken=${token}` : '');
                
                const response = await fetch(url);
                const data = await response.json();
                
                if (data.items?.length > 0) {
                    const videoIds = data.items.map(item => item.snippet.resourceId.videoId).filter(Boolean);
                    const detailsUrl = `https://www.googleapis.com/youtube/v3/videos?` +
                                     `part=snippet&` +
                                     `id=${videoIds.join(',')}&` +
                                     `key=${YOUTUBE_API_KEY}`;
                    
                    const detailsResponse = await fetch(detailsUrl);
                    const detailsData = await detailsResponse.json();
                    
                    allVideos = [...allVideos, ...detailsData.items];
                }
                
                token = data.nextPageToken || '';
            } while (token);
            
            // Filtrer les vidéos selon la recherche
            const filteredVideos = allVideos.filter(video => 
                video.snippet.title.toLowerCase().includes(query.toLowerCase())
            );
            
            if (filteredVideos.length > 0) {
                displayVideos(filteredVideos);
            } else {
                videosGrid.innerHTML = `<p class="no-results">Aucune vidéo trouvée pour "${query}"</p>`;
            }
        } catch (error) {
            console.error("Erreur recherche:", error);
            videosGrid.innerHTML = `
                <div class="error">
                    <p>Erreur lors de la recherche</p>
                    <button onclick="searchInPlaylist('${query}')">Réessayer</button>
                </div>
            `;
        } finally {
            loadingIndicator.style.display = 'none';
        }
    }
});