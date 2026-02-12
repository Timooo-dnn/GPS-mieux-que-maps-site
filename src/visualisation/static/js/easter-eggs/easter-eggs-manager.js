/**
 * Gestionnaire central des Easter Eggs
 * Permet d'enregistrer et déclencher des blagues par ville
 */

class EasterEggsManager {
    constructor() {
        this.easterEggs = new Map();
    }

    /**
     * Enregistre tous les Easter eggs disponibles
     */
    registerEasterEggs() {
        // Enregistrer les Easter eggs depuis les modules spécialisés
        if (typeof ToulsouseEasterEgg !== 'undefined') {
            console.log('✅ Module Toulouse chargé');
            this.register('toulouse', ToulsouseEasterEgg);
        } else {
            console.warn('⚠️ Module Toulouse non disponible');
        }
        
        if (typeof RodezEasterEgg !== 'undefined') {
            console.log('✅ Module Rodez chargé');
            this.register('rodez', RodezEasterEgg);
        } else {
            console.warn('⚠️ Module Rodez non disponible');
        }

        if (typeof MillauEasterEgg !== 'undefined') {
            console.log('✅ Module Millau chargé');
            this.register('millau', MillauEasterEgg);
        } else {
            console.warn('⚠️ Module Millau non disponible');
        }

        if (typeof MontaubanEasterEgg !== 'undefined') {
            console.log('✅ Module Montauban chargé');
            this.register('montauban', MontaubanEasterEgg);
        } else {
            console.warn('⚠️ Module Montauban non disponible');
        }
    }

    /**
     * Enregistre un Easter egg pour une ville
     * @param {string} villeName - Nom de la ville (minuscules)
     * @param {Object} easterEggModule - Module avec méthode trigger()
     */
    register(villeName, easterEggModule) {
        this.easterEggs.set(villeName.toLowerCase(), easterEggModule);
        console.log(`📍 Easter Egg enregistré pour: ${villeName}`);
    }

    /**
     * Déclenche l'Easter egg si une ville en possède un
     * @param {string} villeName - Nom de la ville
     */
    trigger(villeName) {
        const normalizedName = villeName.toLowerCase().trim();
        
        console.log(`🔍 Recherche Easter Egg pour: "${villeName}" (normalisé: "${normalizedName}")`);
        console.log(`📋 Easter Eggs disponibles:`, Array.from(this.easterEggs.keys()));
        
        if (this.easterEggs.has(normalizedName)) {
            const easterEgg = this.easterEggs.get(normalizedName);
            if (easterEgg && typeof easterEgg.trigger === 'function') {
                console.log(`🎉 Easter Egg déclenché: ${villeName}`);
                easterEgg.trigger();
            } else {
                console.warn(`⚠️ Module ${villeName} n'a pas de méthode trigger()`);
            }
        } else {
            console.log(`ℹ️ Pas d'Easter Egg pour: ${villeName}`);
        }
    }

    /**
     * Nettoie les ressources (utile si plusieurs Easter eggs actifs)
     */
    cleanup() {
        this.easterEggs.forEach(egg => {
            if (egg && typeof egg.cleanup === 'function') {
                egg.cleanup();
            }
        });
    }
}

// Créer une instance globale
const easterEggsManager = new EasterEggsManager();

// Attendre que tous les modules soient chargés
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initialisation des Easter Eggs...');
    easterEggsManager.registerEasterEggs();
});
