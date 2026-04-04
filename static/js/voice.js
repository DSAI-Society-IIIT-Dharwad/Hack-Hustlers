/**
 * ═══════════════════════════════════════════════════════════════
 * Voice Module — Speech Recognition & Text-to-Speech
 *
 * ASR: Uses Web Speech API (Chrome) — continuous, auto-restart.
 *      Patient speech is sent to the server in the original language.
 *      Server auto-translates ANY language → English via Google Translate.
 *
 * Supported for ASR: All languages with a BCP-47 code.
 *   (Hindi, Kannada, Telugu, Tamil, Malayalam, Marathi, Gujarati,
 *    Spanish, French, Arabic, Bengali, Punjabi, Urdu, English, etc.)
 * ═══════════════════════════════════════════════════════════════
 */

const LANGUAGES = {
    'en':   { name: 'English',    code: 'en-US',  flag: '🇬🇧' },
    'hi':   { name: 'Hindi',      code: 'hi-IN',  flag: '🇮🇳' },
    'kn':   { name: 'Kannada',    code: 'kn-IN',  flag: '🇮🇳' },
    'te':   { name: 'Telugu',     code: 'te-IN',  flag: '🇮🇳' },
    'ta':   { name: 'Tamil',      code: 'ta-IN',  flag: '🇮🇳' },
    'ml':   { name: 'Malayalam',  code: 'ml-IN',  flag: '🇮🇳' },
    'mr':   { name: 'Marathi',    code: 'mr-IN',  flag: '🇮🇳' },
    'gu':   { name: 'Gujarati',   code: 'gu-IN',  flag: '🇮🇳' },
    'pa':   { name: 'Punjabi',    code: 'pa-IN',  flag: '🇮🇳' },
    'bn':   { name: 'Bengali',    code: 'bn-IN',  flag: '🇮🇳' },
    'ur':   { name: 'Urdu',       code: 'ur-PK',  flag: '🇵🇰' },
    'tulu': { name: 'Tulu',       code: 'kn-IN',  flag: '🇮🇳' },
    'bho':  { name: 'Bhojpuri',   code: 'hi-IN',  flag: '🇮🇳' },
    'es':   { name: 'Spanish',    code: 'es-ES',  flag: '🇪🇸' },
    'fr':   { name: 'French',     code: 'fr-FR',  flag: '🇫🇷' },
    'ar':   { name: 'Arabic',     code: 'ar-SA',  flag: '🇸🇦' },
    'zh':   { name: 'Chinese',    code: 'zh-CN',  flag: '🇨🇳' },
    'de':   { name: 'German',     code: 'de-DE',  flag: '🇩🇪' },
    'ru':   { name: 'Russian',    code: 'ru-RU',  flag: '🇷🇺' },
    'pt':   { name: 'Portuguese', code: 'pt-PT',  flag: '🇵🇹' },
    'ja':   { name: 'Japanese',   code: 'ja-JP',  flag: '🇯🇵' },
    'ko':   { name: 'Korean',     code: 'ko-KR',  flag: '🇰🇷' },
};

class VoiceEngine {
    constructor(options = {}) {
        this.recognition    = null;
        this.isRecording    = false;
        this.currentLanguage= options.language || 'en';
        this.onTranscript   = options.onTranscript   || (() => {});
        this.onInterim      = options.onInterim      || (() => {});
        this.onStatusChange = options.onStatusChange || (() => {});
        this.onError        = options.onError        || (() => {});

        this.mediaRecorder  = null;
        this.audioChunks    = [];
        this._restartTimer  = null;

        this._initSpeechRecognition();
    }

    _initSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            this.onError('Speech Recognition is not supported. Please use Google Chrome.');
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous      = true;
        this.recognition.interimResults  = true;
        this.recognition.maxAlternatives = 3;  // pick best alternative

        this._setLanguage(this.currentLanguage);

        // ── Handlers ──
        this.recognition.onstart = () => {
            this.isRecording = true;
            this.onStatusChange('recording');
        };

        this.recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript   = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                // Pick highest-confidence alternative
                let best = event.results[i][0];
                for (let j = 1; j < event.results[i].length; j++) {
                    if (event.results[i][j].confidence > best.confidence) {
                        best = event.results[i][j];
                    }
                }

