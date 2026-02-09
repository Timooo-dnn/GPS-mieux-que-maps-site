let map = null;
let layerMarkers = null;
let layerRoutes = null;
const state = {
    depart: { id: '', nom: '' },
    arrivee: { id: '', nom: '' },
    villes: {}
};

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    initEventListeners();
    loadVillesData();
});

function initMap() {
    map = L.map('map').setView([43.6045, 1.4442], 7);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
        minZoom: 6
    }).addTo(map);

    layerMarkers = L.layerGroup().addTo(map);
    layerRoutes = L.layerGroup().addTo(map);
}

function initEventListeners() {
    const departInput = document.getElementById('depart_input');
    const arriveeInput = document.getElementById('arrivee_input');
    
    departInput.addEventListener('blur', () => rechercherVille('depart'));
    arriveeInput.addEventListener('blur', () => rechercherVille('arrivee'));

    document.getElementById('btn-calcul').addEventListener('click', lancerCalcul);

    document.getElementById('btn-swap').addEventListener('click', inverserTrajet);

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            fermerSuggestions();
        }
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.input-group')) {
            fermerSuggestions();
        }
    });
}

async function loadVillesData() {
    try {
        const response = await fetch('/api/recherche_ville', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nom: '' })
        });
    } catch (error) {
        console.error('Erreur lors du chargement des villes:', error);
    }
}

function rechercherVille(type) {
    const input = document.getElementById(`${type}_input`);
    const statusDiv = document.getElementById(`${type}_status`);
    const nom = input.value.trim();
    
    if (!nom) {
        document.getElementById(`${type}_id`).value = '';
        statusDiv.innerText = '';
        return;
    }
    
    statusDiv.innerText = '🔍 Recherche...';
    
    fetch('/api/recherche_ville', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nom: nom })
    })
    .then(r => r.json())
    .then(villes => {
        layerMarkers.clearLayers();
        
        if (villes.length === 0) {
            statusDiv.innerHTML = "<span style='color: #e74c3c;'>❌ Introuvable</span>";
            document.getElementById(`${type}_id`).value = '';
        } else if (villes.length === 1) {
            selectionnerVille(type, villes[0]);
        } else {
            statusDiv.innerHTML = `<span style='color: #f39c12;'>⚠️ ${villes.length} résultats. Cliquez sur la carte pour choisir.</span>`;
            afficherHomonymes(type, villes);
        }
    })
    .catch(err => {
        console.error('Erreur:', err);
        statusDiv.innerHTML = "<span style='color: #e74c3c;'>❌ Erreur de recherche</span>";
    });
}

function afficherHomonymes(type, villes) {
    const bounds = L.latLngBounds();
    
    villes.forEach(ville => {
        const marker = L.marker([ville.lat, ville.lon], {
            icon: L.icon({
                iconUrl: `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="${type === 'depart' ? 'green' : 'red'}" width="40" height="40"><path d="M12 2C7.58 2 4 5.58 4 10c0 5.25 8 13 8 13s8-7.75 8-13c0-4.42-3.58-8-8-8zm0 11c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z"/></svg>`,
                iconSize: [40, 40],
                className: 'marker-homonym'
            })
        });
        
        const popupHTML = `
            <div style="text-align: center;">
                <b>${ville.nom}</b>
                <br>
                <small>${ville.id}</small>
                <br>
                <button class="popup-btn" onclick="selectionnerVille('${type}', ${JSON.stringify(ville).replace(/"/g, '&quot;')})">
                    Choisir
                </button>
            </div>
        `;
        
        marker.bindPopup(popupHTML);
        marker.addTo(layerMarkers);
        bounds.extend([ville.lat, ville.lon]);
    });
    
    if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [50, 50] });
    }
}

function selectionnerVille(type, ville) {
    document.getElementById(`${type}_input`).value = ville.nom;
    document.getElementById(`${type}_id`).value = ville.id;
    state[type] = { id: ville.id, nom: ville.nom };
    
    const statusDiv = document.getElementById(`${type}_status`);
    statusDiv.innerHTML = "<span style='color: #27ae60;'>✅ Validé</span>";
    
    layerMarkers.clearLayers();
    map.closePopup();
    map.setView([ville.lat, ville.lon], 10);
    
    showToast(`${ville.nom} sélectionné`, 'success');
}

function inverserTrajet() {
    if (!state.depart.id || !state.arrivee.id) {
        showToast('Veuillez d\'abord sélectionner deux villes', 'warning');
        return;
    }

    const temp = state.depart;
    state.depart = state.arrivee;
    state.arrivee = temp;

    document.getElementById('depart_id').value = state.depart.id;
    document.getElementById('depart_input').value = state.depart.nom;
    document.getElementById('arrivee_id').value = state.arrivee.id;
    document.getElementById('arrivee_input').value = state.arrivee.nom;

    const departStatus = document.getElementById('depart_status');
    const arriveeStatus = document.getElementById('arrivee_status');
    departStatus.innerHTML = "<span style='color: #27ae60;'>✅ Validé</span>";
    arriveeStatus.innerHTML = "<span style='color: #27ae60;'>✅ Validé</span>";

    showToast('Trajets inversés', 'success');
}

