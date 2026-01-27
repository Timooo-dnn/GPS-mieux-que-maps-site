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

    } catch (error) {
        zoneResultat.innerText = "Erreur de communication avec le serveur";
        console.error(error);
    }
}