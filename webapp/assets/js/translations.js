// webapp/assets/js/translations.js

const translations = {
    // Slovak translations
    sk: {
        // -- Page Title --
        pageTitle: "YourDailyPulse | Vaša denná dávka inšpirácie",

        // -- Sidebar Navigation --
        navWelcome: "Vitajte",
        navShowcase: "Ukážky Tém",
        navHowItWorks: "Ako to funguje",
        navTryIt: "Vyskúšajte",
        
        // -- Generic Page Header --
        headerHome: "Domov",
        headerMoreThemes: "Ďalšie Témy",
        headerEnterApp: "Vstúpiť do Aplikácie",

        // -- Intro Section --
        introHeader: "YourDailyPulse",
        introSubtitle: "Vaša denná dávka inšpirácie, vedomostí a reflexie, doručená priamo k vám.<br />Personalizovaný obsah, ktorý rešpektuje váš čas a záujmy.",
        introButton: "Zobraziť Ukážky",

        // -- Spotlights Section (Showcase) --
        spotlightButton_learnMore: "Zistiť Viac",
        
        spotlight1_title: "Ranný Prehľad",
        spotlight1_desc: "Začnite deň informovane. Váš osobný brífing s počasím, meninami, historickými udalosťami a dávkou zaujímavostí, všetko inteligentne zhrnuté umelou inteligenciou.",
        
        spotlight2_title: "Filozofická Jednohubka",
        spotlight2_desc: "Rozšírte si obzory s myšlienkami veľkých filozofov. Každý deň jeden citát, jeho moderná interpretácia a paradox na zamyslenie.",

        spotlight3_title: "Dnešné Európske Dielo",
        spotlight3_desc: "Objavte poklady európskeho umenia. Každý deň vám predstavíme jedno významné dielo z Metropolitného múzea umenia, vrátane detailov o autorovi a technike.",

        spotlight4_title: "Spomienka Dňa",
        spotlight4_desc: "Pripomeňte si vzácne chvíle. Každý deň jedna fotografia z vášho rodinného archívu spolu s myšlienkou o rodine.",

        spotlight5_title: "Lekcia Nemčiny",
        spotlight5_desc: "Zlepšujte sa v nemčine každý deň. Systematicky vám predstavíme nové slovíčka, gramatiku a frázy v kontexte, aby ste si jazyk osvojili prirodzene.",
        
        spotlight6_title: "Duchovná Reflexia",
        spotlight6_desc: "Stíšte sa s denným biblickým textom. Pripravíme pre vás zamyslenie, krátku modlitbu a otázku na reflexiu, ktorá vás bude sprevádzať počas dňa.",

        spotlight7_title: "Štúdium Biblie",
        spotlight7_desc: "Ponorte sa hlbšie do textov Starého a Nového zákona. Každá lekcia prináša detailný historický a duchovný kontext k vybranému veršu.",

        // --- NEW SPOTLIGHT ---
        spotlight8_title: "Užívateľská Pripomienka",
        spotlight8_desc: "Vytvorte si vlastný obsah. Nastavte si denné pripomienky, odkazy na obedové menu reštaurácií alebo motivačné citáty, ktoré chcete vidieť každý deň.",

        // -- Features Section --
        featuresHeader: "Ako to funguje",
        featuresSubtitle: "YourDailyPulse je navrhnutý pre maximálnu jednoduchosť a flexibilitu. Vyberte si témy, nastavte čas a o ostatné sa postaráme my.",
        
        feature1_title: "Plne Personalizovateľné",
        feature1_desc: "Vyberte si len témy, ktoré vás zaujímajú, a nastavte si čas doručenia, ktorý vám vyhovuje.",
        
        feature2_title: "Rôznorodé Témy",
        feature2_desc: "Od duchovnej reflexie, cez jazykové lekcie až po filozofiu. Neustále pridávame nový obsah.",
        
        feature3_title: "Viacjazyčný Obsah",
        feature3_desc: "Vyberte si preferovaný jazyk a dostávajte obsah pripravený špeciálne pre vás.",
        
        feature4_title: "Doručenie na Telegram",
        feature4_desc: "Všetok obsah vám pohodlne doručíme na platformu, ktorú už používate každý deň.",
        
        feature5_title: "Bezpečné a Súkromné",
        feature5_desc: "Vaše nastavenia sú len vaše. Rešpektujeme vaše súkromie a nikdy nezdieľame vaše dáta.",
        
        feature6_title: "Inteligentné Generovanie",
        feature6_desc: "Využívame pokročilú umelú inteligenciu na tvorbu unikátneho a hodnotného obsahu každý deň.",
        
        featuresButton: "Vyskúšať",

        // -- Call to Action Section --
        ctaHeader: "Začnite ešte dnes",
        ctaSubtitle: "Registrácia je bezplatná a trvá len minútu. Vytvorte si účet a objavte svoj denný pulz inšpirácie a vedomostí.",
        ctaButton: "Vstúpiť do Aplikácie",

        // -- Footer --
        footerRights: `&copy; 2025 <a href="https://github.com/OpenXFlow/PulserBot">PulserBot</a> (MIT License) | Kontakt: <a href="mailto:yourpulserbot@gmail.com">yourpulserbot@gmail.com</a>`,

        // -- App Translations --
        appLoading: "Loading application...",
        appPleaseWait: "Prosím, čakajte.",
        
        // Auth Forms
        loginTitle: "Prihlásenie",
        loginButton: "Prihlásiť sa",
        loginSwitch: "Nemáte účet? <a href=\"#\" id=\"show-signup\">Zaregistrujte sa</a>",
        loginForgotPassword: "Zabudli ste heslo?",
        
        signupTitle: "Registrácia",
        signupButton: "Zaregistrovať sa",
        signupSwitch: "Už máte účet? <a href=\"#\" id=\"show-login\">Prihláste sa</a>",
        
        // Password Reset
        resetPasswordTitle: "Obnova hesla",
        resetPasswordButton: "Poslať obnovovací link",
        resetPasswordBack: "Späť na prihlásenie",
        resetPasswordSuccess: "Email na obnovu hesla bol odoslaný. Skontrolujte si schránku.",
        resetPasswordError: "Chyba: Skontrolujte emailovú adresu.",

        // Auth Errors
        authErrorInvalid: "Nesprávny email alebo heslo.",
        authErrorUserNotFound: "Používateľ s týmto emailom neexistuje.",
        authErrorEmailInUse: "Tento email sa už používa.",
        authErrorWeakPassword: "Heslo je príliš slabé (min. 6 znakov).",
        authErrorTooManyRequests: "Príliš veľa pokusov. Skúste to neskôr.",
        authErrorDefault: "Nastala chyba. Skúste to znova.",
        
        passwordPlaceholder: "Heslo (min. 6 znakov)",

        // Verification Screen
        verifyTitle: "Overte svoj email",
        verifyText1: "Ďakujeme za registráciu! Poslali sme vám overovací odkaz na vašu emailovú adresu.",
        verifyText2: "Prosím, kliknite na odkaz v emaili pre aktiváciu vášho účtu. Následne sa môžete prihlásiť.",
        verifyButton: "Poslať znova",
        verifyStatusSuccess: "Nový email bol odoslaný.",
        verifyLogout: "Odhlásiť sa / Zmeniť účet",
        
        // Dashboard General
        welcomeMessage: "Vitajte, {email}!",
        dashboardSubtitle: "Tu si môžete spravovať vaše denné nastavenia.",
        
        // Dashboard Setup - TELEGRAM
        telegramSetupTitle: "1. Nastavenie Telegramu (Povinné)",
        telegramInstruction1: "Otvorte aplikáciu Telegram a v hornej časti kliknite na <strong>ikonu lupy 🔍</strong> (vyhľadávanie).",
        telegramInstruction2: "Do vyhľadávacieho poľa napíšte <strong>@userinfobot</strong>, kliknite na výsledok a stlačte tlačidlo <strong>Start</strong>.",
        telegramInstruction3: "Bot vám odpovie správou s vaším ID (napr. 123456789). Toto číslo skopírujte a vložte do poľa nižšie:",
        telegramInstruction4Title: "Dôležitý Posledný Krok:",
        telegramInstruction4Text: "Musíte aktivovať nášho bota, inak vám správy nedorazia. Vyhľadajte <strong>YourDailyPulse</strong> a stlačte <strong>Start</strong>. Práve do tohto chatu vám bude chodiť váš obsah.",
        telegramIdPlaceholder: "Vložte vaše Telegram ID",
        telegramSaveWarning: "Bez Telegram ID vám nebudeme môcť doručovať správy.",
        
        // Dashboard Setup - TIMEZONE
        timezoneSetupTitle: "2. Časová Zóna",
        timezoneInfo: "Nastavte si časovú zónu, aby sme vám správy doručovali presne vtedy, kedy chcete.",
        
        // Dashboard Setup - WEATHER
        weatherSetupTitle: "3. Nastavenie Počasia",
        weatherAddLocation: "+ Pridať lokalitu",
        weatherPlaceholder: "Mesto, Krajina (napr. Bratislava,SK)",
        weatherInfo: "Povinné, ak odoberáte Ranný Prehľad.",
        
        // Dashboard Setup - THEMES
        themesSetupTitle: "4. Výber Tém a Času",
        themeTimeLabel: "Čas:",
        themeLangLabel: "Jazyk:",
        themeActiveLabel: "Aktívne",
        themeUserReminder: "Užívateľská Pripomienka",
        btnEditContent: "Upraviť Obsah",
        
        // Days of Week Shortcuts
        daysShort: ["Po", "Ut", "St", "Št", "Pi", "So", "Ne"],

        saveSettingsButton: "Uložiť Všetky Nastavenia",
        saveStatusSuccess: "Nastavenia úspešne uložené!",
        saveStatusError: "Chyba pri ukladaní.",
        dangerZoneTitle: "Nebezpečná Zóna",
        deleteAccountButton: "Zmazať Účet",
        deleteAccountConfirm: "Ste si istý? Táto akcia je nezvratná. Všetky vaše nastavenia a dáta budú vymazané.",
        deleteAccountReauth: "Pre vašu bezpečnosť sa musíte odhlásiť a znova prihlásiť, aby ste mohli zmazať účet.",
        
        // Modal
        modalTitle: "Upraviť Pripomienku",
        modalDesc: "Vložte vlastný text a odkazy, ktoré vám doručíme.",
        modalLabelBlocks: "Textové bloky (Max 3)",
        modalLabelLinks: "Odkazy (Max 3)",
        modalPlaceholderText: "Napr. Nezabudni vypiť vodu...",
        modalPlaceholderTitle: "Názov odkazu (napr. Menu)",
        modalPlaceholderUrl: "https://...",
        modalBtnSave: "Uložiť a Zavrieť",
        modalBtnCancel: "Zrušiť",

        backToHome: "&laquo; Späť na hlavnú stránku",
        navLogin: "Prihlásenie",
        navSignup: "Registrácia",
        navSettings: "Moje Nastavenia",
        navProfile: "Profil",
        navLogout: "Odhlásiť sa"
    },

    // English translations
    en: {
        // -- Page Title --
        pageTitle: "YourDailyPulse | Your daily dose of inspiration",

        // -- Sidebar Navigation --
        navWelcome: "Welcome",
        navShowcase: "Theme Showcase",
        navHowItWorks: "How It Works",
        navTryIt: "Try It",

        // -- Generic Page Header --
        headerHome: "Home",
        headerMoreThemes: "More Themes",
        headerEnterApp: "Enter App",

        // -- Intro Section --
        introHeader: "YourDailyPulse",
        introSubtitle: "Your daily dose of inspiration, knowledge, and reflection, delivered directly to you.<br />Personalized content that respects your time and interests.",
        introButton: "View Showcase",

        // -- Spotlights Section (Showcase) --
        spotlightButton_learnMore: "Learn More",
        
        spotlight1_title: "Morning Briefing",
        spotlight1_desc: "Start your day informed. Your personal briefing with weather, name days, historical events, and a dose of trivia, all intelligently summarized by AI.",
        
        spotlight2_title: "Philosophical Bite",
        spotlight2_desc: "Broaden your horizons with the ideas of great philosophers. Each day brings a quote, its modern interpretation, and a paradox to ponder.",

        spotlight3_title: "European Masterpiece of the Day",
        spotlight3_desc: "Discover the treasures of European art. Each day, we'll introduce one significant work from The Metropolitan Museum of Art, including details about the artist and technique.",

        spotlight4_title: "Memory of the Day",
        spotlight4_desc: "Reminisce about precious moments. Every day, a photo from your family archive is paired with a thought about family.",

        spotlight5_title: "German Lesson",
        spotlight5_desc: "Improve your German every day. We systematically introduce new vocabulary, grammar, and phrases in context, helping you to acquire the language naturally.",
        
        spotlight6_title: "Spiritual Reflection",
        spotlight6_desc: "Find a moment of peace with a daily biblical text. We prepare a thought, a short prayer, and a question for reflection to accompany you through the day.",

        spotlight7_title: "Bible Study",
        spotlight7_desc: "Dive deeper into the texts of the Old and New Testaments. Each lesson provides detailed historical and spiritual context to a selected verse.",

        // --- NEW SPOTLIGHT ---
        spotlight8_title: "User Reminder",
        spotlight8_desc: "Create your own content. Set up daily reminders, links to restaurant lunch menus, or motivational quotes you want to see every day.",

        // -- Features Section --
        featuresHeader: "How It Works",
        featuresSubtitle: "YourDailyPulse is designed for maximum simplicity and flexibility. Choose your topics, set the time, and we'll take care of the rest.",
        
        feature1_title: "Fully Customizable",
        feature1_desc: "Select only the topics that interest you and set a delivery time that fits your schedule.",
        
        feature2_title: "Diverse Topics",
        feature2_desc: "From spiritual reflection and language lessons to philosophy. We are constantly adding new content.",
        
        feature3_title: "Multilingual Content",
        feature3_desc: "Choose your preferred language and receive content prepared especially for you.",
        
        feature4_title: "Telegram Delivery",
        feature4_desc: "All content is conveniently delivered to the platform you already use every day.",
        
        feature5_title: "Secure and Private",
        feature5_desc: "Your settings are yours alone. We respect your privacy and never share your data.",
        
        feature6_title: "Intelligent Generation",
        feature6_desc: "We utilize advanced artificial intelligence to create unique and valuable content every day.",
        featuresButton: "Try It",
        ctaHeader: "Get Started Today",
        ctaSubtitle: "Registration is free and takes just a minute. Create an account and discover your daily pulse of inspiration and knowledge.",
        ctaButton: "Enter the App",
        footerRights: `&copy; 2025 <a href="https://github.com/OpenXFlow/PulserBot">PulserBot</a> (MIT License) | Contact: <a href="mailto:yourpulserbot@gmail.com">yourpulserbot@gmail.com</a>`,
        appLoading: "Loading application...",
        appPleaseWait: "Please wait.",
        loginTitle: "Login",
        loginButton: "Log In",
        loginSwitch: "Don't have an account? <a href=\"#\" id=\"show-signup\">Sign up</a>",
        loginForgotPassword: "Forgot Password?",

        signupTitle: "Sign Up",
        signupButton: "Sign Up",
        signupSwitch: "Already have an account? <a href=\"#\" id=\"show-login\">Log in</a>",
        
        // Password Reset
        resetPasswordTitle: "Reset Password",
        resetPasswordButton: "Send Reset Link",
        resetPasswordBack: "Back to Login",
        resetPasswordSuccess: "Password reset email sent. Check your inbox.",
        resetPasswordError: "Error: Check your email address.",

        authErrorInvalid: "Invalid email or password.",
        authErrorUserNotFound: "User not found.",
        authErrorEmailInUse: "Email already in use.",
        authErrorWeakPassword: "Password is too weak (min. 6 chars).",
        authErrorTooManyRequests: "Too many requests. Try again later.",
        authErrorDefault: "An error occurred. Please try again.",
        
        passwordPlaceholder: "Password (min. 6 chars)",

        verifyTitle: "Verify Your Email",
        verifyText1: "Thank you for signing up! We've sent a verification link to your email address.",
        verifyText2: "Please click the link in the email to activate your account. You can then log in.",
        verifyButton: "Resend Email",
        verifyStatusSuccess: "A new email has been sent.",
        verifyLogout: "Log Out / Change Account",
        welcomeMessage: "Welcome, {email}!",
        dashboardSubtitle: "Here you can manage your daily settings.",
        telegramSetupTitle: "1. Telegram Setup (Required)",
        telegramInstruction1: "Open the Telegram app. Click on the <strong>magnifying glass icon 🔍</strong> (search) at the top.",
        telegramInstruction2: "Type <strong>@userinfobot</strong> into the search bar, click on the result, and press the <strong>Start</strong> button.",
        telegramInstruction3: "The bot will reply with a number (Your ID). Copy and paste it into the field below:",
        telegramInstruction4Title: "Important Final Step:",
        telegramInstruction4Text: "You must activate our bot, otherwise messages will not arrive. Search for <strong>YourDailyPulse</strong> and press <strong>Start</strong>. This is the chat where you will receive your daily content.",
        telegramIdPlaceholder: "Paste your Telegram ID",
        telegramSaveWarning: "We cannot deliver messages without a Telegram ID.",
        
        // --- NEW SECTIONS ---
        timezoneSetupTitle: "2. Timezone",
        timezoneInfo: "Set your timezone so we can deliver messages exactly when you want them.",
        
        weatherSetupTitle: "3. Weather Setup",
        weatherAddLocation: "+ Add Location",
        weatherPlaceholder: "City, Country (e.g. London,UK)",
        weatherInfo: "Required if you subscribe to Morning Briefing.",
        
        themesSetupTitle: "4. Theme Selection & Time",
        themeTimeLabel: "Time:",
        themeLangLabel: "Lang:",
        themeActiveLabel: "Active",
        themeUserReminder: "User Reminder",
        btnEditContent: "Edit Content",
        
        // Days of Week Shortcuts
        daysShort: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],

        saveSettingsButton: "Save All Settings",
        saveStatusSuccess: "Settings saved successfully!",
        saveStatusError: "Error saving settings.",
        dangerZoneTitle: "Danger Zone",
        deleteAccountButton: "Delete Account",
        deleteAccountConfirm: "Are you sure? This action is irreversible. All your settings and data will be deleted.",
        deleteAccountReauth: "For your security, you must log out and log in again to delete your account.",
        
        // Modal
        modalTitle: "Edit Reminder",
        modalDesc: "Insert your own text and links to be delivered.",
        modalLabelBlocks: "Text Blocks (Max 3)",
        modalLabelLinks: "Links (Max 3)",
        modalPlaceholderText: "E.g. Don't forget to drink water...",
        modalPlaceholderTitle: "Link Title (e.g. Menu)",
        modalPlaceholderUrl: "https://...",
        modalBtnSave: "Save & Close",
        modalBtnCancel: "Cancel",

        backToHome: "&laquo; Back to Home Page",
        navLogin: "Login",
        navSignup: "Sign Up",
        navSettings: "My Settings",
        navProfile: "Profile",
        navLogout: "Log Out"
    }
};

// End of webapp/assets/js/translations.js (v. 0023)
