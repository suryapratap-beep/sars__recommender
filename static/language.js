
/**
 * STABLE LANGUAGE SYSTEM
 */

function googleTranslateElementInit() {
  new google.translate.TranslateElement({
    pageLanguage: 'en',
    includedLanguages: 'en,hi,es,fr',
    layout: google.translate.TranslateElement.InlineLayout.SIMPLE
  }, 'google_translate_element');
}

function changeLanguage(lang) {
    if (!lang) return;
    
    const currentLang = localStorage.getItem('selectedLanguage');
    if (currentLang === lang && window.location.hash.includes(lang)) {
        return; // Already set, avoid loop
    }

    localStorage.setItem('selectedLanguage', lang);
    const hash = `#googtrans(en|${lang})`;
    
    // Set cookie
    const expires = "; expires=" + new Date(Date.now() + 31536000000).toUTCString();
    document.cookie = "googtrans=/en/" + lang + expires + "; path=/";
    
    // Update hash and reload
    window.location.hash = hash;
    window.location.reload();
}

document.addEventListener('DOMContentLoaded', () => {
    const savedLang = localStorage.getItem('selectedLanguage') || 'en';
    
    // 1. Sync the custom dropdowns
    document.querySelectorAll('.language-selector').forEach(s => {
        s.value = savedLang;
        s.onchange = (e) => changeLanguage(e.target.value);
    });

    // 2. Poll for the Google Widget and force it to match our savedLang
    let checkCount = 0;
    const interval = setInterval(() => {
        const combo = document.querySelector('.goog-te-combo');
        if (combo) {
            if (savedLang !== 'en' && combo.value !== savedLang) {
                combo.value = savedLang;
                combo.dispatchEvent(new Event('change'));
            }
            clearInterval(interval);
        }
        if (++checkCount > 20) clearInterval(interval);
    }, 500);

    // 3. Simple UI hide to keep it clean but functional
    const g = document.getElementById('google_translate_element');
    if (g) {
        g.style.opacity = "0.01";
        g.style.position = "absolute";
        g.style.top = "0";
        g.style.left = "0";
        g.style.pointerEvents = "none";
    }
});
