const MillauEasterEgg = {
    trigger() {
        // 1. Si l'image existe déjà, on ne fait rien
        if (document.getElementById('millau-full-image')) return;

        // 2. Création du conteneur plein écran
        const overlay = document.createElement('div');
        overlay.id = 'millau-full-image';
        
        // Style pour centrer l'image et l'afficher en grand
        Object.assign(overlay.style, {
            position: 'fixed',
            top: '0',
            left: '0',
            width: '100vw',
            height: '100vh',
            backgroundColor: 'rgba(0, 0, 0, 0.9)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: '100000',
            cursor: 'pointer',
            opacity: '0',
            transition: 'opacity 0.5s ease-in-out'
        });

        // 3. L'image du viaduc
        const img = document.createElement('img');
        // Image haute définition du viaduc
        img.src = 'https://upload.wikimedia.org/wikipedia/commons/d/d8/Viaduc_de_Millau_3.jpg';
        
        Object.assign(img.style, {
            maxWidth: '90%',
            maxHeight: '80%',
            borderRadius: '8px',
            boxShadow: '0 0 50px rgba(255, 255, 255, 0.2)',
            border: '2px solid white'
        });

        // 4. Texte explicatif
        const text = document.createElement('div');
        text.innerText = '🌄 Viaduc de Millau';
        Object.assign(text.style, {
            position: 'absolute',
            bottom: '5%',
            color: 'white',
            fontFamily: 'sans-serif',
            fontSize: '24px',
            fontWeight: 'bold'
        });

        overlay.appendChild(img);
        overlay.appendChild(text);
        document.body.appendChild(overlay);

        // Animation d'apparition
        setTimeout(() => overlay.style.opacity = '1', 10);

        // 5. Fermeture au clic ou après 5 secondes
        const close = () => {
            overlay.style.opacity = '0';
            setTimeout(() => overlay.remove(), 500);
        };

        overlay.onclick = close;
        setTimeout(close, 5000);
    }
};