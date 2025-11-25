// webapp/assets/js/lang-switcher.js

document.addEventListener('DOMContentLoaded', function() {
    
    const langOptions = document.querySelectorAll('.lang-option');
    let currentLang = localStorage.getItem('preferredLang') || 'sk';

    /**
     * Updates all text elements on the page based on the selected language.
     * @param {string} lang - The language code to switch to.
     */
    function updateContent(lang) {
        const elementsToTranslate = document.querySelectorAll('[data-translate-key]');
        elementsToTranslate.forEach(element => {
            const key = element.getAttribute('data-translate-key');
            if (translations[lang] && translations[lang][key]) {
                element.innerHTML = translations[lang][key];
            }
        });
        document.documentElement.lang = lang;
    }

    /**
     * Updates the source of theme images based on the selected language.
     * @param {string} lang - The new language code ('sk' or 'en').
     */
    function updateImageSources(lang) {
        const imagesToUpdate = document.querySelectorAll('#one.spotlights img'); // Target only theme images
        
        imagesToUpdate.forEach(img => {
            let currentSrc = img.getAttribute('src');
            if (!currentSrc) return;

            // Determine the opposite language suffix to replace
            const oldLangSuffix = lang === 'sk' ? '_en.png' : '_sk.png';
            const newLangSuffix = lang === 'sk' ? '_sk.png' : '_en.png';

            // Replace the suffix in the path
            if (currentSrc.endsWith(oldLangSuffix)) {
                const newSrc = currentSrc.replace(oldLangSuffix, newLangSuffix);
                img.setAttribute('src', newSrc);
                
                // The template uses the parent 'a' tag for the background image as well
                const parentLink = img.closest('a.image');
                if (parentLink) {
                    parentLink.style.backgroundImage = `url(${newSrc})`;
                }
            }
        });
    }

    /**
     * Sets the visual state of the language switcher buttons.
     * @param {string} lang - The language code to set as active.
     */
    function setSwitcherState(lang) {
        langOptions.forEach(opt => {
            if (opt.getAttribute('data-lang') === lang) {
                opt.classList.add('active');
            } else {
                opt.classList.remove('active');
            }
        });
    }
    
    /**
     * Main function to handle a language switch.
     * @param {string} selectedLang - The new language to switch to.
     */
    function switchLanguage(selectedLang) {
        if (selectedLang === currentLang && document.documentElement.lang === selectedLang) return;

        console.log(`Switching to language: ${selectedLang}`);
        currentLang = selectedLang;
        localStorage.setItem('preferredLang', currentLang);

        setSwitcherState(currentLang);
        updateContent(currentLang);
        updateImageSources(currentLang); // Update images on language switch
    }

    // --- Event Listeners ---
    langOptions.forEach(option => {
        option.addEventListener('click', function() {
            const selectedLang = this.getAttribute('data-lang');
            switchLanguage(selectedLang);
        });
    });

    document.addEventListener('click', function(event) {
        const destinationElement = event.target.closest('[data-destination]');
        if (destinationElement) {
            event.preventDefault();
            event.stopPropagation();
            const destination = destinationElement.getAttribute('data-destination');
            const finalUrl = `${destination}&lang=${currentLang}`;
            console.log(`Navigating to: ${finalUrl}`);
            window.location.href = finalUrl;
        }
    });

    // --- Initial Page Load ---
    switchLanguage(currentLang);
});

// End of webapp/assets/js/lang-switcher.js (v. 0007)