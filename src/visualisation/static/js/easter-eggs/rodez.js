/**
 * Easter Egg RODEZ 🐄🧀
 * - Une vache 3D qui fait meuh
 * - Mini jeu: "Trouve le fromage caché sur la carte"
 * - Le joueur clique sur la carte pour chercher
 * - Indices: "trop chaud" / "trop froid"
 */

const RodezEasterEgg = {
    isActive: false,
    cheeseLocation: null,
    gameContainer: null,
    cowElement: null,
    map: null,

    trigger() {
        if (this.isActive) return;
        this.isActive = true;

        // Récupérer la map
        this.map = window.map;
        if (!this.map) {
            console.warn('⚠️ Map non disponible!');
            return;
        }

        // Créer le container du jeu
        this.createGameContainer();

        // Ajouter la vache 3D
        this.createCow3D();

        // Initialiser le jeu du fromage
        this.initCheesesGame();

        // Sound: meuh de la vache
        this.playCowSound();
    },

    /**
     * Crée le container du jeu
     */
    createGameContainer() {
        this.gameContainer = document.createElement('div');
        this.gameContainer.id = 'rodez-game-container';
        this.gameContainer.innerHTML = `
            <div class="rodez-overlay">
                <div class="rodez-game-panel">
                    <h2>🐄 Jeu de la Vache Heureuse 🧀</h2>
                    <p>La vache a perdu son fromage !</p>
                    <p style="font-size: 14px; color: #666;">Clique sur la carte francaise pour le chercher...</p>
                    <div id="cheese-hint" class="cheese-hint"></div>
                    <p style="font-size: 12px; color: #888; margin-top: 15px;">💡 Tu peux fermer ce message et chercher sur la carte!</p>
                    <button id="rodez-close-btn" class="rodez-close-btn">✕</button>
                </div>
            </div>
        `;

        document.body.appendChild(this.gameContainer);

        // Bouton fermer - ferme juste le panel, pas le jeu
        document.getElementById('rodez-close-btn').addEventListener('click', () => {
            this.closePanel();
        });

        // Fermer en cliquant en dehors du panel
        this.gameContainer.addEventListener('click', (e) => {
            if (e.target === this.gameContainer) {
                this.closePanel();
            }
        });
    },

    /**
     * Ferme juste le panel d'information, le jeu continue
     */
    closePanel() {
        if (this.gameContainer) {
            this.gameContainer.style.display = 'none';
        }
    },

    /**
     * Ouvre le panel d'information
     */
    openPanel() {
        if (this.gameContainer) {
            this.gameContainer.style.display = 'flex';
        }
    },

    /**
     * Crée une vache 3D simple avec CSS3D
     */
    createCow3D() {
        this.cowElement = document.createElement('div');
        this.cowElement.className = 'rodez-cow-3d';
        this.cowElement.innerHTML = `
            <div class="cow-body">
                <div class="cow-head">👀</div>
                <div class="cow-spots"></div>
            </div>
        `;

        document.body.appendChild(this.cowElement);

        // Animer la vache
        this.animateCow();
    },

    /**
     * Anime la vache (bouge doucement)
     */
    animateCow() {
        let rotation = 0;
        const animate = () => {
            rotation += 1;
            if (this.cowElement) {
                this.cowElement.style.transform = `rotateY(${rotation}deg)`;
                if (this.isActive) {
                    requestAnimationFrame(animate);
                }
            }
        };
        animate();
    },

    /**
     * Initialise le jeu du fromage caché
     * Le fromage est placé quelque part en France!
     */
    initCheesesGame() {
        // Coordonnées de la France (approximativement)
        // Nord: 51.1° → Sud: 41.3° | Ouest: -5.5° → Est: 7.5°
        const franceNorth = 51.1;
        const franceSouth = 41.3;
        const franceWest = -5.5;
        const franceEast = 7.5;

        const randomLat = franceSouth + Math.random() * (franceNorth - franceSouth);
        const randomLon = franceWest + Math.random() * (franceEast - franceWest);

        this.cheeseLocation = { lat: randomLat, lng: randomLon };
        
        console.log(`🧀 FROMAGE PLACÉ À: ${randomLat.toFixed(4)}, ${randomLon.toFixed(4)}`);
        console.log(`🗺️ Latitude: ${randomLat} (entre ${franceSouth} et ${franceNorth})`);
        console.log(`🗺️ Longitude: ${randomLon} (entre ${franceWest} et ${franceEast})`);
        console.log(`✅ FROMAGE EN FRANCE: ${randomLat >= franceSouth && randomLat <= franceNorth && randomLon >= franceWest && randomLon <= franceEast}`);

        // 🎯 Ajouter un marqueur VISIBLE pour le fromage!
        this.addCheeseMarkerToMap();

        // Ajouter le gestionnaire de clic sur la map
        this.map.on('click', (e) => this.checkCheese(e.latlng));
    },

    /**
     * Ajoute le fromage ÉNORME et visible sur la carte
     */
    addCheeseMarkerToMap() {
        if (!this.map || !this.cheeseLocation) return;

        console.log(`📍 Création du marqueur à: ${this.cheeseLocation.lat}, ${this.cheeseLocation.lng}`);

        // Créer un marqueur de fromage ÉNORME!
        const cheeseIcon = L.divIcon({
            html: `
                <div style="
                    font-size: 30px; 
                    text-align: center; 
                    filter: drop-shadow(0 0 15px rgba(255, 200, 0, 0.8)) 
                            drop-shadow(0 0 30px rgba(255, 165, 0, 0.6));
                    animation: float 2s ease-in-out infinite;
                    user-select: none;
                    pointer-events: none;
                ">🧀</div>
                <div style="
                    position: absolute;
                    top: 220px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: rgba(0, 0, 0, 0.7);
                    color: white;
                    padding: 5px 10px;
                    border-radius: 5px;
                    font-size: 12px;
                    white-space: nowrap;
                    font-weight: bold;
                    pointer-events: none;
                ">${this.cheeseLocation.lat.toFixed(3)}°, ${this.cheeseLocation.lng.toFixed(3)}°</div>
            `,
            className: 'cheese-marker',
            iconSize: [200, 250],
            iconAnchor: [100, 100]
        });

        const cheeseMarker = L.marker(this.cheeseLocation, { 
            icon: cheeseIcon,
            interactive: false,
            zIndexOffset: 1000
        });

        // Ajouter à layerRoutes (défini globalement dans app.js)
        if (typeof window.layerRoutes !== 'undefined') {
            cheeseMarker.addTo(window.layerRoutes);
            console.log(`✅ Marqueur ajouté à layerRoutes!`);
        } else {
            // Fallback: ajouter directement à la map
            cheeseMarker.addTo(this.map);
            console.log(`✅ Marqueur ajouté directement à la map (fallback)`);
        }
        
        this.cheeseMarker = cheeseMarker;
        console.log(`✅ Fromage visible sur la carte à: ${this.cheeseLocation.lat.toFixed(3)}°, ${this.cheeseLocation.lng.toFixed(3)}°`);
    },

    /**
     * Vérifie si le clic est proche du fromage
     */
    checkCheese(clickedPos) {
        if (!this.cheeseLocation || !this.isActive) return;

        const distance = this.map.latLngToLayerPoint(clickedPos)
            .distanceTo(this.map.latLngToLayerPoint(this.cheeseLocation));

        console.log(`🖱️ Clic à: ${clickedPos.lat.toFixed(3)}°, ${clickedPos.lng.toFixed(3)}°`);
        console.log(`📍 Fromage à: ${this.cheeseLocation.lat.toFixed(3)}°, ${this.cheeseLocation.lng.toFixed(3)}°`);
        console.log(`📏 Distance: ${distance.toFixed(0)}px (succès < 80px)`);

        const hintElement = document.getElementById('cheese-hint');
        if (!hintElement) return;

        // Ouvrir le panel si fermé
        this.openPanel();

        // Zone de "succès" agrandie (80px au lieu de 50px)
        if (distance < 80) {
            // 🎉 TROUVÉ!
            console.log(`🎉 SUCCÈS! Distance: ${distance.toFixed(0)}px`);
            this.findCheese();
            this.map.off('click');
        } else if (distance < 150) {
            hintElement.textContent = '🔥 Très chaud!';
            hintElement.className = 'cheese-hint hot';
        } else if (distance < 300) {
            hintElement.textContent = '🌡️ Chaud!';
            hintElement.className = 'cheese-hint warm';
        } else if (distance < 600) {
            hintElement.textContent = '❄️ Froid...';
            hintElement.className = 'cheese-hint cold';
        } else {
            hintElement.textContent = '🧊 Très froid!';
            hintElement.className = 'cheese-hint frozen';
        }

        // Le jeu continue, le gestionnaire reste actif
    },

    /**
     * Affiche le fromage trouvé
     */
    findCheese() {
        this.openPanel();
        
        const gamePanel = document.querySelector('.rodez-game-panel');
        if (gamePanel) {
            gamePanel.innerHTML = `
                <h2>🎉 BRAVO! 🎉</h2>
                <p style="font-size: 80px;">🧀</p>
                <p>Tu as trouvé le fromage!</p>
                <p>La vache saute de joie! 🐄💕</p>
                <button id="rodez-final-btn" class="rodez-close-btn" style="background: #228B22;">Fermer</button>
            `;

            document.getElementById('rodez-final-btn').addEventListener('click', () => {
                this.cleanup();
            });
        }

        // Sons de victoire
        this.playCowHappySound();
    },

    /**
     * Son: Meuh de la vache
     */
    playCowSound() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const now = audioContext.currentTime;

            // MEUH 1 (basse)
            const osc1 = audioContext.createOscillator();
            const gain1 = audioContext.createGain();
            osc1.connect(gain1);
            gain1.connect(audioContext.destination);
            osc1.frequency.setValueAtTime(200, now);
            osc1.frequency.exponentialRampToValueAtTime(150, now + 0.5);
            gain1.gain.setValueAtTime(0.4, now);
            gain1.gain.exponentialRampToValueAtTime(0.01, now + 0.5);
            osc1.start(now);
            osc1.stop(now + 0.5);

            // MEUH 2 (plus haut)
            const osc2 = audioContext.createOscillator();
            const gain2 = audioContext.createGain();
            osc2.connect(gain2);
            gain2.connect(audioContext.destination);
            osc2.frequency.setValueAtTime(250, now + 0.7);
            osc2.frequency.exponentialRampToValueAtTime(180, now + 1.2);
            gain2.gain.setValueAtTime(0.4, now + 0.7);
            gain2.gain.exponentialRampToValueAtTime(0.01, now + 1.2);
            osc2.start(now + 0.7);
            osc2.stop(now + 1.2);
        } catch (e) {
            console.log('🔇 Son vache non disponible');
        }
    },

    /**
     * Son: Vache heureuse (sons aigus)
     */
    playCowHappySound() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const now = audioContext.currentTime;

            const frequencies = [300, 350, 400, 450, 500];
            frequencies.forEach((freq, idx) => {
                const osc = audioContext.createOscillator();
                const gain = audioContext.createGain();
                osc.connect(gain);
                gain.connect(audioContext.destination);
                osc.frequency.value = freq;
                gain.gain.setValueAtTime(0.2, now + idx * 0.1);
                gain.gain.exponentialRampToValueAtTime(0.01, now + idx * 0.1 + 0.3);
                osc.start(now + idx * 0.1);
                osc.stop(now + idx * 0.1 + 0.3);
            });
        } catch (e) {
            console.log('🔇 Son victoire non disponible');
        }
    },

    cleanup() {
        this.isActive = false;

        if (this.gameContainer) {
            this.gameContainer.remove();
            this.gameContainer = null;
        }

        if (this.cowElement) {
            this.cowElement.remove();
            this.cowElement = null;
        }

        // Supprimer le marqueur du fromage de la carte
        if (this.cheeseMarker && this.map) {
            this.map.removeLayer(this.cheeseMarker);
            this.cheeseMarker = null;
        }

        if (this.map) {
            this.map.off('click');
        }

        this.cheeseLocation = null;
    }
};
