// webapp/assets/js/themes-config.js

/**
 * Configuration of available themes in the application.
 * Maps technical IDs (used by Python bot) to translation keys and defaults.
 * 
 * Defines which language variants (SK/EN/DE) are available for each theme.
 */
const APP_THEMES = [
    // 1. Morning Briefing
    {
        id: 'morning_briefing',
        labelKey: 'spotlight1_title',
        requiresWeather: true,
        defaultTime: '07',
        variants: {
            sk: 'morning_briefing_sk',
            en: 'morning_briefing_en',
            de: 'morning_briefing_de'
        }
    },
    // 2. Philosophical Bite
    {
        id: 'philosophy',
        labelKey: 'spotlight2_title',
        defaultTime: '09',
        variants: {
            sk: 'philosophy_mix',
            en: 'philosophy_mix_en',
            de: 'philosophy_mix_de'
        }
    },
    // 3. European Masterpiece
    {
        id: 'art',
        labelKey: 'spotlight3_title',
        defaultTime: '10',
        variants: {
            sk: 'european_art_sk',
            en: 'european_art_en',
            de: 'european_art_de'
        }
    },
    // 4. World Literature
    {
        id: 'world_literature',
        labelKey: 'spotlight_lit_title',
        defaultTime: '20',
        variants: {
            sk: 'world_literature',
            en: 'world_literature_en',
            de: 'world_literature_de'
        }
    },
    // 5. Memory of the Day
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
    // 6. German Lesson
    {
        id: 'german',
        labelKey: 'spotlight5_title',
        defaultTime: '14',
        variants: {
            sk: 'german_lesson',
            en: 'german_lesson_en'
        }
    },
    // 7. Spiritual Reflection
    {
        id: 'bible',
        labelKey: 'spotlight6_title',
        defaultTime: '08',
        variants: {
            sk: 'bible_sk',
            en: 'bible_en',
            de: 'bible_de'
        }
    },
    // 8. Bible Study (New Testament)
    // Removed hardcoded 'suffix' to allow full translation via labelKey
    {
        id: 'novy_zakon',
        labelKey: 'bible_study_nt', 
        defaultTime: '18',
        variants: {
            sk: 'novy_zakon_sk',
            en: 'novy_zakon_en',
            de: 'novy_zakon_de'
        }
    },
    // 9. Bible Study (Old Testament)
    // Removed hardcoded 'suffix' to allow full translation via labelKey
    {
        id: 'stary_zakon',
        labelKey: 'bible_study_ot',
        defaultTime: '19',
        variants: {
            sk: 'stary_zakon_sk',
            en: 'stary_zakon_en',
            de: 'stary_zakon_de'
        }
    },
    // 10. User Reminder
    {
        id: 'user_reminder',
        labelKey: 'themeUserReminder',
        defaultTime: '11',
        isEditable: true,
        variants: {
            sk: 'user_reminder',
            en: 'user_reminder_en',
            de: 'user_reminder_de'
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

// End of webapp/assets/js/themes-config.js (v. 0013)