                if (event.results[i].isFinal) {
                    finalTranscript += best.transcript;
                } else {
                    interimTranscript += best.transcript;
                }
            }

            if (interimTranscript) {
                this.onInterim(interimTranscript);
            }

            if (finalTranscript.trim()) {
                this.onTranscript({
                    original:   finalTranscript.trim(),
                    translated: finalTranscript.trim(), // server handles actual translation
                    language:   this.currentLanguage,   // the key, e.g. 'hi', 'kn'
                    langCode:   (LANGUAGES[this.currentLanguage] || {}).code || 'en-US',
                    timestamp:  getNowTimestamp()
                });
            }
        };

        this.recognition.onerror = (event) => {
            // 'no-speech' is normal — silently ignore
            if (event.error === 'no-speech') return;
            // 'aborted' happens on manual stop — ignore
            if (event.error === 'aborted') return;

            console.warn('ASR error:', event.error);
            if (event.error === 'not-allowed') {
                this.onError('Microphone access denied. Please allow microphone in browser settings.');
            } else if (event.error === 'network') {
                this.onError('Network error: ASR requires internet. Attempting restart...');
                this._scheduleRestart();
            } else {
                this.onError(`Speech error: ${event.error}`);
            }
        };

        this.recognition.onend = () => {
            // Auto-restart when still in recording mode (Chrome stops after silence)
            if (this.isRecording) {
                this._scheduleRestart();
            } else {
                this.onStatusChange('stopped');
            }
        };
    }

    _scheduleRestart(delay = 200) {
        clearTimeout(this._restartTimer);
        this._restartTimer = setTimeout(() => {
            if (this.isRecording && this.recognition) {
                try { this.recognition.start(); } catch (e) {}
            }
        }, delay);
    }

    _setLanguage(langKey) {
        const lang = LANGUAGES[langKey];
        if (lang && this.recognition) {
            this.recognition.lang = lang.code;
        }
        this.currentLanguage = langKey;
    }

    setLanguage(langKey) {
        this._setLanguage(langKey);
        if (this.isRecording) {
            this.isRecording = false;
            try { this.recognition.stop(); } catch (e) {}
            setTimeout(() => {
                this.isRecording = true;
                try { this.recognition.start(); } catch (e) {}
            }, 400);
        }
    }

    start() {
        if (!this.recognition) {
            this.onError('Speech Recognition not available. Use Google Chrome.');
            return;
        }
        this.isRecording = true;
        try {
            this.recognition.start();
            this._startAudioRecording();
        } catch (e) {
            console.error('Failed to start recognition:', e);
        }
    }

    stop() {
        this.isRecording = false;
        clearTimeout(this._restartTimer);
        if (this.recognition) {
            try { this.recognition.stop(); } catch (e) {}
        }
        this._stopAudioRecording();
        this.onStatusChange('stopped');
    }

    // ── Text-to-Speech ──
    // langCode: a full BCP-47 code like 'hi-IN', 'kn-IN', 'en-US'
    speak(text, langCode = 'en-US') {
        if (!window.speechSynthesis || !text) return;
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang   = langCode;
        utterance.rate   = 0.92;
        utterance.pitch  = 1;
        utterance.volume = 1;

        // Try to pick a voice that matches the language; fall back to any available voice
        const voices = window.speechSynthesis.getVoices();
        const matchingVoice =
            voices.find(v => v.lang === langCode) ||
            voices.find(v => v.lang.startsWith(langCode.split('-')[0])) ||
            voices.find(v => v.lang.startsWith('en'));
        if (matchingVoice) utterance.voice = matchingVoice;

        window.speechSynthesis.speak(utterance);
    }

    stopSpeaking() {
        if (window.speechSynthesis) window.speechSynthesis.cancel();
    }

    // ── Audio Recording (WebM backup) ──
    async _startAudioRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks   = [];
            this.mediaRecorder.ondataavailable = e => this.audioChunks.push(e.data);
            this.mediaRecorder.start(1000);
        } catch (e) {
            console.warn('Audio recording unavailable:', e);
        }
    }

    _stopAudioRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
            this.mediaRecorder.stream.getTracks().forEach(t => t.stop());
        }
    }

    downloadAudio() {
        if (!this.audioChunks.length) return;
        const blob = new Blob(this.audioChunks, { type: 'audio/webm' });
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = `consultation_audio_${Date.now()}.webm`;
        a.click();
        URL.revokeObjectURL(url);
    }

    // ── Static helpers ──
    static getLanguages() { return LANGUAGES; }

    static populateLanguageSelector(selectElement) {
        selectElement.innerHTML = '';
        for (const [key, lang] of Object.entries(LANGUAGES)) {
            const opt   = document.createElement('option');
            opt.value   = key;
            opt.textContent = `${lang.flag} ${lang.name}`;
            selectElement.appendChild(opt);
        }
    }
}

// Ensure Chrome lazy-loads voices before we need them
if (window.speechSynthesis) {
    window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
}
