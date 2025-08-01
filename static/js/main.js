document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const elements = {
        fileInput: document.getElementById('file-input'),
        dropZone: document.getElementById('drop-zone'),
        uploadSection: document.getElementById('upload-section'),
        processingSection: document.getElementById('processing-section'),
        resultsSection: document.getElementById('results-section'),
        vocalsPlayer: document.getElementById('vocals-player'),
        accompanimentPlayer: document.getElementById('accompaniment-player'),
        vocalsDownload: document.getElementById('vocals-download'),
        accompanimentDownload: document.getElementById('accompaniment-download'),
        newFileButton: document.getElementById('new-file'),
        historyList: document.getElementById('history-list'),
        downloadAllButton: document.getElementById('download-all'),
        downloadVocalsButton: document.getElementById('download-vocals'),
        downloadAccompanimentButton: document.getElementById('download-accompaniment'),
        clearHistoryButton: document.getElementById('clear-history'),
        separationMethod: document.getElementById('separation-method'),
        processFileButton: document.getElementById('process-file'),
        selectedFilename: document.getElementById('selected-filename')
    };

    // State
    let state = {
        selectedFile: null,
        isProcessing: false,
        currentUploadData: null
    };

    // Event Handlers
    function handleFileSelect() {
        const file = elements.fileInput.files[0];
        if (!file) return;

        if (!file.type.match('audio.*')) {
            alert('Please select an audio file (MP3 or WAV)');
            return;
        }

        state.selectedFile = file;
        elements.processFileButton.disabled = false;
        state.isProcessing = true;

        elements.selectedFilename.textContent = `Selected: ${file.name}`;
        elements.selectedFilename.classList.remove('hidden');

        uploadFile(file);
    }

    function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            state.currentUploadData = data;
            state.isProcessing = false;
        })
        .catch(error => {
            alert('Error: ' + error.message);
            elements.uploadSection.classList.remove('hidden');
            elements.processingSection.classList.add('hidden');
            state.isProcessing = false;
        });
    }

    async function processFile(filename, uniqueId) {
        try {
            elements.uploadSection.classList.add('hidden');
            elements.processingSection.classList.remove('hidden');
            
            const response = await fetch('/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename,
                    unique_id: uniqueId,
                    method: elements.separationMethod.value
                })
            });
            
            const data = await response.json();
            if (!data.success) throw new Error(data.error);
            return data;
        } catch (error) {
            console.error('Error:', error);
            throw error;
        }
    }

    function displayResults(data) {
        elements.vocalsPlayer.src = `/play/${data.vocals_path}`;
        elements.accompanimentPlayer.src = `/play/${data.accompaniment_path}`;
        elements.vocalsDownload.href = `/download/${data.vocals_path}`;
        elements.accompanimentDownload.href = `/download/${data.accompaniment_path}`;
        elements.processingSection.classList.add('hidden');
        elements.resultsSection.classList.remove('hidden');
    }

    function updateHistory() {
        fetch('/history')
            .then(() => window.location.reload())
            .catch(error => console.error('Error updating history:', error));
    }

    function resetUploadForm() {
        elements.uploadSection.classList.remove('hidden');
        elements.processingSection.classList.add('hidden');
        elements.resultsSection.classList.add('hidden');
        elements.fileInput.value = '';
        state.selectedFile = null;
        state.currentUploadData = null;
        elements.processFileButton.disabled = true;
        state.isProcessing = false;
        elements.selectedFilename.textContent = '';
        elements.selectedFilename.classList.add('hidden');
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

    elements.newFileButton.addEventListener('click', resetUploadForm);
    elements.processFileButton.addEventListener('click', () => {
        if (state.currentUploadData) {
            processFile(state.currentUploadData.filename, state.currentUploadData.unique_id)
                .then(data => {
                    displayResults(data);
                    updateHistory();
                    state.isProcessing = false;
                })
                .catch(error => {
                    alert('Error: ' + error.message);
                    elements.uploadSection.classList.remove('hidden');
                    elements.processingSection.classList.add('hidden');
                    state.isProcessing = false;
                });
        }
    });

    elements.downloadAllButton.addEventListener('click', () => window.location.href = '/download-all');
    elements.downloadVocalsButton.addEventListener('click', () => window.location.href = '/download-vocals');
    elements.downloadAccompanimentButton.addEventListener('click', () => window.location.href = '/download-accompaniment');

    elements.clearHistoryButton.addEventListener('click', () => {
        if (confirm('Are you sure you want to clear all history? This will delete all processed files.')) {
            fetch('/clear-history', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) window.location.reload();
                    else alert('Error clearing history: ' + data.error);
                })
                .catch(error => alert('Error clearing history: ' + error));
        }
    });

    document.querySelectorAll('.process-again-btn').forEach(button => {
        button.addEventListener('click', () => {
            const { filename, id: uniqueId } = button.dataset;
            elements.uploadSection.classList.add('hidden');
            elements.processingSection.classList.remove('hidden');
            window.scrollTo({ top: 0, behavior: 'smooth' });
            
            processFile(filename, uniqueId)
                .then(updateHistory)
                .catch(error => {
                    alert('Error: ' + error.message);
                    elements.uploadSection.classList.remove('hidden');
                    elements.processingSection.classList.add('hidden');
                });
        });
    });

    // Prevent leaving during processing
    window.addEventListener('beforeunload', (e) => {
        if (state.isProcessing) {
            e.preventDefault();
            e.returnValue = '';
            return 'You have files being processed. Are you sure you want to leave?';
        }
    });
}); 