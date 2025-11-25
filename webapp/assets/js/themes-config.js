// webapp/assets/js/themes-config.js

/**
 * Configuration of available themes in the application.
 * Maps technical IDs (used by Python bot) to translation keys and defaults.
 */
const APP_THEMES = [
    {
        id: 'morning_briefing',
        labelKey: 'spotlight1_title',
        requiresWeather: true,
        defaultTime: '07',
        variants: {
            sk: 'morning_briefing_sk',
            en: 'morning_briefing_en'
        }
    },
    {
        id: 'bible',
        labelKey: 'spotlight6_title',
        defaultTime: '08',
        variants: {
            sk: 'bible_sk',
            en: 'bible_en'
        }
    },
    {
        id: 'philosophy',
        labelKey: 'spotlight2_title',
        defaultTime: '09',
        variants: {
            sk: 'philosophy_mix',
            en: 'philosophy_mix_en'
        }
    },
    {
        id: 'art',
        labelKey: 'spotlight3_title',
        defaultTime: '10',
        variants: {
            sk: 'european_art',
            en: 'european_art_en'
        }
    },
    {
        id: 'german',
        labelKey: 'spotlight5_title',
        defaultTime: '14',
        variants: {
            sk: 'german_lesson',
            en: 'german_lesson_en'
        }
    },
    {
        id: 'novy_zakon',
        labelKey: 'spotlight7_title', 
        suffix: '(Nový Zákon)',
        defaultTime: '18',
        variants: {
            sk: 'novy_zakon_sk',
            en: 'novy_zakon_en'
        }
    },
    {
        id: 'stary_zakon',
        labelKey: 'spotlight7_title',
        suffix: '(Starý Zákon)',
        defaultTime: '19',
        variants: {
            sk: 'stary_zakon_sk',
            en: 'stary_zakon_en'
        }
    },
    {
        id: 'family',
        labelKey: 'spotlight4_title',
        adminOnly: true,
        defaultTime: '12',
        variants: {
            sk: 'family_photo',
            en: 'family_photo_en'
        }
    },
    // --- USER REMINDER ---
    {
        id: 'user_reminder',
        labelKey: 'themeUserReminder',
        defaultTime: '11',
        isEditable: true,
        variants: {
            sk: 'user_reminder',
            en: 'user_reminder_en' // Enabled English variant!
        }
    }
];

/**
 * Supported Timezones for the Dropdown
 */
const TIMEZONES = [
    { value: "Europe/Bratislava", label: "Europe/Bratislava (Stredná Európa)" },
    { value: "Europe/London", label: "Europe/London (UK, Írsko)" },
    { value: "America/New_York", label: "America/New_York (USA Východ)" },
    { value: "America/Chicago", label: "America/Chicago (USA Stred)" },
    { value: "America/Denver", label: "America/Denver (USA Hory)" },
    { value: "America/Los_Angeles", label: "America/Los_Angeles (USA Západ)" },
    { value: "Asia/Tokyo", label: "Asia/Tokyo (Japonsko)" },
    { value: "Australia/Sydney", label: "Australia/Sydney (Austrália)" },
    { value: "UTC", label: "UTC (Univerzálny čas)" }
];

// End of webapp/assets/js/themes-config.js (v. 0009)