/**
 * Easter Egg MONTAUBAN 🌋
 * - Un petit volcan cartoon qui fume
 * - Message: "Erreur géologique détectée"
 * - C'est pas du tout volcanique!
 */

const MontaubanEasterEgg = {
    isActive: false,
    volcanoElement: null,
    messageElement: null,
    smokeElements: [],
    animationTimeout: null,

    trigger() {
        if (this.isActive) return;
        this.isActive = true;

        console.log('🌋 Easter Egg Montauban déclenché!');

        // Créer le volcan
        this.createVolcano();

        // Afficher le message d'erreur
        this.displayErrorMessage();

        // Animer la fumée
        this.startSmoking();

        // Sons
        this.playSounds();

        // Arrêter après 6 secondes
        this.animationTimeout = setTimeout(() => {
            this.cleanup();
        }, 6000);
    },

    /**
     * Crée le volcan cartoon
     */
    createVolcano() {
        this.volcanoElement = document.createElement('div');
        this.volcanoElement.id = 'montauban-volcano';
        this.volcanoElement.innerHTML = `
            <div class="volcano-container">
                <!-- Base du volcan -->
                <div class="volcano-base">
                    <!-- Roche du volcan -->
                    <div class="volcano-body"></div>
                    <!-- Cratère -->
                    <div class="volcano-crater"></div>
                    <!-- Lave à l'intérieur (pour l'effet) -->
                    <div class="volcano-lava"></div>
                </div>
            </div>
        `;

        document.body.appendChild(this.volcanoElement);
    },

    /**
     * Affiche le message d'erreur géologique
     */
    displayErrorMessage() {
        this.messageElement = document.createElement('div');
        this.messageElement.className = 'geology-error-message';
        this.messageElement.innerHTML = `
            <h2>⚠️ ERREUR GÉOLOGIQUE DÉTECTÉE! ⚠️</h2>
            <p>🌋 Montauban n'est PAS volcanique!</p>
            <p style="font-size: 14px; color: #888;">Système de vérification géographique: CONFUS</p>
        `;

        document.body.appendChild(this.messageElement);
    },

    /**
     * Crée et anime les nuages de fumée
     */
    startSmoking() {
        const interval = setInterval(() => {
            if (!this.isActive) {
                clearInterval(interval);
                return;
            }

            const smoke = document.createElement('div');
            smoke.className = 'volcano-smoke';
            smoke.style.left = (45 + Math.random() * 10) + '%';
            smoke.innerHTML = '💨';

            this.volcanoElement.appendChild(smoke);
            this.smokeElements.push(smoke);

            // Supprimer la fumée après son animation
            setTimeout(() => {
                smoke.remove();
                this.smokeElements = this.smokeElements.filter(s => s !== smoke);
            }, 2000);
        }, 300);

        // Sauvegarder l'interval pour pouvoir l'arrêter
        this.smokeInterval = interval;
    },

    /**
     * Sons pour le volcan
     */
    playSounds() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const now = audioContext.currentTime;

            // Grondement du volcan (bruit grave qui rumble)
            const grumbleOsc = audioContext.createOscillator();
            const grumbleGain = audioContext.createGain();
            grumbleOsc.connect(grumbleGain);
            grumbleGain.connect(audioContext.destination);
            grumbleOsc.type = 'sawtooth';
            grumbleOsc.frequency.setValueAtTime(80, now);
            grumbleOsc.frequency.exponentialRampToValueAtTime(120, now + 3);
            grumbleGain.gain.setValueAtTime(0.08, now);
            grumbleGain.gain.exponentialRampToValueAtTime(0.02, now + 3);
            grumbleOsc.start(now);
            grumbleOsc.stop(now + 3);

            // Sifflement de vapeur
            const steamOsc = audioContext.createOscillator();
            const steamGain = audioContext.createGain();
            steamOsc.connect(steamGain);
            steamGain.connect(audioContext.destination);
            steamOsc.type = 'sine';
            steamOsc.frequency.setValueAtTime(400, now + 0.5);
            steamOsc.frequency.exponentialRampToValueAtTime(600, now + 3);
            steamGain.gain.setValueAtTime(0.05, now + 0.5);
            steamGain.gain.exponentialRampToValueAtTime(0.01, now + 3);
            steamOsc.start(now + 0.5);
            steamOsc.stop(now + 3);
        } catch (e) {
            console.log('🔇 Sons non disponibles');
        }
    },

    cleanup() {
        this.isActive = false;

        if (this.smokeInterval) {
            clearInterval(this.smokeInterval);
        }

        if (this.volcanoElement) {
            this.volcanoElement.remove();
            this.volcanoElement = null;
        }

        if (this.messageElement) {
            this.messageElement.remove();
            this.messageElement = null;
        }

        this.smokeElements.forEach(smoke => {
            smoke.remove();
        });
        this.smokeElements = [];

        if (this.animationTimeout) {
            clearTimeout(this.animationTimeout);
        }

        console.log('🧹 Easter Egg Montauban terminé');
    }
};
