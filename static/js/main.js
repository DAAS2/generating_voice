// DOM Elements
const videoForm = document.getElementById('videoForm');
const promptTextarea = document.getElementById('prompt');
const voiceSelect = document.getElementById('voice');
const backdropSelect = document.getElementById('backdrop');
const previewArea = document.getElementById('previewArea');
const loadingSpinner = document.getElementById('loadingSpinner');
const generateBtn = document.getElementById('generateBtn');
const topicInput = document.getElementById('topic');
const styleSelect = document.getElementById('style');
const lengthSelect = document.getElementById('length');

// Batch Generation Buttons
const generateBatch10Btn = document.getElementById('generateBatch10Btn');
const generateBatch20Btn = document.getElementById('generateBatch20Btn');

// Generate AI Prompt
async function generateAIPrompt() {
    const topic = topicInput.value.trim();
    if (!topic) {
        showToast('Please enter a topic!', 'warning');
        return;
    }
    
    try {
        // Show loading state
        const generateBtn = document.querySelector('#topic').nextElementSibling;
        const originalText = generateBtn.innerHTML;
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Generating...';
        
        const response = await fetch('/generate-prompt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                topic: topic,
                style: styleSelect.value,
                length: lengthSelect.value
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Update textarea with generated prompt
        promptTextarea.value = data.prompt;
        showToast('Script generated successfully!', 'success');
        
    } catch (error) {
        showToast(error.message || 'Failed to generate script', 'error');
    } finally {
        // Reset button state
        generateBtn.disabled = false;
        generateBtn.innerHTML = originalText;
    }
}

// Copy to Clipboard Function
function copyToClipboard() {
    const text = promptTextarea.value;
    if (!text) {
        showToast('No text to copy!', 'warning');
        return;
    }
    
    navigator.clipboard.writeText(text).then(() => {
        showToast('Text copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy text', 'error');
    });
}

// Play Voice Preview
function playVoice() {
    const selectedVoice = voiceSelect.value;
    if (!selectedVoice) {
        showToast('Please select a voice first!', 'warning');
        return;
    }
    
    // Create audio element
    const audio = new Audio(`/audios/${selectedVoice}`);
    audio.className = 'audio-preview';
    
    // Clear and show preview
    previewArea.innerHTML = '';
    previewArea.appendChild(audio);
    
    // Play audio
    audio.play().catch(() => {
        showToast('Failed to play voice preview', 'error');
    });
}

// Preview Backdrop
function previewBackdrop() {
    const selectedBackdrop = backdropSelect.value;
    if (!selectedBackdrop) {
        showToast('Please select a backdrop first!', 'warning');
        return;
    }
    
    // Create video preview
    const videoPreview = document.createElement('video');
    videoPreview.src = `/downloads/${selectedBackdrop}`;
    videoPreview.controls = true;
    videoPreview.className = 'video-preview fade-in';
    videoPreview.muted = false;
    
    // Clear and show preview
    previewArea.innerHTML = '';
    previewArea.appendChild(videoPreview);
    
    // Play video
    videoPreview.play().catch(() => {
        showToast('Failed to play backdrop preview', 'error');
    });
}

// Show Toast Notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0 position-fixed bottom-0 end-0 m-3`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Handle Form Submission
videoForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Validate form
    if (!promptTextarea.value || !voiceSelect.value || !backdropSelect.value) {
        showToast('Please fill in all fields!', 'warning');
        return;
    }
    
    // Show loading state
    generateBtn.disabled = true;
    loadingSpinner.classList.remove('d-none');
    previewArea.innerHTML = '';
    
    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: promptTextarea.value,
                voice: voiceSelect.value,
                backdrop: backdropSelect.value
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Show generated video
        const video = document.createElement('video');
        video.src = data.video_url;
        video.controls = true;
        video.className = 'video-preview fade-in';
        video.autoplay = true;
        
        // Add download button
        const downloadBtn = document.createElement('a');
        downloadBtn.href = data.video_url;
        downloadBtn.download = 'generated_video.mp4';
        downloadBtn.className = 'btn btn-success mt-3';
        downloadBtn.innerHTML = '<i class="fas fa-download me-2"></i>Download Video';
        
        previewArea.innerHTML = '';
        previewArea.appendChild(video);
        previewArea.appendChild(downloadBtn);
        
        showToast('Video generated successfully!', 'success');
        
    } catch (error) {
        showToast(error.message || 'Failed to generate video', 'error');
    } finally {
        // Reset loading state
        generateBtn.disabled = false;
        loadingSpinner.classList.add('d-none');
    }
});

// Add input validation
promptTextarea.addEventListener('input', () => {
    if (promptTextarea.value.length > 1000) {
        showToast('Script is too long! Maximum 1000 characters.', 'warning');
        promptTextarea.value = promptTextarea.value.slice(0, 1000);
    }
});

async function handleBatchGenerate(count) {
    // Validate form
    if (!voiceSelect.value || !backdropSelect.value) {
        showToast('Please select a voice and backdrop!', 'warning');
        return;
    }
    generateBatch10Btn.disabled = true;
    generateBatch20Btn.disabled = true;
    loadingSpinner.classList.remove('d-none');
    previewArea.innerHTML = '';
    try {
        const response = await fetch('/generate-batch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                count: count,
                voice: voiceSelect.value,
                backdrop: backdropSelect.value,
                prompt: promptTextarea.value // Use current script if set, else backend will randomize
            })
        });
        const data = await response.json();
        if (data.error) throw new Error(data.error);
        // Show download links for all videos
        previewArea.innerHTML = '<h5 class="mb-3">Batch Videos</h5>';
        data.video_urls.forEach((url, idx) => {
            const link = document.createElement('a');
            link.href = url;
            link.download = `batch_video_${idx+1}.mp4`;
            link.className = 'btn btn-success m-1';
            link.innerHTML = `<i class='fas fa-download me-1'></i>Download Video ${idx+1}`;
            previewArea.appendChild(link);
        });
        showToast('Batch videos generated successfully!', 'success');
    } catch (error) {
        showToast(error.message || 'Batch generation failed', 'error');
    } finally {
        generateBatch10Btn.disabled = false;
        generateBatch20Btn.disabled = false;
        loadingSpinner.classList.add('d-none');
    }
}

generateBatch10Btn.addEventListener('click', () => handleBatchGenerate(10));
generateBatch20Btn.addEventListener('click', () => handleBatchGenerate(20)); 