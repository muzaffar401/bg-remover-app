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
const spinnerOverlay = document.querySelector('.spinner-overlay');
const processedSpinner = document.getElementById('processed-spinner');

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
        // Create an image to check dimensions
        const img = new Image();
        img.onload = function() {
            // Min and max allowed dimensions
            const minWidth = 500, minHeight = 500;
            const maxWidth = 1200, maxHeight = 1200;

            if (img.width < minWidth || img.height < minHeight) {
                showError(`Image is too small. Minimum size is ${minWidth}x${minHeight} pixels. Your image is ${img.width}x${img.height}.`);
                return;
            }
            if (img.width > maxWidth || img.height > maxHeight) {
                showError(`Image is too large. Maximum size is ${maxWidth}x${maxHeight} pixels. Your image is ${img.width}x${img.height}.`);
                return;
            }
            currentImage = e.target.result;
            originalImage.src = currentImage;
            imageComparison.style.display = 'block';
            showProcessedSpinner();
            processImage();
        };
        img.onerror = function() {
            showError('Invalid image file.');
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

// Show/hide processed image spinner
function showProcessedSpinner() {
    if (processedSpinner) {
        processedSpinner.style.display = 'flex';
    }
    if (processedImage) {
        processedImage.style.display = 'none';
    }
}
function hideProcessedSpinner() {
    if (processedSpinner) {
        processedSpinner.style.display = 'none';
    }
    if (processedImage) {
        processedImage.style.display = 'block';
    }
}

// Process image with current settings
async function processImage() {
    if (!currentImage) {
        showError('No image selected');
        return;
    }

    try {
        showProcessedSpinner();
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

        let data;
        try {
            data = await response.json();
        } catch (e) {
            throw new Error('Invalid response from server');
        }
        
        if (!response.ok) {
            throw new Error(data.detail || `Server error: ${response.status}`);
        }
        
        if (data.success) {
            processedImageData = data.image;
            processedImage.onload = () => {
                hideProcessedSpinner();
                processedImage.onload = null;
            };
            processedImage.src = processedImageData;
        } else {
            throw new Error(data.error || 'Failed to process image');
        }
    } catch (error) {
        showError(error.message);
        hideProcessedSpinner();
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

        if (!response.ok) {
            let errorMessage = 'Download failed';
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (e) {
                errorMessage = response.statusText || errorMessage;
            }
            throw new Error(errorMessage);
        }

        const blob = await response.blob();
        if (blob.size === 0) {
            throw new Error('Received empty file from server');
        }

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `processed_image.${format.toLowerCase()}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
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
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: #ff4444;
        color: white;
        padding: 15px 25px;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        z-index: 1000;
    `;
    document.body.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 5000);
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