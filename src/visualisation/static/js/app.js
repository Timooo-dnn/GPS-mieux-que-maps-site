let map;
let routeLayerGroup = null;
let villesLayerGroup = null;

// ============================
// INITIALISATION DE LA CARTE
// ============================
document.addEventListener("DOMContentLoaded", () => {
    map = L.map('map').setView([43.6045, 1.4442], 12);

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap'
    }).addTo(map);
});

// ============================
// FETCH + TRACÉ DE L'ITINÉRAIRE
// ============================
async function lancerRecherche() {
    const depart = document.getElementById('ville-depart').value;
    const arrivee = document.getElementById('ville-arrivee').value;
    const zoneResultat = document.getElementById('resultat-brut');

    if (!depart || !arrivee) {
        alert("Merci de renseigner un départ et une arrivée");
        return;
    }

    zoneResultat.innerText = "Calcul de l'itinéraire...";

    try {
        const reponse = await fetch('/api/calculer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ depart, arrivee })
        });

        const donnees = await reponse.json();
        zoneResultat.innerText = JSON.stringify(donnees, null, 2);

        tracerItineraire(donnees);

    } catch (error) {
        zoneResultat.innerText = "Erreur de communication avec le serveur";
        console.error(error);
    }
}

// ============================
// TRACÉ DE LA ROUTE SUR LA CARTE
// ============================
function tracerItineraire(donnees) {

    if (routeLayerGroup) map.removeLayer(routeLayerGroup);
    if (villesLayerGroup) map.removeLayer(villesLayerGroup);

    routeLayerGroup = L.layerGroup();
    villesLayerGroup = L.layerGroup();

    let allLatLngs = [];

    // tracer les routes
    donnees.cartographie.routes.forEach(route => {
        const latlngs = route.geometry.map(p => [p[1], p[0]]); // [lat, lon]
        allLatLngs.push(...latlngs);

        L.polyline(latlngs, {
            color: route.autoroute ? 'red' : 'blue',
            weight: 5,
            opacity: 0.8
        }).addTo(routeLayerGroup);
    });

    // tracer les villes
    Object.values(donnees.cartographie.villes).forEach(ville => {
        L.marker([ville.lat, ville.lon])
            .bindPopup(`<b>${ville.nom}</b>`)
            .addTo(villesLayerGroup);
    });

    // ajout des couches et zoom automatique
    routeLayerGroup.addTo(map);
    villesLayerGroup.addTo(map);
    map.fitBounds(allLatLngs);
}