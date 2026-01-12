// webapp/assets/js/lang-switcher.js

document.addEventListener('DOMContentLoaded', function() {
    
    const langOptions = document.querySelectorAll('.lang-option');
    let currentLang = localStorage.getItem('preferredLang') || 'sk';

    /**
     * Updates all static text elements on the page based on data-translate-key.
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
     * Updates the source of theme images on the Landing Page.
     */
    function updateImageSources(lang) {
        const imagesToUpdate = document.querySelectorAll('#one.spotlights img');
        
        imagesToUpdate.forEach(img => {
            let currentSrc = img.getAttribute('src');
            if (!currentSrc) return;

            const oldLangSuffix = lang === 'sk' ? '_en.png' : '_sk.png';
            const newLangSuffix = lang === 'sk' ? '_sk.png' : '_en.png';

            if (currentSrc.endsWith(oldLangSuffix)) {
                const newSrc = currentSrc.replace(oldLangSuffix, newLangSuffix);
                img.setAttribute('src', newSrc);
                
                const parentLink = img.closest('a.image');
                if (parentLink) {
                    parentLink.style.backgroundImage = `url(${newSrc})`;
                }
            }
        });
    }

    /**
     * NEW: Updates dynamic content on generic.html (Theme Details Page).
     * This ensures title, description, and lists update immediately without reload.
     */
    function updateDynamicThemeContent(lang) {
        // Check if we are on the generic page and if themeDetails is loaded
        if (typeof themeDetails === 'undefined') return;

        const urlParams = new URLSearchParams(window.location.search);
        const theme = urlParams.get('theme');
        
        if (!theme || !themeDetails[theme]) return;

        const details = themeDetails[theme][lang];
        if (!details) return;

        // 1. Update Page Title & Main Header
        document.title = details.pageTitle;
        const mainHeader = document.querySelector('#main .major');
        if (mainHeader) mainHeader.innerHTML = details.title;

        // 2. Update Descriptions
        const descriptions = document.querySelectorAll('#main .inner p');
        if (descriptions.length >= 2) {
            descriptions[0].innerHTML = details.description1;
            descriptions[1].innerHTML = details.description2;
        }

        // 3. Update Lists
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

        // 4. Update Gallery Images & Title
        const galleryTitle = document.querySelector('#main .inner h2:nth-of-type(3)');
        if (galleryTitle) galleryTitle.innerHTML = details.galleryTitle;

        const galleryImages = document.querySelectorAll('#main .inner .box.alt .image img');
        if (galleryImages.length <= details.galleryImages.length) {
            galleryImages.forEach((img, index) => {
                img.src = details.galleryImages[index];
            });
        }

        // 5. Update CTA Section
        const ctaTitle = document.querySelector('#main .inner h2:nth-of-type(4)');
        if (ctaTitle) ctaTitle.innerHTML = details.ctaTitle;
        
        // Note: CTA Subtitle is usually the 3rd paragraph (index 2)
        if (descriptions.length > 2) {
            descriptions[2].innerHTML = details.ctaSubtitle;
        }

        const ctaButton = document.querySelector('#main .inner .actions .button.primary');
        if (ctaButton) ctaButton.innerHTML = details.ctaButton;
        
        const backButton = document.querySelector('#main .inner .actions .button:not(.primary)');
        if (backButton) backButton.innerHTML = details.backButton;
    }

    /**
     * Sets the visual state of the language switcher buttons.
     */
    function setSwitcherState(lang) {
        // Handle both Sidebar and Floating switchers
        const allOptions = document.querySelectorAll('.lang-option');
        allOptions.forEach(opt => {
            if (opt.getAttribute('data-lang') === lang) {
                opt.classList.add('active');
            } else {
                opt.classList.remove('active');
            }
        });
    }
    
    /**
     * Main function to handle a language switch.
     */
    function switchLanguage(selectedLang) {
        console.log(`Switching to language: ${selectedLang}`);
        currentLang = selectedLang;
        localStorage.setItem('preferredLang', currentLang);

        setSwitcherState(currentLang);
        updateContent(currentLang);
        updateImageSources(currentLang);
        
        // Call the new function for dynamic pages
        updateDynamicThemeContent(currentLang);
    }

    // --- Event Listeners ---
    // Use event delegation for dynamically added floating switchers if needed, 
    // or just bind to all existing .lang-option classes.
    const allLangOptions = document.querySelectorAll('.lang-option');
    allLangOptions.forEach(option => {
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
            // Append language parameter to persist selection across page loads
            const separator = destination.includes('?') ? '&' : '?';
            const finalUrl = `${destination}${separator}lang=${currentLang}`;
            window.location.href = finalUrl;
        }
    });

    // --- Initial Page Load ---
    switchLanguage(currentLang);
});

// End of webapp/assets/js/lang-switcher.js (v. 0008)
