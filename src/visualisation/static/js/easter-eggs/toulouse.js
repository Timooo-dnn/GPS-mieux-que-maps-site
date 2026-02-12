/**
 * Easter Egg TOULOUSE 🎸🚌
 * - Un bus (aribus) traverse l'écran
 * - Le GPS tremble
 * - Messages amusants
 * - Son "beep beep"
 */

const ToulsouseEasterEgg = {
    isActive: false,

    trigger() {
        if (this.isActive) return;
        this.isActive = true;

        const container = document.querySelector('.app-container');
        const busElement = document.getElementById('bus-easter-egg');

        if (!busElement) {
            console.warn('⚠️ Élément bus non trouvé!');
            return;
        }

        // Afficher ✈️
        busElement.textContent = '✈️';
        busElement.classList.add('active');

        // Faire trembler l'écran
        container.classList.add('trembling');

        // Afficher un message amusant
        const messages = [
            '🏉 Dupont! 🏉',
            '✈️ ARIBUS! ✈️',
        ];

        const message = messages[Math.floor(Math.random() * messages.length)];
        const messageElement = document.createElement('div');
        messageElement.className = 'toulouse-message';
        messageElement.textContent = message;
        document.body.appendChild(messageElement);

        // Sons amusants
        this.playBusSound();

        // Arrêter après 4 secondes
        setTimeout(() => {
            this.cleanup();
        }, 4000);
    },

    /**
     * Petit son amusant (beep beep du bus)
     */
    playBusSound() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();

            // Premier beep
            const osc1 = audioContext.createOscillator();
            const gain1 = audioContext.createGain();
            osc1.connect(gain1);
            gain1.connect(audioContext.destination);
            osc1.frequency.value = 600;
            gain1.gain.setValueAtTime(0.3, audioContext.currentTime);
            gain1.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
            osc1.start(audioContext.currentTime);
            osc1.stop(audioContext.currentTime + 0.2);

            // Deuxième beep
            const osc2 = audioContext.createOscillator();
            const gain2 = audioContext.createGain();
            osc2.connect(gain2);
            gain2.connect(audioContext.destination);
            osc2.frequency.value = 700;
            gain2.gain.setValueAtTime(0.3, audioContext.currentTime + 0.3);
            gain2.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            osc2.start(audioContext.currentTime + 0.3);
            osc2.stop(audioContext.currentTime + 0.5);
        } catch (e) {
            console.log('🔇 Son non disponible');
        }
    },

    cleanup() {
        const container = document.querySelector('.app-container');
        const busElement = document.getElementById('bus-easter-egg');

        if (container) {
            container.classList.remove('trembling');
        }

        if (busElement) {
            busElement.classList.remove('active');
        }

        // Supprimer le message
        const messageElement = document.querySelector('.toulouse-message');
        if (messageElement) {
            messageElement.remove();
        }

        this.isActive = false;
    }
};
