// Global variable to store current post data
let currentPostData = null;
let selectedPlatform = 'instagram'; // Default platform

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    loadStatistics();
    loadBrands();
    setupEventListeners();
    setupPlatformButtons();
});

// Load brands from API
async function loadBrands() {
    try {
        const response = await fetch('/api/brands/list');
        const data = await response.json();
        
        const brandSelect = document.getElementById('brandSelect');
        if (data.success && data.brands && data.brands.length > 0) {
            brandSelect.innerHTML = '<option value="">Use Active Brand</option>';
            
            data.brands.forEach(brand => {
                const option = document.createElement('option');
                option.value = brand.id;
                option.textContent = `${brand.brand_name}${brand.is_active ? ' (Active)' : ''}`;
                if (brand.is_active) {
                    option.selected = true;
                }
                brandSelect.appendChild(option);
            });
        } else {
            brandSelect.innerHTML = '<option value="">No brands available - Create one first</option>';
        }
    } catch (error) {
        console.error('Error loading brands:', error);
        const brandSelect = document.getElementById('brandSelect');
        brandSelect.innerHTML = '<option value="">Error loading brands</option>';
    }
}

// Setup event listeners
function setupEventListeners() {
    const generateBtn = document.getElementById('generateBtn');
    generateBtn.addEventListener('click', generatePost);
}

// Setup platform button listeners
function setupPlatformButtons() {
    const platformButtons = document.querySelectorAll('.platform-btn');
    
    platformButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons
            platformButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            button.classList.add('active');
            
            // Update selected platform
            selectedPlatform = button.getAttribute('data-platform');
            
            console.log(`Platform selected: ${selectedPlatform}`);
        });
    });
}

