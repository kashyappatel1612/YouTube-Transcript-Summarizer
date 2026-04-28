document.addEventListener('DOMContentLoaded', () => {
    const urlInput = document.getElementById('urlInput');
    const summarizeBtn = document.getElementById('summarizeBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorMsg = document.getElementById('errorMsg');
    const resultsSection = document.getElementById('resultsSection');
    const summaryContent = document.getElementById('summaryContent');
    const translateBtn = document.getElementById('translateBtn');
    const languageSelect = document.getElementById('languageSelect');
    const translationCard = document.getElementById('translationCard');
    const translationLoading = document.getElementById('translationLoading');
    const translationContent = document.getElementById('translationContent');
    const translatedLangLabel = document.getElementById('translatedLangLabel');
    
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsModal = document.getElementById('settingsModal');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const saveApiBtn = document.getElementById('saveApiBtn');
    const apiKeyInput = document.getElementById('apiKeyInput');
    const apiStatusMessage = document.getElementById('apiStatusMessage');

    let currentSummaryText = "";

    if (!window.APP_CONFIG.apiKeySet) {
        setTimeout(() => { settingsModal.classList.remove('hidden'); }, 1000);
    }

    const closeModal = () => { settingsModal.classList.add('hidden'); };

    settingsBtn.addEventListener('click', () => {
        settingsModal.classList.remove('hidden');
        apiStatusMessage.classList.add('hidden');
    });
    
    closeModalBtn.addEventListener('click', closeModal);
    settingsModal.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal-overlay')) closeModal();
    });

    const showApiStatus = (message, type) => {
        apiStatusMessage.textContent = message;
        apiStatusMessage.className = `status-msg ${type}`;
        apiStatusMessage.classList.remove('hidden');
    };

    saveApiBtn.addEventListener('click', async () => {
        const apiKey = apiKeyInput.value.trim();
        if (!apiKey) {
            showApiStatus("API Key cannot be empty", 'error');
            return;
        }

        saveApiBtn.textContent = "Saving...";
        saveApiBtn.disabled = true;

        try {
            const response = await fetch('/api/configure', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: apiKey })
            });
            const data = await response.json();
            if (data.success) {
                showApiStatus("API key saved successfully!", 'success');
                window.APP_CONFIG.apiKeySet = true;
                setTimeout(closeModal, 1500);
            } else {
                showApiStatus(data.message, 'error');
            }
        } catch (err) {
            showApiStatus("Network error occurred", 'error');
        } finally {
            saveApiBtn.textContent = "Save Key";
            saveApiBtn.disabled = false;
        }
    });

    const showError = (message) => {
        errorMsg.textContent = message;
        errorMsg.classList.remove('hidden');
    }

    summarizeBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        
        if (!url || (!url.includes('youtube.com') && !url.includes('youtu.be'))) {
            showError("Please enter a valid YouTube URL");
            return;
        }

        if (!window.APP_CONFIG.apiKeySet) {
            settingsModal.classList.remove('hidden');
            showApiStatus("Please configure your API key first", 'error');
            return;
        }

        errorMsg.classList.add('hidden');
        resultsSection.classList.add('hidden');
        translationCard.classList.add('hidden');
        loadingIndicator.classList.remove('hidden');
        summarizeBtn.disabled = true;

        try {
            const response = await fetch('/api/summarize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url })
            });
            const data = await response.json();

            if (data.success) {
                currentSummaryText = data.summary;
                summaryContent.innerHTML = marked.parse(currentSummaryText);
                resultsSection.classList.remove('hidden');
            } else {
                if (data.message.includes('missing')) {
                    settingsModal.classList.remove('hidden');
                } else {
                    showError(data.message);
                }
            }
        } catch (err) {
            showError("A network error occurred.");
        } finally {
            loadingIndicator.classList.add('hidden');
            summarizeBtn.disabled = false;
        }
    });

    translateBtn.addEventListener('click', async () => {
        if (!currentSummaryText) return;

        const lang = languageSelect.value;
        translatedLangLabel.textContent = lang;
        
        translationCard.classList.remove('hidden');
        translationContent.innerHTML = '';
        translationLoading.classList.remove('hidden');
        translateBtn.disabled = true;

        try {
            const response = await fetch('/api/translate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    text: currentSummaryText,
                    language: lang
                })
            });
            const data = await response.json();

            if (data.success) {
                translationContent.innerHTML = marked.parse(data.translation);
            } else {
                translationContent.innerHTML = `<p class="error-msg">Failed: ${data.message}</p>`;
            }
        } catch (err) {
            translationContent.innerHTML = `<p class="error-msg">A network error occurred.</p>`;
        } finally {
            translationLoading.classList.add('hidden');
            translateBtn.disabled = false;
        }
    });
});
