/**
 * Easter Egg DOUBLE-CLIC 🎬
 * - Double-clic sur la carte
 * - Rick Roll surprise!
 * - Message amusant: "Clique moins vite la prochaine fois"
 */

const DoubleClickEasterEgg = {
    isActive: false,
    rickRollPanel: null,

    trigger() {
        if (this.isActive) return;
        this.isActive = true;

        console.log('🎬 Easter Egg Rick Roll déclenché!');

        // Créer le panel du rick roll
        this.createRickRollPanel();

        // Sons amusants
        this.playSounds();

        // Arrêter après 15 secondes
        setTimeout(() => {
            this.cleanup();
        }, 15000);
    },

    /**
     * Crée le panel du rick roll
     */
    createRickRollPanel() {
        this.rickRollPanel = document.createElement('div');
        this.rickRollPanel.id = 'rick-roll-panel';
        this.rickRollPanel.className = 'rick-roll-overlay';

        // Structure principale
        this.rickRollPanel.innerHTML = `
            <div class="rick-roll-content">
                <button class="rick-roll-close" id="rick-roll-close">✕</button>
                
                <h1 class="rick-roll-title">🎬 SURPRISE! 🎬</h1>
                
                <div class="rick-roll-video"></div>
                
                <div class="rick-roll-message">
                    <p>🚀 CLIQUE MOINS VITE LA PROCHAINE FOIS! 🚀</p>
                    <p style="font-size: 14px; margin-top: 10px; color: #666;">
                        Tu viens de déclencher un Easter egg!<br>
                        Tu viens de te faire Rick Roll! 🎉
                    </p>
                </div>
            </div>
        `;

        document.body.appendChild(this.rickRollPanel);

        // Ajout du GIF dans le container
        const videoContainer = this.rickRollPanel.querySelector('.rick-roll-video');
        const gif = document.createElement('img');
        gif.src = "/static/img/memes/rick.gif"; // ← mets ici ton GIF
        gif.style.width = "100%";
        gif.style.borderRadius = "10px";
        gif.style.boxShadow = "0 0 20px rgba(0,0,0,0.4)";
        videoContainer.appendChild(gif);

        // Fermer en cliquant le bouton
        document.getElementById('rick-roll-close').addEventListener('click', () => {
            this.cleanup();
        });

        // Fermer en cliquant en dehors
        this.rickRollPanel.addEventListener('click', (e) => {
            if (e.target === this.rickRollPanel) {
                this.cleanup();
            }
        });

        // Fermer avec Échap
        const closeOnEsc = (e) => {
            if (e.key === 'Escape') {
                this.cleanup();
                document.removeEventListener('keydown', closeOnEsc);
            }
        };
        document.addEventListener('keydown', closeOnEsc);
    },

    /**
     * Sons amusants pour le rick roll
     */
    playSounds() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const now = audioContext.currentTime;

            // Sonnerie amusante - notes de la mélodie "Never Gonna Give You Up"
            const notes = [
                { freq: 440, duration: 0.3 },   // A
                { freq: 493, duration: 0.3 },   // B
                { freq: 554, duration: 0.6 },   // C#
                { freq: 494, duration: 0.3 },   // B
                { freq: 440, duration: 0.3 },   // A
                { freq: 392, duration: 0.6 },   // G
            ];

            let time = now;
            notes.forEach(note => {
                const osc = audioContext.createOscillator();
                const gain = audioContext.createGain();
                osc.connect(gain);
                gain.connect(audioContext.destination);
                osc.frequency.value = note.freq;
                gain.gain.setValueAtTime(0.2, time);
                gain.gain.exponentialRampToValueAtTime(0.01, time + note.duration);
                osc.start(time);
                osc.stop(time + note.duration);
                time += note.duration;
            });
        } catch (e) {
            console.log('🔇 Sons non disponibles');
        }
    },

    cleanup() {
        this.isActive = false;

        if (this.rickRollPanel) {
            this.rickRollPanel.remove();
            this.rickRollPanel = null;
        }

        console.log('🧹 Rick Roll fermé');
    }
};
