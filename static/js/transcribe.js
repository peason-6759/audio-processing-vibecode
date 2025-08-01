document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const elements = {
        fileInput: document.getElementById('file-input'),
        dropZone: document.getElementById('drop-zone'),
        uploadSection: document.getElementById('upload-section'),
        processingSection: document.getElementById('processing-section'),
        resultsSection: document.getElementById('results-section'),
        transcribeButton: document.getElementById('transcribe-button'),
        newFileButton: document.getElementById('new-file'),
        copyButton: document.getElementById('copy-button'),
        selectedFilename: document.getElementById('selected-filename'),
        transcriptionText: document.getElementById('transcription-text'),
        languageSelect: document.getElementById('language')
    };

    // State
    let state = {
        selectedFile: null,
        isProcessing: false
    };

    // Event Handlers
    function handleFileSelect() {
        const file = elements.fileInput.files[0];
        if (!file) return;

        if (!file.type.match('audio.*')) {
            alert('Please select an audio file (MP3, WAV, etc.)');
            return;
        }

        state.selectedFile = file;
        elements.transcribeButton.disabled = false;
        elements.selectedFilename.textContent = `Selected: ${file.name}`;
        elements.selectedFilename.classList.remove('hidden');
    }

    async function transcribeAudio() {
        if (!state.selectedFile) return;

        const formData = new FormData();
        formData.append('file', state.selectedFile);
        formData.append('language', elements.languageSelect.value);

        try {
            elements.uploadSection.classList.add('hidden');
            elements.processingSection.classList.remove('hidden');
            state.isProcessing = true;

            const response = await fetch('/transcribe', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (data.error) throw new Error(data.error);

            elements.processingSection.classList.add('hidden');
            elements.resultsSection.classList.remove('hidden');
            elements.transcriptionText.textContent = data.text;
            state.isProcessing = false;
        } catch (error) {
            alert('Error: ' + error.message);
            elements.uploadSection.classList.remove('hidden');
            elements.processingSection.classList.add('hidden');
            state.isProcessing = false;
        }
    }

    function resetForm() {
        elements.uploadSection.classList.remove('hidden');
        elements.processingSection.classList.add('hidden');
        elements.resultsSection.classList.add('hidden');
        elements.fileInput.value = '';
        elements.transcribeButton.disabled = true;
        elements.selectedFilename.textContent = '';
        elements.selectedFilename.classList.add('hidden');
        state.selectedFile = null;
        state.isProcessing = false;
    }

    function copyToClipboard() {
        const text = elements.transcriptionText.textContent;
        navigator.clipboard.writeText(text)
            .then(() => alert('Text copied to clipboard!'))
            .catch(err => alert('Failed to copy text: ' + err));
    }

    // Event Listeners
    elements.fileInput.addEventListener('change', handleFileSelect);
    elements.dropZone.addEventListener('click', () => elements.fileInput.click());
    elements.dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.dropZone.classList.add('border-blue-500');
    });
    elements.dropZone.addEventListener('dragleave', () => {
        elements.dropZone.classList.remove('border-blue-500');
    });
    elements.dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.dropZone.classList.remove('border-blue-500');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            elements.fileInput.files = files;
            handleFileSelect();
        }
    });

    elements.transcribeButton.addEventListener('click', transcribeAudio);
    elements.newFileButton.addEventListener('click', resetForm);
    elements.copyButton.addEventListener('click', copyToClipboard);

    // Prevent leaving during processing
    window.addEventListener('beforeunload', (e) => {
        if (state.isProcessing) {
            e.preventDefault();
            e.returnValue = '';
            return 'You have files being processed. Are you sure you want to leave?';
        }
    });
}); 