async function lancerCalcul() {
    const departId = document.getElementById('depart_id').value;
    const arriveeId = document.getElementById('arrivee_id').value;

    if (!departId || !arriveeId) {
        showToast('Veuillez sélectionner ville de départ et d\'arrivée', 'error');
        return;
    }

    if (departId === arriveeId) {
        showToast('La ville de départ et d\'arrivée sont identiques', 'warning');
        return;
    }

    const btnCalcul = document.getElementById('btn-calcul');
    const loadingOverlay = document.getElementById('loading-overlay');

    btnCalcul.disabled = true;
    loadingOverlay.style.display = 'flex';

    try {
        const response = await fetch('/api/calculer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ depart: departId, arrivee: arriveeId })
        });

        const data = await response.json();

        if (data.erreur) {
            showToast(`Erreur: ${data.erreur}`, 'error');
        } else {
            afficherResultats(data.itineraire);
            showToast('Itinéraire calculé avec succès!', 'success');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showToast('Erreur lors du calcul', 'error');
    } finally {
        btnCalcul.disabled = false;
        loadingOverlay.style.display = 'none';
    }
}

function afficherResultats(itineraire) {
    const resultatsDiv = document.getElementById('resultats');
    document.getElementById('res_dist').textContent = `${itineraire.distance.toFixed(1)} km`;
    document.getElementById('res_temps').textContent = itineraire.temps_formate;
    resultatsDiv.style.display = 'block';
    
    tracerChemin(itineraire);
}

function tracerChemin(itineraire) {
    layerRoutes.clearLayers();
    
    const villes = itineraire.villes || {};
    const routes = itineraire.routes || [];
    const chemin = itineraire.chemin || [];
    
    console.log('📍 Données reçues:', {
        villes: Object.keys(villes).length,
        routes: routes.length,
        chemin: chemin.length
    });

    routes.forEach((route, idx) => {
        try {
            const geometry = route.geometry;
            console.log(`Route ${idx}: from=${route.from} to=${route.to}, autoroute=${route.autoroute}, hasGeometry=${!!geometry}`);
            
            if (geometry && geometry.type === 'LineString' && geometry.coordinates && geometry.coordinates.length > 0) {
                const latlngs = geometry.coordinates.map(coord => [coord[1], coord[0]]);
                
                console.log(`  → Traçage de ${latlngs.length} points`);
                
                const color = route.autoroute ? '#ff0000' : '#124668';
                const weight = route.autoroute ? 4 : 2;
                const dashArray = route.autoroute ? null : null;
                
                L.polyline(latlngs, {
                    color: color,
                    weight: weight,
                    opacity: 0.8,
                    dashArray: dashArray
                }).addTo(layerRoutes);
            } else {
                console.warn(`Route ${idx} : Pas de géométrie valide`);
            }
        } catch (error) {
            console.error('Erreur en traçant la route:', error);
        }
    });
    
    // Ajouter les marqueurs pour les villes du chemin
    const villesMap = {};
    for (const [id, v] of Object.entries(villes)) {
        villesMap[id] = v;
    }
    
    console.log(`🏙️ Placement de ${chemin.length} marqueurs`);
    
    chemin.forEach((villeId, idx) => {
        const v = villesMap[villeId];
        if (v && v.lat && v.lon) {
            const isStart = idx === 0;
            const isEnd = idx === chemin.length - 1;
            
            let icon = null;
            if (isStart) {
                icon = L.icon({
                    iconUrl: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="green" width="40" height="40"><path d="M12 2C7.58 2 4 5.58 4 10c0 5.25 8 13 8 13s8-7.75 8-13c0-4.42-3.58-8-8-8zm0 11c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z"/></svg>',
                    iconSize: [40, 40]
                });
            } else if (isEnd) {
                icon = L.icon({
                    iconUrl: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="red" width="40" height="40"><path d="M12 2C7.58 2 4 5.58 4 10c0 5.25 8 13 8 13s8-7.75 8-13c0-4.42-3.58-8-8-8zm0 11c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z"/></svg>',
                    iconSize: [40, 40]
                });
            } else {
                icon = L.icon({
                    iconUrl: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="blue" width="30" height="30"><path d="M12 2C7.58 2 4 5.58 4 10c0 5.25 8 13 8 13s8-7.75 8-13c0-4.42-3.58-8-8-8zm0 11c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z"/></svg>',
                    iconSize: [30, 30]
                });
            }
            
            const marker = L.marker([v.lat, v.lon], { icon: icon });
            marker.bindPopup(`<b>${v.nom}</b>`);
            marker.addTo(layerRoutes);
            console.log(`  ✓ ${v.nom} (${villeId})`);
        } else {
            console.warn(`Ville ${villeId} : données manquantes`, v);
        }
    });
    
    // Construire les bounds à partir des villes si pas de routes
    if (Object.keys(villes).length > 0) {
        const bounds = L.latLngBounds();
        Object.values(villes).forEach(v => {
            bounds.extend([v.lat, v.lon]);
        });
        
        if (bounds.isValid()) {
            map.fitBounds(bounds, { padding: [50, 50] });
        }
    }
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 4000);
}

function formatTime(minutes) {
    try {
        minutes = parseFloat(minutes);
        if (minutes < 60) {
            return `${Math.round(minutes)} min`;
        } else {
            const hours = Math.floor(minutes / 60);
            const mins = Math.round(minutes % 60);
            return `${hours}h ${mins}min`;
        }
    } catch {
        return '0 min';
    }
}