// Load statistics from API
async function loadStatistics() {
    try {
        const response = await fetch('/statistics');
        const stats = response.json();
        
        stats.then(data => {
            const statsElement = document.getElementById('statistics');
            statsElement.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; text-align: left;">
                    <div>
                        <div style="font-size: 11px; opacity: 0.8; margin-bottom: 3px;">Total Documents</div>
                        <div style="font-size: 18px; font-weight: 600;">${data.total_documents}</div>
                    </div>
                    <div>
                        <div style="font-size: 11px; opacity: 0.8; margin-bottom: 3px;">Trending Keywords</div>
                        <div style="font-size: 18px; font-weight: 600;">${data.trending_keywords}</div>
                    </div>
                    <div>
                        <div style="font-size: 11px; opacity: 0.8; margin-bottom: 3px;">Hashtag Knowledge</div>
                        <div style="font-size: 18px; font-weight: 600;">${data.hashtag_knowledge}</div>
                    </div>
                    <div>
                        <div style="font-size: 11px; opacity: 0.8; margin-bottom: 3px;">LLM Model</div>
                        <div style="font-size: 14px; font-weight: 600;">${data.llm_model || 'N/A'}</div>
                    </div>
                </div>
            `;
        });
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// Generate post
async function generatePost() {
    const generateBtn = document.getElementById('generateBtn');
    const btnText = generateBtn.querySelector('.btn-text');
    const btnLoader = generateBtn.querySelector('.btn-loader');
    const postContainer = document.getElementById('postContainer');
    const errorContainer = document.getElementById('errorContainer');
    
    // Hide previous results
    postContainer.style.display = 'none';
    errorContainer.style.display = 'none';
    
    // Show loading state
    generateBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline-flex';
    
    try {
        // Get selected brand ID
        const brandSelect = document.getElementById('brandSelect');
        const brandId = brandSelect.value ? parseInt(brandSelect.value) : null;
        
        const response = await fetch('/generate-post', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                keyword: null, // Random keyword
                brand_id: brandId,
                platform: selectedPlatform
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        currentPostData = data;
        console.log('Generated Post Data:', data);
        // Display the post
        displayPost(data);
        
        // Scroll to post
        setTimeout(() => {
            postContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 300);
        
    } catch (error) {
        console.error('Error generating post:', error);
        showError(error.message);
    } finally {
        // Reset button state
        generateBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
}

// Display post
function displayPost(data) {
    const postContainer = document.getElementById('postContainer');
    const imageContainer = document.getElementById('imageContainer');
    
    // Log the received data for debugging
    console.log('Display Post - Platform received:', data.platform);
    console.log('Display Post - Selected platform:', selectedPlatform);
    
    // Update caption
    document.getElementById('captionText').textContent = data.caption;
    
    // Update hashtags
    document.getElementById('hashtagsText').textContent = data.hashtags.join(' ');
    
    // Update metadata - use the platform from response data
    const platformDisplay = (data.platform || selectedPlatform || 'instagram').toUpperCase();
    console.log('Displaying platform as:', platformDisplay);
    document.getElementById('platformText').textContent = platformDisplay;
    document.getElementById('keywordText').textContent = data.keyword;
    document.getElementById('visualStyleText').textContent = data.visual_style;
    document.getElementById('imagePromptText').textContent = data.image_prompt;
    document.getElementById('methodText').textContent = data.generation_method;
    
    // Update timestamp
    const timestamp = new Date(data.timestamp);
    document.getElementById('postTime').textContent = formatTimestamp(timestamp);
    
    // Handle image
    if (data.image_base64) {
        imageContainer.innerHTML = `
            <img src="data:image/png;base64,${data.image_base64}" alt="Generated coffee image">
        `;
    } else {
        imageContainer.innerHTML = `
            <div class="placeholder-image">
                <span class="placeholder-icon">🖼️</span>
                <p>Image prompt generated successfully</p>
                <p class="placeholder-subtitle">Use the prompt below with any image generation tool</p>
            </div>
        `;
    }
    
    // Store context_snippets for regeneration (important for RAG consistency)
    if (data.context_snippets && data.context_snippets.length > 0) {
        currentPostData.context_snippets = data.context_snippets;
        console.log(`Stored ${data.context_snippets.length} context snippets for regeneration`);
    }
    
    // Show post
    postContainer.style.display = 'block';
}

// Show error
function showError(message) {
    const errorContainer = document.getElementById('errorContainer');
    const errorMessage = document.getElementById('errorMessage');
    
    errorMessage.textContent = message || 'An unexpected error occurred. Please try again.';
    errorContainer.style.display = 'block';
    
    // Scroll to error
    setTimeout(() => {
        errorContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 300);
}

// Format timestamp
function formatTimestamp(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
}

// Copy caption to clipboard
function copyToClipboard() {
    if (!currentPostData) return;
    
    const textToCopy = currentPostData.full_caption;
    
    navigator.clipboard.writeText(textToCopy).then(() => {
        showNotification('Caption copied to clipboard! ✅');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showNotification('Failed to copy caption ❌');
    });
}

// Copy image prompt to clipboard
function copyImagePrompt() {
    if (!currentPostData) return;
    
    const textToCopy = currentPostData.image_prompt;
    
    navigator.clipboard.writeText(textToCopy).then(() => {
        showNotification('Image prompt copied to clipboard! ✅');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showNotification('Failed to copy image prompt ❌');
    });
}

// Download post as JSON
function downloadPost() {
    if (!currentPostData) return;
    
    const dataStr = JSON.stringify(currentPostData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `coffee_post_${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showNotification('Post data downloaded! 💾');
}

// Regenerate image with new prompt
async function regenerateImage() {
    if (!currentPostData) {
        showNotification('No post available to regenerate ❌');
        return;
    }
    
    const regenerateBtn = document.getElementById('regenerateImageBtn');
    const btnText = regenerateBtn.querySelector('.btn-text');
    const btnLoader = regenerateBtn.querySelector('.btn-loader');
    const imageContainer = document.getElementById('imageContainer');
    
    // Show loading state
    regenerateBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline-flex';
    
    try {
        const response = await fetch('/regenerate-image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                keyword: currentPostData.keyword,
                caption: currentPostData.caption,
                context_snippets: currentPostData.context_snippets || []  // Send RAG context
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Regenerated image data:', data);
        
        // Update current post data with new values
        currentPostData.image_prompt = data.image_prompt;
        currentPostData.image_base64 = data.image_base64;
        currentPostData.visual_style = data.visual_style;
        
        // Update image display
        if (data.image_base64) {
            imageContainer.innerHTML = `
                <img src="data:image/png;base64,${data.image_base64}" alt="Generated coffee image">
            `;
        } else {
            imageContainer.innerHTML = `
                <div class="placeholder-image">
                    <span class="placeholder-icon">🖼️</span>
                    <p>New image prompt generated</p>
                    <p class="placeholder-subtitle">Use the prompt below with any image generation tool</p>
                </div>
            `;
        }
        
        // Update metadata display
        document.getElementById('imagePromptText').textContent = data.image_prompt;
        document.getElementById('visualStyleText').textContent = data.visual_style;
        
        // Show success notification
        showNotification('Image regenerated successfully! 🎨');
        
    } catch (error) {
        console.error('Error regenerating image:', error);
        showNotification('Failed to regenerate image ❌');
    } finally {
        // Reset button state
        regenerateBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
}

// Show notification
function showNotification(message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #6f4e37;
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        z-index: 1000;
        animation: slideIn 0.3s ease;
        font-weight: 500;
    `;
    notification.textContent = message;
    
    // Add animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
            document.head.removeChild(style);
        }, 300);
    }, 3000);
}
