// DOM Elements
const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');
const originalImage = document.getElementById('original-image');
const processedImage = document.getElementById('processed-image');
const imageComparison = document.querySelector('.image-comparison');
const processingStatus = document.querySelector('.processing-status');
const progressBar = document.querySelector('.progress');
const statusText = document.querySelector('.status-text');
const downloadBtn = document.getElementById('download-btn');
const bgTypeSelect = document.getElementById('bg-type');
const bgColorOptions = document.getElementById('bg-color-options');
const bgGradientOptions = document.getElementById('bg-gradient-options');
const bgImageOptions = document.getElementById('bg-image-options');

// State
let currentImage = null;
let processedImageData = null;

// Event Listeners
uploadArea.addEventListener('click', () => fileInput.click());
uploadArea.addEventListener('dragover', handleDragOver);
uploadArea.addEventListener('drop', handleDrop);
fileInput.addEventListener('change', handleFileSelect);
bgTypeSelect.addEventListener('change', handleBackgroundTypeChange);
downloadBtn.addEventListener('click', handleDownload);

// Initialize slider values
document.querySelectorAll('.slider-group input[type="range"]').forEach(slider => {
    const valueDisplay = slider.nextElementSibling;
    slider.addEventListener('input', () => {
        valueDisplay.textContent = slider.value;
    });
});

// Handle drag and drop
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.add('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

// Handle file selection
function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

// Process selected file
function handleFile(file) {
    if (!file.type.match('image.*')) {
        showError('Please select an image file');
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        currentImage = e.target.result;
        originalImage.src = currentImage;
        imageComparison.style.display = 'block';
        processImage();
    };
    reader.readAsDataURL(file);
}

// Process image with current settings
async function processImage() {
    if (!currentImage) {
        showError('No image selected');
        return;
    }

    try {
        showProcessingStatus();
        
        const settings = getSettings();
        const response = await fetch('/api/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image: currentImage,
                settings: settings
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (data.success) {
            processedImageData = data.image;
            processedImage.src = processedImageData;
            hideProcessingStatus();
        } else {
            throw new Error(data.error || 'Failed to process image');
        }
    } catch (error) {
        showError(error.message);
        hideProcessingStatus();
    }
}

// Handle background image selection
function handleBackgroundImageSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.type.match('image.*')) {
        showError('Please select an image file for background');
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        const bgPreview = document.getElementById('bg-preview');
        bgPreview.innerHTML = `<img src="${e.target.result}" alt="Background Preview">`;
        // Store the background image data
        document.getElementById('bg-image').dataset.imageData = e.target.result;
    };
    reader.readAsDataURL(file);
}

// Get current settings
function getSettings() {
    const settings = {
        quality: document.getElementById('quality-select')?.value || 'Ultra HD',
        edge_refinement: document.getElementById('edge-refinement')?.checked || true,
        preserve_details: document.getElementById('preserve-details')?.checked || true,
        upscale_small: document.getElementById('upscale-small')?.checked || false,
        enhance_details: document.getElementById('enhance-details')?.checked || true,
        super_resolution: document.getElementById('super-resolution')?.checked || false,
        background_type: document.getElementById('bg-type')?.value || 'Transparent',
        bg_color: document.getElementById('bg-color')?.value || '#FFFFFF',
        gradient_start: document.getElementById('gradient-start')?.value || '#4CAF50',
        gradient_end: document.getElementById('gradient-end')?.value || '#2196F3',
        matting_foreground: parseInt(document.getElementById('foreground-threshold')?.value || '240'),
        matting_background: parseInt(document.getElementById('background-threshold')?.value || '10'),
        matting_erode: parseInt(document.getElementById('edge-refinement-size')?.value || '15')
    };

    // Add background image data if available
    const bgImageInput = document.getElementById('bg-image');
    if (bgImageInput?.dataset.imageData) {
        settings.bg_image = bgImageInput.dataset.imageData;
    }

    return settings;
}

// Handle background type change
function handleBackgroundTypeChange() {
    const type = bgTypeSelect.value;
    
    // Hide all options
    bgColorOptions.style.display = 'none';
    bgGradientOptions.style.display = 'none';
    bgImageOptions.style.display = 'none';
    
    // Show selected option
    switch (type) {
        case 'Color':
            bgColorOptions.style.display = 'block';
            break;
        case 'Gradient':
            bgGradientOptions.style.display = 'block';
            break;
        case 'Image':
            bgImageOptions.style.display = 'block';
            break;
    }
}

// Handle download
async function handleDownload() {
    if (!processedImageData) {
        showError('No processed image available');
        return;
    }

    try {
        const format = document.querySelector('input[name="format"]:checked').value;
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image: processedImageData,
                format: format
            })
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `processed_image.${format.toLowerCase()}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } else {
            throw new Error('Download failed');
        }
    } catch (error) {
        showError(error.message);
    }
}

// Show processing status
function showProcessingStatus() {
    processingStatus.style.display = 'block';
    progressBar.style.width = '0%';
    statusText.textContent = 'Processing image...';
    
    // Simulate progress
    let progress = 0;
    const interval = setInterval(() => {
        progress += 5;
        if (progress <= 90) {
            progressBar.style.width = `${progress}%`;
        } else {
            clearInterval(interval);
        }
    }, 200);
}

// Hide processing status
function hideProcessingStatus() {
    processingStatus.style.display = 'none';
    progressBar.style.width = '0%';
}

// Show error message
function showError(message) {
    alert(message);
}

// Initialize comparison slider
function initComparisonSlider() {
    const slider = document.querySelector('.comparison-slider');
    const handle = document.querySelector('.slider-handle');
    const container = document.querySelector('.comparison-container');
    let isDragging = false;

    handle.addEventListener('mousedown', () => {
        isDragging = true;
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        
        const rect = slider.getBoundingClientRect();
        const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
        const percentage = (x / rect.width) * 100;
        
        handle.style.left = `${percentage}%`;
        container.style.clipPath = `inset(0 ${100 - percentage}% 0 0)`;
    });

    document.addEventListener('mouseup', () => {
        isDragging = false;
    });
}

// Initialize the application
function init() {
    initComparisonSlider();
    
    // Add event listener for background image selection
    const bgImageInput = document.getElementById('bg-image');
    if (bgImageInput) {
        bgImageInput.addEventListener('change', handleBackgroundImageSelect);
    }
}

// Start the application
init(); 