// webapp/assets/js/app.js

$(function() {
    // --- 1. STATE ---
    let state = {
        currentUser: null,
        lang: localStorage.getItem('preferredLang') || 'sk',
        isVerified: false,
        verificationTimer: null,
        userData: null, // Data from Firestore
        tempCustomContent: null // Holds changes from modal before save
    };

    // --- 2. ELEMENT SELECTORS ---
    const elements = {
        body: $('body'),
        loadingContainer: $('#loading-container'),
        authContainer: $('#auth-container'),
        verificationContainer: $('#verification-container'),
        dashboardContainer: $('#dashboard-container'),
        loginForm: $('#login-form'),
        signupForm: $('#signup-form'),
        appNav: $('#app-nav'),
        logoutButtonContainer: $('#logout-button-container'),
        langOptions: $('.lang-option'),
        loginError: $('#login-error'),
        signupError: $('#signup-error'),
        verificationStatus: $('#verification-status'),
        resendVerificationButton: $('#resend-verification-button'),
        signupButton: $('#signup-button'),
        loginButton: $('#login-button'),
        subscriptionsForm: $('#subscriptions-form'),
        saveSettingsButton: $('#save-settings-button'),
        saveStatus: $('#save-status'),
        
        // Modal elements
        userContentModal: $('#user-content-modal'),
        modalBlocksContainer: $('#modal-blocks-container'),
        modalLinksContainer: $('#modal-links-container'),
        modalSaveBtn: $('#modal-save-btn'),
        modalCancelBtn: $('#modal-cancel-btn')
    };
    
    const allContainers = [elements.loadingContainer, elements.authContainer, elements.verificationContainer, elements.dashboardContainer];
    const db = firebase.firestore();

    // --- 3. UI BUILDER (Dashboard & Modal Logic) ---
    const UIBuilder = {
        
        renderDashboard: function() {
            const t = translations[state.lang];
            const data = state.userData || {};
            const isAdmin = data.isAdmin === true; 

            const channels = data.channels || [];
            const telegramId = channels.length > 0 ? channels[0].identifier : "";
            
            let userTimezone = data.timezone;
            if (!userTimezone) {
                try {
                    userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                } catch (e) {
                    userTimezone = "Europe/Bratislava";
                }
            }

            const weatherLocs = data.weather && data.weather.locations ? data.weather.locations : [{location: ""}];
            let html = '';

            // A. Telegram Section
            html += `
                <div class="setup-section">
                    <h3>${t.telegramSetupTitle}</h3>
                    <p class="instruction">
                        1. ${t.telegramInstruction1}<br>
                        2. ${t.telegramInstruction2}<br>
                        3. ${t.telegramInstruction3}
                    </p>
                    <div class="field">
                        <input type="text" id="telegram-id" value="${telegramId}" placeholder="${t.telegramIdPlaceholder}" pattern="[0-9]+" title="Numbers only">
                    </div>
                    
                    <div style="margin-top: 2em; padding: 1.5em; background: rgba(94, 66, 166, 0.3); border-left: 4px solid #b74e91; border-radius: 4px; display: flex; align-items: center; gap: 20px;">
                        <img src="images/logo/YourDailyPulse.png" alt="Bot Logo" style="width: 90px; height: 90px; border-radius: 50%; border: 3px solid rgba(255,255,255,0.3); box-shadow: 0 4px 10px rgba(0,0,0,0.3); object-fit: cover; flex-shrink: 0;">
                        <div>
                            <h4 style="color: #ffffff; font-size: 1.1em; margin-bottom: 0.5em;">${t.telegramInstruction4Title}</h4>
                            <p style="margin: 0; font-size: 0.95em; color: rgba(255,255,255,0.9); line-height: 1.5;">${t.telegramInstruction4Text}</p>
                        </div>
                    </div>
                </div>
                <hr>
            `;

            // B. Timezone Section
            let timezoneOptions = '';
            TIMEZONES.forEach(tz => {
                const selected = tz.value === userTimezone ? 'selected' : '';
                timezoneOptions += `<option value="${tz.value}" ${selected}>${tz.label}</option>`;
            });

            html += `
                <div class="setup-section">
                    <h3>${t.timezoneSetupTitle}</h3>
                    <p class="instruction">${t.timezoneInfo}</p>
                    <div class="field">
                        <select id="timezone-select">
                            ${timezoneOptions}
                        </select>
                    </div>
                </div>
                <hr>
            `;

            // C. Weather Section
            html += `
                <div class="setup-section">
                    <h3>${t.weatherSetupTitle}</h3>
                    <p class="instruction">${t.weatherInfo}</p>
                    <div id="weather-locations-container">
            `;
            
            if (weatherLocs.length === 0) weatherLocs.push({location: ""});
            weatherLocs.forEach((locObj, index) => {
                html += UIBuilder.getWeatherRowHtml(index, locObj.location, t.weatherPlaceholder);
            });

            html += `
                    </div>
                    <button class="button small" id="add-weather-btn">${t.weatherAddLocation}</button>
                </div>
                <hr>
            `;

            // D. Themes Section
            html += `
                <div class="setup-section">
                    <h3>${t.themesSetupTitle}</h3>
                    <div class="themes-list">
            `;

            let timeOptions = '';
            for (let i = 1; i <= 23; i++) {
                const hour = i.toString().padStart(2, '0');
                timeOptions += `<option value="time${i}">${hour}:00</option>`;
            }

            APP_THEMES.forEach(theme => {
                if (theme.adminOnly && !isAdmin) return; 

                const variants = theme.variants || {};
                const hasSk = !!variants.sk;
                const hasEn = !!variants.en;

                let isActive = false;
                let selectedTime = `time${parseInt(theme.defaultTime)}`;
                let selectedLang = 'sk'; 
                let activeDays = []; // Default empty

                if (data.subscriptions) {
                    for (const [timeKey, subList] of Object.entries(data.subscriptions)) {
                        if (!Array.isArray(subList)) continue;

                        for (const item of subList) {
                            let themeId = "";
                            let itemDays = null;

                            if (typeof item === 'string') {
                                themeId = item;
                                itemDays = [0, 1, 2, 3, 4, 5, 6]; // Legacy support
                            } else {
                                themeId = item.theme;
                                itemDays = item.days;
                            }

                            if ((hasSk && themeId === variants.sk) || (hasEn && themeId === variants.en)) {
                                isActive = true;
                                selectedTime = timeKey;
                                selectedLang = (themeId === variants.en) ? 'en' : 'sk';
                                if (itemDays) activeDays = itemDays;
                                break;
                            }
                        }
                        if (isActive) break;
                    }
                }

                const label = t[theme.labelKey] + (theme.suffix ? ` ${theme.suffix}` : '');
                const adminBadge = theme.adminOnly ? ' <span style="color: #ff6384; font-size: 0.7em; border: 1px solid #ff6384; padding: 0 4px; border-radius: 4px; margin-left: 5px;">ADMIN</span>' : '';

                // Language Selector
                let langSelectHtml = '';
                if (hasSk && hasEn) {
                    langSelectHtml = `
                        <div class="control-group" style="margin-left: 1em;">
                            <label style="margin-right: 0.5em;">${t.themeLangLabel}</label>
                            <select class="theme-lang-select">
                                <option value="sk">SK</option>
                                <option value="en">EN</option>
                            </select>
                        </div>
                    `;
                } else {
                    const singleLang = hasSk ? 'sk' : 'en';
                    langSelectHtml = `<input type="hidden" class="theme-lang-select" value="${singleLang}">`;
                }
                
                // Edit Button
                let editBtnHtml = '';
                if (theme.isEditable) {
                    editBtnHtml = `<button class="edit-content-btn" data-action="edit-content">${t.btnEditContent}</button>`;
                }

                // Day Picker
                let dayPickerHtml = `<div class="day-picker">`;
                t.daysShort.forEach((dayLabel, idx) => {
                    const isChecked = activeDays.includes(idx) ? 'checked' : '';
                    dayPickerHtml += `
                        <input type="checkbox" id="d-${theme.id}-${idx}" class="day-cb" value="${idx}" ${isChecked}>
                        <label for="d-${theme.id}-${idx}">${dayLabel}</label>
                    `;
                });
                dayPickerHtml += `</div>`;


                html += `
                    <div class="theme-row box" data-theme-base-id="${theme.id}">
                        <div class="theme-header">
                            <div class="theme-title-wrapper">
                                <h4>${label}${adminBadge}</h4>
                                ${editBtnHtml}
                            </div>
                            <div class="theme-controls">
                                <div class="control-group">
                                    <label>${t.themeTimeLabel}</label>
                                    <select class="theme-time-select">
                                        ${timeOptions}
                                    </select>
                                </div>
                                ${langSelectHtml}
                                <div class="control-group toggle-group">
                                    <input type="checkbox" id="cb-${theme.id}" class="theme-active-cb" ${isActive ? 'checked' : ''}>
                                    <label for="cb-${theme.id}">${t.themeActiveLabel}</label>
                                </div>
                            </div>
                        </div>
                        ${dayPickerHtml}
                    </div>
                `;
            });

            html += `</div></div>`;

            // E. Danger Zone
            html += `
                <hr style="margin-top: 3em; margin-bottom: 3em;">
                <div class="setup-section">
                    <h3 style="color: #ff6384;">${t.dangerZoneTitle}</h3>
                    <button class="button small" id="delete-account-btn" style="border-color: #ff6384; color: #ff6384;">${t.deleteAccountButton}</button>
                </div>
            `;
            
            elements.subscriptionsForm.html(html);
            UIBuilder.postRenderSetup(data);
        },
        
        postRenderSetup: function(data) {
            // Restore dropdown states
            APP_THEMES.forEach(theme => {
                if (theme.adminOnly && !(data.isAdmin === true)) return;
                
                const variants = theme.variants || {};
                const hasSk = !!variants.sk;
                const hasEn = !!variants.en;
                
                let selectedTime = `time${parseInt(theme.defaultTime)}`;
                let selectedLang = 'sk';

                if (data.subscriptions) {
                    for (const [timeKey, subList] of Object.entries(data.subscriptions)) {
                        if (!Array.isArray(subList)) continue;
                         for (const item of subList) {
                             const themeId = (typeof item === 'string') ? item : item.theme;
                             
                             if (hasSk && themeId === variants.sk) {
                                 selectedTime = timeKey; selectedLang = 'sk'; break;
                             }
                             if (hasEn && themeId === variants.en) {
                                 selectedTime = timeKey; selectedLang = 'en'; break;
                             }
                         }
                    }
                }
                const $row = $(`[data-theme-base-id="${theme.id}"]`);
                $row.find('.theme-time-select').val(selectedTime);
                if (hasSk && hasEn) {
                    $row.find('.theme-lang-select').val(selectedLang);
                }
            });

            // Bind dynamic events
            $('#add-weather-btn').off().on('click', UIBuilder.addWeatherRow);
            $(document).off('click', '.remove-weather-btn').on('click', '.remove-weather-btn', function() { $(this).parent().remove(); });
            $('#delete-account-btn').off().on('click', AuthManager.deleteAccount);
            $('.edit-content-btn').off().on('click', UIBuilder.openModal);
        },

        getWeatherRowHtml: function(index, value, placeholder) {
            return `
                <div class="field weather-row" style="display: flex; gap: 10px; margin-bottom: 10px;">
                    <input type="text" class="weather-input" value="${value}" placeholder="${placeholder}">
                    ${index > 0 ? '<button class="button small icon solid fa-trash remove-weather-btn" style="height: 2.75em; line-height: 2.75em; padding: 0 1em;"></button>' : ''}
                </div>
            `;
        },

        addWeatherRow: function(e) {
            e.preventDefault();
            const count = $('.weather-row').length;
            if (count >= 5) return;
            const t = translations[state.lang];
            $('#weather-locations-container').append(UIBuilder.getWeatherRowHtml(count, "", t.weatherPlaceholder));
        },

        // --- MODAL LOGIC ---
        openModal: function(e) {
            e.preventDefault();
            const t = translations[state.lang];
            
            const content = state.tempCustomContent || (state.userData && state.userData.custom_content) || {};
            const blocks = content.blocks || ["", "", ""];
            const links = content.links || [{}, {}, {}];

            let blocksHtml = '';
            for(let i=0; i<3; i++) {
                blocksHtml += `<div class="field"><textarea class="modal-block-input" rows="2" maxlength="1000" placeholder="${t.modalPlaceholderText}">${blocks[i] || ''}</textarea></div>`;
            }
            elements.modalBlocksContainer.html(blocksHtml);

            let linksHtml = '';
            for(let i=0; i<3; i++) {
                linksHtml += `
                    <div class="modal-input-row">
                        <input type="text" class="modal-link-title" value="${links[i].title || ''}" placeholder="${t.modalPlaceholderTitle}" style="flex:1">
                        <input type="text" class="modal-link-url" value="${links[i].url || ''}" placeholder="${t.modalPlaceholderUrl}" style="flex:2">
                    </div>`;
            }
            elements.modalLinksContainer.html(linksHtml);
            elements.userContentModal.removeClass('hidden');
        },

        closeModal: function() {
            elements.userContentModal.addClass('hidden');
        },

        saveModal: function() {
            const blocks = [];
            $('.modal-block-input').each(function() { blocks.push($(this).val()); });
            
            const links = [];
            const titles = $('.modal-link-title');
            const urls = $('.modal-link-url');
            
            for(let i=0; i<titles.length; i++) {
                links.push({
                    title: $(titles[i]).val(),
                    url: $(urls[i]).val()
                });
            }
            state.tempCustomContent = { blocks, links };
            UIBuilder.closeModal();
        }
    };

    // --- 4. UI MANAGER (General Helpers) ---
    const UIManager = {
        initPageFx: function() { setTimeout(() => { elements.body.removeClass('is-preload'); }, 100); },
        showContainer: function($c) { allContainers.forEach(c => c.toggleClass('hidden', !c.is($c))); },
        
        updateContent: function(lang) {
            $('[data-translate-key]').each(function() {
                const key = $(this).data('translate-key');
                if (translations[lang] && translations[lang][key]) {
                    let text = translations[lang][key];
                    if (state.currentUser && key === 'welcomeMessage') text = text.replace('{email}', state.currentUser.email);
                    $(this).html(text);
                }
            });
            $('html').attr('lang', lang);
            if(state.currentUser && state.isVerified) UIBuilder.renderDashboard();
        },

        updateAppNav: function(lang) {
            const t = translations[lang];
            let html = '<ul>';
            if (state.currentUser && state.isVerified) {
                html += `<li><a href="#" style="cursor: default; color:#fff; border-bottom: none;">${state.currentUser.email}</a></li><li><a href="#" class="active">${t.navSettings}</a></li><li><a href="#" id="sidebar-logout-button">${t.navLogout}</a></li>`;
            } else {
                html += `<li><a href="#" class="nav-link active" data-auth-form="login-form">${t.navLogin}</a></li><li><a href="#" class="nav-link" data-auth-form="signup-form">${t.navSignup}</a></li>`;
            }
            html += '</ul>';
            elements.appNav.html(html);
        },

        setLanguage: function(l) { 
            state.lang = l; 
            localStorage.setItem('preferredLang', l); 
            this.updateAppNav(l); 
            this.updateContent(l); 
            elements.langOptions.each(function() { $(this).toggleClass('active', $(this).data('lang') === l); }); 
        },

        showAuthForm: function(form) {
            elements.loginForm.toggleClass('hidden', form !== 'login-form');
            elements.signupForm.toggleClass('hidden', form !== 'signup-form');
            elements.loginError.text(''); elements.signupError.text('');
        }
    };

    // --- 5. AUTH MANAGER ---
    const AuthManager = {
        verificationTimer: null,
        init: function() {
            UIManager.showContainer(elements.loadingContainer);
            firebase.auth().onAuthStateChanged(user => {
                state.currentUser = user;
                state.isVerified = user ? user.emailVerified : false;
                clearInterval(this.verificationTimer);
                if (user) {
                    if (state.isVerified) {
                        this.loadDashboard(user);
                    } else {
                        UIManager.showContainer(elements.verificationContainer);
                        this.startVerificationCheck();
                        UIManager.updateAppNav(state.lang);
                        UIManager.updateContent(state.lang);
                    }
                } else {
                    state.userData = null;
                    UIManager.showContainer(elements.authContainer);
                    UIManager.showAuthForm('login-form');
                    UIManager.updateAppNav(state.lang);
                    UIManager.updateContent(state.lang);
                }
            });
        },
        
        getErrorMessage: function(error) {
             const t = translations[state.lang];
             if(error.code === 'auth/invalid-credential' || error.code === 'auth/invalid-login-credentials' || error.code === 'auth/user-not-found' || error.code === 'auth/wrong-password') return t.authErrorInvalid;
             if(error.code === 'auth/email-already-in-use') return t.authErrorEmailInUse;
             if(error.code === 'auth/weak-password') return t.authErrorWeakPassword;
             if(error.code === 'auth/too-many-requests') return t.authErrorTooManyRequests;
             return error.message || t.authErrorDefault;
        },
        startVerificationCheck: function() {
            this.verificationTimer = setInterval(async () => {
                if (state.currentUser) {
                    await state.currentUser.reload();
                    state.currentUser = firebase.auth().currentUser;
                    if (state.currentUser && state.currentUser.emailVerified) {
                        clearInterval(this.verificationTimer);
                        this.init();
                    }
                }
            }, 5000);
        },
        signUp: function() {
            const email = $('#signup-email').val();
            const password = $('#signup-password').val();
            elements.signupError.text('');
            firebase.auth().createUserWithEmailAndPassword(email, password)
                .then(cred => cred.user.sendEmailVerification())
                .catch(error => elements.signupError.text(AuthManager.getErrorMessage(error)));
        },
        logIn: function() {
            const email = $('#login-email').val();
            const password = $('#login-password').val();
            elements.loginError.text('');
            firebase.auth().signInWithEmailAndPassword(email, password)
                .catch(error => elements.loginError.text(AuthManager.getErrorMessage(error)));
        },
        logOut: function() { firebase.auth().signOut(); },
        resendVerification: function() {
            if (state.currentUser) state.currentUser.sendEmailVerification().catch(console.error);
        },
        deleteAccount: async function() {
            const t = translations[state.lang];
            if (!confirm(t.deleteAccountConfirm)) return;
            try {
                await db.collection('users').doc(state.currentUser.uid).delete();
                await state.currentUser.delete();
                window.location.reload();
            } catch (error) {
                alert("Error: " + error.message);
            }
        },

        loadDashboard: async function(user) {
            try {
                const doc = await db.collection('users').doc(user.uid).get();
                if (doc.exists) {
                    state.userData = doc.data();
                } else {
                    state.userData = { channels: [], weather: { locations: [] }, subscriptions: {} };
                }
                state.tempCustomContent = null; // Reset temp
                UIManager.showContainer(elements.dashboardContainer);
                UIManager.updateAppNav(state.lang);
                UIManager.updateContent(state.lang); 
            } catch (error) {
                console.error("Error:", error);
                elements.saveStatus.text("Error loading data.");
            }
        },

        saveSettings: async function() {
            const t = translations[state.lang];
            elements.saveStatus.text("");
            elements.saveSettingsButton.addClass('disabled');

            const telegramId = $('#telegram-id').val().trim();
            if (!telegramId) {
                elements.saveStatus.text(t.telegramSaveWarning).css('color', '#ff6384');
                elements.saveSettingsButton.removeClass('disabled');
                return;
            }

            // --- VALIDATION: Check Unique Telegram ID ---
            try {
                const channelQuery = { platform: "telegram", identifier: telegramId };
                const snapshot = await db.collection('users').where('channels', 'array-contains', channelQuery).get();
                
                let isDuplicate = false;
                snapshot.forEach(doc => {
                    if (doc.id !== state.currentUser.uid) isDuplicate = true;
                });

                if (isDuplicate) {
                    const errorMsg = state.lang === 'sk' ? "Toto Telegram ID už používa iný používateľ." : "This Telegram ID is already in use.";
                    elements.saveStatus.text(errorMsg).css('color', '#ff6384');
                    elements.saveSettingsButton.removeClass('disabled');
                    return;
                }
            } catch (error) {
                console.error("Validation error:", error);
            }
            // --------------------------------------------
            
            const timezone = $('#timezone-select').val();
            const weatherLocations = [];
            $('.weather-input').each(function() {
                const val = $(this).val().trim();
                if (val) weatherLocations.push({ location: val });
            });

            const subscriptions = {};
            let weatherRequired = false;
            
            $('.theme-row').each(function() {
                const baseId = $(this).data('theme-base-id');
                const isActive = $(this).find('.theme-active-cb').is(':checked');
                const timeKey = $(this).find('.theme-time-select').val();
                const selectedLang = $(this).find('.theme-lang-select').val();
                
                const selectedDays = [];
                $(this).find('.day-cb:checked').each(function() {
                    selectedDays.push(parseInt($(this).val()));
                });

                const themeConfig = APP_THEMES.find(th => th.id === baseId);

                if (isActive && themeConfig) {
                    const actualThemeId = themeConfig.variants[selectedLang];

                    if (actualThemeId) {
                        if (!subscriptions[timeKey]) {
                            subscriptions[timeKey] = [];
                        }
                        
                        subscriptions[timeKey].push({
                            theme: actualThemeId,
                            days: selectedDays
                        });

                        if (themeConfig.requiresWeather) {
                            weatherRequired = true;
                        }
                    }
                }
            });

            if (weatherRequired && weatherLocations.length === 0) {
                const errorMsg = state.lang === 'sk' 
                    ? "Pre zvolené témy (Ranný Prehľad) je povinné zadať aspoň jednu lokalitu počasia."
                    : "Weather location is required for selected themes (Morning Briefing).";
                
                elements.saveStatus.text(errorMsg).css('color', '#ff6384');
                elements.saveSettingsButton.removeClass('disabled');
                return;
            }

            const existingDbLang = (state.userData && state.userData.language) || 'slovak';
            const currentAdminStatus = (state.userData && state.userData.isAdmin) || false;

            const dataToSave = {
                description: state.currentUser.email,
                active: true,
                language: existingDbLang,
                timezone: timezone,
                channels: [{ platform: "telegram", identifier: telegramId }],
                weather: { locations: weatherLocations },
                subscriptions: subscriptions,
                lastUpdated: firebase.firestore.FieldValue.serverTimestamp()
            };
            
            if (state.tempCustomContent) {
                dataToSave.custom_content = state.tempCustomContent;
            } else if (state.userData && state.userData.custom_content) {
                dataToSave.custom_content = state.userData.custom_content;
            }
            
            if(currentAdminStatus) {
                dataToSave.isAdmin = true;
            }

            try {
                await db.collection('users').doc(state.currentUser.uid).set(dataToSave);
                state.userData = { ...state.userData, ...dataToSave };
                elements.saveStatus.text(t.saveStatusSuccess).css('color', '#4bc0c0');
            } catch (error) {
                console.error("Save error:", error);
                elements.saveStatus.text(t.saveStatusError).css('color', '#ff6384');
            } finally {
                elements.saveSettingsButton.removeClass('disabled');
            }
        }
    };

    // --- 6. BIND EVENTS & START ---
    function bindEvents() {
        $(document.body).on('click', '#show-signup, [data-auth-form="signup-form"]', function(e) { e.preventDefault(); UIManager.showAuthForm('signup-form'); });
        $(document.body).on('click', '#show-login, [data-auth-form="login-form"]', function(e) { e.preventDefault(); UIManager.showAuthForm('login-form'); });
        $('#signup-button').on('click', AuthManager.signUp);
        $('#login-button').on('click', AuthManager.logIn);
        $(document.body).on('click', '#sidebar-logout-button', function(e) { e.preventDefault(); AuthManager.logOut(); });
        $('#resend-verification-button').on('click', AuthManager.resendVerification);
        
        // Verification Logout
        $('#verification-logout').on('click', function(e) {
            e.preventDefault();
            AuthManager.logOut();
        });
        
        $('#save-settings-button').on('click', AuthManager.saveSettings);
        $('.lang-option').on('click', function() { UIManager.setLanguage($(this).data('lang')); });
        
        elements.modalSaveBtn.on('click', UIBuilder.saveModal);
        elements.modalCancelBtn.on('click', UIBuilder.closeModal);
    }

    UIManager.initPageFx();
    AuthManager.init();
    bindEvents();
});

// End of webapp/assets/js/app.js (v. 0038)