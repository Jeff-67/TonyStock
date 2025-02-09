document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const audioFileInput = document.getElementById('audioFile');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const transcriptsList = document.getElementById('transcriptsList');
    const fullTextContent = document.getElementById('fullTextContent');
    const timestampsContent = document.getElementById('timestampsContent');
    const fullTextTab = document.getElementById('fullTextTab');
    const timestampsTab = document.getElementById('timestampsTab');

    // Tab switching logic
    fullTextTab.addEventListener('click', () => {
        fullTextTab.classList.add('border-blue-500', 'text-blue-600');
        fullTextTab.classList.remove('border-transparent', 'text-gray-500');
        timestampsTab.classList.remove('border-blue-500', 'text-blue-600');
        timestampsTab.classList.add('border-transparent', 'text-gray-500');
        fullTextContent.classList.remove('hidden');
        timestampsContent.classList.add('hidden');
    });

    timestampsTab.addEventListener('click', () => {
        timestampsTab.classList.add('border-blue-500', 'text-blue-600');
        timestampsTab.classList.remove('border-transparent', 'text-gray-500');
        fullTextTab.classList.remove('border-blue-500', 'text-blue-600');
        fullTextTab.classList.add('border-transparent', 'text-gray-500');
        timestampsContent.classList.remove('hidden');
        fullTextContent.classList.add('hidden');
    });

    // Add file selection handler
    audioFileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        const fileLabel = this.parentElement.querySelector('p');
        if (file) {
            console.log('File selected:', file.name);
            fileLabel.textContent = file.name;
            fileLabel.classList.remove('text-gray-400');
            fileLabel.classList.add('text-blue-500');
        } else {
            fileLabel.textContent = 'Select audio file';
            fileLabel.classList.remove('text-blue-500');
            fileLabel.classList.add('text-gray-400');
        }
    });

    // Load existing transcripts on page load
    loadTranscripts();

    // Handle form submission
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const file = audioFileInput.files[0];
        if (!file) {
            alert('Please select an audio file first.');
            return;
        }

        // Show loading overlay
        loadingOverlay.classList.remove('hidden');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                // Clear file input
                audioFileInput.value = '';

                // Reload transcripts
                loadTranscripts();

                // Display the new transcript
                displayTranscript(result.transcript);
            } else {
                alert(result.error || 'Failed to transcribe audio');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while transcribing the audio');
        } finally {
            // Hide loading overlay
            loadingOverlay.classList.add('hidden');
        }
    });

    async function loadTranscripts() {
        try {
            const response = await fetch('/transcripts');
            const data = await response.json();

            // Clear existing list
            transcriptsList.innerHTML = '';

            // Create transcript list items
            data.transcripts.forEach((transcript) => {
                const div = document.createElement('div');
                div.className = 'p-3 hover:bg-gray-100 cursor-pointer border-b';

                // Format timestamp
                const timestamp = new Date(transcript.created_at).toLocaleString();

                // Create display name from original filename
                const displayName = transcript.original_filename.replace(/^\d{8}_\d{6}_/, '');

                // Format duration
                const duration = formatDuration(transcript.duration);

                div.innerHTML = `
                    <div class="font-medium text-gray-800">${displayName}</div>
                    <div class="text-sm text-gray-500">${timestamp}</div>
                    <div class="text-xs text-gray-400 mt-1">
                        <span class="uppercase">${transcript.language}</span> • ${duration}
                    </div>
                    <div class="text-sm text-gray-600 mt-2 line-clamp-2">${transcript.text_preview}</div>
                `;

                div.addEventListener('click', () => {
                    loadAndDisplayTranscript(transcript.id);
                });

                transcriptsList.appendChild(div);
            });
        } catch (error) {
            console.error('Error loading transcripts:', error);
        }
    }

    async function loadAndDisplayTranscript(transcriptId) {
        try {
            const response = await fetch(`/transcripts/${transcriptId}`);
            const transcript = await response.json();
            displayTranscript(transcript);
        } catch (error) {
            console.error('Error loading transcript:', error);
        }
    }

    function displayTranscript(transcript) {
        // Update full text content
        fullTextContent.innerHTML = `
            <div class="mb-4">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <h3 class="text-lg font-medium text-gray-800">${transcript.original_filename}</h3>
                        <div class="text-sm text-gray-500 mt-1">
                            Created: ${new Date(transcript.created_at).toLocaleString()}
                        </div>
                    </div>
                    <div class="text-right text-sm text-gray-500">
                        <div>Language: <span class="uppercase">${transcript.metadata.language}</span></div>
                        <div>Duration: ${formatDuration(transcript.metadata.duration)}</div>
                    </div>
                </div>

                <!-- Download buttons -->
                <div class="flex gap-4 mb-4">
                    <a href="/download/transcript/${transcript.id}"
                       class="inline-flex items-center px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd" />
                        </svg>
                        Download Transcript
                    </a>
                    <a href="/download/audio/${encodeURIComponent(transcript.audio_file.split('/').pop())}"
                       class="inline-flex items-center px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-opacity-50">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" />
                        </svg>
                        Download Audio
                    </a>
                </div>

                <div class="bg-gray-50 rounded-lg p-4">
                    <p class="text-gray-600 whitespace-pre-wrap">${transcript.text}</p>
                </div>
            </div>
        `;

        // Update timestamped content
        timestampsContent.innerHTML = `
            <div class="mb-4">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <h3 class="text-lg font-medium text-gray-800">${transcript.original_filename}</h3>
                        <div class="text-sm text-gray-500 mt-1">
                            Created: ${new Date(transcript.created_at).toLocaleString()}
                        </div>
                    </div>
                    <div class="text-right text-sm text-gray-500">
                        <div>Language: <span class="uppercase">${transcript.metadata.language}</span></div>
                        <div>Duration: ${formatDuration(transcript.metadata.duration)}</div>
                    </div>
                </div>

                <!-- Download buttons -->
                <div class="flex gap-4 mb-4">
                    <a href="/download/transcript/${transcript.id}"
                       class="inline-flex items-center px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd" />
                        </svg>
                        Download Transcript
                    </a>
                    <a href="/download/audio/${encodeURIComponent(transcript.audio_file.split('/').pop())}"
                       class="inline-flex items-center px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-opacity-50">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" />
                        </svg>
                        Download Audio
                    </a>
                </div>

                <div class="bg-gray-50 rounded-lg p-4 space-y-2">
                    ${transcript.segments.map(segment => {
                        const start = formatTimestamp(segment.start);
                        const end = formatTimestamp(segment.end);
                        return `<div class="flex">
                            <span class="text-gray-500 font-mono whitespace-nowrap mr-4">[${start} → ${end}]</span>
                            <span class="text-gray-600">${segment.text.trim()}</span>
                        </div>`;
                    }).join('')}
                </div>
            </div>
        `;

        // Highlight selected transcript in sidebar
        const items = transcriptsList.getElementsByTagName('div');
        for (let item of items) {
            item.classList.remove('bg-blue-50');
            if (item.textContent.includes(transcript.original_filename)) {
                item.classList.add('bg-blue-50');
            }
        }
    }

    function formatDuration(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    function formatTimestamp(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = (seconds % 60).toFixed(3);
        return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.padStart(6, '0')}`;
    }
});
