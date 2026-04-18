
function googleTranslateElementInit() {
    new google.translate.TranslateElement({
        pageLanguage: 'en',
        includedLanguages: 'en,hi,te',
        layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
        autoDisplay: false
    }, 'google_translate_element');
}

(function() {
    function setCookie(name, value, days) {
        var expires = "";
        if (days) {
            var date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = "; expires=" + date.toUTCString();
        }
        // Set cookie for the whole domain and path
        document.cookie = name + "=" + (value || "") + expires + "; path=/";
        
        // Also try setting it for the host domain directly just in case
        const host = window.location.hostname;
        document.cookie = name + "=" + (value || "") + expires + "; path=/; domain=" + host;
    }

    function changeLanguage(lang) {
        if (!lang) return;
        
        // Save to local storage for persistence across reloads
        localStorage.setItem('selectedLanguage', lang);
        
        // Update URL hash immediately
        window.location.hash = "#googtrans(en|" + lang + ")";
        
        // Set the google translate cookie
        const cookieValue = '/en/' + lang;
        setCookie('googtrans', cookieValue, 1);
        
        // Sync with backend session
        fetch('/set_language', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lang: lang })
        }).then(() => {
            // Force reload to apply changes
            location.reload();
        }).catch(() => {
            // Fallback reload if backend call fails
            location.reload();
        });
    }

    // Attempt to apply the stored language preference on load
    function initLanguage() {
        const currentLang = localStorage.getItem('selectedLanguage') || 'en';
        const selectors = document.querySelectorAll('.language-selector');
        
        selectors.forEach(s => {
            s.value = currentLang;
            s.addEventListener('change', function() {
                changeLanguage(this.value);
            });
        });

        // If we have a preference that isn't 'en', ensure the hash and cookie are present
        if (currentLang !== 'en') {
            const hash = window.location.hash;
            if (!hash.includes('googtrans')) {
                window.location.hash = "#googtrans(en|" + currentLang + ")";
            }
            
            // Check if Google Translate widget is ready and try to force it if needed
            const checkWidget = setInterval(() => {
                const combo = document.querySelector('.goog-te-combo');
                if (combo) {
                    if (combo.value !== currentLang) {
                        combo.value = currentLang;
                        combo.dispatchEvent(new Event('change'));
                    }
                    clearInterval(checkWidget);
                }
            }, 500);
            
            // Safety: Clear interval after 5 seconds
            setTimeout(() => clearInterval(checkWidget), 5000);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initLanguage);
    } else {
        initLanguage();
    }

    window.changeLanguage = changeLanguage;
})();
