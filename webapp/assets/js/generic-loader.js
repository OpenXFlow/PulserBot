// webapp/assets/js/generic-loader.js

document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. Get Parameters from URL ---
    const urlParams = new URLSearchParams(window.location.search);
    const theme = urlParams.get('theme');
    const lang = urlParams.get('lang') || 'sk';

    /**
     * Translates static parts of the page (like the header)
     * using the main translations.js file.
     * @param {string} langCode - The language to translate to.
     */
    function translateStaticParts(langCode) {
        // This function requires 'translations' object from translations.js
        if (typeof translations === 'undefined') {
            console.error("translations.js is not loaded or 'translations' object is missing.");
            return;
        }
        
        const elementsToTranslate = document.querySelectorAll('[data-translate-key]');
        elementsToTranslate.forEach(element => {
            const key = element.getAttribute('data-translate-key');
            if (translations[langCode] && translations[langCode][key]) {
                element.innerHTML = translations[langCode][key];
            }
        });
    }

    // --- Execute Static Translation Immediately ---
    translateStaticParts(lang);

    // If 'theme' parameter is missing, stop further execution.
    if (!theme) {
        console.error("Theme parameter is missing in the URL.");
        const mainHeader = document.querySelector('#main .major');
        if (mainHeader) mainHeader.textContent = (lang === 'en') ? 'Theme Not Found' : 'Téma Nenájdená';
        return;
    }

    // --- 2. Get the Correct Dynamic Data for the Theme ---
    // This function requires 'themeDetails' object from theme-details.js
    if (typeof themeDetails === 'undefined') {
        console.error("theme-details.js is not loaded or 'themeDetails' object is missing.");
        return;
    }
    const details = themeDetails[theme] ? themeDetails[theme][lang] : null;

    if (!details) {
        console.error(`No details found for theme '${theme}' in language '${lang}'.`);
        const mainHeader = document.querySelector('#main .major');
        if (mainHeader) mainHeader.textContent = (lang === 'en') ? 'Theme Details Not Found' : 'Detaily Témy Nenájdené';
        return;
    }

    // --- 3. Populate the Page with Dynamic Data ---
    document.title = details.pageTitle;

    const mainHeader = document.querySelector('#main .major');
    if (mainHeader) mainHeader.innerHTML = details.title;

    const descriptions = document.querySelectorAll('#main .inner p');
    if (descriptions.length >= 2) {
        descriptions[0].innerHTML = details.description1;
        descriptions[1].innerHTML = details.description2;
    }

    const listTitle = document.querySelector('#main .inner h2:nth-of-type(2)');
    if (listTitle) listTitle.innerHTML = details.listTitle;

    const listContainer = document.querySelector('#main .inner ul');
    if (listContainer) {
        listContainer.innerHTML = '';
        details.listItems.forEach(itemText => {
            const li = document.createElement('li');
            li.innerHTML = itemText;
            listContainer.appendChild(li);
        });
    }

    const galleryTitle = document.querySelector('#main .inner h2:nth-of-type(3)');
    if (galleryTitle) galleryTitle.innerHTML = details.galleryTitle;

    const galleryImages = document.querySelectorAll('#main .inner .box.alt .image img');
    if (galleryImages.length <= details.galleryImages.length) {
        galleryImages.forEach((img, index) => {
            img.src = details.galleryImages[index];
            img.alt = `Showcase ${index + 1}`;
        });
    }

    const ctaTitle = document.querySelector('#main .inner h2:nth-of-type(4)');
    if (ctaTitle) ctaTitle.innerHTML = details.ctaTitle;
    
    const ctaSubtitle = document.querySelectorAll('#main .inner p')[2];
    if (ctaSubtitle) ctaSubtitle.innerHTML = details.ctaSubtitle;

    const ctaButton = document.querySelector('#main .inner .actions .button.primary');
    if (ctaButton) ctaButton.innerHTML = details.ctaButton;
    
    const backButton = document.querySelector('#main .inner .actions .button:not(.primary)');
    if (backButton) backButton.innerHTML = details.backButton;
});

// End of webapp/assets/js/generic-loader.js (v. 0003)